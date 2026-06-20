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
    COMMANDING_DEONTIC_LEMMAS,
    THREAT_DIVINE_WRATH_LEMMAS,
    THREAT_OUTCOME_LEMMAS,
    REWARD_ESCHATOLOGICAL_LEMMAS,
    REWARD_BEATITUDE_LEMMAS,
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


def _infer_from_intention(primary_intention: str) -> str:
    return _INTENTION_TO_EFFECT.get(primary_intention, "effect_indeterminate")


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
    if not any([has_fear, has_hope, has_wonder, has_guilt]):
        if has_reader:
            return f"{inferred_effect}; reader_directly_addressed"
        return inferred_effect

    # Tenzionálne prípady: emotívny slovník kontrastuje s ilokučným zámerom
    if has_hope and primary_intention in {"condemning", "warning"}:
        effect = "evoke_fear_urgency+hope_despite_judgment"
        return f"{effect}; reader_directly_addressed" if has_reader else effect

    if has_guilt and primary_intention == "promising":
        effect = "evoke_hope_trust+guilt_awareness"
        return f"{effect}; reader_directly_addressed" if has_reader else effect

    if has_wonder and primary_intention == "commanding":
        effect = "evoke_compliance_obedience+awe_reverence"
        return f"{effect}; reader_directly_addressed" if has_reader else effect

    # Potvrdenie: emotívny slovník súhlasí s inferovaným efektom
    if has_fear and primary_intention in {"warning", "condemning"}:
        confirmed = "evoke_fear_urgency[lexically_confirmed]"
    elif has_hope and primary_intention in {"promising", "justifying", "mobilizing"}:
        confirmed = "evoke_hope_trust[lexically_confirmed]"
    elif has_wonder and primary_intention in {"praising", "declaring", "legitimation"}:
        confirmed = "evoke_awe_reverence[lexically_confirmed]"
    elif has_guilt and primary_intention == "condemning":
        confirmed = "evoke_shame_guilt[lexically_confirmed]"
    else:
        # Emotívny slovník prítomný, ale nesúhlasí s hlavným zámerom → obe vrstvy
        dominant = _dominant_emotive(has_fear, has_hope, has_wonder, has_guilt)
        confirmed = f"{inferred_effect}+{dominant}_evoked"

    return f"{confirmed}; reader_directly_addressed" if has_reader else confirmed


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
