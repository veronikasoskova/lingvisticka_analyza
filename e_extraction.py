from dataclasses import dataclass, asdict
from typing import List, Optional
import csv
from pathlib import Path

from d_preprocessing import (
    PreprocessedText,
    SentenceData
)


# Subordinate clause dependency relations — shared with y_dependency_hierarchy.py
_CLAUSE_DEPS = frozenset({
    "advcl", "relcl", "acl", "csubj", "ccomp", "xcomp", "parataxis",
})


@dataclass
class SentenceFeatures:
    sentence_id: int
    sentence: str

    token_count: int

    noun_count: int
    verb_count: int
    aux_count: int
    pronoun_count: int
    adjective_count: int
    adverb_count: int

    has_question: bool
    has_negation: bool
    has_modal: bool
    is_imperative_like: bool
    has_conditional: bool

    root_token: Optional[str]
    root_lemma: Optional[str]
    root_pos: Optional[str]
    root_tense: str

    subject_present: bool
    object_present: bool
    indirect_object_present: bool
    dative_present: bool

    dependency_pattern: str
    dependency_set: str
    root_children_deps: str
    root_children_text: str

    # ── new (E task) ──────────────────────────────────────────
    word_count: int             # non-PUNCT token count
    type_token_ratio: float     # unique lemmas / total lemmas (lexical diversity)
    clause_count: int           # 1 + subordinate clause dep count
    has_coordination: bool      # cc or conj dependency present
    dep_tree: str               # parenthetical dependency tree (depth ≤ 2)
    # ─────────────────────────────────────────────────────────

    local_pattern: str
    lemmas: str


def count_pos(sentence: SentenceData, pos_type: str) -> int:
    return sum(
        1 for token in sentence.tokens
        if token.pos == pos_type
    )


def get_root_token(sentence: SentenceData):
    for token in sentence.tokens:
        if token.dep == "root":
            return token
    return None


def has_question(sentence: SentenceData) -> bool:
    return "?" in sentence.text


def has_negation(sentence: SentenceData) -> bool:
    """
    Detect negation at three levels:

    1. Standalone negation particles / pronouns / adverbs
       ("ne", "nikdy", "nic", "žádný", "nikdo", "nikoliv")

    2. Syntactic negation dependency label
       (dep == "advmod:neg")

    3. Prefix-negation on verbs, adjectives, adverbs
       Stanza marks fused `ne-` with Polarity=Neg in morphological features.
       Examples: "nepůjdeš" (text="nepůjdeš", lemma="jít", Polarity=Neg),
                 "nespravedlivý" (Polarity=Neg).
       Also catches the feats string "Polarity=Neg" for tokens without
       feats_dict (old preprocessing path).
    """
    _NEG_WORDS = frozenset({
        "ne", "nikdy", "nic",
        "žádný", "žádná", "žádné",
        "nikdo", "nikoliv", "nikoli",
        "nijak", "nikde", "nikam",
    })

    for token in sentence.tokens:
        # Level 1 — standalone particle or pronoun
        if token.lemma.lower() in _NEG_WORDS or token.text.lower() in _NEG_WORDS:
            return True

        # Level 2 — syntactic negation dep
        if token.dep == "advmod:neg":
            return True

        # Level 3 — prefix-negation via morphological Polarity=Neg
        # (Stanza sets this for indicative negated verbs and adjectives)
        feats_d = getattr(token, "feats_dict", None)
        if feats_d is not None:
            if feats_d.get("Polarity") == "Neg":
                return True
        elif "Polarity=Neg" in (token.feats or ""):
            return True

        # Level 4 — text/lemma mismatch fallback for negated imperatives and
        # forms where Stanza omits Polarity=Neg (e.g. "nebuďte", "nepůjdte").
        # Rule: content token whose surface form starts "ne" but whose lemma
        # does NOT start "ne" → the "ne-" is a derivational negation prefix.
        # Excludes lexicalised "ne-" words ("nést", "nechat", "nenávidět")
        # because for those the lemma also starts with "ne".
        #
        # Known limitation: Stanza cs-pdt sometimes mislemmatises negated
        # imperatives as unrelated "ne-" verbs (e.g. "Nechoď" → lemma "nechat"),
        # which puts both text and lemma under "ne-" and prevents this check.
        # Such sentences are still correctly classified as imperative_action_object
        # via is_imperative_like(), so the negation aspect is the only gap.
        if token.pos in {"VERB", "AUX", "ADJ", "ADV"}:
            t_lower = token.text.lower()
            l_lower = (token.lemma or "").lower()
            if t_lower.startswith("ne") and not l_lower.startswith("ne"):
                return True

    return False


