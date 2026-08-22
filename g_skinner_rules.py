"""B.F. Skinner — Verbal Behavior framework rules and proxy detectors."""

from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from h_classifiers import SkinnerDecision

from e_extraction import SentenceFeatures
from f_semantics import SemanticFeatures
from lexicons_common import STOP_LEMMAS as _REPEATED_STOP_LEMMAS  # unified lemma stopwords


# ==========================================================
# E1. SOURCE TYPES
# ==========================================================

WRITTEN_RECORD_SOURCES = {
    "written_record",
    "uploaded_document",
}


# ==========================================================
# E2. LEXICAL SEEDS
# ==========================================================

REPORTED_SPEECH_LEMMAS = {
    "říci",
    "odpovědět",
    "mluvit",
    "volat",
    "pravit",
}

VISUAL_PERCEPTION_LEMMAS = {
    "vidět",
    "uvidět",
    "uzřít",
    "spatřit",
    "hledět",
}

REVELATION_LEMMAS = {
    "zjevit",
}

# IMPORTANT:
# "hle" is intentionally NOT a tact trigger by itself.
# In biblical Czech it often works as a discourse/deictic marker
# inside reported speech, not as evidence of visual stimulus.
DEICTIC_ATTENTION_LEMMAS = {
    "hle",
    "aj",
}

REPORTED_TEXTUAL_LEMMAS = {
    "číst",
    "přečíst",
    "napsat",
    "napsaný",   # pasívne particípium — lemmatizér vracia ADJ formu
    "psát",
    "psaný",     # pasívne particípium "psáno jest"
    "čtení",
    "citovat",
    "zapsat",
}

TEXTUAL_OBJECT_LEMMAS = {
    "kniha",
    "list",
    "epištola",
    "písmo",
    "zákon",
    "svitek",
    "slovo",
}

CITATION_CHAIN_LEMMAS = {
    "psáno",
    "napsáno",
    "písmo",
    "proroctví",
    "prorok",
    "zákon",
    "praví",
}

DESCRIPTIVE_PREDICATION_LEMMAS = {
    "nazvat",
    "jmenovat",
    "zvat",
}

LOW_RISK_ASSERTIVE_PREDICATION_LEMMAS = {
    # possession / relation
    "mít",
    # persistence / duration
    "zůstávat",
    "zůstat",
    "trvat",
    # residence / abiding
    "přebývat",
    # state-location
    "ležet",
}

HIGH_RISK_ASSERTIVE_PREDICATION_LEMMAS = {
    # habitual conduct / way-of-life, but risky without complement
    "chodit",
    # production / action verbs, too broad without complement
    "činit",
    "dělat",
}

ASSERTIVE_LOCAL_PATTERNS = {
    "general_statement",
    "copular_description",
}

RELATIONAL_STATUS_MARKERS = {
    " z boha ",
    " z světa ",
    " z pravdy ",
    " z otce ",
    " od otce ",

    " v něm ",
    " v nás ",
    " v sobě ",
    " v bohu ",
    " v synu ",
    " v otci ",

    " v smrti ",
    " v životě ",
    " v světle ",
    " v temnosti ",

    " na věky ",
}

PROCESS_STATE_ASSERTION_LEMMAS = {
    "hynout",
    "pomíjet",
    "svítit",
}

FIRST_PERSON_LEMMAS = {
    "já",
    "my",
}

ANSWER_MARKER_LEMMAS = {
    "odpovědět",
    "říci",
    "pravit",
}

ECHOIC_FORMULAS = {
    "amen amen",
    "amen amen amen",
    "svatý svatý",
    "svatý svatý svatý",
    "hosanna hosanna",
    "haleluja haleluja",
    "běda běda",
}

AUTOCLITIC_UNCERTAINTY_LEMMAS = {
    "možná",
    "snad",
    "asi",
    "myslet",
    "domnívat",
    "pochybovat",
}

AUTOCLITIC_SOURCE_LEMMAS = {
    "vědět",
    "znát",
    "poznat",
    "poznávat",
    "slyšet",
    "číst",
}

AUTOCLITIC_EMPHASIS_LEMMAS = {
    "opravdu",
    "jistě",
    "zajisté",
    "vpravdě",
    "amen",
}

AUTOCLITIC_RELATIONAL_LEMMAS = {
    "proto",
    "tedy",
    "neboť",
    "poněvadž",
    "jelikož",
}

