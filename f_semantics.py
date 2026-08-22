"""
f_semantics.py — Sentence-level semantic enrichment.

Architecture note on distributional semantics
----------------------------------------------
The scoring uses curated seed lexicons (lexical density approach) plus two
structural bonuses.  Section F4 (below) documents why this design was chosen
over word embeddings and what the upgrade path looks like.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from typing import List, Optional
from pathlib import Path
import csv

import numpy as np

from e_extraction import SentenceFeatures
from a_paths import MODELS_DIR
from lexicons_common import OPPOSITIONS, opposition_present_in
from t_config_tradition import canonicalize_lemma


# ==========================================================
# F1. SEED LEXICONS
# ==========================================================
# These sets are Stanza-lemmatised Czech (BKR) forms.  Every entry must
# match the lemma string that Stanza cs-pdt produces — NOT the surface form.
#
# Sizing rationale:
#   score_cluster() = matches / total_tokens.  For a 10-token sentence with
#   only 1 match the score is 0.10, barely different from 0.  Expanding each
#   lexicon to 20-30 entries raises typical scores to 0.15-0.30, which gives
#   meaningful discrimination between clusters.

# ── Request / mand ──────────────────────────────────────────────────────────
REQUEST_WORDS: frozenset = frozenset({
    # Original 6
    "dát", "pomoci", "potřebovat", "chtít", "prosit", "moci",
    # BKR imperative / request verbs
    "jít", "přijít", "vzít", "přinést", "nést", "donést",
    "zachránit", "vysvobodit", "vyslyšet", "naklonit",
    "žádat", "naléhat", "volat", "křičet",
    "hledat", "toužit", "doufat", "čekat",
    "slyšet", "poslouchat", "dbát", "dbáti",
    # Deontic / modal
    "muset", "smět", "mít",
    # Performative giving/sending
    "poslat", "posílat", "udělat", "učinit",
})

# ── Description / state ──────────────────────────────────────────────────────
# Very small original set (3) meant that score_cluster returned ~0 for almost
# every sentence; the entire description signal came from the structural
# bonuses (see F2).  The expanded set lets the base score contribute.
DESCRIPTION_WORDS: frozenset = frozenset({
    # Original 3
    "být", "existovat", "stvořit",
    # Stative presence / dwelling (common in BKR)
    "přebývat", "dlít", "dlíti", "přebýti",
    "zůstávat", "zůstat", "trvat", "setrvat",
    # Copular / attributive
    "jevit", "zdát", "zdáti", "vypadat",
    "stávat", "stát",
    # Existential / locative
    "nacházet", "ležet", "sedět",
    # Named / identified as
    "nazývat", "nazvat", "jmenovat", "zvát",
    "znamenat", "sloužit",
    # Attributive possession
    "patřit", "náležet", "vlastnit",
    # Creation / formation
    "učinit", "udělat", "vytvořit", "utvořit", "zformovat",
})

# ── Reported speech ──────────────────────────────────────────────────────────
REPORTED_SPEECH_WORDS: frozenset = frozenset({
    # Original 5
    "říci", "odpovědět", "mluvit", "volat", "pravit",
    # Extended speech verbs (Stanza lemmas from BKR)
    "promluvit", "oznámit", "zvěstovat", "kázat",
    "vzkázat", "hlásit", "ohlásit", "vypravovat",
    "svědčit", "vyznávat", "přiznat",
    "tázat", "ptát", "zpovídat",
    "napsat", "psát",
})

# ── Uncertainty / epistemic hedge ────────────────────────────────────────────
UNCERTAINTY_WORDS: frozenset = frozenset({
    # Original 4
    "možná", "snad", "asi", "myslet",
    # Extended hedge markers
    "domnívat", "pochybovat", "zdát", "zdáti",
    "připadnout", "pravděpodobně",
    "nevědět", "neznát", "tázat", "ptát",
    "nejistý", "pochybný",
    "hádat", "odhadovat",
})

# ── Negation ─────────────────────────────────────────────────────────────────
NEGATION_WORDS: frozenset = frozenset({
    # Original 5
    "ne", "nikdy", "nic", "žádný", "nikdo",
    # Extended (Stanza lemma forms)
    "žádná", "žádné",
    "nikoliv", "nikoli",
    "ani",                  # "ani X ani Y" = neither
    "bez",                  # "bez Boha" = without God
    "nelze",
    "nebudeš",              # archaic 2sg negative future (not lemmatised away)
    "zakázat",              # prohibitive verb
    "zapírat",
})


# ==========================================================
# F2. STRUCTURAL BONUS CONSTANTS FOR description_score
# ==========================================================
#
# score_cluster() = matches / total_tokens.  For a 10-token sentence:
#   1 DESCRIPTION_WORDS match → 0.10 — loses to a request sentence with
#   2 matches (0.20) even when the sentence is clearly descriptive.
#
# The structural bonuses compensate for this density dilution:
#
#   _DESC_ROOT_BONUS (+0.40)
#     Applied when the dependency-tree root lemma is a descriptive verb.
#     Rationale: the syntactic head of the sentence is the MOST semantically
#     representative token; if it is a copula or stative verb, the sentence
#     is structurally descriptive independent of other tokens.
#     The value 0.40 ensures that even for a 15-token sentence with a single
#     DESCRIPTION_WORDS match (base = 0.067), the boosted score is 0.467 —
#     above a typical request score (0.10–0.25) in neutral narrative text.
#
#   _DESC_COPULAR_BONUS (+0.50)
#     Applied when local_pattern == "copular_description" (cop+nsubj deps).
#     Rationale: the copular dependency structure is the strongest syntactic
#     diagnostic for attribute / identity predication.  It is detected by the
#     dependency parser independently of vocabulary, so it can fire even when
#     DESCRIPTION_WORDS lexicon coverage is absent.  +0.50 ensures this
#     signal always wins the semantic_cluster decision (caps at 1.0).
#
# Re-evaluation trigger: if the expanded DESCRIPTION_WORDS lexicon (F1)
# already pushes typical scores above 0.35, the root bonus may be reduced
# to 0.25; run the calibration query in the test block to check.

_DESC_ROOT_BONUS:    float = 0.40
_DESC_COPULAR_BONUS: float = 0.50


# ==========================================================
# F3. OUTPUT DATACLASS
# ==========================================================

@dataclass
class SemanticFeatures:
    sentence_id: int
    sentence: str

    request_score: float
    description_score: float
    uncertainty_score: float
    negation_score: float

    lexical_reinforcement: float
    opposition_present: bool

    # One of: request, description, uncertainty, negation, neutral.
    # "neutral" means no curated semantic seed scored above 0.
    semantic_cluster: str

    # Optional: cluster assigned by embedding similarity, if an embedding
    # model was loaded (see F4).  None when no model is available.
    embedding_cluster: Optional[str] = dc_field(default=None)


# ==========================================================
# F4. FASTTEXT EMBEDDING SCORER
# ==========================================================
#
# Architecture:
#   FastTextScorer wraps the fasttext Python package (fasttext-wheel).
#   It loads models/bkr_fasttext.bin (trained by setup_fasttext_model.py)
#   and assigns embedding_cluster by comparing the sentence average vector
#   to pre-computed cluster centroids (from seed lexicons F1).
#
#   fasttext.get_word_vector() handles OOV via subword n-grams, making it
#   robust to BKR archaic forms that are missing from generic Czech corpora.
#
# Fallback chain:
#   1. FastText (fasttext package + models/bkr_fasttext.bin) — preferred
#   2. gensim KeyedVectors (legacy hook, for .kv/.bin files)
#   3. None → embedding_cluster stays None; lexicon scores take over

_CLUSTER_SEEDS: dict[str, frozenset] = {
    "request":     REQUEST_WORDS,
    "description": DESCRIPTION_WORDS,
    "uncertainty": UNCERTAINTY_WORDS,
    "negation":    NEGATION_WORDS,
}

_FASTTEXT_MODEL_PATH: Path = MODELS_DIR / "bkr_fasttext.bin"
_SIM_THRESHOLD: float = 0.20   # minimum cosine similarity to assign a cluster


class FastTextScorer:
    """
    Embedding-based semantic cluster scorer using fasttext.

    Loaded once at module level via _get_embedding_scorer().
    Returns None from score() when the sentence has no recognisable vocabulary.
    """

    def __init__(self, model, centroids: dict[str, np.ndarray]):
        self._model    = model
        self._centroids = centroids   # {cluster: unit-norm centroid vector}

    @classmethod
    def load(cls, model_path: Path = _FASTTEXT_MODEL_PATH) -> Optional["FastTextScorer"]:
        if not model_path.exists():
            return None
        try:
            import fasttext as _ft
            model = _ft.load_model(str(model_path))
            centroids: dict[str, np.ndarray] = {}
            for cluster, seeds in _CLUSTER_SEEDS.items():
                vecs = np.array([model.get_word_vector(w) for w in seeds],
                                dtype=np.float32)
                centroid = vecs.mean(axis=0)
                norm = np.linalg.norm(centroid)
                centroids[cluster] = centroid / norm if norm else centroid
            return cls(model, centroids)
        except Exception:
            return None

    def score(self, words: list[str]) -> Optional[str]:
        if not words:
            return None
        vecs = np.array(
            [self._model.get_word_vector(w.lower()) for w in words if w],
            dtype=np.float32,
        )
        if len(vecs) == 0:
            return None
        sent_vec = vecs.mean(axis=0)
        norm = float(np.linalg.norm(sent_vec))
        if norm == 0:
            return None
        sent_unit = sent_vec / norm

        best_cluster, best_sim = None, _SIM_THRESHOLD
        for cluster, centroid in self._centroids.items():
            sim = float(np.dot(sent_unit, centroid))
            if sim > best_sim:
                best_sim, best_cluster = sim, cluster
        return best_cluster


class _GensimFallback:
    """Legacy gensim-based scorer (kept for .kv / Word2Vec .bin models)."""

    MODEL_PATH: Optional[Path] = None

    def __init__(self, model=None):
        self._model = model

    @classmethod
    def load(cls) -> Optional["_GensimFallback"]:
        if cls.MODEL_PATH and cls.MODEL_PATH.exists():
            try:
                from gensim.models import KeyedVectors as _KV
                return cls(model=_KV.load(str(cls.MODEL_PATH)))
            except Exception:
                return None
        try:
            import gensim  # noqa: F401
            return cls(model=None)
        except ImportError:
            return None

    def score(self, words: list[str]) -> Optional[str]:
        lowered = [w.lower() for w in words if w]
        if self._model is not None:
            vecs = []
            for w in lowered:
                try:
                    vecs.append(self._model[w])
                except KeyError:
                    pass
            if not vecs:
                return None
            sent_vec = np.mean(vecs, axis=0)
            best_cluster, best_sim = "neutral", -1.0
            for cluster, seeds in _CLUSTER_SEEDS.items():
                seed_vecs = [self._model[sw] for sw in seeds if sw in self._model]
                if not seed_vecs:
                    continue
                centroid = np.mean(seed_vecs, axis=0)
                denom = np.linalg.norm(sent_vec) * np.linalg.norm(centroid)
                sim = float(np.dot(sent_vec, centroid) / denom) if denom else 0.0
                if sim > best_sim:
                    best_sim, best_cluster = sim, cluster
            return best_cluster if best_sim > _SIM_THRESHOLD else None
        # Prototype lexicon overlap fallback
        scores = {
            c: sum(1 for w in lowered if w in s) / max(len(lowered), 1)
            for c, s in _CLUSTER_SEEDS.items()
        }
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else None


# Module-level singleton — loaded once on first call to semantic_enrichment.
_EMBEDDING_SCORER: Optional[FastTextScorer | _GensimFallback] = None
_EMBEDDING_CHECKED: bool = False


def _get_embedding_scorer():
    global _EMBEDDING_SCORER, _EMBEDDING_CHECKED
    if not _EMBEDDING_CHECKED:
        _EMBEDDING_CHECKED = True
        scorer = FastTextScorer.load()
        if scorer is None:
            scorer = _GensimFallback.load()
        _EMBEDDING_SCORER = scorer
    return _EMBEDDING_SCORER


# ==========================================================
# F5. SCORING HELPERS
# ==========================================================

def score_cluster(words: list[str], cluster: frozenset) -> float:
    """
    Lexical density score = matches / total_tokens.

    Returns 0.0 for empty input.  Higher = sentence vocabulary is more
    concentrated in the given cluster.
    """
    if not words:
        return 0.0
    matches = sum(1 for w in words if w.lower() in cluster)
    return matches / len(words)


def lexical_reinforcement(words: list[str]) -> float:
    """
    Return the density of the highest-scoring cluster.

    > 0 only when ≥ 2 words from the same cluster appear in the sentence,
    signalling formulaic / ritual repetition.
    """
    if not words:
        return 0.0

    lowered = [w.lower() for w in words]
    cluster_hits = max(
        sum(1 for w in lowered if w in REQUEST_WORDS),
        sum(1 for w in lowered if w in DESCRIPTION_WORDS),
        sum(1 for w in lowered if w in REPORTED_SPEECH_WORDS),
        sum(1 for w in lowered if w in UNCERTAINTY_WORDS),
        sum(1 for w in lowered if w in NEGATION_WORDS),
    )

    if cluster_hits <= 1:
        return 0.0

    return round(cluster_hits / len(lowered), 3)


def opposition_present(words: list[str]) -> bool:
    tokens = {canonicalize_lemma(w) for w in words if w}
    return opposition_present_in(tokens)


# ==========================================================
# F6. MAIN ENRICHMENT
# ==========================================================

def semantic_enrichment(
    features: List[SentenceFeatures],
) -> List[SemanticFeatures]:

    results = []
    scorer  = _get_embedding_scorer()

    for f in features:
        words = f.lemmas.split()

        # ── Lexical density scores ───────────────────────────────────────────
        request_score     = score_cluster(words, REQUEST_WORDS)
        description_score = score_cluster(words, DESCRIPTION_WORDS)
        uncertainty_score = score_cluster(words, UNCERTAINTY_WORDS)
        negation_score    = score_cluster(words, NEGATION_WORDS)

        # ── Structural bonuses for description (see F2 for rationale) ───────
        # Guard: bonuses are suppressed when uncertainty or negation already
        # score higher than a threshold — e.g. "Možná to tak je" is a hedged
        # copular sentence but semantically belongs to "uncertainty", not
        # "description".  Threshold 0.18 ≈ 1.5 hits / 8-token sentence.
        _override_threshold = 0.18
        _has_override = (
            uncertainty_score > _override_threshold
            or negation_score  > _override_threshold
        )

        if (
            not _has_override
            and f.root_lemma
            and f.root_lemma.lower() in DESCRIPTION_WORDS
        ):
            description_score += _DESC_ROOT_BONUS

        if (
            not _has_override
            and f.local_pattern == "copular_description"
        ):
            description_score += _DESC_COPULAR_BONUS

        # ── Clamp all scores to [0, 1] ───────────────────────────────────────
        request_score     = min(request_score,     1.0)
        description_score = min(description_score, 1.0)
        uncertainty_score = min(uncertainty_score, 1.0)
        negation_score    = min(negation_score,    1.0)

        # ── Optional embedding cluster ───────────────────────────────────────
        embedding_cluster: Optional[str] = None
        if scorer is not None and words:
            embedding_cluster = scorer.score(words)

        # ── Lexical cluster decision ─────────────────────────────────────────
        scores = {
            "request":     request_score,
            "description": description_score,
            "uncertainty": uncertainty_score,
            "negation":    negation_score,
        }
        max_score = max(scores.values())
        semantic_cluster = (
            "neutral" if max_score == 0
            else max(scores, key=scores.get)
        )

        # Fallback: embedding resolves sentences without any lexical signal
        if semantic_cluster == "neutral" and embedding_cluster is not None:
            semantic_cluster = embedding_cluster

        results.append(
            SemanticFeatures(
                sentence_id=f.sentence_id,
                sentence=f.sentence,
                request_score=round(request_score,     3),
                description_score=round(description_score, 3),
                uncertainty_score=round(uncertainty_score, 3),
                negation_score=round(negation_score,    3),
                lexical_reinforcement=lexical_reinforcement(words),
                opposition_present=opposition_present(words),
                semantic_cluster=semantic_cluster,
                embedding_cluster=embedding_cluster,
            )
        )

    return results


def export_semantics_csv(semantics: List[SemanticFeatures], output_path: str):

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    from dataclasses import asdict
    rows = [asdict(s) for s in semantics]

    if not rows:
        raise ValueError("No semantics to export.")

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


# ==========================================================
# TEST BLOCK
# ==========================================================

if __name__ == "__main__":

    from c_input import create_input_from_text
    from d_preprocessing import preprocess_text
    from e_extraction import extract_features

    _TESTS = [
        # (sentence, expected_cluster, description)
        ("Dej mi vodu.",                      "request",     "clear request — imperative"),
        ("Prosím, pomoz mi!",                 "request",     "request verbs"),
        ("Hospodin jest dobrý pastýř.",        "description", "copular → description"),
        ("Na počátku stvořil Bůh nebe.",       "description", "stvořit root → description"),
        ("Možná to tak je, snad přijde.",      "uncertainty", "hedge markers"),
        ("Nikdo nikdy nepřišel.",              "negation",    "negation words"),
        ("Šel do města.",                      "neutral",     "neutral narrative"),
    ]

    print("=== Lexicon sizes ===")
    for name, lex in [
        ("REQUEST_WORDS",       REQUEST_WORDS),
        ("DESCRIPTION_WORDS",   DESCRIPTION_WORDS),
        ("REPORTED_SPEECH",     REPORTED_SPEECH_WORDS),
        ("UNCERTAINTY_WORDS",   UNCERTAINTY_WORDS),
        ("NEGATION_WORDS",      NEGATION_WORDS),
    ]:
        print(f"  {name:<22} {len(lex):>3} lemmas")
    print()

    print(f"=== Structural bonuses ===")
    print(f"  _DESC_ROOT_BONUS    = {_DESC_ROOT_BONUS}")
    print(f"  _DESC_COPULAR_BONUS = {_DESC_COPULAR_BONUS}")
    print()

    embedding_scorer = _get_embedding_scorer()
    print(f"=== Embedding scorer ===")
    if isinstance(embedding_scorer, FastTextScorer):
        print(f"  Mode: FastText  ({_FASTTEXT_MODEL_PATH})")
        print(f"  Clusters: {sorted(embedding_scorer._centroids)}")
    elif isinstance(embedding_scorer, _GensimFallback) and embedding_scorer._model:
        print("  Mode: gensim KeyedVectors (legacy)")
    elif embedding_scorer:
        print("  Mode: prototype lexicon overlap (no model loaded)")
    else:
        print(f"  Mode: disabled — run setup_fasttext_model.py to create {_FASTTEXT_MODEL_PATH}")
    print()

    sample = create_input_from_text(
        text=" ".join(s for s, *_ in _TESTS),
        source="written_record",
    )
    preprocessed = preprocess_text(sample)
    features_list = extract_features(preprocessed)
    semantics = semantic_enrichment(features_list)

    # Align results (Stanza may produce different segmentation)
    print(f"{'VETA':<45} {'cluster':<14} {'req':>5} {'desc':>5} {'unc':>5} {'neg':>5} {'emb'}")
    print("-" * 100)
    for s in semantics:
        print(
            f"{s.sentence[:43]:<45} "
            f"{s.semantic_cluster:<14} "
            f"{s.request_score:>5.3f} "
            f"{s.description_score:>5.3f} "
            f"{s.uncertainty_score:>5.3f} "
            f"{s.negation_score:>5.3f} "
            f"{s.embedding_cluster or '-'}"
        )

    export_semantics_csv(semantics, "output/semantics_for_flourish.csv")
    print("\nCSV exported: output/semantics_for_flourish.csv")
