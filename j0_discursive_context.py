from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from e_extraction import SentenceFeatures
import g_skinner_rules as rules

from i_q_skinner_lexicons import (
    PRAISING_HYMNIC_LEMMAS, PRAISING_DIRECT_LEMMAS, PRAISING_DOXOLOGY_LEMMAS,
    REPETITION_FORMULA_LEMMAS, REPETITION_ANAPHORIC_LEMMAS,
    JUSTIFYING_CAUSAL_LEMMAS, JUSTIFYING_EXPLANATORY_LEMMAS,
    PERSUADING_CONNECTOR_LEMMAS, PERSUADING_APPEAL_LEMMAS,
    COMMANDING_LEMMAS, COMMANDING_NORMATIVE_LEMMAS,
    MOBILIZING_MISSIONARY_LEMMAS,
    CONDEMNING_PROPHETIC_LEMMAS, WARNING_CONDITION_LEMMAS,
    THREAT_DIVINE_WRATH_LEMMAS,
    QUESTIONING_IRONIC_LEMMAS, INTERVENTION_RESPONSE_LEMMAS, INTERVENTION_DISPUTE_LEMMAS,
    NARRATIVE_EXAMPLE_PARABLE_LEMMAS, DECLARING_ABSTRACT_LEMMAS,
    DIRECT_ADDRESS_VOCATIVE_LEMMAS, DIRECT_ADDRESS_PRONOUN_LEMMAS,
    DIRECT_ADDRESS_EPISTOLAR_LEMMAS,
    REWARD_ESCHATOLOGICAL_LEMMAS, THREAT_OUTCOME_LEMMAS,
)


# ==========================================================
# J0-1. DATACLASS
# ==========================================================

@dataclass
class DiscursiveContext:
    # Dimenzia 1 — dominantný ilokučný mód textu
    dominant_mode: str

    # Dimenzia 2 — adresačná štruktúra
    address_structure: str

    # Dimenzia 3 — temporálna orientácia
    temporal_orientation: str

    # Dimenzia 4 — hustota ilokučného obsahu (0.0–1.0)
    illocutionary_density: float

    # Vplyv 1 — confidence delta per intention pre classify_q_skinner
    intention_boosts: dict = field(default_factory=dict)

    # Vplyv 1b — potlačenie past-tense→record fallback
    suppress_past_tense_fallback: bool = False

    # Vplyv 3 — cross-validačné signály
    genre_signal: str = "unknown"
    genre_mode_note: str = ""

    def cross_validate_sentence(self, primary_intention: str) -> str:
        if self.dominant_mode == "undetermined":
            return ""
        expected = _MODE_EXPECTED.get(self.dominant_mode, frozenset())
        if primary_intention in expected or primary_intention in {"unclassified", "record", "narrative"}:
            return ""
        return f"context_tension:{self.dominant_mode}_mode+{primary_intention}"


# ==========================================================
# J0-2. KONFIGURÁCIA MÓDOV
# ==========================================================

# Adjustments aplikované na base_conf po confidence_boost()
_MODE_INTENTION_BOOSTS: dict[str, dict[str, float]] = {
    "narrative": {
        "record": +0.05, "narrative": +0.04,
        "declaring": -0.03, "commanding": -0.04,
    },
    "directive": {
        "commanding": +0.06, "mobilizing": +0.04, "warning": +0.04,
        "record": -0.05,
    },
    "hymnic": {
        "praising": +0.08, "promising": +0.04, "declaring": +0.03,
        "condemning": -0.03, "record": -0.05,
    },
    "argumentative": {
        "justifying": +0.06, "persuading": +0.05, "declaring": +0.04,
        "record": -0.04,
    },
    "prophetic": {
        "condemning": +0.07, "warning": +0.06, "declaring": +0.03,
        "record": -0.05,
    },
    "dialogic": {
        "questioning": +0.06, "intervention": +0.05,
        "ideological_contestation": +0.04, "record": -0.03,
    },
    "didactic": {
        "declaring": +0.05, "persuading": +0.04,
        "justifying": +0.04, "warning": +0.03,
    },
}