def has_modal(sentence: SentenceData) -> bool:
    # "musit" is an accepted alternative infinitive for "muset" in cs-pdt.
    # "lze" is an impersonal frozen modal form (no inflection, no lemma variant).
    _MODALS = frozenset({"moci", "muset", "musit", "chtít", "smět", "lze"})

    for token in sentence.tokens:
        lemma = token.lemma.lower()
        if lemma in _MODALS:
            return True
        # "mít" is only modal when governing an infinitive via xcomp
        # ("Máš mlčet" = you should be silent), not in the possessive sense
        # ("Mám dům" = I have a house).
        if lemma == "mít":
            if any(
                t.head_id == token.id and t.dep == "xcomp" and t.pos in {"VERB", "AUX"}
                for t in sentence.tokens
            ):
                return True

    return False


def subject_present(sentence: SentenceData) -> bool:
    return any(
        token.dep in {"nsubj", "csubj"}
        for token in sentence.tokens
    )


def object_present(sentence: SentenceData) -> bool:
    return any(
        token.dep == "obj"
        for token in sentence.tokens
    )


# Dependency proxy for indirect object relation.
# Not equivalent to grammatical dative.

def indirect_object_present(sentence: SentenceData) -> bool:
    return any(
        token.dep in {"iobj", "obl:arg"}
        for token in sentence.tokens
    )


# Morphological dative detection via Stanza features.

def dative_present(sentence: SentenceData) -> bool:
    return any(
        "Case=Dat" in token.feats
        for token in sentence.tokens
    )


def root_tense_from_sentence(sentence: SentenceData) -> str:
    """Return Tense value from root token feats; falls back to cop/aux tense (copular sentences)."""
    root = get_root_token(sentence)
    if root is None:
        return ""
    tense = root.feats_dict.get("Tense", "")
    if tense:
        return tense
    # Kopulárna konštrukcia: root je nominál, tense nesie cop/aux závislý od root
    for token in sentence.tokens:
        if token.head_id == root.id and token.dep in {"cop", "aux", "aux:pass"}:
            tense = token.feats_dict.get("Tense", "")
            if tense:
                return tense
    return ""


def is_imperative_like(sentence: SentenceData) -> bool:
    """
    Sentence-level imperative detection.

    Dispatches to per-language logic based on d_preprocessing.PIPELINE_LANG.
    Mirrors g_skinner_rules.is_imperative_like(token, lang) but avoids the
    circular-import constraint (g_skinner_rules imports SentenceFeatures from
    here, so we cannot import back from there).

    Language behaviour
    ------------------
    cs / sk : feats_dict Mood=Imp (primary) + surface suffix fallback
              (BKR / snk models don't always tag archaic imperatives).
    en      : feats_dict Mood=Imp (primary)
              + hortative "let" at ROOT
              + ROOT base-form verb with no Tense/Person (archaic EN fallback)
    """
    import d_preprocessing as _dp
    lang = _dp.PIPELINE_LANG

    for token in sentence.tokens:
        feats_d   = getattr(token, "feats_dict", None)
        feats_str = token.feats or ""
        pos       = token.pos
        text      = token.text.lower().strip(".,;:!?")
        dep       = getattr(token, "dep", "")
        lemma     = getattr(token, "lemma", text)

        mood_imp = (
            feats_d.get("Mood") == "Imp"
            if feats_d is not None
            else "Mood=Imp" in feats_str
        )

        # ── primary: Stanza Mood=Imp (reliable for cs-pdt, sk-snk, en-ewt) ─
        if pos in {"VERB", "AUX"} and mood_imp:
            return True

        # ── cs / sk suffix fallback ──────────────────────────────────────────
        if lang in {"cs", "sk"}:
            if pos == "VERB" and (
                text.endswith("ej") or text.endswith("aj") or text.endswith("uj")
            ):
                return True
            # negated imperatives: ne-Xej / ne-Xaj / ne-Xuj
            if pos == "VERB" and text.startswith("ne") and (
                text.endswith("ej") or text.endswith("aj") or text.endswith("uj")
            ):
                return True
            # Slovak 2pl endings not always tagged
            if lang == "sk" and pos == "VERB" and (
                text.endswith("ajte") or text.endswith("ujte")
                or (text.endswith("te") and len(text) > 4)
            ):
                return True

        # ── English supplementary signals ────────────────────────────────────
        if lang == "en":
            # Hortative "let": "Let there be light", "Let us go"
            if lemma == "let" and pos == "VERB" and dep.lower() == "root":
                return True
            # Archaic / biblical EN: ROOT base-form verb without subject agreement
            if pos == "VERB" and dep.lower() == "root":
                no_tense  = not (feats_d.get("Tense")  if feats_d else "Tense="  in feats_str)
                no_person = not (feats_d.get("Person") if feats_d else "Person=" in feats_str)
                if no_tense and no_person:
                    return True

    return False