AUTOCLITIC_NEGATION_LEMMAS = {
    "ne",
    "nikdy",
    "nic",
    "žádný",
    "nikdo",
}

_EN_IMPERATIVE_LEMMAS = frozenset({
    # motion / presence
    "go", "come", "arise", "rise", "stand", "sit", "return", "flee",
    "walk", "follow",
    # perception / attention
    "listen", "hear", "see", "look", "behold",
    # speech / communication
    "speak", "tell", "say", "cry", "call", "proclaim", "declare",
    # devotional / religious
    "obey", "fear", "love", "worship", "repent", "believe",
    "praise", "pray", "sing", "bless", "sanctify", "serve",
    "trust", "remember", "rejoice",
    # action / transfer
    "keep", "do", "make", "give", "take", "bring", "put", "set",
    "seek", "ask", "receive", "open", "turn",
    # prohibitions (often "do not X")
    "kill", "steal", "lie", "covet", "swear", "murder",
    # existential / hortative
    "be", "let",
})


# ==========================================================
# E2b. LANGUAGE HELPERS
# ==========================================================

def is_imperative_like(token, lang: str = "cs") -> bool:
    """
    Token-level imperative detection.  Returns True if `token` is or
    strongly resembles an imperative verb.

    Uses feats_dict when available (d_preprocessing ≥ 2026-06-04);
    falls back to string search on `token.feats` for backward compat.

    Parameters
    ----------
    token : TokenData
    lang  : "cs" | "sk" | "en"  (default "cs")
    """
    feats_d   = getattr(token, "feats_dict", None)
    feats_str = token.feats or ""
    pos       = getattr(token, "pos", getattr(token, "upos", ""))
    dep       = getattr(token, "dep", "")
    text      = token.text.lower().strip(".,;:!?")
    lemma     = getattr(token, "lemma", text)

    def _mood_imp() -> bool:
        if feats_d is not None:
            return feats_d.get("Mood") == "Imp"
        return "Mood=Imp" in feats_str

    # ── Czech ────────────────────────────────────────────────────────────────
    if lang == "cs":
        if pos in {"VERB", "AUX"} and _mood_imp():
            return True
        # BKR surface fallback: Czech 2sg imperatives → -(e/a/u)j, neg. ne-(e/a/u)j
        if pos == "VERB" and (
            text.endswith("ej") or text.endswith("aj") or text.endswith("uj")
        ):
            return True
        if pos == "VERB" and text.startswith("ne") and (
            text.endswith("ej") or text.endswith("aj") or text.endswith("uj")
        ):
            return True
        return False

    # ── Slovak ───────────────────────────────────────────────────────────────
    if lang == "sk":
        if pos in {"VERB", "AUX"} and _mood_imp():
            return True
        # Slovak 2sg / 2pl imperative suffixes not always tagged by snk model:
        # -i / -te / -aj / -ajte / -uj / -ujte / -í / -íte
        if pos == "VERB" and (
            text.endswith("ajte") or text.endswith("ujte") or text.endswith("íte")
            or text.endswith("aj")  or text.endswith("uj")
            or (text.endswith("te") and len(text) > 4)
        ):
            return True
        return False

    # ── English ──────────────────────────────────────────────────────────────
    if lang == "en":
        # Primary: Stanza tags Mood=Imp for most English imperatives (ewt model).
        if pos in {"VERB", "AUX"} and _mood_imp():
            return True

        # Hortative "let": "Let there be light", "Let us go" — ROOT verb 'let'.
        if lemma == "let" and pos == "VERB" and dep.lower() == "root":
            return True

        # Fallback for cases where Stanza misses Mood=Imp (archaic/biblical EN):
        # ROOT verb in base form (no Tense, no Person agreement) from known list.
        if pos == "VERB" and dep.lower() == "root":
            no_tense  = not (feats_d.get("Tense")  if feats_d else ("Tense="  in feats_str))
            no_person = not (feats_d.get("Person") if feats_d else ("Person=" in feats_str))
            if no_tense and no_person and lemma in _EN_IMPERATIVE_LEMMAS:
                return True

        return False

    return False


# ==========================================================
# E3. GENERIC HELPERS
# ==========================================================

def lemmas_of(
    feature: SentenceFeatures,
) -> List[str]:

    return feature.lemmas.split()


def lemma_set_of(
    feature: SentenceFeatures,
) -> set:

    return set(lemmas_of(feature))


