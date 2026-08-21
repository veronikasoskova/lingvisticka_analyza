"""B.F. Skinner — Verbal Behavior classifier and training helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import pandas as pd
import scipy.sparse
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import Pipeline
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder
import joblib

from a_paths import DATA_DIR, MODELS_DIR, OUTPUT_DIR
from c_input import TextInput, create_input_from_text
from d_preprocessing import preprocess_text
from e_extraction import extract_features, SentenceFeatures
from f_semantics import semantic_enrichment, SemanticFeatures
import g_skinner_rules as rules


# ==========================================================
# F1. PATHS / CONFIG
# ==========================================================

DATA_PATH      = DATA_DIR / "annotated_skinner.csv"
SEED_PATH      = DATA_DIR / "annotated_skinner_seed.csv"
MODEL_DIR      = MODELS_DIR
EVAL_OUT       = OUTPUT_DIR / "eval_rule_classifier.csv"
TARGET_COLUMN  = "skinner_class"

# Categorical and boolean feature columns used by build_feature_transformer().
CAT_COLS: list[str] = [
    "source", "stimulus", "local_pattern", "semantic_cluster", "control_role",
]
BOOL_COLS: list[str] = [
    "is_imperative_like", "has_negation", "has_modal", "has_question",
    "subject_present", "has_verbum_dicendi", "previous_was_trigger",
]


# ==========================================================
# F1b. CONFIDENCE CALIBRATION
# ==========================================================
#
# Confidence values are no longer hardcoded at every call site.
# _PROXY_CONFIDENCE_DEFAULTS holds the author-estimated priors.
# calibrate_confidence() updates _CONFIDENCE_CALIBRATION in-place from
# an annotated CSV once it becomes available, using an accuracy-weighted
# blend: 30 % prior + 70 % empirical accuracy (min. 3 annotated examples).

_PROXY_CONFIDENCE_DEFAULTS: dict[str, float] = {
    "mand_like":                    0.70,
    "reported_textual_proxy":       0.65,
    "textual_trigger":              0.55,
    "citation_chain_proxy":         0.60,
    "visual_tact_proxy":            0.60,
    "revelation_tact_proxy":        0.60,
    "descriptive_proxy":            0.60,
    "echoic_proxy":                 0.55,
    "intraverbal_trigger":          0.55,
    "intraverbal_proxy":            0.65,
    "negation_autoclitic_proxy":    0.60,
    "uncertainty_autoclitic_proxy": 0.60,
    "emphasis_autoclitic_proxy":    0.60,
    "source_autoclitic_proxy":      0.60,
    "relation_autoclitic_proxy":    0.60,
    "autoclitic_proxy":             0.60,
    "carry_over_tact_proxy":        0.55,
    "dialogue_chain_proxy":         0.55,
    "written_record":               0.55,
    "uncertain":                    0.30,
}

_CONFIDENCE_CALIBRATION: dict[str, float] = dict(_PROXY_CONFIDENCE_DEFAULTS)


def get_confidence(proxy_subtype: str) -> float:
    """Return the (possibly calibrated) confidence for a proxy_subtype."""
    return _CONFIDENCE_CALIBRATION.get(proxy_subtype, 0.50)


def calibrate_confidence(data_path: Path = DATA_PATH) -> None:
    """
    Update _CONFIDENCE_CALIBRATION from an annotated CSV (in-place).

    Expects columns: sentence, source, stimulus, label (= true proxy_subtype).
    Runs apply_skinner_rules() on each row, compares predicted proxy_subtype
    to the annotated label, and computes per-class accuracy.

    Blending formula: 0.3 * prior + 0.7 * empirical_accuracy
    Applied only when a class has ≥ 3 annotated examples.

    Safe to call even if data_path doesn't exist — keeps defaults.
    """
    if not data_path.exists():
        return

    try:
        df = pd.read_csv(data_path)
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning(
            "Could not load calibration CSV %s: %s", data_path, exc
        )
        return

    if "sentence" not in df.columns or "label" not in df.columns:
        return

    from collections import defaultdict
    correct: dict[str, int] = defaultdict(int)
    total:   dict[str, int] = defaultdict(int)

    for _, row in df.iterrows():
        true_label = str(row.get("label", ""))
        if not true_label or pd.isna(row.get("label")):
            continue
        try:
            inp = create_input_from_text(
                text=str(row["sentence"]),
                source=str(row.get("source", "written_record")),
                stimulus=str(row.get("stimulus", "unknown")),
            )
            decisions = apply_skinner_rules(inp)
            if not decisions:
                continue
            predicted = decisions[0].proxy_subtype
            total[true_label] += 1
            if predicted == true_label:
                correct[true_label] += 1
        except Exception:
            continue

    for subtype, n in total.items():
        if n < 3:
            continue
        empirical = correct[subtype] / n
        prior     = _PROXY_CONFIDENCE_DEFAULTS.get(subtype, 0.50)
        _CONFIDENCE_CALIBRATION[subtype] = round(0.30 * prior + 0.70 * empirical, 3)
        print(f"  calibrated {subtype:<30} n={n:>4}  acc={empirical:.2f}  → conf={_CONFIDENCE_CALIBRATION[subtype]:.3f}")


# ==========================================================
# F2. OUTPUT DATA STRUCTURE
# ==========================================================

@dataclass
class SkinnerDecision:
    sentence_id: int
    sentence: str

    # Skinner family / super-class.
    skinner_class: str

    # Text-adapted proxy subtype.
    proxy_subtype: str

    # Backward-compatible alias for older G/F code.
    skinner_label: str

    confidence: float
    reason: str

    source: str
    stimulus: str
    local_pattern: str
    semantic_cluster: str

    # C-features propagated from SentenceFeatures
    root_lemma: Optional[str]
    is_imperative_like: bool
    has_negation: bool
    has_modal: bool
    has_question: bool
    subject_present: bool
    has_verbum_dicendi: bool

    # response / stimulus / record
    control_role: str = "response"


# ==========================================================
# F3. HIERARCHY / DECISION HELPERS
# ==========================================================

def map_skinner_class(proxy_subtype: str) -> str:

    mapping = {
        # Mand family
        "mand_like": "mand",

        # Tact family
        "visual_tact_proxy": "tact",
        "revelation_tact_proxy": "tact",
        "reported_tact_proxy": "tact",
        "carry_over_tact_proxy": "tact",
        "descriptive_proxy": "tact",

        # Textual family
        "reported_textual_proxy": "textual",
        "textual_trigger": "textual",
        "citation_chain_proxy": "textual",

        # Intraverbal family
        "intraverbal_proxy": "intraverbal",
        "intraverbal_trigger": "intraverbal",
        "dialogue_chain_proxy": "intraverbal",

        # Echoic family
        "echoic_proxy": "echoic",

        # Autoclitic family
        "negation_autoclitic_proxy": "autoclitic",
        "uncertainty_autoclitic_proxy": "autoclitic",
        "emphasis_autoclitic_proxy": "autoclitic",
        "source_autoclitic_proxy": "autoclitic",
        "relation_autoclitic_proxy": "autoclitic",
        "autoclitic_proxy": "autoclitic",

        # Non-classified layer
        "written_record": "none",
        "uncertain": "none",
    }

    return mapping.get(proxy_subtype, "none")


def make_decision(
    feature: SentenceFeatures,
    semantic: SemanticFeatures,
    text_input: TextInput,
    proxy_subtype: str,
    confidence: float,
    reason: str,
    control_role: str = "response",
) -> SkinnerDecision:

    return SkinnerDecision(
        sentence_id=feature.sentence_id,
        sentence=feature.sentence,
        skinner_class=map_skinner_class(proxy_subtype),
        proxy_subtype=proxy_subtype,
        skinner_label=proxy_subtype,
        confidence=confidence,
        reason=reason,
        source=text_input.context.source,
        stimulus=text_input.context.stimulus,
        local_pattern=feature.local_pattern,
        semantic_cluster=semantic.semantic_cluster,
        root_lemma=feature.root_lemma,
        is_imperative_like=feature.is_imperative_like,
        has_negation=feature.has_negation,
        has_modal=feature.has_modal,
        has_question=feature.has_question,
        subject_present=feature.subject_present,
        has_verbum_dicendi=rules.has_reported_speech_pattern(feature),
        control_role=control_role,
    )


def clone_decision(
    decision: SkinnerDecision,
    proxy_subtype: str,
    confidence: float,
    reason: str,
    control_role: Optional[str] = None,
) -> SkinnerDecision:

    role = control_role if control_role is not None else decision.control_role

    return SkinnerDecision(
        sentence_id=decision.sentence_id,
        sentence=decision.sentence,
        skinner_class=map_skinner_class(proxy_subtype),
        proxy_subtype=proxy_subtype,
        skinner_label=proxy_subtype,
        confidence=confidence,
        reason=reason,
        source=decision.source,
        stimulus=decision.stimulus,
        local_pattern=decision.local_pattern,
        semantic_cluster=decision.semantic_cluster,
        root_lemma=decision.root_lemma,
        is_imperative_like=decision.is_imperative_like,
        has_negation=decision.has_negation,
        has_modal=decision.has_modal,
        has_question=decision.has_question,
        subject_present=decision.subject_present,
        has_verbum_dicendi=decision.has_verbum_dicendi,
        control_role=role,
    )


# ==========================================================
# F4. DECISION LOGIC
# ==========================================================

def decide_skinner_family(
    feature: SentenceFeatures,
    semantic: SemanticFeatures,
    text_input: TextInput,
) -> str:

    source = text_input.context.source
    stimulus = text_input.context.stimulus

    if (
        feature.is_imperative_like
        or feature.local_pattern == "imperative_action_object"
    ):
        return "mand"

    if rules.is_intraverbal_trigger_pattern(feature):
        return "intraverbal"

    if stimulus in {"question_prompt", "answer_context"}:
        return "intraverbal"

    if stimulus == "auditory_verbal_stimulus":
        return "echoic"

    if (
        source in rules.WRITTEN_RECORD_SOURCES
        and (
            rules.has_reported_textual_pattern(feature)
            or rules.has_textual_trigger_pattern(feature)
            or rules.has_citation_chain_pattern(feature)
        )
    ):
        return "textual"

    # Fix P1: verbum dicendi pred descriptive checkpointom — vety v rámci
    # reportovanej reči majú intraverbal rodinu, nie tact/descriptive.
    if (
        source in rules.WRITTEN_RECORD_SOURCES
        and rules.has_reported_speech_pattern(feature)
    ):
        return "intraverbal"

    # Fix P2: AUTOCLITIC_SOURCE nesmie prebiť vizuálnu percepciu —
    # ak veta obsahuje aj vizuálne sloveso, tact má prioritu.
    if (
        rules.has_any_lemma(feature, rules.AUTOCLITIC_SOURCE_LEMMAS)
        and not rules.has_visual_tact_pattern(feature)
    ):
        return "autoclitic"

    if (
        source in rules.WRITTEN_RECORD_SOURCES
        and (
            rules.has_visual_tact_pattern(feature)
            or rules.has_revelation_tact_pattern(feature)
            or rules.has_descriptive_proxy_pattern(feature)
        )
    ):
        return "tact"

    if rules.has_echoic_proxy_pattern(feature):
        return "echoic"

    if rules.detect_autoclitic_proxy_subtype(feature, semantic) is not None:
        return "autoclitic"

    return "none"


def decide_skinner_label(
    feature: SentenceFeatures,
    semantic: SemanticFeatures,
    text_input: TextInput,
) -> SkinnerDecision:

    source = text_input.context.source
    stimulus = text_input.context.stimulus

    family = decide_skinner_family(feature, semantic, text_input)

    if family == "mand":
        return make_decision(
            feature=feature,
            semantic=semantic,
            text_input=text_input,
            proxy_subtype="mand_like",
            confidence=get_confidence("mand_like"),
            reason=(
                "Sentence is first assigned to mand family because request-like "
                "or imperative form is present; subtype is mand_like because "
                "motivating operation is not directly observable in the written record."
            ),
        )

    if family == "textual":

        if rules.has_reported_textual_pattern(feature):
            return make_decision(
                feature=feature,
                semantic=semantic,
                text_input=text_input,
                proxy_subtype="reported_textual_proxy",
                confidence=get_confidence("reported_textual_proxy"),
                reason=(
                    "Sentence is first assigned to textual family because written, "
                    "reading, writing, or citation control is represented; subtype "
                    "is reported_textual_proxy."
                ),
            )

        if rules.has_textual_trigger_pattern(feature):
            return make_decision(
                feature=feature,
                semantic=semantic,
                text_input=text_input,
                proxy_subtype="textual_trigger",
                confidence=get_confidence("textual_trigger"),
                reason=(
                    "Sentence is first assigned to textual family because a written "
                    "object or source context is explicit; subtype is textual_trigger."
                ),
                control_role="stimulus",
            )

        if rules.has_citation_chain_pattern(feature):
            return make_decision(
                feature=feature,
                semantic=semantic,
                text_input=text_input,
                proxy_subtype="citation_chain_proxy",
                confidence=get_confidence("citation_chain_proxy"),
                reason=(
                    "Sentence is first assigned to textual family because a scriptural, "
                    "prophetic, or written citation relation is represented; subtype "
                    "is citation_chain_proxy."
                ),
            )

    if family == "tact":

        if rules.has_visual_tact_pattern(feature):
            return make_decision(
                feature=feature,
                semantic=semantic,
                text_input=text_input,
                proxy_subtype="visual_tact_proxy",
                confidence=get_confidence("visual_tact_proxy"),
                reason=(
                    "Sentence is first assigned to tact family because visual "
                    "perception is represented; subtype is visual_tact_proxy."
                ),
            )

        if rules.has_revelation_tact_pattern(feature):
            return make_decision(
                feature=feature,
                semantic=semantic,
                text_input=text_input,
                proxy_subtype="revelation_tact_proxy",
                confidence=get_confidence("revelation_tact_proxy"),
                reason=(
                    "Sentence is first assigned to tact family because revelation "
                    "or appearing is represented; subtype is revelation_tact_proxy."
                ),
            )

        if (
            source in rules.WRITTEN_RECORD_SOURCES
            and stimulus == "unknown"
            and rules.has_descriptive_proxy_pattern(feature)
        ):
            return make_decision(
                feature=feature,
                semantic=semantic,
                text_input=text_input,
                proxy_subtype="descriptive_proxy",
                confidence=get_confidence("descriptive_proxy"),
                reason=(
                    "Sentence is first assigned to tact family because explicit "
                    "descriptive or assertive predication is present; subtype is "
                    "descriptive_proxy because direct nonverbal control is not observable."
                ),
            )

    if family == "echoic":
        return make_decision(
            feature=feature,
            semantic=semantic,
            text_input=text_input,
            proxy_subtype="echoic_proxy",
            confidence=get_confidence("echoic_proxy"),
            reason=(
                "Sentence is first assigned to echoic family because repeated "
                "or formulaic verbal form is present; subtype is echoic_proxy."
            ),
        )

    if family == "intraverbal":

        if rules.is_intraverbal_trigger_pattern(feature):
            return make_decision(
                feature=feature,
                semantic=semantic,
                text_input=text_input,
                proxy_subtype="intraverbal_trigger",
                confidence=get_confidence("intraverbal_trigger"),
                reason=(
                    "Sentence is first assigned to intraverbal family because "
                    "question-like verbal stimulus is present; subtype is "
                    "intraverbal_trigger."
                ),
                control_role="stimulus",
            )

        if (
            source in rules.WRITTEN_RECORD_SOURCES
            and rules.has_reported_speech_pattern(feature)
        ):
            return make_decision(
                feature=feature,
                semantic=semantic,
                text_input=text_input,
                proxy_subtype="intraverbal_proxy",
                confidence=get_confidence("intraverbal_proxy"),
                reason=(
                    "Sentence is first assigned to intraverbal family because "
                    "reported verbal interaction is represented; subtype is "
                    "intraverbal_proxy."
                ),
            )

        if stimulus in {"question_prompt", "answer_context"}:
            return make_decision(
                feature=feature,
                semantic=semantic,
                text_input=text_input,
                proxy_subtype="intraverbal_proxy",
                confidence=get_confidence("intraverbal_proxy"),
                reason=(
                    "Sentence is first assigned to intraverbal family because "
                    "prior verbal stimulus or answer context is indicated; "
                    "subtype is intraverbal_proxy."
                ),
            )

    if family == "autoclitic":

        autoclitic_subtype = rules.detect_autoclitic_proxy_subtype(
            feature, semantic
        )

        return make_decision(
            feature=feature,
            semantic=semantic,
            text_input=text_input,
            proxy_subtype=autoclitic_subtype,
            confidence=get_confidence(autoclitic_subtype),
            reason=rules.autoclitic_reason(autoclitic_subtype),
        )

    if source in rules.WRITTEN_RECORD_SOURCES and stimulus == "unknown":
        return make_decision(
            feature=feature,
            semantic=semantic,
            text_input=text_input,
            proxy_subtype="written_record",
            confidence=get_confidence("written_record"),
            reason=(
                "Sentence is assigned to none/fallback family because no reliable "
                "operant-like proxy pattern was detected in the written record."
            ),
            control_role="record",
        )

    return make_decision(
        feature=feature,
        semantic=semantic,
        text_input=text_input,
        proxy_subtype="uncertain",
        confidence=get_confidence("uncertain"),
        reason=(
            "Insufficient behavioral context; no reliable controlling stimulus "
            "is observable."
        ),
        control_role="record",
    )


# ==========================================================
# F5. CONTEXTUAL PASS / APPLY CLASSIFICATION
# ==========================================================

def can_context_refine_decision(
    decision: SkinnerDecision,
    target_proxy_subtype: str,
) -> bool:

    current_family = decision.skinner_class
    target_family = map_skinner_class(target_proxy_subtype)

    if current_family == "none":
        return False

    if current_family != target_family:
        return False

    return True


def can_context_override_decision(
    decision: SkinnerDecision,
    target_proxy_subtype: str,
) -> bool:

    target_family = map_skinner_class(target_proxy_subtype)

    if decision.control_role == "stimulus":
        return False

    if decision.proxy_subtype in {
        "visual_tact_proxy",
        "revelation_tact_proxy",
        "reported_textual_proxy",
        "textual_trigger",
        "intraverbal_trigger",
        "echoic_proxy",
        "negation_autoclitic_proxy",
        "uncertainty_autoclitic_proxy",
        "emphasis_autoclitic_proxy",
        "source_autoclitic_proxy",
        "relation_autoclitic_proxy",
    }:
        return False

    if decision.skinner_class != target_family:
        return False

    return True


def apply_skinner_rules(
    text_input: TextInput,
) -> List[SkinnerDecision]:

    preprocessed = preprocess_text(text_input)
    features = extract_features(preprocessed)
    semantics = semantic_enrichment(features)

    decisions = []

    previous_reported_tact_context = False
    active_intraverbal_trigger = False

    dialogue_chain_scope = 0
    textual_chain_scope = 0

    for feature, semantic in zip(features, semantics):

        inherited_reported_tact = False
        fulfilled_intraverbal_trigger = False

        active_dialogue_chain = dialogue_chain_scope > 0
        active_textual_chain = textual_chain_scope > 0

        decision = decide_skinner_label(feature, semantic, text_input)

        if rules.is_intraverbal_trigger_pattern(feature):
            active_intraverbal_trigger = True
            dialogue_chain_scope = 2

            decision = clone_decision(
                decision=decision,
                proxy_subtype="intraverbal_trigger",
                confidence=get_confidence("intraverbal_trigger"),
                reason=(
                    "Question-like verbal stimulus detected; it activates an "
                    "intraverbal trigger for a possible subsequent verbal response."
                ),
                control_role="stimulus",
            )

        elif decision.proxy_subtype in {
            "textual_trigger",
            "reported_textual_proxy",
            "citation_chain_proxy",
        }:
            textual_chain_scope = 2

        elif (
            active_textual_chain
            and can_context_refine_decision(decision, "citation_chain_proxy")
            and decision.proxy_subtype in {
                "reported_textual_proxy",
                "textual_trigger",
                "citation_chain_proxy",
            }
        ):
            decision = clone_decision(
                decision=decision,
                proxy_subtype="citation_chain_proxy",
                confidence=get_confidence("citation_chain_proxy"),
                reason=(
                    "Previous textual or citation context remains active; "
                    "this sentence is refined within the textual family as "
                    "citation_chain_proxy."
                ),
                control_role="response",
            )

        elif (
            previous_reported_tact_context
            and decision.proxy_subtype == "descriptive_proxy"
            and rules.has_descriptive_proxy_pattern(feature)
            and can_context_override_decision(decision, "carry_over_tact_proxy")
        ):
            decision = clone_decision(
                decision=decision,
                proxy_subtype="carry_over_tact_proxy",
                confidence=get_confidence("carry_over_tact_proxy"),
                reason=(
                    "Previous sentence reports visual perception or revelation; "
                    "this explicit descriptive predication is treated as a "
                    "context-linked tact-inspired proxy."
                ),
                control_role="response",
            )

            inherited_reported_tact = True

        elif (
            active_intraverbal_trigger
            and rules.is_intraverbal_response_candidate(feature, decision)
        ):
            decision = clone_decision(
                decision=decision,
                proxy_subtype="intraverbal_proxy",
                confidence=get_confidence("intraverbal_proxy"),
                reason=(
                    "An active intraverbal trigger from prior verbal stimulus is present; "
                    "this utterance is treated as a response controlled by that verbal context."
                ),
                control_role="response",
            )

            active_intraverbal_trigger = False
            fulfilled_intraverbal_trigger = True
            dialogue_chain_scope = 2

        elif (
            active_dialogue_chain
            and rules.is_dialogue_chain_candidate(feature, decision)
            and can_context_override_decision(decision, "dialogue_chain_proxy")
            and decision.proxy_subtype != "intraverbal_proxy"
        ):
            decision = clone_decision(
                decision=decision,
                proxy_subtype="dialogue_chain_proxy",
                confidence=get_confidence("dialogue_chain_proxy"),
                reason=(
                    "A dialogue chain is active; this utterance is treated as part "
                    "of an extended intraverbal sequence."
                ),
                control_role="response",
            )

        elif (
            active_intraverbal_trigger
            and rules.is_narrative_interruption(feature, decision)
        ):
            # Narrative interruption does not fulfill or cancel the trigger.
            pass

        elif (
            active_intraverbal_trigger
            and rules.is_stronger_competing_control(decision)
        ):
            active_intraverbal_trigger = False

        decisions.append(decision)

        previous_reported_tact_context = (
            decision.proxy_subtype in {
                "visual_tact_proxy",
                "revelation_tact_proxy",
                "reported_tact_proxy",
                "carry_over_tact_proxy",
            }
            and not inherited_reported_tact
        )

        if fulfilled_intraverbal_trigger:
            previous_reported_tact_context = False

        if decision.proxy_subtype == "written_record":
            dialogue_chain_scope = 0
            textual_chain_scope = 0
        else:
            if dialogue_chain_scope > 0:
                dialogue_chain_scope -= 1

            if textual_chain_scope > 0:
                textual_chain_scope -= 1

    return decisions


# ==========================================================
# F6. DATASET LOAD + VALIDATION
# ==========================================================

def load_dataset(path: Path) -> pd.DataFrame:

    if not path.exists():
        raise FileNotFoundError(
            f"Missing annotated dataset: {path}"
        )

    df = pd.read_csv(path)

    required_columns = {
        "sentence",
        "source",
        "stimulus",
        "label",
        "local_pattern",
        "semantic_cluster",
        "control_role",
        "root_lemma",
        "is_imperative_like",
        "has_negation",
        "has_modal",
        "has_question",
        "subject_present",
        "has_verbum_dicendi",
        "previous_was_trigger",
    }

    missing = required_columns - set(df.columns)

    if missing:
        raise ValueError(f"Missing columns: {missing}")

    if "label" in df.columns:
        df = df[df["label"].notna() & (df["label"].astype(str).str.strip() != "")]
        df["proxy_subtype"] = df["label"]
        df["skinner_class"] = df["label"].map(map_skinner_class)

    return df


# ==========================================================
# F7. FEATURE ENGINEERING
# ==========================================================

def build_feature_transformer() -> ColumnTransformer:
    """
    Return an UNFITTED ColumnTransformer for training ML classifiers.

    Feature groups
    --------------
    text  : TF-IDF (1-2 gram, sublinear_tf) on the "sentence" column.
            Captures surface lexical patterns without full bag-of-words noise.
    cat   : OneHotEncoder on CAT_COLS (source, stimulus, local_pattern,
            semantic_cluster, control_role).  handle_unknown="ignore" makes
            the transformer safe on unseen values at prediction time.
    bool  : Passthrough binary BOOL_COLS as integer 0/1 columns.

    Usage
    -----
        ct = build_feature_transformer()
        X  = ct.fit_transform(df_train)     # sparse matrix
        pipeline = Pipeline([("features", ct), ("clf", LinearSVC(...))])

    Notes
    -----
    proxy_subtype and skinner_class are NOT included — they are the targets.
    root_lemma is excluded because its cardinality is too high for OHE and
    embedding it as a raw token already happens inside the TF-IDF step if the
    sentence column contains the lemma.
    """
    bool_cols_present = [c for c in BOOL_COLS]  # resolved at call time

    return ColumnTransformer(
        transformers=[
            (
                "text",
                TfidfVectorizer(
                    ngram_range=(1, 2),
                    min_df=1,
                    max_df=0.95,
                    sublinear_tf=True,
                ),
                "sentence",
            ),
            (
                "cat",
                OneHotEncoder(sparse_output=True, handle_unknown="ignore"),
                CAT_COLS,
            ),
            (
                "bool",
                "passthrough",
                bool_cols_present,
            ),
        ],
        remainder="drop",
        verbose_feature_names_out=False,
    )


def build_combined_text(df: pd.DataFrame) -> pd.Series:
    """
    DEPRECATED — use build_feature_transformer() for new code.

    Concatenates all features into a single pseudo-text string for
    TF-IDF consumption.  Kept for backward compatibility with existing
    trained models that depend on this representation.

    proxy_subtype and skinner_class are intentionally NOT included
    in combined_text to prevent label leakage.
    """
    df = df.copy()
    df["is_record_role"]   = (df["control_role"] == "record")
    df["is_stimulus_role"] = (df["control_role"] == "stimulus")
    df["is_response_role"] = (df["control_role"] == "response")

    return (
        df["sentence"].astype(str)
        + " SOURCE_" + df["source"].astype(str)
        + " STIMULUS_" + df["stimulus"].astype(str)
        + " LOCAL_PATTERN_" + df["local_pattern"].astype(str)
        + " SEMANTIC_CLUSTER_" + df["semantic_cluster"].astype(str)
        + " RECORD_ROLE_" + df["is_record_role"].astype(str)
        + " STIMULUS_ROLE_" + df["is_stimulus_role"].astype(str)
        + " RESPONSE_ROLE_" + df["is_response_role"].astype(str)
        + " ROOT_LEMMA_" + df["root_lemma"].fillna("none").astype(str)
        + " IMPERATIVE_" + df["is_imperative_like"].astype(str)
        + " NEGATION_" + df["has_negation"].astype(str)
        + " MODAL_" + df["has_modal"].astype(str)
        + " QUESTION_" + df["has_question"].astype(str)
        + " SUBJECT_" + df["subject_present"].astype(str)
        + " VERBUM_DICENDI_" + df["has_verbum_dicendi"].astype(str)
        + " PREV_TRIGGER_" + df["previous_was_trigger"].astype(str)
    )


# ==========================================================
# F8. AUDIT PRINTS
# ==========================================================

def print_audit(df: pd.DataFrame) -> None:

    print("\nSKINNER CLASS DISTRIBUTION")
    print(df["skinner_class"].value_counts().to_string())


# ==========================================================
# F9. ML MODEL DEFINITIONS
# ==========================================================

def train_naive_bayes(use_feature_transformer: bool = True) -> Pipeline:
    """
    Naive Bayes classifier pipeline.

    use_feature_transformer=True  → uses build_feature_transformer() with proper
        ColumnTransformer (TF-IDF + OHE + binary) and expects a DataFrame input.
    use_feature_transformer=False → legacy TF-IDF only, expects a text Series
        (backward compat with build_combined_text()).
    """
    if use_feature_transformer:
        return Pipeline([
            ("features", build_feature_transformer()),
            ("clf", MultinomialNB(fit_prior=False)),
        ])
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95,
            sublinear_tf=True,
        )),
        ("clf", MultinomialNB(fit_prior=False)),
    ])


def train_svm(use_feature_transformer: bool = True) -> Pipeline:
    """
    LinearSVC classifier pipeline.

    use_feature_transformer=True  → ColumnTransformer + DataFrame input (preferred).
    use_feature_transformer=False → legacy TF-IDF + text Series.
    """
    if use_feature_transformer:
        return Pipeline([
            ("features", build_feature_transformer()),
            ("clf", LinearSVC(class_weight="balanced", max_iter=2000)),
        ])
    return Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.95,
            sublinear_tf=True,
        )),
        ("clf", LinearSVC(class_weight="balanced")),
    ])


# ==========================================================
# F10. TRAIN / EVALUATE / SAVE
# ==========================================================

_SEP = "=" * 44


def _per_class_df(
    y_true: pd.Series,
    y_pred: pd.Series,
    model_name: str,
) -> pd.DataFrame:
    """Return per-class precision / recall / F1 / support as a tidy DataFrame."""
    d = classification_report(y_true, y_pred, zero_division=0, output_dict=True)
    rows = []
    for cls, m in sorted(d.items()):
        if cls in {"accuracy", "macro avg", "weighted avg"}:
            continue
        rows.append({
            "model":        model_name,
            "class":        cls,
            "skinner_class": map_skinner_class(cls),
            "precision":    round(m["precision"], 3),
            "recall":       round(m["recall"],    3),
            "f1_score":     round(m["f1-score"],  3),
            "support":      int(m["support"]),
        })
    return pd.DataFrame(rows)

_LABEL_SHORT = {
    "descriptive_proxy":            "desc_proxy",
    "carry_over_tact_proxy":        "carry_tact",
    "visual_tact_proxy":            "vis_tact",
    "revelation_tact_proxy":        "rev_tact",
    "reported_tact_proxy":          "rep_tact",
    "reported_textual_proxy":       "rep_text",
    "textual_trigger":              "text_trig",
    "citation_chain_proxy":         "cit_chain",
    "intraverbal_proxy":            "intrav_px",
    "intraverbal_trigger":          "intrav_tr",
    "dialogue_chain_proxy":         "dial_chain",
    "echoic_proxy":                 "echoic",
    "mand_like":                    "mand",
    "negation_autoclitic_proxy":    "neg_auto",
    "uncertainty_autoclitic_proxy": "unc_auto",
    "emphasis_autoclitic_proxy":    "emph_auto",
    "source_autoclitic_proxy":      "src_auto",
    "relation_autoclitic_proxy":    "rel_auto",
    "autoclitic_proxy":             "auto",
    "written_record":               "written",
    "uncertain":                    "uncertain",
}

_MISCLASSIFIED_META_COLS = [
    "source",
    "stimulus",
    "local_pattern",
    "semantic_cluster",
    "control_role",
]


def _compact_report(
    y_test: pd.Series,
    y_pred: pd.Series,
    model_name: str,
    label: str,
) -> str:

    from sklearn.metrics import classification_report as _cr

    d = _cr(y_test, y_pred, zero_division=0, output_dict=True)

    acc      = d.pop("accuracy", None)
    macro    = d.pop("macro avg", None)
    weighted = d.pop("weighted avg", None)

    acc_str = f"{acc:.2f}" if acc is not None else ""

    lines = [
        f"\n{model_name} REPORT — {label}   acc={acc_str}",
        f"{'label':<18} {'P':>5} {'R':>5} {'F1':>5} {'sup':>4}",
    ]

    for cls, m in sorted(d.items()):
        short = _LABEL_SHORT.get(cls, cls[:18])
        lines.append(
            f"{short:<18} {m['precision']:>5.2f} {m['recall']:>5.2f}"
            f" {m['f1-score']:>5.2f} {int(m['support']):>4}"
        )

    if macro:
        lines.append(
            f"{'macro':<18} {macro['precision']:>5.2f} {macro['recall']:>5.2f}"
            f" {macro['f1-score']:>5.2f} {int(macro['support']):>4}"
        )
    if weighted:
        lines.append(
            f"{'weighted':<18} {weighted['precision']:>5.2f} {weighted['recall']:>5.2f}"
            f" {weighted['f1-score']:>5.2f} {int(weighted['support']):>4}"
        )

    return "\n".join(lines)


def _print_diagnostics(
    model_name: str,
    y_test: pd.Series,
    y_pred: pd.Series,
    df_test: pd.DataFrame,
) -> None:

    print(f"\n{model_name} PREDICTION DISTRIBUTION:")
    print(y_pred.value_counts().to_string())

    print(f"\n{model_name} CONFUSION MATRIX:")
    print("rows = true labels")
    print("columns = predicted labels")
    cm = pd.crosstab(
        y_test,
        y_pred,
        rownames=["true"],
        colnames=["predicted"],
    )
    print(cm.to_string())

    misclassified_mask = y_test != y_pred
    n_wrong = misclassified_mask.sum()

    print(f"\n{model_name} MISCLASSIFIED EXAMPLES ({n_wrong} total, showing top 10):")
    print("sentence | true | predicted | source | stimulus | local_pattern | semantic_cluster | control_role")

    if n_wrong == 0:
        print("  None.")
        return

    df_wrong = df_test[misclassified_mask].copy()
    df_wrong["true"] = y_test[misclassified_mask].values
    df_wrong["predicted"] = y_pred[misclassified_mask].values

    show_cols = ["sentence", "true", "predicted"]

    print(df_wrong[show_cols].head(10).to_string(index=False))


def train_and_evaluate_target(
    df: pd.DataFrame,
    X,
    target_column: str,
    label: str,
    use_feature_transformer: bool = True,
) -> None:
    """
    Train NB + SVM on X → target_column, evaluate, and save models.

    X may be either a DataFrame (for ColumnTransformer pipelines) or a
    pd.Series of combined text strings (legacy path).
    Per-class precision / recall / F1 are printed and saved to CSV.
    """
    y = df[target_column]

    # HEADER
    print(f"\n{_SEP}")
    print(f"TARGET: {label}")
    print(_SEP)

    # SPLIT
    label_counts = y.value_counts()
    use_stratify  = y.nunique() > 1 and label_counts.min() >= 2

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.25,
        random_state=42,
        stratify=y if use_stratify else None,
    )
    df_test = df.loc[y_test.index]

    # FIT
    nb_model  = train_naive_bayes(use_feature_transformer)
    svm_model = train_svm(use_feature_transformer)

    nb_model.fit(X_train, y_train)
    svm_model.fit(X_train, y_train)

    nb_pred  = pd.Series(nb_model.predict(X_test),  index=y_test.index)
    svm_pred = pd.Series(svm_model.predict(X_test), index=y_test.index)

    # DIAGNOSTICS
    print(f"\n--- DIAGNOSTICS — {label} ---")
    print("\nLABEL DISTRIBUTION:")
    print(label_counts.to_string())
    print(f"\nTRAIN rows : {len(X_train)}")
    print(f"TEST  rows : {len(X_test)}")
    print(f"Stratify   : {use_stratify}")
    print("\nY_TEST DISTRIBUTION:")
    print(y_test.value_counts().to_string())

    _print_diagnostics("NAIVE BAYES", y_test, nb_pred, df_test)
    _print_diagnostics("SVM",         y_test, svm_pred, df_test)

    # COMPACT P/R/F1 REPORT per class
    print(_compact_report(y_test, nb_pred,  "NAIVE BAYES", label))
    print(_compact_report(y_test, svm_pred, "SVM",         label))

    # SAVE per-class metrics to CSV
    slug    = label.lower().replace(" ", "_")
    eval_nb  = _per_class_df(y_test, nb_pred,  "naive_bayes")
    eval_svm = _per_class_df(y_test, svm_pred, "svm")
    eval_out = OUTPUT_DIR / f"eval_ml_{slug}.csv"
    eval_out.parent.mkdir(exist_ok=True)
    pd.concat([eval_nb, eval_svm]).to_csv(eval_out, index=False)
    print(f"\nPer-class metrics saved: {eval_out}")

    # SAVE models
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    nb_path  = MODEL_DIR / f"naive_bayes_{slug}.pkl"
    svm_path = MODEL_DIR / f"svm_{slug}.pkl"
    joblib.dump(nb_model,  nb_path)
    joblib.dump(svm_model, svm_path)
    print(f"\nMODELS SAVED:")
    print(f"  {nb_path}")
    print(f"  {svm_path}")


def train_and_evaluate() -> None:
    """
    Load annotated data, build features, train and evaluate NB + SVM.

    Tries proper ColumnTransformer feature engineering first.  Falls back to
    legacy build_combined_text() if the DataFrame lacks required bool columns.
    """
    df = load_dataset(DATA_PATH)

    # Determine if all required columns for ColumnTransformer are present
    missing_bool = [c for c in BOOL_COLS if c not in df.columns]
    use_ct = len(missing_bool) == 0

    if use_ct:
        X = df          # ColumnTransformer reads directly from DataFrame
        label = "(ColumnTransformer)"
    else:
        print(f"  Missing bool cols for ColumnTransformer: {missing_bool}")
        print("  Falling back to build_combined_text().")
        X = build_combined_text(df)
        use_ct = False
        label = "(legacy combined_text)"

    print(f"\nFeature engineering: {label}")

    train_and_evaluate_target(df, X, TARGET_COLUMN, "SKINNER CLASS", use_ct)

    if "proxy_subtype" in df.columns:
        train_and_evaluate_target(df, X, "proxy_subtype", "PROXY SUBTYPE", use_ct)


# ==========================================================
# F11. ANNOTATION SEED GENERATOR
# ==========================================================

def generate_annotation_seed(
    output_path: Path = SEED_PATH,
    max_per_class: int = 30,
    db_limit: int = 5000,
) -> None:
    """
    Generate a stratified CSV seed file for manual annotation.

    Runs the rule classifier on up to *db_limit* DB sentences, samples
    *max_per_class* examples per predicted proxy_subtype, and writes a CSV
    with all extracted features plus an empty "label" column for annotators.

    Annotators should fill "label" with the correct proxy_subtype and save
    the file as DATA_PATH (data/annotated_skinner.csv).  After annotation,
    call calibrate_confidence() to update confidence values from the data.

    Output columns
    --------------
    sentence, predicted_skinner_class, predicted_proxy_subtype, confidence,
    source, stimulus, local_pattern, semantic_cluster, control_role,
    root_lemma, is_imperative_like, has_negation, has_modal, has_question,
    subject_present, has_verbum_dicendi, label (empty — to fill)
    """
    from collections import defaultdict
    from n_db import load_rows as _load_db, TABLE_REFINED

    db_rows = _load_db(TABLE_REFINED)
    if not db_rows:
        print("generate_annotation_seed: no DB rows found.")
        return

    buckets: dict[str, list] = defaultdict(list)
    errors = 0

    for row in db_rows[:db_limit]:
        sentence = row.get("sentence", "").strip()
        if not sentence:
            continue
        try:
            inp  = create_input_from_text(text=sentence, source="written_record")
            decs = apply_skinner_rules(inp)
            if not decs:
                continue
            d = decs[0]
            buckets[d.proxy_subtype].append({
                "sentence":                   sentence,
                "predicted_skinner_class":    d.skinner_class,
                "predicted_proxy_subtype":    d.proxy_subtype,
                "confidence":                 round(d.confidence, 3),
                "source":                     d.source,
                "stimulus":                   d.stimulus,
                "local_pattern":              d.local_pattern,
                "semantic_cluster":           d.semantic_cluster,
                "control_role":               d.control_role,
                "root_lemma":                 d.root_lemma or "",
                "is_imperative_like":         d.is_imperative_like,
                "has_negation":               d.has_negation,
                "has_modal":                  d.has_modal,
                "has_question":               d.has_question,
                "subject_present":            d.subject_present,
                "has_verbum_dicendi":         d.has_verbum_dicendi,
                "previous_was_trigger":       False,
                "label":                      "",  # to be filled by annotator
            })
        except Exception as exc:
            errors += 1
            import logging
            logging.getLogger(__name__).debug(
                "generate_annotation_seed skipped a sentence: %s", exc
            )
            continue

    if not buckets:
        print(f"generate_annotation_seed: no sentences classified (errors={errors}).")
        return

    # Stratified sample
    seed_rows: list = []
    for cls, rows in sorted(buckets.items()):
        seed_rows.extend(rows[:max_per_class])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(seed_rows).to_csv(output_path, index=False, encoding="utf-8")

    print(f"\nAnnotation seed written: {output_path}  ({len(seed_rows)} rows, {errors} errors)")
    print(f"{'proxy_subtype':<35} sampled / total")
    for cls, rows in sorted(buckets.items()):
        print(f"  {cls:<35} {min(len(rows), max_per_class):>3} / {len(rows):>4}")
    print(f"\nFill the 'label' column and save as: {DATA_PATH}")


# ==========================================================
# F12. RULE-CLASSIFIER PRECISION / RECALL EVALUATION
# ==========================================================

def evaluate_rule_classifier(data_path: Path = DATA_PATH) -> pd.DataFrame:
    """
    Evaluate the rule-based classifier against manually annotated labels.

    Expects a CSV with columns: label (true proxy_subtype) and either
    predicted_proxy_subtype (from annotation seed) or proxy_subtype.

    Per-class precision, recall, F1 and support are:
    - Printed as a compact table (_compact_report)
    - Saved to EVAL_OUT (output/eval_rule_classifier.csv)

    Also reports at the skinner_class (family) level.

    Returns
    -------
    pd.DataFrame  with columns: proxy_subtype, skinner_class, precision,
                                recall, f1_score, support
    """
    if not data_path.exists():
        raise FileNotFoundError(
            f"Annotated data not found: {data_path}\n"
            f"Generate a seed with generate_annotation_seed() first."
        )

    df = pd.read_csv(data_path)

    # Resolve label and prediction columns
    if "label" not in df.columns:
        raise ValueError("Expected 'label' column in annotated CSV.")

    labeled = df[df["label"].notna() & (df["label"].astype(str).str.strip() != "")]
    if labeled.empty:
        raise ValueError("No annotated rows found (label column is empty).")

    y_true = labeled["label"].astype(str)

    if "predicted_proxy_subtype" in labeled.columns:
        y_pred = labeled["predicted_proxy_subtype"].astype(str)
    elif "proxy_subtype" in labeled.columns:
        y_pred = labeled["proxy_subtype"].astype(str)
    else:
        raise ValueError(
            "Expected 'predicted_proxy_subtype' or 'proxy_subtype' column."
        )

    # Per proxy_subtype report
    print(f"\nAnnotated examples : {len(labeled)}")
    print(_compact_report(y_true, y_pred, "RULE CLASSIFIER", "proxy_subtype"))

    # Per skinner_class (family) report
    y_true_cls = y_true.map(lambda x: map_skinner_class(x))
    y_pred_cls = y_pred.map(lambda x: map_skinner_class(x))
    print(_compact_report(y_true_cls, y_pred_cls, "RULE CLASSIFIER", "skinner_class"))

    # Build result DataFrame
    result_df = _per_class_df(y_true, y_pred, "rule_classifier")

    # Save
    EVAL_OUT.parent.mkdir(exist_ok=True)
    result_df.to_csv(EVAL_OUT, index=False, encoding="utf-8")
    print(f"\nPer-class evaluation saved: {EVAL_OUT}")

    return result_df


# ==========================================================
# F13. DEBUG / SMOKE TEST
# ==========================================================

if __name__ == "__main__":

    import sys as _sys

    if len(_sys.argv) > 1 and _sys.argv[1] == "seed":
        # python h_classifiers.py seed
        generate_annotation_seed()
    elif len(_sys.argv) > 1 and _sys.argv[1] == "eval":
        # python h_classifiers.py eval
        evaluate_rule_classifier()
    elif len(_sys.argv) > 1 and _sys.argv[1] == "calibrate":
        # python h_classifiers.py calibrate
        print("Calibrating confidence from annotated data...")
        calibrate_confidence()
        print("\nCurrent calibration:")
        for k, v in sorted(_CONFIDENCE_CALIBRATION.items()):
            default = _PROXY_CONFIDENCE_DEFAULTS.get(k, 0.5)
            mark = " *" if abs(v - default) > 0.01 else ""
            print(f"  {k:<35} {default:.2f} → {v:.3f}{mark}")
    else:
        train_and_evaluate()