def has_conditional(sentence: SentenceData) -> bool:
    """
    True if the sentence opens with a conditional connector.

    Handles two surface patterns:
    - SCONJ/ADV with Mood=Cnd directly (e.g. jestliže tagged by some models)
    - Stanza cs-pdt MWT split: kdyby → Když (SCONJ, no feats) + by (AUX, Mood=Cnd).
      Detection: first SCONJ in first 3 tokens has lemma "když" AND any of
      the first 3 tokens carries Mood=Cnd.  The lemma guard prevents matching
      mid-sentence "by" in constructions like "udělal by" (conditional verb).
    """
    head = sentence.tokens[:3]

    # Pattern 1: SCONJ/ADV directly tagged Mood=Cnd
    for token in head:
        if token.pos not in {"SCONJ", "ADV"}:
            continue
        feats_d   = getattr(token, "feats_dict", None)
        feats_str = token.feats or ""
        mood_cnd  = (
            feats_d.get("Mood") == "Cnd"
            if feats_d is not None
            else "Mood=Cnd" in feats_str
        )
        if mood_cnd:
            return True

    # Pattern 2: MWT split — Když (SCONJ) + by (AUX Mood=Cnd)
    head_sconj_lemmas = {
        getattr(t, "lemma", "").lower()
        for t in head
        if t.pos == "SCONJ"
    }
    if "když" in head_sconj_lemmas:
        for token in head:
            feats_d   = getattr(token, "feats_dict", None)
            feats_str = token.feats or ""
            mood_cnd  = (
                feats_d.get("Mood") == "Cnd"
                if feats_d is not None
                else "Mood=Cnd" in feats_str
            )
            if mood_cnd:
                return True

    return False


def dependency_pattern(sentence: SentenceData) -> str:
    return " -> ".join(
        token.dep for token in sentence.tokens
    )


def dependency_set(sentence: SentenceData) -> str:
    deps = sorted(
        set(
            token.dep
            for token in sentence.tokens
            if token.dep != "punct"
        )
    )
    return ", ".join(deps)


def root_children_deps(sentence: SentenceData) -> str:
    root = get_root_token(sentence)

    if root is None:
        return ""

    children = [
        token.dep
        for token in sentence.tokens
        if (
           token.head_id == root.id
          and token.dep != "punct"
       )
    ]

    return ", ".join(children)


def root_children_text(sentence: SentenceData) -> str:
    root = get_root_token(sentence)

    if root is None:
        return ""

    children = [
        token.text
        for token in sentence.tokens
        if (
            token.head_id == root.id
            and token.dep != "punct"
       )
    ]

    return ", ".join(children)


# ==========================================================
# NEW EXTRACTION FUNCTIONS (E task)
# ==========================================================

def word_count(sentence: SentenceData) -> int:
    """Non-PUNCT token count — actual words in the sentence."""
    return sum(1 for t in sentence.tokens if t.pos != "PUNCT")


def type_token_ratio(sentence: SentenceData) -> float:
    """
    Lexical diversity: unique lemmas / total lemmas (excluding punctuation).

    Values near 1.0 = high lexical variety (each word used once).
    Values near 0.0 = heavy repetition (few distinct words).
    Useful for distinguishing formulaic ritual text from narrative prose.
    """
    lemmas = [
        t.lemma.lower()
        for t in sentence.tokens
        if t.pos != "PUNCT" and t.lemma
    ]
    if not lemmas:
        return 0.0
    return round(len(set(lemmas)) / len(lemmas), 4)