def has_any_lemma(
    feature: SentenceFeatures,
    lemma_set: set,
) -> bool:

    return any(
        lemma in lemma_set
        for lemma in lemmas_of(feature)
    )


def sentence_lower(
    feature: SentenceFeatures,
) -> str:

    return feature.sentence.lower()


# ==========================================================
# E4. TEXTUAL RULE SEARCH
# ==========================================================

def has_passive_textual_pattern(
    feature: SentenceFeatures,
) -> bool:

    return (
        feature.root_lemma in {"psaný", "napsaný"}
        and feature.root_pos == "ADJ"
    )


def has_reported_textual_pattern(
    feature: SentenceFeatures,
) -> bool:

    lemmas = lemma_set_of(feature)

    if lemmas & REPORTED_TEXTUAL_LEMMAS:
        return True

    if has_passive_textual_pattern(feature):
        return True

    return False


def has_textual_trigger_pattern(
    feature: SentenceFeatures,
) -> bool:

    lemmas = lemma_set_of(feature)

    if not (lemmas & TEXTUAL_OBJECT_LEMMAS):
        return False

    sentence = sentence_lower(feature)

    textual_cues = {
        "v knize",
        "v listu",
        "v písmu",
        "v zákoně",
        "v prorocích",
        "podle písma",
        "vedlé písma",
        "psáno",
        "napsáno",
    }

    return any(cue in sentence for cue in textual_cues)


def has_citation_chain_pattern(
    feature: SentenceFeatures,
) -> bool:

    sentence = sentence_lower(feature)
    lemmas = lemma_set_of(feature)

    explicit_citation_phrases = {
        "jakož psáno",
        "jakž psáno",
        "jako psáno",
        "aby se naplnilo",
        "podle písma",
        "vedlé písma",
        "skrze proroka",
    }

    if any(phrase in sentence for phrase in explicit_citation_phrases):
        return True

    if (
        "praví" in sentence
        and lemmas & {"písmo", "prorok", "zákon", "hospodin"}
    ):
        return True

    return False


# ==========================================================
# E5. TACT RULE SEARCH
# ==========================================================

def has_negated_visual_context(
    feature: SentenceFeatures,
) -> bool:

    sentence = sentence_lower(feature)

    negated_visual_phrases = {
        "neviděl",
        "neviděli",
        "neviděla",
        "nevidělo",
        "neuzřel",
        "neuzřeli",
        "nespatřil",
        "nespatřili",
        "nemohl viděti",
        "nemohli viděti",
        "nebylo viděti",
        "aniž viděl",
        "aniž viděli",
    }

    return any(phrase in sentence for phrase in negated_visual_phrases)


def has_visual_tact_pattern(
    feature: SentenceFeatures,
) -> bool:

    if has_negated_visual_context(feature):
        return False

    return has_any_lemma(feature, VISUAL_PERCEPTION_LEMMAS)


def has_revelation_tact_pattern(
    feature: SentenceFeatures,
) -> bool:

    return has_any_lemma(feature, REVELATION_LEMMAS)


def has_assertive_subject_anchor(
    feature: SentenceFeatures,
) -> bool:

    sentence = f" {sentence_lower(feature)} "

    subject_markers = {
        " my ",
        " vy ",
        " oni ",
        " on ",
        " ona ",
        " to ",
        " kdo ",
        " kdož ",
        " každý ",
        " každý,",
        " což ",
        " všecko ",
        " všeliký ",
    }

    return (
        feature.subject_present
        or any(marker in sentence for marker in subject_markers)
    )


def has_predicative_complement(
    feature: SentenceFeatures,
) -> bool:

    lemmas = lemma_set_of(feature)

    predicative_markers = {
        "jako",
        "za",
        "v",
        "ve",
        "s",
        "se",
    }

    return bool(lemmas & predicative_markers)


def has_non_copular_status_assertion(
    feature: SentenceFeatures,
) -> bool:

    sentence = f" {sentence_lower(feature)} "

    if not has_assertive_subject_anchor(feature):
        return False

    if feature.local_pattern not in ASSERTIVE_LOCAL_PATTERNS:
        return False

    return any(marker in sentence for marker in RELATIONAL_STATUS_MARKERS)


def has_process_state_assertion(
    feature: SentenceFeatures,
) -> bool:

    if not has_assertive_subject_anchor(feature):
        return False

    if feature.local_pattern not in ASSERTIVE_LOCAL_PATTERNS:
        return False

    return feature.root_lemma in PROCESS_STATE_ASSERTION_LEMMAS