# Zámery očakávané v danom móde — odchýlka → cross-validation note
_MODE_EXPECTED: dict[str, frozenset] = {
    "narrative":     frozenset({"record", "narrative", "declaring", "justifying"}),
    "directive":     frozenset({"commanding", "mobilizing", "warning", "promising", "condemning"}),
    "hymnic":        frozenset({"praising", "promising", "declaring", "repetition"}),
    "argumentative": frozenset({"justifying", "persuading", "declaring", "questioning",
                                "ideological_contestation"}),
    "prophetic":     frozenset({"condemning", "warning", "declaring", "mobilizing", "promising"}),
    "dialogic":      frozenset({"questioning", "intervention", "ideological_contestation", "persuading"}),
    "didactic":      frozenset({"declaring", "persuading", "justifying", "warning"}),
}

# Mapovanie žánru z detect_book_genre() na očakávaný diskurzívny mód
_GENRE_EXPECTED_MODE: dict[str, str] = {
    "psalm":      "hymnic",
    "wisdom":     "didactic",
    "prophetic":  "prophetic",
    "epistle":    "argumentative",
    "gospel":     "didactic",
    "historical": "narrative",
    "lyrical":    "hymnic",
}


# ==========================================================
# J0-3. DETEKCIA SIGNÁLOV
# ==========================================================

def _density(features: List[SentenceFeatures], lemma_set: frozenset) -> float:
    if not features:
        return 0.0
    return sum(1 for f in features if rules.has_any_lemma(f, lemma_set)) / len(features)


def _structural_ratios(features: List[SentenceFeatures]) -> dict[str, float]:
    n = len(features)
    if n == 0:
        return {}
    return {
        "past":        sum(1 for f in features if f.root_tense == "Past") / n,
        "imperative":  sum(1 for f in features if f.is_imperative_like) / n,
        "question":    sum(1 for f in features if f.has_question) / n,
    }


def _mode_scores(
    features: List[SentenceFeatures],
    ratios: dict[str, float],
) -> dict[str, float]:
    hymnic_d       = _density(features, PRAISING_HYMNIC_LEMMAS | PRAISING_DIRECT_LEMMAS)
    formula_d      = _density(features, REPETITION_FORMULA_LEMMAS | REPETITION_ANAPHORIC_LEMMAS)
    causal_d       = _density(features, JUSTIFYING_CAUSAL_LEMMAS | JUSTIFYING_EXPLANATORY_LEMMAS)
    connector_d    = _density(features, PERSUADING_CONNECTOR_LEMMAS | PERSUADING_APPEAL_LEMMAS)
    commanding_d   = _density(features, COMMANDING_LEMMAS | COMMANDING_NORMATIVE_LEMMAS)
    prophetic_d    = _density(features, CONDEMNING_PROPHETIC_LEMMAS | THREAT_DIVINE_WRATH_LEMMAS)
    warning_d      = _density(features, WARNING_CONDITION_LEMMAS)
    intervention_d = _density(features, INTERVENTION_RESPONSE_LEMMAS | INTERVENTION_DISPUTE_LEMMAS)
    parable_d      = _density(features, NARRATIVE_EXAMPLE_PARABLE_LEMMAS)
    abstract_d     = _density(features, DECLARING_ABSTRACT_LEMMAS)

    return {
        "narrative":     ratios.get("past", 0.0) * 2.0,
        "directive":     ratios.get("imperative", 0.0) * 2.5 + commanding_d * 1.5,
        "hymnic":        hymnic_d * 3.0 + formula_d * 2.0,
        "argumentative": causal_d * 2.0 + connector_d * 1.5,
        "prophetic":     prophetic_d * 3.5 + warning_d * 1.5,
        "dialogic":      ratios.get("question", 0.0) * 2.0 + intervention_d * 2.5,
        "didactic":      parable_d * 3.0 + abstract_d * 1.5,
    }


def _detect_address_structure(
    features: List[SentenceFeatures],
    ratios: dict[str, float],
) -> str:
    vocative_d   = _density(features, DIRECT_ADDRESS_VOCATIVE_LEMMAS)
    pronoun_d    = _density(features, DIRECT_ADDRESS_PRONOUN_LEMMAS)
    epistolar_d  = _density(features, DIRECT_ADDRESS_EPISTOLAR_LEMMAS)
    intervention_d = _density(features, INTERVENTION_RESPONSE_LEMMAS)

    if intervention_d > 0.05 or ratios.get("question", 0) > 0.15:
        return "dialogic"
    if (vocative_d + pronoun_d) > 0.08 or epistolar_d > 0.04:
        return "community_address"
    return "monologue"