def clause_count(sentence: SentenceData) -> int:
    """
    Total clause count = 1 (main clause) + number of subordinate clause deps.

    Subordinate clause dep relations counted: advcl, relcl, acl, csubj,
    ccomp, xcomp, parataxis  (same set as y_dependency_hierarchy.py).

    Returns at least 1 for any non-empty sentence.
    """
    subordinate = sum(
        1 for t in sentence.tokens if t.dep.split(":")[0] in _CLAUSE_DEPS
    )
    return 1 + subordinate


def has_coordination(sentence: SentenceData) -> bool:
    """
    True if the sentence contains syntactic coordination.

    Detects:
    - dep == "cc"   (coordinating conjunction: "a", "nebo", "ale", "and", "but")
    - dep == "conj" (conjunct: the second conjoint of a coordinate structure)
    """
    return any(t.dep in {"cc", "conj"} for t in sentence.tokens)


def dep_tree(sentence: SentenceData, max_depth: int = 2) -> str:
    """
    Parenthetical dependency tree rooted at the sentence root.

    Format (depth ≤ max_depth): root_lemma(dep:child(dep:grandchild), ...)
    Punctuation tokens are excluded.

    Examples
    --------
    "Dej mi vodu."
        → "dát(iobj:já, obj:voda)"

    "Hospodin jest Bůh váš."
        → "být(nsubj:hospodin, nsubj:bůh)"

    "Neboť tak Bůh miloval svět."
        → "milovat(advmod:tak, nsubj:bůh, obj:svět)"

    The tree representation captures parent–child relations that the linear
    dependency_pattern field (token-order dep labels) cannot express.
    """
    root = get_root_token(sentence)
    if root is None:
        return ""

    # Build id→token map for fast lookup
    id_map = {t.id: t for t in sentence.tokens}

    def _node(token_id: int, depth: int) -> str:
        tok = id_map.get(token_id)
        if tok is None:
            return "?"
        lemma = (tok.lemma or tok.text).lower()
        if depth == 0:
            return lemma
        children = [
            t for t in sentence.tokens
            if t.head_id == token_id and t.dep != "punct"
        ]
        if not children:
            return lemma
        parts = [f"{c.dep}:{_node(c.id, depth - 1)}" for c in children]
        return f"{lemma}({', '.join(parts)})"

    return _node(root.id, max_depth)


# ==========================================================
# PATTERN DETECTION
# ==========================================================

def detect_local_pattern(sentence: SentenceData) -> str:
    """
    Assign a single local structural label to the sentence.

    Priority waterfall — each level is checked in this fixed order.
    The first matching pattern wins; lower patterns are not evaluated.

    Priority rationale
    ------------------
    1. modal_question_request_like
       Checked first because a modal + question combination is a highly
       specific illocutionary signal (indirect request, rhetorical possibility
       question) that must take precedence over both "plain question" and
       "copular/general" patterns.  Example: "Můžeš mi pomoci?"

    2. imperative_action_object
       Checked before copular and negation because imperative sentences are
       the primary directive act.  An imperative with negation ("Nechoď!") is
       still a command, not a negated_statement.  An imperative that happens
       to be copular in surface form ("Buď silný!") is still a command.

    3. copular_description
       Checked before bare question and negated_statement.  The cop+nsubj
       dependency pair is a reliable structural marker for identity/state
       assertions (declaring, justifying).  A negated copular ("Nejsi prorok")
       is classified here — the negation is captured separately by has_negation
       and does not override the copular structure.

    4. question_structure
       Checked after copular because "?"-marked copular sentences were already
       captured in step 1 (modal_question) or step 3 (copular_description).
       This step handles plain direct questions.

    5. negated_statement
       Catches sentences with negation that are not imperative, copular, or
       questions.  Negation is secondary to structural patterns but is
       analytically important for condemning/autoclitic classification.

    6. general_statement  (fallback)
       Any sentence that does not match patterns 1–5.
    """
    # 1 — modal + question → indirect request / rhetorical possibility
    if has_modal(sentence) and has_question(sentence):
        return "modal_question_request_like"

    # 2 — imperative → primary directive act
    if is_imperative_like(sentence):
        return "imperative_action_object"

    deps = {token.dep for token in sentence.tokens}

    # 3 — copular structure → identity / state assertion
    if "cop" in deps and "nsubj" in deps:
        return "copular_description"

    # 4 — plain question
    if has_question(sentence):
        return "question_structure"

    # 5 — negated non-copular, non-imperative, non-question sentence
    if has_negation(sentence):
        return "negated_statement"

    # 6 — fallback
    return "general_statement"