def has_descriptive_proxy_pattern(
    feature: SentenceFeatures,
) -> bool:

    if feature.local_pattern == "copular_description":
        return True

    if (
        feature.root_lemma in DESCRIPTIVE_PREDICATION_LEMMAS
        and has_assertive_subject_anchor(feature)
    ):
        return True

    if (
        feature.root_lemma in LOW_RISK_ASSERTIVE_PREDICATION_LEMMAS
        and has_assertive_subject_anchor(feature)
        and feature.local_pattern in ASSERTIVE_LOCAL_PATTERNS
    ):
        return True

    if (
        feature.root_lemma in HIGH_RISK_ASSERTIVE_PREDICATION_LEMMAS
        and has_assertive_subject_anchor(feature)
        and feature.local_pattern in ASSERTIVE_LOCAL_PATTERNS
        and has_predicative_complement(feature)
    ):
        return True

    if has_non_copular_status_assertion(feature):
        return True

    if has_process_state_assertion(feature):
        return True

    return False


# ==========================================================
# E6. INTRAVERBAL RULE SEARCH
# ==========================================================

def has_reported_speech_pattern(
    feature: SentenceFeatures,
) -> bool:

    return (
        feature.root_lemma in REPORTED_SPEECH_LEMMAS
        or has_any_lemma(feature, REPORTED_SPEECH_LEMMAS)
    )


def is_question_structure(
    feature: SentenceFeatures,
) -> bool:

    return feature.local_pattern == "question_structure"


def is_rhetorical_or_argument_question(
    feature: SentenceFeatures,
) -> bool:

    sentence = sentence_lower(feature)

    rhetorical_markers = {
        "kterak",
        "kdo by",
        "což",
        "zdali",
        "proč",
        "který",
    }

    return (
        feature.local_pattern == "modal_question_request_like"
        and any(marker in sentence for marker in rhetorical_markers)
    )


def is_intraverbal_trigger_pattern(
    feature: SentenceFeatures,
) -> bool:

    return (
        is_question_structure(feature)
        or is_rhetorical_or_argument_question(feature)
    )


def is_dialogue_chain_candidate(
    feature: SentenceFeatures,
    decision: SkinnerDecision,
) -> bool:

    if decision.control_role != "response":
        return False

    if decision.proxy_subtype in {
        "written_record",
        "uncertain",
        "reported_textual_proxy",
        "textual_trigger",
        "citation_chain_proxy",
    }:
        return False

    if has_reported_speech_pattern(feature):
        return True

    if decision.proxy_subtype in {
        "intraverbal_proxy",
        "mand_like",
        "descriptive_proxy",
        "negation_autoclitic_proxy",
        "uncertainty_autoclitic_proxy",
        "emphasis_autoclitic_proxy",
    }:
        return True

    return False


def is_intraverbal_response_candidate(
    feature: SentenceFeatures,
    decision: SkinnerDecision,
) -> bool:

    if decision.proxy_subtype in {
        "visual_tact_proxy",
        "revelation_tact_proxy",
        "reported_tact_proxy",
        "reported_textual_proxy",
        "textual_trigger",
        "citation_chain_proxy",
        "intraverbal_proxy",
        "dialogue_chain_proxy",
        "echoic_proxy",
    }:
        return False

    if decision.proxy_subtype in {
        "descriptive_proxy",
        "carry_over_tact_proxy",
    }:
        return True

    if has_any_lemma(feature, ANSWER_MARKER_LEMMAS):
        return True

    if has_any_lemma(feature, FIRST_PERSON_LEMMAS):
        return True

    if (
        feature.is_imperative_like
        or feature.local_pattern in {
            "imperative_action_object",
            "modal_question_request_like",
        }
    ):
        return True

    return False


# ==========================================================
# E7. ECHOIC RULE SEARCH
# ==========================================================

