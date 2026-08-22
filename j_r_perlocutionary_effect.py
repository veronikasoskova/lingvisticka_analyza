from __future__ import annotations

from e_extraction import SentenceFeatures
import g_skinner_rules as rules

from i_q_skinner_lexicons import (
    EMOTIVE_FEAR_LEMMAS,
    EMOTIVE_HOPE_LEMMAS,
    EMOTIVE_WONDER_LEMMAS,
    EMOTIVE_GUILT_LEMMAS,
    READER_ADDRESS_LEMMAS,
    DIRECT_ADDRESS_PRONOUN_LEMMAS,
    DIRECT_ADDRESS_VOCATIVE_LEMMAS,
)


# ==========================================================
# JR1. KROK A — inferencia z ilokúcie
# ==========================================================
#
# Teoretická mapa Quentin Skinner: ilokučný zámer → zamýšľaný
# perlokatívny efekt na čitateľa/poslucháča.
# Tento krok vždy produkuje výsledok — aj bez emotívneho lexikónu.

_INTENTION_TO_EFFECT: dict[str, str] = {
    "warning":                  "evoke_fear_urgency",
    "condemning":               "evoke_shame_guilt",
    "commanding":               "evoke_compliance_obedience",
    "mobilizing":               "evoke_commitment_action",
    "promising":                "evoke_hope_trust",
    "praising":                 "evoke_awe_reverence",
    "persuading":               "evoke_conviction_assent",
    "questioning":              "evoke_doubt_reflection",
    "justifying":               "evoke_trust_assurance",
    "declaring":                "evoke_belief_understanding",
    "legitimation":             "evoke_deference_submission",
    "ideological_contestation": "evoke_critical_reappraisal",
    "intervention":             "evoke_reconsideration",
    "record":                   "evoke_credibility_witness",
    "narrative":                "evoke_orientation_memory",
    "unclassified":             "effect_indeterminate",
}

# Emotívny signál, ktorý skutočne potvrdzuje inferovaný efekt — nie iný.
_EFFECT_CONFIRMED_BY: dict[str, str] = {
    "evoke_fear_urgency":      "fear",
    "evoke_hope_trust":        "hope",
    "evoke_awe_reverence":     "wonder",
    "evoke_shame_guilt":       "guilt",
}


def _infer_from_intention(primary_intention: str) -> str:
    return _INTENTION_TO_EFFECT.get(primary_intention, "effect_indeterminate")


def _with_reader(effect: str, has_reader: bool) -> str:
    return f"{effect}; reader_directly_addressed" if has_reader else effect


# ==========================================================
# JR2. KROK B — potvrdenie / spresnenie z emotívnych lexikónov
# ==========================================================
#
# Kontroluje, či je emotívny lexikón prítomný vo vete.
# Ak áno, spresní alebo reviduje inferovaný efekt.
# Tenzionálne prípady (napr. HOPE v CONDEMNING) sú zachytené
# explicitne ako kompozitné labely.

def _confirm_from_lexicon(
    feature: SentenceFeatures,
    inferred_effect: str,
    primary_intention: str,
) -> str:
    has_fear   = rules.has_any_lemma(feature, EMOTIVE_FEAR_LEMMAS)
    has_hope   = rules.has_any_lemma(feature, EMOTIVE_HOPE_LEMMAS)
    has_wonder = rules.has_any_lemma(feature, EMOTIVE_WONDER_LEMMAS)
    has_guilt  = rules.has_any_lemma(feature, EMOTIVE_GUILT_LEMMAS)
    has_reader = (
        rules.has_any_lemma(feature, READER_ADDRESS_LEMMAS)
        or rules.has_any_lemma(feature, DIRECT_ADDRESS_PRONOUN_LEMMAS)
        or rules.has_any_lemma(feature, DIRECT_ADDRESS_VOCATIVE_LEMMAS)
    )

    # Ak žiaden emotívny signál nie je prítomný, vráť inferovaný efekt
    if not any((has_fear, has_hope, has_wonder, has_guilt)):
        return _with_reader(inferred_effect, has_reader)

    # Tenzionálne prípady: emotívny slovník kontrastuje s ilokučným zámerom
    if has_hope and primary_intention in {"condemning", "warning"}:
        return _with_reader("evoke_fear_urgency+hope_despite_judgment", has_reader)

    if has_guilt and primary_intention == "promising":
        return _with_reader("evoke_hope_trust+guilt_awareness", has_reader)

    if has_wonder and primary_intention == "commanding":
        return _with_reader("evoke_compliance_obedience+awe_reverence", has_reader)

    # Potvrdenie len keď dominantný emotívny signál súhlasí s inferovaným efektom.
    # Predtým sa napr. condemning+fear pretagoval ako evoke_fear_urgency[lexically_confirmed]
    # a justifying+hope ako evoke_hope_trust[lexically_confirmed] — to nie je potvrdenie
    # inferovaného efektu, ale jeho tichá náhrada.
    dominant = _dominant_emotive(has_fear, has_hope, has_wonder, has_guilt)
    if _EFFECT_CONFIRMED_BY.get(inferred_effect) == dominant:
        confirmed = f"{inferred_effect}[lexically_confirmed]"
    else:
        confirmed = f"{inferred_effect}+{dominant}_evoked"
    return _with_reader(confirmed, has_reader)


def _dominant_emotive(
    has_fear: bool,
    has_hope: bool,
    has_wonder: bool,
    has_guilt: bool,
) -> str:
    # Priorita: strach > vina > nádej > úžas (hierarchia intenzity v biblickom texte)
    if has_fear:
        return "fear"
    if has_guilt:
        return "guilt"
    if has_hope:
        return "hope"
    return "wonder"


# ==========================================================
# JR3. HLAVNÁ FUNKCIA
# ==========================================================

def derive_perlocutionary_effect(
    feature: SentenceFeatures,
    primary_intention: str,
) -> str:
    inferred = _infer_from_intention(primary_intention)
    return _confirm_from_lexicon(feature, inferred, primary_intention)