def _detect_temporal_orientation(
    features: List[SentenceFeatures],
    ratios: dict[str, float],
) -> str:
    future_d = _density(features, REWARD_ESCHATOLOGICAL_LEMMAS | THREAT_OUTCOME_LEMMAS)
    past_r   = ratios.get("past", 0.0)

    if past_r > 0.5:
        return "past_dominant"
    if future_d > 0.10:
        return "future_dominant"
    if past_r < 0.25 and future_d < 0.05:
        return "present_dominant"
    return "mixed"


def _illocutionary_density(
    features: List[SentenceFeatures],
    ratios: dict[str, float],
) -> float:
    active = sum(
        1 for f in features
        if (
            f.is_imperative_like
            or f.has_question
            or rules.has_any_lemma(f, PRAISING_HYMNIC_LEMMAS)
            or rules.has_any_lemma(f, CONDEMNING_PROPHETIC_LEMMAS)
            or rules.has_any_lemma(f, JUSTIFYING_CAUSAL_LEMMAS)
            or rules.has_any_lemma(f, WARNING_CONDITION_LEMMAS)
            or rules.has_any_lemma(f, MOBILIZING_MISSIONARY_LEMMAS)
        )
    )
    return round(active / len(features), 3) if features else 0.0


# ==========================================================
# J0-4. CROSS-VALIDÁCIA S detect_book_genre()
# ==========================================================

def _genre_cross_validate(dominant_mode: str, file_name: str) -> tuple[str, str]:
    if not file_name:
        return "unknown", ""
    try:
        from m_verbal_relations import detect_book_genre
        genre = detect_book_genre(file_name)
    except ImportError:
        return "unknown", ""

    if genre == "unknown":
        return "unknown", ""

    expected_mode = _GENRE_EXPECTED_MODE.get(genre, "")
    if not expected_mode:
        return genre, ""

    if dominant_mode == expected_mode:
        note = f"genre_mode_agreement:{genre}/{dominant_mode}"
    else:
        note = f"genre_mode_divergence:{genre}_expected_{expected_mode}_detected_{dominant_mode}"

    return genre, note


# ==========================================================
# J0-5. HLAVNÁ FUNKCIA
# ==========================================================

def resolve_discursive_context(
    features: List[SentenceFeatures],
    file_name: str = "",
    use_genre_priors: bool = True,
) -> DiscursiveContext:
    if not features:
        return DiscursiveContext(
            dominant_mode="undetermined",
            address_structure="monologue",
            temporal_orientation="mixed",
            illocutionary_density=0.0,
        )

    ratios  = _structural_ratios(features)
    scores  = _mode_scores(features, ratios)
    best_mode, best_score = max(scores.items(), key=lambda kv: kv[1])

    dominant_mode = best_mode if best_score >= 0.08 else "undetermined"
    boosts        = _MODE_INTENTION_BOOSTS.get(dominant_mode, {})

    # Potlač past-tense→record fallback pre argumentatívne/epistoliárne texty
    # kde minulý čas funguje rétoricky, nie chronisticky
    epistolar_d = _density(features, DIRECT_ADDRESS_EPISTOLAR_LEMMAS)
    suppress_fallback = (
        dominant_mode == "argumentative"
        and epistolar_d > 0.03
    )

    genre_signal, genre_note = (
        _genre_cross_validate(dominant_mode, file_name)
        if use_genre_priors
        else ("unknown", "")
    )

    return DiscursiveContext(
        dominant_mode=dominant_mode,
        address_structure=_detect_address_structure(features, ratios),
        temporal_orientation=_detect_temporal_orientation(features, ratios),
        illocutionary_density=_illocutionary_density(features, ratios),
        intention_boosts=boosts,
        suppress_past_tense_fallback=suppress_fallback,
        genre_signal=genre_signal,
        genre_mode_note=genre_note,
    )