def repeated_content_lemma_present(
    feature: SentenceFeatures,
    window: int = 6,
) -> bool:
    """
    Detect anaphoric / echoic repetition of a content lemma within the sentence.

    Returns True when the same content lemma appears at least twice within
    `window` positions (gaps allowed).  This captures near-adjacent anaphora
    missed by the original adjacent-only check, e.g.:

        "Hospodin jest Bůh váš, Hospodin jest mocný"
        → 'hospodin' at positions 0 and 3  → True  (window=6)

        "Amen, amen pravím vám"
        → already caught by ECHOIC_FORMULAS; this is the general fallback.

    Parameters
    ----------
    feature : SentenceFeatures
    window  : int  – maximum token distance between the two occurrences.
                     Default 6 covers typical biblical verse length.
    """
    lemmas = [
        lemma
        for lemma in lemmas_of(feature)
        if lemma not in _REPEATED_STOP_LEMMAS
    ]
    n = len(lemmas)

    for i in range(n):
        for j in range(i + 1, min(i + window + 1, n)):
            if lemmas[i] == lemmas[j]:
                return True

    return False


def has_echoic_proxy_pattern(
    feature: SentenceFeatures,
) -> bool:

    sentence = " ".join(sentence_lower(feature).split())

    if any(formula in sentence for formula in ECHOIC_FORMULAS):
        return True

    return repeated_content_lemma_present(feature)


# ==========================================================
# E8. AUTOCLITIC RULE SEARCH
# ==========================================================

def detect_autoclitic_proxy_subtype(
    feature: SentenceFeatures,
    semantic: SemanticFeatures,
) -> Optional[str]:

    if (
        semantic.negation_score > 0
        or has_any_lemma(feature, AUTOCLITIC_NEGATION_LEMMAS)
        or feature.local_pattern == "negated_statement"
    ):
        return "negation_autoclitic_proxy"

    if (
        semantic.uncertainty_score > 0
        or has_any_lemma(feature, AUTOCLITIC_UNCERTAINTY_LEMMAS)
    ):
        return "uncertainty_autoclitic_proxy"

    if (
        semantic.lexical_reinforcement > 0
        or has_any_lemma(feature, AUTOCLITIC_EMPHASIS_LEMMAS)
    ):
        # Textual act ("napsáno jest", "psáno jest") s dôrazovým adverbom
        # nie je emphasis_autoclitic — písanie je primárne verbálne správanie.
        if not has_any_lemma(feature, REPORTED_TEXTUAL_LEMMAS):
            return "emphasis_autoclitic_proxy"

    if has_any_lemma(feature, AUTOCLITIC_SOURCE_LEMMAS):
        return "source_autoclitic_proxy"

    if has_any_lemma(feature, AUTOCLITIC_RELATIONAL_LEMMAS):
        return "relation_autoclitic_proxy"

    return None


def autoclitic_reason(
    proxy_subtype: str,
) -> str:

    reasons = {
        "negation_autoclitic_proxy": (
            "Utterance modifies primary verbal behavior through negation; "
            "treated as autoclitic proxy."
        ),
        "uncertainty_autoclitic_proxy": (
            "Utterance modifies primary verbal behavior through uncertainty "
            "or qualification; treated as autoclitic proxy."
        ),
        "emphasis_autoclitic_proxy": (
            "Utterance modifies primary verbal behavior through emphasis, "
            "certainty, or reinforcement; treated as autoclitic proxy."
        ),
        "source_autoclitic_proxy": (
            "Utterance marks source, evidence, knowledge, hearing, reading, "
            "or recognition; treated as autoclitic proxy."
        ),
        "relation_autoclitic_proxy": (
            "Utterance marks logical, causal, inferential, or discourse relation; "
            "treated as autoclitic proxy."
        ),
        "autoclitic_proxy": (
            "Utterance modifies primary verbal behavior; treated as autoclitic proxy."
        ),
    }

    return reasons.get(
        proxy_subtype,
        "Utterance modifies primary verbal behavior; treated as autoclitic proxy."
    )


# ==========================================================
# E9. CONTEXT HELPER PREDICATES
# ==========================================================

def is_narrative_interruption(
    feature: SentenceFeatures,
    decision: SkinnerDecision,
) -> bool:

    return (
        decision.proxy_subtype == "written_record"
        and feature.local_pattern == "general_statement"
    )


def is_stronger_competing_control(
    decision: SkinnerDecision,
) -> bool:

    # FIX: "reported_tact_proxy" removed — orphan label, never produced
    return decision.proxy_subtype in {
        "visual_tact_proxy",
        "revelation_tact_proxy",
        "reported_tact_proxy",
        "reported_textual_proxy",
        "textual_trigger",
        "citation_chain_proxy",
        "intraverbal_proxy",
        "dialogue_chain_proxy",
        "echoic_proxy",
    }