# ==========================================================
# MAIN EXTRACTION
# ==========================================================

def extract_features(
    preprocessed: PreprocessedText
) -> List[SentenceFeatures]:

    results = []

    for index, sentence in enumerate(preprocessed.sentences, start=1):

        root = get_root_token(sentence)

        features = SentenceFeatures(
            sentence_id=index,
            sentence=sentence.text,

            token_count=len(sentence.tokens),

            noun_count=count_pos(sentence, "NOUN"),
            verb_count=count_pos(sentence, "VERB"),
            aux_count=count_pos(sentence, "AUX"),
            pronoun_count=count_pos(sentence, "PRON"),
            adjective_count=count_pos(sentence, "ADJ"),
            adverb_count=count_pos(sentence, "ADV"),

            has_question=has_question(sentence),
            has_negation=has_negation(sentence),
            has_modal=has_modal(sentence),
            is_imperative_like=is_imperative_like(sentence),
            has_conditional=has_conditional(sentence),

            root_token=root.text if root else None,
            root_lemma=root.lemma if root else None,
            root_pos=root.pos if root else None,
            root_tense=root_tense_from_sentence(sentence),

            subject_present=subject_present(sentence),
            object_present=object_present(sentence),
            indirect_object_present=indirect_object_present(sentence),
            dative_present=dative_present(sentence),

            dependency_pattern=dependency_pattern(sentence),
            dependency_set=dependency_set(sentence),
            root_children_deps=root_children_deps(sentence),
            root_children_text=root_children_text(sentence),

            word_count=word_count(sentence),
            type_token_ratio=type_token_ratio(sentence),
            clause_count=clause_count(sentence),
            has_coordination=has_coordination(sentence),
            dep_tree=dep_tree(sentence),

            local_pattern=detect_local_pattern(sentence),
            lemmas=" ".join(
              token.lemma.lower()
              for token in sentence.tokens
              if token.lemma and token.pos != "PUNCT"
            ),
        )

        results.append(features)

    return results


def export_features_to_csv(
    features: List[SentenceFeatures],
    output_path: str
) -> None:

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    rows = [
        asdict(feature)
        for feature in features
    ]

    if not rows:
        raise ValueError("No features to export.")

    with path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(
            csvfile,
            fieldnames=rows[0].keys()
        )

        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":

    from c_input import create_input_from_text
    from d_preprocessing import preprocess_text

    sample = create_input_from_text(
        text=(
            "Dej mi vodu. "
            "Neodcházej. "
            "Nepůjdeš k nám. "
            "To je pes. "
            "Nejsi prorok. "
            "Může a jde sem i tam. "
            "Neboť tak Bůh miloval svět, že Syna svého jednorozeného dal. "
            "Blahoslavení chudí duchem, nebo jejich jest království nebeské."
        ),
        source="written_record",
        interaction="monologue",
        stimulus="unknown"
    )

    preprocessed = preprocess_text(sample)
    features     = extract_features(preprocessed)

    _FIELDS = [
        "sentence", "word_count", "type_token_ratio", "clause_count",
        "has_coordination", "has_negation", "dep_tree", "local_pattern",
    ]

    print(f"\n{'Sentence':<52} {'wc':>3} {'ttr':>5} {'cl':>3} {'coord':>5} {'neg':>5} {'pat':<26} dep_tree")
    print("-" * 140)
    for f in features:
        print(
            f"{f.sentence[:50]:<52} "
            f"{f.word_count:>3} "
            f"{f.type_token_ratio:>5.3f} "
            f"{f.clause_count:>3} "
            f"{str(f.has_coordination):>5} "
            f"{str(f.has_negation):>5} "
            f"{f.local_pattern:<26} "
            f"{f.dep_tree}"
        )

    export_features_to_csv(features, "output/features_for_flourish.csv")
    print("\nCSV exported: output/features_for_flourish.csv")
