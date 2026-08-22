"""Quentin Skinner — Cambridge illocutionary taxonomy and analysis."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, List
import csv
import re
from collections import Counter

from c_input import TextInput
from d_preprocessing import preprocess_text
from e_extraction import SentenceFeatures, extract_features
from f_semantics import SemanticFeatures, semantic_enrichment
import g_skinner_rules as rules

from j0_discursive_context import DiscursiveContext, resolve_discursive_context
from j0_context_profile import ContextProfile, compute_profile_idf_delta
from j_r_perlocutionary_effect import derive_perlocutionary_effect

from i_q_skinner_lexicons import (
    ILLOCUTIONARY_FORCE_MAP,
    POLITICAL_VOCABULARY_LEMMAS,
    WARNING_CONDITION_LEMMAS,
    WARNING_OUTCOME_LEMMAS,
    WARNING_JUDGMENT_LEMMAS,
    WARNING_PREVENTIVE_LEMMAS,
    PROMISING_EXPLICIT_LEMMAS,
    PROMISING_POSITIVE_OUTCOME_LEMMAS,
    PROMISING_CONTRACT_LEMMAS,
    PROMISING_OATH_LEMMAS,
    REWARD_BEATITUDE_LEMMAS,
    REWARD_ESCHATOLOGICAL_LEMMAS,
    REWARD_CONDITION_LEMMAS,
    REWARD_DIRECT_LEMMAS,
    REWARD_RECIPROCAL_LEMMAS,
    JUSTIFYING_CAUSAL_LEMMAS,
    JUSTIFYING_THEOLOGICAL_LEMMAS,
    JUSTIFYING_EXPLANATORY_LEMMAS,
    JUSTIFYING_RETROSPECTIVE_LEMMAS,
    JUSTIFYING_PASSIVE_LEMMAS,
    PRAISING_DIRECT_LEMMAS,
    PRAISING_HYMNIC_LEMMAS,
    PRAISING_DOXOLOGY_LEMMAS,
    PRAISING_ATTRIBUTE_LEMMAS,
    PRAISING_CONFESSION_LEMMAS,
    MOBILIZING_MISSIONARY_LEMMAS,
    MOBILIZING_MOVEMENT_LEMMAS,
    MOBILIZING_COMMISSION_LEMMAS,
    MOBILIZING_COLLECTIVE_LEMMAS,
    MOBILIZING_URGENCY_LEMMAS,
    CONDEMNING_PROPHETIC_LEMMAS,
    CONDEMNING_LABEL_LEMMAS,
    CONDEMNING_ACCUSATION_LEMMAS,
    CONDEMNING_VIOLATION_LEMMAS,
    CONDEMNING_JUDGMENT_LEMMAS,
    DECLARING_ABSTRACT_LEMMAS,
    DECLARING_PROCLAMATION_LEMMAS,
    DECLARING_IDENTITY_LEMMAS,
    DECLARING_COPULAR_LEMMAS,
    DECLARING_UNIVERSAL_LEMMAS,
    COMMANDING_LEMMAS,
    COMMANDING_PROHIBITION_LEMMAS,
    COMMANDING_NORMATIVE_LEMMAS,
    COMMANDING_DEONTIC_LEMMAS,
    QUESTIONING_MARKER_LEMMAS,
    QUESTIONING_POSSIBILITY_LEMMAS,
    QUESTIONING_IRONIC_LEMMAS,
    QUESTIONING_EPISTEMIC_LEMMAS,
    QUESTIONING_CHALLENGE_LEMMAS,
    PERSUADING_CONNECTOR_LEMMAS,
    PERSUADING_APPEAL_LEMMAS,
    PERSUADING_QUESTION_LEMMAS,
    PERSUADING_CONTRAST_LEMMAS,
    PERSUADING_ANALOGY_LEMMAS,
    AUTHORITY_DIVINE_LEMMAS,
    AUTHORITY_EXPLICIT_LEMMAS,
    AUTHORITY_FIRST_PERSON_LEMMAS,
    AUTHORITY_PROPHETIC_LEMMAS,
    AUTHORITY_APOSTOLIC_LEMMAS,
    SCRIPTURE_CITATION_LEMMAS,
    SCRIPTURE_REFERENCE_LEMMAS,
    SCRIPTURE_FULFILLMENT_LEMMAS,
    SCRIPTURE_FORMULA_LEMMAS,
    SCRIPTURE_TYPOLOGY_LEMMAS,
    TRADITION_ANCESTORS_LEMMAS,
    TRADITION_PRECEDENT_LEMMAS,
    TRADITION_COVENANT_LEMMAS,
    TRADITION_RITUAL_LEMMAS,
    TRADITION_CONTINUITY_LEMMAS,
    THREAT_CONDITION_LEMMAS,
    THREAT_OUTCOME_LEMMAS,
    THREAT_DIVINE_WRATH_LEMMAS,
    THREAT_URGENCY_LEMMAS,
    THREAT_EXEMPLAR_LEMMAS,
    CONTRAST_CONNECTOR_LEMMAS,
    CONTRAST_GOOD_EVIL_LEMMAS,
    CONTRAST_LIGHT_DARK_LEMMAS,
    CONTRAST_LIFE_DEATH_LEMMAS,
    CONTRAST_OLD_NEW_LEMMAS,
    REPETITION_FORMULA_LEMMAS,
    REPETITION_REFRAIN_LEMMAS,
    REPETITION_EMPHATIC_LEMMAS,
    REPETITION_PARALLELISM_LEMMAS,
    REPETITION_ANAPHORIC_LEMMAS,
    NARRATIVE_EXAMPLE_PARABLE_LEMMAS,
    NARRATIVE_EXAMPLE_FIGURE_LEMMAS,
    NARRATIVE_EXAMPLE_COMPARATIVE_LEMMAS,
    NARRATIVE_EXAMPLE_HISTORICAL_LEMMAS,
    NARRATIVE_EXAMPLE_MORAL_LEMMAS,
    DIRECT_ADDRESS_PRONOUN_LEMMAS,
    DIRECT_ADDRESS_VOCATIVE_LEMMAS,
    DIRECT_ADDRESS_INCLUSIVE_LEMMAS,
    DIRECT_ADDRESS_IMPERATIVE_LEMMAS,
    DIRECT_ADDRESS_EPISTOLAR_LEMMAS,
    RHETORICAL_NEGATIVE_LEMMAS,
    RHETORICAL_CONSEQUENCE_LEMMAS,
    RHETORICAL_IRONIC_LEMMAS,
    RHETORICAL_CHALLENGE_LEMMAS,
    RHETORICAL_ARGUMENTATIVE_LEMMAS,
    LEGITIMATION_DIVINE_VOICE_LEMMAS,
    LEGITIMATION_DIVINE_MANDATE_LEMMAS,
    LEGITIMATION_ROYAL_LEMMAS,
    LEGITIMATION_PRIESTLY_LEMMAS,
    LEGITIMATION_COVENANT_LEMMAS,
    IDEOLOGICAL_CONTESTATION_NEW_AUTH_LEMMAS,
    IDEOLOGICAL_CONTESTATION_POLEMIC_LEMMAS,
    IDEOLOGICAL_CONTESTATION_CRITIQUE_LEMMAS,
    IDEOLOGICAL_CONTESTATION_CONCEPT_LEMMAS,
    IDEOLOGICAL_CONTESTATION_REDEF_LEMMAS,
    INTERVENTION_RESPONSE_LEMMAS,
    INTERVENTION_POLEMIC_LEMMAS,
    INTERVENTION_DISPUTE_LEMMAS,
    INTERVENTION_CORRECTIVE_LEMMAS,
    INTERVENTION_META_LEMMAS,
    LEMMA_IDF_CROSS,
    confidence_boost,
)


# ==========================================================
# IQ3. DETEKČNÉ FUNKCIE
# ==========================================================

def has_warning_pattern(feature: SentenceFeatures) -> bool:
    # primárny: podmienka + výsledok
    if (
        rules.has_any_lemma(feature, WARNING_CONDITION_LEMMAS)
        and rules.has_any_lemma(feature, WARNING_OUTCOME_LEMMAS)
    ):
        return True

    # sekundárny: súdne / eschatologické výrazy
    # poznámka: „běda" je primárny signál condemning, nie warning
    # has_question guard: rečnícka otázka o súde → questioning, nie warning
    if (
        rules.has_any_lemma(feature, WARNING_JUDGMENT_LEMMAS)
        and not feature.has_question
    ):
        return True

    # sekundárny: preventívne sloveso + imperatív — "Varuj se / Střez se"
    if (
        feature.is_imperative_like
        and rules.has_any_lemma(feature, WARNING_PREVENTIVE_LEMMAS)
    ):
        return True

    # sekundárny: preventívne sloveso + negácia alebo výsledok
    # (negácia môže byť pohlcená prefixom "ne-" pri lemmatizácii)
    if rules.has_any_lemma(feature, WARNING_PREVENTIVE_LEMMAS) and (
        feature.has_negation
        or rules.has_any_lemma(feature, WARNING_OUTCOME_LEMMAS)
    ):
        return True

    return False


def has_promising_pattern(feature: SentenceFeatures) -> bool:
    # primárny: explicitný prísľub + pozitívny výsledok
    if (
        rules.has_any_lemma(feature, PROMISING_EXPLICIT_LEMMAS)
        and rules.has_any_lemma(feature, PROMISING_POSITIVE_OUTCOME_LEMMAS)
    ):
        return True

    # sekundárny: explicitný sľubový akt bez potreby výsledkového lemma
    # ("Zaslíbil jsem vám zemi" — zaslíbit samo o sebe je sľub)
    if rules.has_any_lemma(feature, {"zaslíbit", "slíbit"}):
        return True

    # sekundárny: beatitúda s kauzálnou štruktúrou
    # "Blahoslavení X, nebo oni Y budou" — "nebo" = quoniam (for/because)
    if (
        rules.has_any_lemma(feature, REWARD_BEATITUDE_LEMMAS)
        and rules.has_any_lemma(feature, JUSTIFYING_CAUSAL_LEMMAS)
    ):
        return True

    # sekundárny: blahoslavenstvá — "požehnaný" bez explicitného slovesa sľubu
    # Guard: ak je prítomné božské meno, ide o doxológiu (praising), nie sľub
    if (
        rules.has_any_lemma(feature, {"požehnaný", "požehnat"})
        and not rules.has_any_lemma(feature, AUTHORITY_DIVINE_LEMMAS)
    ):
        return True

    # sekundárny: zmluvná terminológia
    if rules.has_any_lemma(feature, PROMISING_CONTRACT_LEMMAS):
        return True

    # sekundárny: prísažná formula
    if rules.has_any_lemma(feature, PROMISING_OATH_LEMMAS):
        return True

    # sekundárny: eschatologická odmena + priame obdržanie
    # ("Dostanete věčný život / obdržíte království nebeské")
    if (
        rules.has_any_lemma(feature, REWARD_ESCHATOLOGICAL_LEMMAS)
        and rules.has_any_lemma(feature, REWARD_DIRECT_LEMMAS)
    ):
        return True

    # sekundárny: recipročná štruktúra + priame obdržanie
    # ("Kdo hledá, najde" — reciprocita bez explicitného sľubového slovesa)
    if (
        rules.has_any_lemma(feature, REWARD_RECIPROCAL_LEMMAS)
        and rules.has_any_lemma(feature, REWARD_DIRECT_LEMMAS)
    ):
        return True

    return False


def _warning_confidence(feature: SentenceFeatures) -> tuple[float, str]:
    _lemmas = rules.lemma_set_of(feature)
    if (
        rules.has_any_lemma(feature, WARNING_CONDITION_LEMMAS)
        and rules.has_any_lemma(feature, WARNING_OUTCOME_LEMMAS)
    ):
        return (
            confidence_boost(0.80, _lemmas, [WARNING_CONDITION_LEMMAS, WARNING_OUTCOME_LEMMAS], LEMMA_IDF_CROSS),
            "Primary warning: conditional structure with explicit outcome.",
        )
    if rules.has_any_lemma(feature, WARNING_JUDGMENT_LEMMAS):
        return (
            confidence_boost(0.65, _lemmas, [WARNING_JUDGMENT_LEMMAS], LEMMA_IDF_CROSS),
            "Secondary warning: judgment or eschatological vocabulary.",
        )
    if (
        rules.has_any_lemma(feature, WARNING_PREVENTIVE_LEMMAS)
        and rules.has_any_lemma(feature, WARNING_OUTCOME_LEMMAS)
    ):
        return (
            confidence_boost(0.70, _lemmas, [WARNING_PREVENTIVE_LEMMAS, WARNING_OUTCOME_LEMMAS], LEMMA_IDF_CROSS),
            "Secondary warning: preventive verb with outcome (negation in prefix).",
        )
    return (
        confidence_boost(0.60, _lemmas, [WARNING_PREVENTIVE_LEMMAS], LEMMA_IDF_CROSS),
        "Secondary warning: preventive verb with negation.",
    )


def _promising_confidence(feature: SentenceFeatures) -> tuple[float, str]:
    _lemmas = rules.lemma_set_of(feature)
    if (
        rules.has_any_lemma(feature, PROMISING_EXPLICIT_LEMMAS)
        and rules.has_any_lemma(feature, PROMISING_POSITIVE_OUTCOME_LEMMAS)
    ):
        return (
            confidence_boost(0.80, _lemmas, [PROMISING_EXPLICIT_LEMMAS, PROMISING_POSITIVE_OUTCOME_LEMMAS], LEMMA_IDF_CROSS),
            "Primary promise: explicit giving verb with positive outcome.",
        )
    if rules.has_any_lemma(feature, {"požehnaný", "požehnat"}):
        return (
            confidence_boost(0.70, _lemmas, [PROMISING_POSITIVE_OUTCOME_LEMMAS], LEMMA_IDF_CROSS),
            "Secondary promise: beatitude/blessing formula.",
        )
    if rules.has_any_lemma(feature, PROMISING_CONTRACT_LEMMAS):
        return (
            confidence_boost(0.70, _lemmas, [PROMISING_CONTRACT_LEMMAS], LEMMA_IDF_CROSS),
            "Secondary promise: covenant or contract vocabulary.",
        )
    return (
        confidence_boost(0.60, _lemmas, [PROMISING_OATH_LEMMAS], LEMMA_IDF_CROSS),
        "Secondary promise: oath formula.",
    )


def has_praising_pattern(feature: SentenceFeatures) -> bool:
    # Beatitúda s kauzálnou štruktúrou ("nebo") → promising, nie praising
    if (
        rules.has_any_lemma(feature, REWARD_BEATITUDE_LEMMAS)
        and rules.has_any_lemma(feature, JUSTIFYING_CAUSAL_LEMMAS)
    ):
        return False

    # Citácia Písma dominuje nad atribútovou chválou ("jakož psáno jest")
    if rules.has_any_lemma(feature, SCRIPTURE_CITATION_LEMMAS):
        return False

    # primárny: priama chvála alebo epitet
    # Guard: naratívne/konštruktívne slovesá s "svatý" v nomináli nie sú akt chvály
    _NARRATIVE_ROOTS = frozenset({"učinit", "udělat", "přikázat", "postavit", "udělati"})
    if (
        rules.has_any_lemma(feature, PRAISING_DIRECT_LEMMAS)
        and feature.root_lemma not in _NARRATIVE_ROOTS
    ):
        return True

    # primárny: hymnická formula
    if rules.has_any_lemma(feature, PRAISING_HYMNIC_LEMMAS):
        return True

    # sekundárny: doxologická terminológia (sláva, čest, moc, amen)
    if rules.has_any_lemma(feature, PRAISING_DOXOLOGY_LEMMAS):
        return True

    # sekundárny: božský atribút
    if rules.has_any_lemma(feature, PRAISING_ATTRIBUTE_LEMMAS):
        return True

    # sekundárny: konfesionálna formula (láska, milosrdenství, věrnost)
    if rules.has_any_lemma(feature, PRAISING_CONFESSION_LEMMAS):
        return True

    return False


def _praising_confidence(feature: SentenceFeatures) -> tuple[float, str]:
    _lemmas = rules.lemma_set_of(feature)
    if rules.has_any_lemma(feature, PRAISING_HYMNIC_LEMMAS):
        return (
            confidence_boost(0.85, _lemmas, [PRAISING_HYMNIC_LEMMAS], LEMMA_IDF_CROSS),
            "Primary praise: hymnic formula (sing/hallelujah/glorify).",
        )
    if rules.has_any_lemma(feature, PRAISING_DIRECT_LEMMAS):
        return (
            confidence_boost(0.85, _lemmas, [PRAISING_DIRECT_LEMMAS], LEMMA_IDF_CROSS),
            "Primary praise: direct praise verb or epithet.",
        )
    if rules.has_any_lemma(feature, PRAISING_DOXOLOGY_LEMMAS):
        return (
            confidence_boost(0.70, _lemmas, [PRAISING_DOXOLOGY_LEMMAS], LEMMA_IDF_CROSS),
            "Secondary praise: doxological vocabulary (glory/honor/amen).",
        )
    if rules.has_any_lemma(feature, PRAISING_ATTRIBUTE_LEMMAS):
        return (
            confidence_boost(0.65, _lemmas, [PRAISING_ATTRIBUTE_LEMMAS], LEMMA_IDF_CROSS),
            "Secondary praise: divine attribute predication.",
        )
    return (
        confidence_boost(0.60, _lemmas, [PRAISING_CONFESSION_LEMMAS], LEMMA_IDF_CROSS),
        "Secondary praise: confessional formula (love/faithfulness).",
    )


def has_mobilizing_pattern(feature: SentenceFeatures) -> bool:
    # primárny: misijný výkon (kázanie, svedectvo, krst)
    if rules.has_any_lemma(feature, MOBILIZING_MISSIONARY_LEMMAS):
        return True

    # primárny: pohyb + poverenie (jdi + poslat/pověřit)
    if (
        rules.has_any_lemma(feature, MOBILIZING_MOVEMENT_LEMMAS)
        and rules.has_any_lemma(feature, MOBILIZING_COMMISSION_LEMMAS)
    ):
        return True

    # sekundárny: kolektívna akcia
    # "my" samotné nestačí — príliš veľa FP ("uprostřed nás" = prepozícia)
    # vyžaduje is_imperative_like alebo iné kolektívne sloveso (bojovat/vytrvat/pracovat)
    if rules.has_any_lemma(feature, MOBILIZING_COLLECTIVE_LEMMAS):
        non_my = any(
            l in feature.lemmas.split()
            for l in MOBILIZING_COLLECTIVE_LEMMAS - {"my"}
        )
        if non_my or feature.is_imperative_like:
            return True

    # sekundárny: naliehavosť ako motivácia k akcii
    if rules.has_any_lemma(feature, MOBILIZING_URGENCY_LEMMAS):
        return True

    return False


def _mobilizing_confidence(feature: SentenceFeatures) -> tuple[float, str]:
    _lemmas = rules.lemma_set_of(feature)
    if rules.has_any_lemma(feature, MOBILIZING_MISSIONARY_LEMMAS):
        return (
            confidence_boost(0.85, _lemmas, [MOBILIZING_MISSIONARY_LEMMAS], LEMMA_IDF_CROSS),
            "Primary mobilization: missionary commission verb (preach/baptize/witness).",
        )
    if (
        rules.has_any_lemma(feature, MOBILIZING_MOVEMENT_LEMMAS)
        and rules.has_any_lemma(feature, MOBILIZING_COMMISSION_LEMMAS)
    ):
        return (
            confidence_boost(0.80, _lemmas, [MOBILIZING_MOVEMENT_LEMMAS, MOBILIZING_COMMISSION_LEMMAS], LEMMA_IDF_CROSS),
            "Primary mobilization: movement verb with commission (go + send/commission).",
        )
    if rules.has_any_lemma(feature, MOBILIZING_COLLECTIVE_LEMMAS):
        return (
            confidence_boost(0.65, _lemmas, [MOBILIZING_COLLECTIVE_LEMMAS], LEMMA_IDF_CROSS),
            "Secondary mobilization: collective action vocabulary.",
        )
    return (
        confidence_boost(0.65, _lemmas, [MOBILIZING_URGENCY_LEMMAS], LEMMA_IDF_CROSS),
        "Secondary mobilization: urgency marker as action motivation.",
    )


def has_condemning_pattern(feature: SentenceFeatures) -> bool:
    # primárny: prorocká formula „běda"
    if rules.has_any_lemma(feature, CONDEMNING_PROPHETIC_LEMMAS):
        return True

    # primárny: nálepka osoby + morálna akuzácia
    if (
        rules.has_any_lemma(feature, CONDEMNING_LABEL_LEMMAS)
        and rules.has_any_lemma(feature, CONDEMNING_ACCUSATION_LEMMAS)
    ):
        return True

    # sekundárny: transgresívne sloveso (porušenie normy)
    if rules.has_any_lemma(feature, CONDEMNING_VIOLATION_LEMMAS):
        return True

    # sekundárny: verdikt (odsúdenie, prekliatie)
    if rules.has_any_lemma(feature, CONDEMNING_JUDGMENT_LEMMAS):
        return True

    # sekundárny: kopulárna akuzácia — "vy jste plni nepravosti / hříchu"
    # (morálna vlastnosť v predikátovej pozícii bez nálepky osoby)
    if (
        feature.local_pattern == "copular_description"
        and rules.has_any_lemma(feature, CONDEMNING_ACCUSATION_LEMMAS)
    ):
        return True

    return False


def _condemning_confidence(feature: SentenceFeatures) -> tuple[float, str]:
    _lemmas = rules.lemma_set_of(feature)
    if rules.has_any_lemma(feature, CONDEMNING_PROPHETIC_LEMMAS):
        return (
            confidence_boost(0.80, _lemmas, [CONDEMNING_PROPHETIC_LEMMAS], LEMMA_IDF_CROSS),
            "Primary condemnation: prophetic woe formula (běda).",
        )
    if (
        rules.has_any_lemma(feature, CONDEMNING_LABEL_LEMMAS)
        and rules.has_any_lemma(feature, CONDEMNING_ACCUSATION_LEMMAS)
    ):
        return (
            confidence_boost(0.80, _lemmas, [CONDEMNING_LABEL_LEMMAS, CONDEMNING_ACCUSATION_LEMMAS], LEMMA_IDF_CROSS),
            "Primary condemnation: person label with moral accusation.",
        )
    if rules.has_any_lemma(feature, CONDEMNING_VIOLATION_LEMMAS):
        return (
            confidence_boost(0.65, _lemmas, [CONDEMNING_VIOLATION_LEMMAS], LEMMA_IDF_CROSS),
            "Secondary condemnation: transgression verb.",
        )
    return (
        confidence_boost(0.65, _lemmas, [CONDEMNING_JUDGMENT_LEMMAS], LEMMA_IDF_CROSS),
        "Secondary condemnation: verdict vocabulary (odsoudit, proklít).",
    )


def has_declaring_pattern(feature: SentenceFeatures) -> bool:

    # --- GUARDY (blokujú fallback declaring) ---

    # Typ 1 — naratívna próza: slovesný koreň + general_statement bez teologického obsahu
    # ("Roboám kraloval nad Judou" / "houf pustil se cestou")
    if (
        feature.root_pos == "VERB"
        and feature.local_pattern == "general_statement"
        and not rules.has_any_lemma(feature, DECLARING_ABSTRACT_LEMMAS)
        and not rules.has_any_lemma(feature, DECLARING_PROCLAMATION_LEMMAS)
    ):
        return False

    # Typ 2 — slabá kopulárna veta bez teologického predikátu ani božského subjektu
    # ("Teď jsem." / "Kdož nevěří Bohu, lhářem jej učinil.")
    if (
        feature.local_pattern == "copular_description"
        and not rules.has_any_lemma(feature, DECLARING_ABSTRACT_LEMMAS)
        and not rules.has_any_lemma(feature, AUTHORITY_DIVINE_LEMMAS)
    ):
        return False

    # Typ 3 — genealógie a zoznamy: žiadne sloveso ani auxiliár, alebo príliš veľa substantív
    # ("Synové Mojžíšovi: Gersom a Eliezer.")
    # POZOR: "jest" je AUX, nie VERB → verb_count=0 pri kopulárnych vetách → nutný aux_count guard
    if feature.verb_count == 0 and feature.aux_count == 0:
        return False
    if (
        feature.noun_count > 3
        and feature.verb_count <= 1
        and not rules.has_any_lemma(feature, DECLARING_ABSTRACT_LEMMAS)
        and not rules.has_any_lemma(feature, AUTHORITY_DIVINE_LEMMAS)
    ):
        return False

    # --- DETEKČNÉ VZORY ---

    # primárny: citácia Písma + kopulárna deklarácia o Bohu
    # ("Jakož psáno jest: Hospodin spravedlivý jest") — scripture ako autorita pre deklaráciu
    if (
        rules.has_any_lemma(feature, SCRIPTURE_CITATION_LEMMAS)
        and feature.local_pattern == "copular_description"
        and rules.has_any_lemma(feature, AUTHORITY_DIVINE_LEMMAS)
    ):
        return True

    # primárny: kopulárna veta + abstraktný teologický predikát
    if (
        feature.local_pattern == "copular_description"
        and rules.has_any_lemma(feature, DECLARING_ABSTRACT_LEMMAS)
    ):
        return True

    # primárny: VERB root + general_statement + abstraktný teologický predikát
    # ("Poznáte pravdu" / "Ukázal světlo") — epistemická deklarácia bez kopuly
    if (
        feature.root_pos == "VERB"
        and feature.local_pattern == "general_statement"
        and rules.has_any_lemma(feature, DECLARING_ABSTRACT_LEMMAS)
    ):
        return True

    # sekundárny: identitná formula + proklamačná partikulá
    # ideological_contestation má prednosť — "ale já pravím" ≠ deklarácia
    if (
        rules.has_any_lemma(feature, DECLARING_IDENTITY_LEMMAS)
        and rules.has_any_lemma(feature, DECLARING_PROCLAMATION_LEMMAS)
        and not has_ideological_contestation_pattern(feature)
    ):
        return True

    # sekundárny: univerzálny kvantor
    if rules.has_any_lemma(feature, DECLARING_UNIVERSAL_LEMMAS):
        return True

    # sekundárny: kopulárne sloveso (slabý signál) — potlačené ak sú prítomné
    # silnejšie vzory alebo ak ide o otázku (otázky → questioning, nie declaring)
    # legitimation má prednosť pred declaring pri sebaidentifikácii božského hlasu
    # Past tense root: naratívny past-tense "byl" nie je deklarácia (→ record)
    if (
        rules.has_any_lemma(feature, DECLARING_COPULAR_LEMMAS)
        and not feature.has_question
        and not has_persuading_pattern(feature)
        and not has_justifying_pattern(feature)
        and not has_legitimation_pattern(feature)
        and feature.root_tense != "Past"
    ):
        return True

    return False


def _declaring_confidence(feature: SentenceFeatures) -> tuple[float, str]:
    _lemmas = rules.lemma_set_of(feature)
    if (
        feature.local_pattern == "copular_description"
        and rules.has_any_lemma(feature, DECLARING_ABSTRACT_LEMMAS)
    ):
        return (
            confidence_boost(0.80, _lemmas, [DECLARING_ABSTRACT_LEMMAS], LEMMA_IDF_CROSS),
            "Primary declaration: copular structure with abstract theological predicate.",
        )
    if (
        rules.has_any_lemma(feature, DECLARING_IDENTITY_LEMMAS)
        and rules.has_any_lemma(feature, DECLARING_PROCLAMATION_LEMMAS)
    ):
        return (
            confidence_boost(0.75, _lemmas, [DECLARING_IDENTITY_LEMMAS, DECLARING_PROCLAMATION_LEMMAS], LEMMA_IDF_CROSS),
            "Secondary declaration: identity formula with proclamation particle.",
        )
    if rules.has_any_lemma(feature, DECLARING_UNIVERSAL_LEMMAS):
        return (
            confidence_boost(0.65, _lemmas, [DECLARING_UNIVERSAL_LEMMAS], LEMMA_IDF_CROSS),
            "Secondary declaration: universal quantifier (all/every/none).",
        )
    return (
        confidence_boost(0.50, _lemmas, [DECLARING_COPULAR_LEMMAS], LEMMA_IDF_CROSS),
        "Secondary declaration: copular verb (weak signal).",
    )


def has_justifying_pattern(feature: SentenceFeatures) -> bool:
    # primárny: kauzálny konektor + teologické zdôvodnenie
    if (
        rules.has_any_lemma(feature, JUSTIFYING_CAUSAL_LEMMAS)
        and rules.has_any_lemma(feature, JUSTIFYING_THEOLOGICAL_LEMMAS)
    ):
        return True

    # sekundárny: explanačná partikulá alebo explicitný dôvod
    if rules.has_any_lemma(feature, JUSTIFYING_EXPLANATORY_LEMMAS):
        return True

    # sekundárny: retrospektívne sloveso + kauzálny konektor
    # ("stalo sa, neboť / učinil, proto")
    # potlačené ak sú prítomné persuading signály — "být" sa vyskytuje v oboch
    if (
        rules.has_any_lemma(feature, JUSTIFYING_RETROSPECTIVE_LEMMAS)
        and rules.has_any_lemma(feature, JUSTIFYING_CAUSAL_LEMMAS)
        and not has_persuading_pattern(feature)
    ):
        return True

    # sekundárny: kauzálny konektor + božský subjekt
    # ("Neboť tak Bůh miloval svět / Proto Hospodin učinil...")
    if (
        rules.has_any_lemma(feature, JUSTIFYING_CAUSAL_LEMMAS)
        and rules.has_any_lemma(feature, AUTHORITY_DIVINE_LEMMAS)
        and not has_persuading_pattern(feature)
    ):
        return True

    # sekundárny: dvojitý kauzálny konektor — "neboť...proto", "poněvadž...tedy"
    # explicitná kauzálna reťaz bez potreby retrospektívneho slovesa
    causal_present = {l for l in feature.lemmas.split() if l in JUSTIFYING_CAUSAL_LEMMAS}
    if len(causal_present) >= 2 and not has_persuading_pattern(feature):
        return True

    # sekundárny: pasívna konštrukcia ("bylo řečeno/psáno") + koreňový ADJ
    # guard: citačná formula → declaring, nie justifying
    # ("jakož psáno jest: Hospodin spravedlivý" — psaný je v SCRIPTURE_CITATION)
    if (
        rules.has_any_lemma(feature, JUSTIFYING_PASSIVE_LEMMAS)
        and feature.root_pos == "ADJ"
        and not rules.has_any_lemma(feature, SCRIPTURE_CITATION_LEMMAS)
    ):
        return True

    return False


def _justifying_confidence(feature: SentenceFeatures) -> tuple[float, str]:
    _lemmas = rules.lemma_set_of(feature)
    if (
        rules.has_any_lemma(feature, JUSTIFYING_CAUSAL_LEMMAS)
        and rules.has_any_lemma(feature, JUSTIFYING_THEOLOGICAL_LEMMAS)
    ):
        return (
            confidence_boost(0.75, _lemmas, [JUSTIFYING_CAUSAL_LEMMAS, JUSTIFYING_THEOLOGICAL_LEMMAS], LEMMA_IDF_CROSS),
            "Primary justification: causal connector with theological vocabulary.",
        )
    if (
        rules.has_any_lemma(feature, JUSTIFYING_PASSIVE_LEMMAS)
        and feature.root_pos == "ADJ"
    ):
        return (
            confidence_boost(0.65, _lemmas, [JUSTIFYING_PASSIVE_LEMMAS], LEMMA_IDF_CROSS),
            "Secondary justification: passive construction (it was said/written/established).",
        )
    if rules.has_any_lemma(feature, JUSTIFYING_EXPLANATORY_LEMMAS):
        return (
            confidence_boost(0.65, _lemmas, [JUSTIFYING_EXPLANATORY_LEMMAS], LEMMA_IDF_CROSS),
            "Secondary justification: explanatory particle or explicit reason.",
        )
    return (
        confidence_boost(0.60, _lemmas, [JUSTIFYING_RETROSPECTIVE_LEMMAS, JUSTIFYING_CAUSAL_LEMMAS], LEMMA_IDF_CROSS),
        "Secondary justification: retrospective verb with causal connector.",
    )


def has_commanding_pattern(feature: SentenceFeatures) -> bool:
    # primárny: imperatívna štruktúra
    if feature.is_imperative_like:
        return True

    # sekundárny: príkazové sloveso
    if rules.has_any_lemma(feature, COMMANDING_LEMMAS):
        return True

    # sekundárny: zákazová formula — negácia môže byť pohlcená prefixom "ne-"
    # pri lemmatizácii, preto stačí samotný lemma bez požiadavky na has_negation
    if rules.has_any_lemma(feature, COMMANDING_PROHIBITION_LEMMAS):
        return True

    # sekundárny: normatívna terminológia
    if rules.has_any_lemma(feature, COMMANDING_NORMATIVE_LEMMAS):
        return True

    # sekundárny: deontická modalita
    # has_question guard: "Máte uši?" — "mít" = mať (nie musieť), otázka → questioning
    if (
        rules.has_any_lemma(feature, COMMANDING_DEONTIC_LEMMAS)
        and not feature.has_question
    ):
        return True

    return False


def has_questioning_pattern(feature: SentenceFeatures) -> bool:
    # Silné otázkové partikuly signalizujú otázku aj bez "?" (BKR končí ".")
    _STRONG_Q_PARTICLES = frozenset({"zdali", "zdaliž", "zdaž", "liž"})
    if not feature.has_question and not rules.has_any_lemma(feature, _STRONG_Q_PARTICLES):
        return False

    # Fix F: local_pattern priamo signalizuje otázku
    if feature.local_pattern in {"question_structure", "modal_question_request_like"}:
        return True

    # primárny: otázkový marker
    if rules.has_any_lemma(feature, QUESTIONING_MARKER_LEMMAS):
        return True

    # sekundárny: modálna možnosť ("může? možné?")
    if rules.has_any_lemma(feature, QUESTIONING_POSSIBILITY_LEMMAS):
        return True

    # sekundárny: ironická / rečnícka formula ("zdaž, liž, není")
    if rules.has_any_lemma(feature, QUESTIONING_IRONIC_LEMMAS):
        return True

    # sekundárny: epistemická neistota
    if rules.has_any_lemma(feature, QUESTIONING_EPISTEMIC_LEMMAS):
        return True

    # sekundárny: konfrontačné sloveso
    if rules.has_any_lemma(feature, QUESTIONING_CHALLENGE_LEMMAS):
        return True

    # sekundárny: percepčná výzva — zdieľa slovník s rhetorical_question
    # ("Máte uši, a neslyšíte?" — ucho/slyšet v otázkovom kontexte)
    if rules.has_any_lemma(feature, RHETORICAL_CHALLENGE_LEMMAS):
        return True

    # sekundárny: kondicionálna otázka s kopulárnou štruktúrou
    # ("Přivázáns k ženě?" / "Služebníkem povolán jsi?")
    if feature.local_pattern == "copular_description":
        return True

    return False


def _questioning_confidence(feature: SentenceFeatures) -> tuple[float, str]:
    _lemmas = rules.lemma_set_of(feature)
    if rules.has_any_lemma(feature, QUESTIONING_MARKER_LEMMAS):
        return (
            confidence_boost(0.80, _lemmas, [QUESTIONING_MARKER_LEMMAS], LEMMA_IDF_CROSS),
            "Primary questioning: question marker with interrogative structure.",
        )
    if rules.has_any_lemma(feature, QUESTIONING_IRONIC_LEMMAS):
        return (
            confidence_boost(0.75, _lemmas, [QUESTIONING_IRONIC_LEMMAS], LEMMA_IDF_CROSS),
            "Secondary questioning: ironic/rhetorical particle (zdaž, liž).",
        )
    if rules.has_any_lemma(feature, QUESTIONING_POSSIBILITY_LEMMAS):
        return (
            confidence_boost(0.70, _lemmas, [QUESTIONING_POSSIBILITY_LEMMAS], LEMMA_IDF_CROSS),
            "Secondary questioning: modal possibility in question context.",
        )
    if rules.has_any_lemma(feature, QUESTIONING_EPISTEMIC_LEMMAS):
        return (
            confidence_boost(0.65, _lemmas, [QUESTIONING_EPISTEMIC_LEMMAS], LEMMA_IDF_CROSS),
            "Secondary questioning: epistemic uncertainty marker.",
        )
    return (
        confidence_boost(0.65, _lemmas, [QUESTIONING_CHALLENGE_LEMMAS], LEMMA_IDF_CROSS),
        "Secondary questioning: confrontational verb in question context.",
    )


def has_persuading_pattern(feature: SentenceFeatures) -> bool:
    # primárny: argumentačný konektor + apelačné sloveso
    if (
        rules.has_any_lemma(feature, PERSUADING_CONNECTOR_LEMMAS)
        and rules.has_any_lemma(feature, PERSUADING_APPEAL_LEMMAS)
    ):
        return True

    # sekundárny: rečnícka otázka (has_question + otázková partikulá)
    if (
        feature.has_question
        and rules.has_any_lemma(feature, PERSUADING_QUESTION_LEMMAS)
    ):
        return True

    # sekundárny: kontrastná štruktúra
    # ideological_contestation má prednosť — "ale já pravím" ≠ persuasion
    if (
        rules.has_any_lemma(feature, PERSUADING_CONTRAST_LEMMAS)
        and not has_ideological_contestation_pattern(feature)
    ):
        return True

    # sekundárny: analógia / prirovnanie
    if rules.has_any_lemma(feature, PERSUADING_ANALOGY_LEMMAS):
        return True

    return False


def _persuading_confidence(feature: SentenceFeatures) -> tuple[float, str]:
    _lemmas = rules.lemma_set_of(feature)
    if (
        rules.has_any_lemma(feature, PERSUADING_CONNECTOR_LEMMAS)
        and rules.has_any_lemma(feature, PERSUADING_APPEAL_LEMMAS)
    ):
        return (
            confidence_boost(0.75, _lemmas, [PERSUADING_CONNECTOR_LEMMAS, PERSUADING_APPEAL_LEMMAS], LEMMA_IDF_CROSS),
            "Primary persuasion: causal connector with appeal verb.",
        )
    if (
        feature.has_question
        and rules.has_any_lemma(feature, PERSUADING_QUESTION_LEMMAS)
    ):
        return (
            confidence_boost(0.70, _lemmas, [PERSUADING_QUESTION_LEMMAS], LEMMA_IDF_CROSS),
            "Secondary persuasion: rhetorical question structure.",
        )
    if rules.has_any_lemma(feature, PERSUADING_CONTRAST_LEMMAS):
        return (
            confidence_boost(0.60, _lemmas, [PERSUADING_CONTRAST_LEMMAS], LEMMA_IDF_CROSS),
            "Secondary persuasion: contrastive structure.",
        )
    return (
        confidence_boost(0.60, _lemmas, [PERSUADING_ANALOGY_LEMMAS], LEMMA_IDF_CROSS),
        "Secondary persuasion: analogical structure.",
    )


def _commanding_confidence(feature: SentenceFeatures) -> tuple[float, str]:
    _lemmas = rules.lemma_set_of(feature)
    if feature.is_imperative_like:
        # Syntactic signal — boost by lexical specificity of matching command lemmas
        return (
            confidence_boost(0.80, _lemmas, [COMMANDING_LEMMAS], LEMMA_IDF_CROSS),
            "Primary command: imperative syntactic structure.",
        )
    if rules.has_any_lemma(feature, COMMANDING_PROHIBITION_LEMMAS):
        return (
            confidence_boost(0.75, _lemmas, [COMMANDING_PROHIBITION_LEMMAS], LEMMA_IDF_CROSS),
            "Secondary command: prohibition formula (forbidden act; negation may be in prefix).",
        )
    if rules.has_any_lemma(feature, COMMANDING_DEONTIC_LEMMAS):
        return (
            confidence_boost(0.65, _lemmas, [COMMANDING_DEONTIC_LEMMAS], LEMMA_IDF_CROSS),
            "Secondary command: deontic modal (obligation/duty).",
        )
    if rules.has_any_lemma(feature, COMMANDING_NORMATIVE_LEMMAS):
        return (
            confidence_boost(0.65, _lemmas, [COMMANDING_NORMATIVE_LEMMAS], LEMMA_IDF_CROSS),
            "Secondary command: normative vocabulary (law/commandment).",
        )
    return (
        confidence_boost(0.60, _lemmas, [COMMANDING_LEMMAS], LEMMA_IDF_CROSS),
        "Secondary command: command-class verb.",
    )


def has_appeal_to_authority_pattern(feature: SentenceFeatures) -> bool:
    # primárny: božský subjekt + výrokové/príkazové sloveso
    # ("Hospodin řekl / Bůh přikázal / Pán zjevil")
    if (
        rules.has_any_lemma(feature, AUTHORITY_DIVINE_LEMMAS)
        and rules.has_any_lemma(feature, AUTHORITY_EXPLICIT_LEMMAS)
    ):
        return True

    # primárny: prvá osoba + kopulárna veta — božská sebadeklarácia
    # ("Já jsem Hospodin / Já jsem Bůh tvůj")
    if (
        rules.has_any_lemma(feature, AUTHORITY_FIRST_PERSON_LEMMAS)
        and feature.local_pattern == "copular_description"
    ):
        return True

    # sekundárny: božský posesív + normatívne substantívum
    # ("přikázání Hospodinova / zákon Boží") — posesív v lemmate: hospodinův / boží
    if (
        rules.has_any_lemma(feature, AUTHORITY_DIVINE_LEMMAS)
        and rules.has_any_lemma(feature, COMMANDING_NORMATIVE_LEMMAS)
    ):
        return True

    # sekundárny: prorocký / pneumatický register
    if rules.has_any_lemma(feature, AUTHORITY_PROPHETIC_LEMMAS):
        return True

    # sekundárny: apoštolský register
    if rules.has_any_lemma(feature, AUTHORITY_APOSTOLIC_LEMMAS):
        return True

    # sekundárny: kauzálna veta s božským subjektom
    # ("Neboť tak Bůh miloval svět" — kauzálny odkaz na Božiu akciu ako ospravedlnenie)
    # "nebo" vynechané — v biblickej češtine ambivalentné (spojka OR vs. kauzálna)
    _STRONG_CAUSAL = {"neboť", "poněvadž", "jelikož", "protože", "protož"}
    if (
        any(l in _STRONG_CAUSAL for l in feature.lemmas.split())
        and rules.has_any_lemma(feature, AUTHORITY_DIVINE_LEMMAS)
    ):
        return True

    return False


def has_appeal_to_scripture_pattern(feature: SentenceFeatures) -> bool:
    # primárny: citačná formula + odkaz na písomný prameň
    # ("jakož je psáno v zákoně / stojí v písmu / psáno v prorocích")
    if (
        rules.has_any_lemma(feature, SCRIPTURE_CITATION_LEMMAS)
        and rules.has_any_lemma(feature, SCRIPTURE_REFERENCE_LEMMAS)
    ):
        return True

    # primárny: formula naplnenia proroctva
    # ("naplnilo se slovo proroka / aby se naplnilo písmo skrze...")
    if rules.has_any_lemma(feature, SCRIPTURE_FULFILLMENT_LEMMAS):
        return True

    # sekundárny: formula odvolávania sa na tradíciu
    # ("praví Hospodin / slovo Pána / Duch Svatý")
    if rules.has_any_lemma(feature, SCRIPTURE_FORMULA_LEMMAS):
        return True

    # sekundárny: typologická štruktúra — prirovnanie k biblickej postave
    # ("jako Mojžíš / znamenie Jonáše")
    if rules.has_any_lemma(feature, SCRIPTURE_TYPOLOGY_LEMMAS):
        return True

    return False


def has_appeal_to_tradition_pattern(feature: SentenceFeatures) -> bool:
    # primárny: odvolanie na predkov + časový precedens
    # ("otcové od počátku činili / jak pradávno Abraham")
    if (
        rules.has_any_lemma(feature, TRADITION_ANCESTORS_LEMMAS)
        and rules.has_any_lemma(feature, TRADITION_PRECEDENT_LEMMAS)
    ):
        return True

    # primárny: zmluvné dedičstvo + predkovia
    # ("smlouva s Abrahamem / zaslíbení otcům")
    if (
        rules.has_any_lemma(feature, TRADITION_COVENANT_LEMMAS)
        and rules.has_any_lemma(feature, TRADITION_ANCESTORS_LEMMAS)
    ):
        return True

    # sekundárny: rituálna / opakujúca sa prax
    # ("ustanovení věčné / každoročně / po všechna pokolení")
    if rules.has_any_lemma(feature, TRADITION_RITUAL_LEMMAS):
        return True

    # sekundárny: kontinuita viery a praxe
    # ("zachovávat víru / podání otců / držet tradici")
    if rules.has_any_lemma(feature, TRADITION_CONTINUITY_LEMMAS):
        return True

    return False


def has_conditional_threat_pattern(feature: SentenceFeatures) -> bool:
    # primárny: podmienková štruktúra + explicitný výsledok hrozby
    # ("Jestliže neposlechneš / kdo nepřijme → zahyne / bude odsouzen")
    if (
        rules.has_any_lemma(feature, THREAT_CONDITION_LEMMAS)
        and rules.has_any_lemma(feature, THREAT_OUTCOME_LEMMAS)
    ):
        return True

    # primárny: božský hnev ako priama hrozba
    # ("Hněv Boží zůstává / neujde Božímu soudu")
    if rules.has_any_lemma(feature, THREAT_DIVINE_WRATH_LEMMAS):
        return True

    # sekundárny: naliehavosť + výsledok hrozby
    # ("Již je sekyra přiložena ke kořeni / brzy padne")
    if (
        rules.has_any_lemma(feature, THREAT_URGENCY_LEMMAS)
        and rules.has_any_lemma(feature, THREAT_OUTCOME_LEMMAS)
    ):
        return True

    # sekundárny: naliehavosť samotná — dostatočne špecifický metaforický slovník
    # ("Již je sekyra přiložena ke kořeni stromů" — hrozba bez explicitného výsledku)
    # THREAT_URGENCY_LEMMAS je úzky (sekyra/kořen/přiložit/přicházet/již/brzy) →
    # nízka pravdepodobnosť FP; výsledok je implicitný v obraze
    if rules.has_any_lemma(feature, THREAT_URGENCY_LEMMAS):
        return True

    # sekundárny: exemplárna hrozba — príbeh ako výstraha
    # ("jako oni padli / tak stane se i vám")
    # conditional_threat vs narrative_example: threat používa príbeh ako hrozbu,
    # narrative_example ako argument; rozdiel je v THREAT_OUTCOME_LEMMAS
    if (
        rules.has_any_lemma(feature, THREAT_EXEMPLAR_LEMMAS)
        and rules.has_any_lemma(feature, THREAT_OUTCOME_LEMMAS)
    ):
        return True

    return False


def has_promise_of_reward_pattern(feature: SentenceFeatures) -> bool:
    # primárny: blahoslavenstvo + eschatologická odmena
    # ("Blahoslavení chudí duchem, neboť jejich je království nebeské")
    if (
        rules.has_any_lemma(feature, REWARD_BEATITUDE_LEMMAS)
        and rules.has_any_lemma(feature, REWARD_ESCHATOLOGICAL_LEMMAS)
    ):
        return True

    # primárny: podmienka + priame obdržanie odmeny
    # ("Kdo hledá, najde / Jestliže budete zachovávat, dostanete")
    if (
        rules.has_any_lemma(feature, REWARD_CONDITION_LEMMAS)
        and rules.has_any_lemma(feature, REWARD_DIRECT_LEMMAS)
    ):
        return True

    # sekundárny: recipročná štruktúra + priame obdržanie
    # ("Proste a dostanete / Tlucte a bude vám otevřeno")
    if (
        rules.has_any_lemma(feature, REWARD_RECIPROCAL_LEMMAS)
        and rules.has_any_lemma(feature, REWARD_DIRECT_LEMMAS)
    ):
        return True

    # sekundárny: eschatologická odmena ako motivácia
    # ("Věčný život / království nebeské / věnec slávy")
    # promise_of_reward = motivovanie odmenou; legitimation = ospravedlnenie moci
    if rules.has_any_lemma(feature, REWARD_ESCHATOLOGICAL_LEMMAS):
        return True

    # sekundárny: blahoslavenstvo samotné bez explicitnej eschatologickej odmeny
    # ("Blahoslavení milosrdní" — odmena je implikovaná formou beatitúdy)
    if rules.has_any_lemma(feature, REWARD_BEATITUDE_LEMMAS):
        return True

    return False


def has_contrast_pattern(feature: SentenceFeatures) -> bool:
    # primárny: explicitný kontrastný konektor + morálna/teologická antitéza
    # ("ale / však / nýbrž" + "dobrý/zlý, pravda/lež, spravedlivý/bezbožný")
    if (
        rules.has_any_lemma(feature, CONTRAST_CONNECTOR_LEMMAS)
        and rules.has_any_lemma(feature, CONTRAST_GOOD_EVIL_LEMMAS)
    ):
        return True

    # primárny: svetlo/tma antitéza — dostatočne špecifický teologický obraz
    # ("světlo vs. tma / den vs. noc") — contrast vs. declaring: declaring tvrdí identitu,
    # contrast stavia dve hodnoty proti sebe (aj bez konektoru)
    if rules.has_any_lemma(feature, CONTRAST_LIGHT_DARK_LEMMAS):
        return True

    # sekundárny: život/smrt antitéza — eschatologický dualizmus
    # ("život vs. smrt / zahynout vs. věčný život")
    if rules.has_any_lemma(feature, CONTRAST_LIFE_DEATH_LEMMAS):
        return True

    # sekundárny: staré/nové + konektor — ideologická polemika, boj o pojmy
    # ("Slyšeli jste, že bylo řečeno... ale já pravím vám")
    # contrast vs. appeal_to_tradition: tradition odkazuje na minulosť ako autoritu,
    # contrast ju stavia voči novému — ideological_contestation o pojmy
    if (
        rules.has_any_lemma(feature, CONTRAST_OLD_NEW_LEMMAS)
        and rules.has_any_lemma(feature, CONTRAST_CONNECTOR_LEMMAS)
    ):
        return True

    return False


def has_repetition_pattern(feature: SentenceFeatures) -> bool:
    # primárny: anaforické opakovanie content-lemmy v okne ±6 tokenov
    # rules.repeated_content_lemma_present() zachytáva aj neprilehlé opakovania
    # ("Hospodin jest Bůh, Hospodin jest mocný") nielen susedné ("amen amen")
    if rules.repeated_content_lemma_present(feature):
        return True

    # primárny: liturgická formula — "amen/haleluja/hosanna/věk"
    # tieto lemmy sú inherentne formulaické a vždy naznačujú opakujúci sa register
    # repetition vs. praising: praising fires first if PRAISING_DIRECT/DOXOLOGY present;
    # repetition cross-cutting potom dopĺňa secondary slot
    if rules.has_any_lemma(feature, REPETITION_FORMULA_LEMMAS):
        return True

    # primárny: žalmový refrén — trvat + milosrdenství / chválit / zpívat
    # "neboť jeho milosrdenství trvá na věky" — klasický refrén žalmov
    if (
        rules.has_any_lemma(feature, {"trvat"})
        and rules.has_any_lemma(feature, REPETITION_REFRAIN_LEMMAS)
    ):
        return True

    # sekundárny: emfatický zdůrazňovač — "věru / zajisté"
    # naznačujú emfatický register typický pre formulaické výroky
    if rules.has_any_lemma(feature, REPETITION_EMPHATIC_LEMMAS):
        return True

    # sekundárny: štrukturálny paralelizmus — 2+ paralelné lemmy v jednej vete
    # "Proste a dostane, hledejte a naleznete, tlucte a bude otevřeno"
    # repetition vs. promise_of_reward: parallelism = forma; reward = zámer — odlišné vrstvy
    _parallel = {l for l in feature.lemmas.split() if l in REPETITION_PARALLELISM_LEMMAS}
    if len(_parallel) >= 2:
        return True

    # sekundárny: anaforický marker — "blahoslavený/běda" signalizuje sériu
    # beatitúdy a beda-orákly sú klasické anafory biblického textu
    if rules.has_any_lemma(feature, REPETITION_ANAPHORIC_LEMMAS):
        return True

    return False


def has_narrative_example_pattern(feature: SentenceFeatures) -> bool:
    # primárny: parabolická formula — "podobenství, království je podobné, přirovnat"
    # narrative_example vs. declaring: podobenstvo = argument príbehom; declaring = priamy výrok
    # narrative_example vs. appeal_to_scripture: morálny príklad = argument; citácia = prameň
    if rules.has_any_lemma(feature, NARRATIVE_EXAMPLE_PARABLE_LEMMAS):
        return True

    # primárny: biblická postava + komparatívna štruktúra
    # ("jako Mojžíš vyzdvihl... tak / Abraham uvěřil... jako David")
    # narrative_example vs. appeal_to_tradition: príbeh = rétorický argument;
    # tradícia = norma/zvyk predkov — rozdiel je v funkcii odkazu
    if (
        rules.has_any_lemma(feature, NARRATIVE_EXAMPLE_FIGURE_LEMMAS)
        and rules.has_any_lemma(feature, NARRATIVE_EXAMPLE_COMPARATIVE_LEMMAS)
    ):
        return True

    # sekundárny: historická alúzia + komparatívna štruktúra
    # ("v dni Noé... ako tehdy / stalo se, když... tak aj teraz")
    if (
        rules.has_any_lemma(feature, NARRATIVE_EXAMPLE_HISTORICAL_LEMMAS)
        and rules.has_any_lemma(feature, NARRATIVE_EXAMPLE_COMPARATIVE_LEMMAS)
    ):
        return True

    # sekundárny: morálna aplikácia — "tak, také, podobně" ako záver príbehu
    # slabý signál — môže ísť o záver akéhokoľvek argumentu, nie len príbehu
    if rules.has_any_lemma(feature, NARRATIVE_EXAMPLE_MORAL_LEMMAS):
        return True

    return False


def has_direct_address_pattern(feature: SentenceFeatures) -> bool:
    # primárny: zámenný osloveník + imperatívna forma
    # ("vy/ty + imperatív" — priame oslovenie konkrétneho adresáta s výzvou)
    if (
        rules.has_any_lemma(feature, DIRECT_ADDRESS_PRONOUN_LEMMAS)
        and feature.is_imperative_like
    ):
        return True

    # primárny: vokativ — menné oslovu biblickej entity alebo komunity
    # ("Hospodine / Izraeli / bratři")
    if rules.has_any_lemma(feature, DIRECT_ADDRESS_VOCATIVE_LEMMAS):
        return True

    # sekundárny: inkluzívne prvé osoby množného čísla
    # ("my / nás / náš" — rétorika zahrňujúcej komunity)
    if rules.has_any_lemma(feature, DIRECT_ADDRESS_INCLUSIVE_LEMMAS):
        return True

    # sekundárny: performatívne imperatívne formuly
    # ("slyšte / vězte / oznamte") — guard is_imperative_like zabraňuje
    # false positive z indikatívnych foriem ("nevíte", "neslyšíte")
    if (
        feature.is_imperative_like
        and rules.has_any_lemma(feature, DIRECT_ADDRESS_IMPERATIVE_LEMMAS)
    ):
        return True

    # sekundárny: epistolárna formula
    # ("píšu / oznamuji / prosím" — list adresovaný konkrétnej komunite)
    if rules.has_any_lemma(feature, DIRECT_ADDRESS_EPISTOLAR_LEMMAS):
        return True

    # sekundárny: zámenný osloveník bez imperatívu
    # ("Běda vám" — dativ 2. osoby ako adresátový signál bez slovesného imperativu)
    if rules.has_any_lemma(feature, DIRECT_ADDRESS_PRONOUN_LEMMAS):
        return True

    # sekundárny: imperatívna forma bez zámenníka
    # ("Jděte do všeho světa" — výzva k akcii bez explicitného zámenníka)
    if feature.is_imperative_like:
        return True

    return False


def has_rhetorical_question_pattern(feature: SentenceFeatures) -> bool:
    # has_question je potrebná podmienka pre všetky signály
    if not feature.has_question:
        return False

    # primárny: negatívna rétorická otázka
    # ("Což nevíte? / Zdali neunikne?")
    if rules.has_any_lemma(feature, RHETORICAL_NEGATIVE_LEMMAS):
        return True

    # primárny: otázka s dôsledkom / nevyhnutnosťou
    # ("Kdo obstojí? / Čemu prospěje?")
    if rules.has_any_lemma(feature, RHETORICAL_CONSEQUENCE_LEMMAS):
        return True

    # sekundárny: ironický zvrat
    # ("Zdaž sbírají z trní hrozny?")
    if rules.has_any_lemma(feature, RHETORICAL_IRONIC_LEMMAS):
        return True

    # sekundárny: výzva k percepcii / pochopeniu
    # ("Máte uši a neslyšíte? / Nepochopíte?")
    if rules.has_any_lemma(feature, RHETORICAL_CHALLENGE_LEMMAS):
        return True

    # sekundárny: argumentatívna otázka
    # ("Co si myslíte? / Které přikázání?")
    if rules.has_any_lemma(feature, RHETORICAL_ARGUMENTATIVE_LEMMAS):
        return True

    return False


# ==========================================================
# IQ3b. PLACEHOLDERY — budúca implementácia
# ==========================================================

def has_legitimation_pattern(feature: SentenceFeatures) -> bool:
    # primárny: božská sebaidentifikácia — viacnásobná zhoda v DIVINE_VOICE
    # ("Já jsem Hospodin Bůh tvůj" → "já" + "hospodin" = 2 divine voice lemy)
    _divine_hits = {
        l for l in feature.lemmas.split()
        if l in LEGITIMATION_DIVINE_VOICE_LEMMAS
    }
    if len(_divine_hits) >= 2 and feature.local_pattern == "copular_description":
        return True

    # primárny: božský mandát + kráľovská/mocenská terminológia
    if (
        rules.has_any_lemma(feature, LEGITIMATION_DIVINE_MANDATE_LEMMAS)
        and rules.has_any_lemma(feature, LEGITIMATION_ROYAL_LEMMAS)
    ):
        return True

    # primárny: božský hlas + kopulárna formula + kráľovská terminológia
    if (
        rules.has_any_lemma(feature, LEGITIMATION_DIVINE_VOICE_LEMMAS)
        and feature.local_pattern == "copular_description"
        and rules.has_any_lemma(feature, LEGITIMATION_ROYAL_LEMMAS)
    ):
        return True

    # sekundárny: kňazsko-prorocká rola + božský mandát
    if (
        rules.has_any_lemma(feature, LEGITIMATION_PRIESTLY_LEMMAS)
        and rules.has_any_lemma(feature, LEGITIMATION_DIVINE_MANDATE_LEMMAS)
    ):
        return True

    # sekundárny: zmluvná terminológia + božský mandát
    if (
        rules.has_any_lemma(feature, LEGITIMATION_COVENANT_LEMMAS)
        and rules.has_any_lemma(feature, LEGITIMATION_DIVINE_MANDATE_LEMMAS)
    ):
        return True

    return False


def has_ideological_contestation_pattern(feature: SentenceFeatures) -> bool:
    # primárny: nová autorita vs. stará tradícia
    # ("Slyšeli jste... ale já pravím" — polemic connector + new authority voice)
    if (
        rules.has_any_lemma(feature, IDEOLOGICAL_CONTESTATION_NEW_AUTH_LEMMAS)
        and rules.has_any_lemma(feature, IDEOLOGICAL_CONTESTATION_POLEMIC_LEMMAS)
    ):
        return True

    # primárny: kritika interpretácie + kľúčový pojem
    # ("Nerozumíte písmu / mýlíte se v zákoně")
    if (
        rules.has_any_lemma(feature, IDEOLOGICAL_CONTESTATION_CRITIQUE_LEMMAS)
        and rules.has_any_lemma(feature, IDEOLOGICAL_CONTESTATION_CONCEPT_LEMMAS)
    ):
        return True

    # sekundárny: redefinícia pojmu
    # ("Spravedlnost neznamená..." / "Zákon říká...")
    if (
        rules.has_any_lemma(feature, IDEOLOGICAL_CONTESTATION_REDEF_LEMMAS)
        and rules.has_any_lemma(feature, IDEOLOGICAL_CONTESTATION_CONCEPT_LEMMAS)
    ):
        return True

    # sekundárny: polemic connector + kľúčový pojem
    # ("Ale pravda je..." / "Nýbrž zákon...")
    if (
        rules.has_any_lemma(feature, IDEOLOGICAL_CONTESTATION_POLEMIC_LEMMAS)
        and rules.has_any_lemma(feature, IDEOLOGICAL_CONTESTATION_CONCEPT_LEMMAS)
    ):
        return True

    return False


def has_intervention_pattern(feature: SentenceFeatures) -> bool:
    # primárny: odpoveď adresovaná oponentovi
    # ("Odpověděl jim... Mýlíte se, vy říkáte...")
    if (
        rules.has_any_lemma(feature, INTERVENTION_RESPONSE_LEMMAS)
        and rules.has_any_lemma(feature, INTERVENTION_POLEMIC_LEMMAS)
    ):
        return True

    # primárny: odpoveď v kontexte sporu
    # ("Přišli farizeové a otázali se... odpověděl")
    if (
        rules.has_any_lemma(feature, INTERVENTION_DISPUTE_LEMMAS)
        and rules.has_any_lemma(feature, INTERVENTION_RESPONSE_LEMMAS)
    ):
        return True

    # primárny: odpoveď s explicitnou kritikou adresáta
    # ("Odpověděl... Mýlíte se, neznajíce písma")
    if (
        rules.has_any_lemma(feature, INTERVENTION_RESPONSE_LEMMAS)
        and rules.has_any_lemma(feature, IDEOLOGICAL_CONTESTATION_CRITIQUE_LEMMAS)
    ):
        return True

    # sekundárny: korekcia + odpoveď
    # ("Nikoliv, já pravím..." — opravenie výroku oponenta)
    if (
        rules.has_any_lemma(feature, INTERVENTION_CORRECTIVE_LEMMAS)
        and rules.has_any_lemma(feature, INTERVENTION_RESPONSE_LEMMAS)
    ):
        return True

    # sekundárny: meta-signál sporu
    if rules.has_any_lemma(feature, INTERVENTION_META_LEMMAS):
        return True

    return False


# ==========================================================
# IQ3d. RECORD & NARRATIVE
# ==========================================================

def has_record_pattern(feature: SentenceFeatures) -> bool:
    # primárny: naratívna veta v general_statement bez ilokučného obsahu
    # ("Přibral se Roboám do Sichem." / "Potom odšel Samuel do Ráma.")
    if (
        feature.local_pattern == "general_statement"
        and feature.verb_count >= 1
        and not rules.has_any_lemma(feature, DECLARING_ABSTRACT_LEMMAS)
        and not rules.has_any_lemma(feature, {"věru", "amen", "vpravdě"})
        and not feature.has_question
        and not feature.is_imperative_like
    ):
        return True

    # sekundárny: kopulárna genealógia — "jest otec / jsou synové"
    # ("Onť jest otec Estonův." / "Ti jsou rodové Zarati.")
    # Vyžaduje copular_description — vylučuje general_statement (zachytené primárnym)
    # a vylučuje čisté zoznamy bez aux (→ narrative sekundárny)
    if (
        feature.local_pattern == "copular_description"
        and feature.aux_count >= 1
        and feature.noun_count >= 1
        and not rules.has_any_lemma(feature, DECLARING_ABSTRACT_LEMMAS)
        and not rules.has_any_lemma(feature, AUTHORITY_DIVINE_LEMMAS)
        and not feature.has_question
        and not feature.is_imperative_like
    ):
        return True

    return False


def has_narrative_pattern(feature: SentenceFeatures) -> bool:
    # primárny: kopulárna enumerácia s mnohými substantívami — "jsou synové/mená"
    # ("Tito jsou synové jejich..." / "Synové Mojžíšovi: Gersom a Eliezer.")
    # verb_count == 0: bežné naratívne vety s jedným plným slovesom → record, nie narrative
    # AUTHORITY_DIVINE_LEMMAS guard: božský subjekt → declaring/record, nie zoznam
    if (
        feature.noun_count > 2
        and feature.verb_count == 0
        and not rules.has_any_lemma(feature, DECLARING_ABSTRACT_LEMMAS)
        and not rules.has_any_lemma(feature, AUTHORITY_DIVINE_LEMMAS)
        and not feature.has_question
    ):
        return True

    # sekundárny: genealogické zoznamy a architektonické popisy — žiadne sloveso ani auxiliár
    # ("Adam, Set, Enos..." / "Synové pak Jáfetovi: Gomer, Magog..." / "A jablek zrnatých čtyři sta.")
    # Mená sú PROPN (nie NOUN) → noun_count môže byť 0; token_count >= 4 filtruje krátke výkričníky
    if (
        feature.verb_count == 0
        and feature.aux_count == 0
        and feature.token_count >= 4
    ):
        return True

    return False


# ==========================================================
# IQ3c. POMOCNÉ FUNKCIE
# ==========================================================

def get_illocutionary_force(primary_intention: str) -> str:
    return ILLOCUTIONARY_FORCE_MAP.get(
        primary_intention, "unknown"
    )


# ==========================================================
# IQ3e. LAYER 2 — CONVENTION, ANTI_ANACHRONISM, POLITICAL VOCAB
# ==========================================================

_CONVENTION_MAP: dict[str, str] = {
    "intervention":             "dialogic_controversy",
    "ideological_contestation": "antithetical_disputation",
    "legitimation":             "theophanic_self_presentation",
    "warning":                  "prophetic_admonition",
    "mobilizing":               "missionary_commission",
    "commanding":               "apodictic_law",
    "promising":                "covenant_promise",
    "condemning":               "woe_oracle",
    "persuading":               "deliberative_rhetoric",
    "questioning":              "elenctic_questioning",
    "justifying":               "theological_rationale",
    "praising":                 "doxological_hymn",
    "declaring":                "declarative_assertion",
    "record":                   "narrative_chronicle",
    "narrative":                "enumerative_list",
    "unclassified":             "undetermined",
}

# Public alias for demo DB / UI consumers.  Keep _CONVENTION_MAP as the
# implementation name so existing internal references stay unchanged.
CONVENTION_MAP = _CONVENTION_MAP

# When no rhetorical-device pattern fires, keep the speech-act readable
# instead of storing primary_strategy = "unclassified".  Same mapping the
# demo DB already used (intention → typical strategy).
INTENTION_DEFAULT_STRATEGY: dict[str, str] = {
    "legitimation":             "appeal_to_authority",
    "commanding":               "direct_address",
    "warning":                  "conditional_threat",
    "record":                   "narrative_example",
    "praising":                 "repetition",
    "declaring":                "appeal_to_authority",
    "promising":                "promise_of_reward",
    "condemning":               "contrast",
    "justifying":               "appeal_to_scripture",
    "intervention":             "rhetorical_question",
    "mobilizing":               "direct_address",
    "ideological_contestation": "contrast",
    "persuading":               "appeal_to_tradition",
    "questioning":              "rhetorical_question",
    "narrative":                "narrative_example",
}


def apply_strategy_fallback(intention: str, strategy: str) -> str:
    """Replace a bare ``unclassified`` strategy with the intention default."""
    if strategy != "unclassified":
        return strategy
    return INTENTION_DEFAULT_STRATEGY.get(intention, strategy)


# BKR 2nd-person prohibition / Decalogue future: "Nepokradeš", "neodmlčujž se".
_BKR_PROHIBITIVE_Z_RE = re.compile(
    r"(?iu)(?:^|[\s,;:])ne[a-záčďéěíňóřšťúůýž]{3,}ž\b"
)
_BKR_NEG_START_RE = re.compile(
    r"(?iu)^(?:a\s+|ale\s+|i\s+|protož\s+)?"
    r"ne(?!boť|bo\b|žli|ž\b|kteř|kter)[a-záčďéěíňóřšťúůýž]{3,}"
)
_KDOZ_START_RE = re.compile(r"(?iu)^kdož?\b")
_LITURGICAL_RECORD = frozenset({
    "sélah", "selah", "aleph", "beth", "gimel", "daleth", "he", "vau",
    "zain", "cheth", "teth", "jod", "caph", "lamed", "mem", "nun",
    "samech", "ain", "pe", "zade", "koph", "res", "schin", "thau",
})

# Czech locution keys expected by VALUE_LABELS["locution"] (not the raw sentence).
LOCUTION_LABELS = (
    "výrok o Bohu",
    "přímý příkaz",
    "zaslíbení",
    "výzva k poslušnosti",
    "narativní popis",
    "prorocké zvolání",
    "chvála",
    "nářek",
    "právní předpis",
    "teologické tvrzení",
)


def has_bkr_prohibitive_surface(sentence: str) -> bool:
    """True for BKR negated imperatives / Decalogue futures Stanza often misses."""
    text = sentence or ""
    return bool(
        _BKR_PROHIBITIVE_Z_RE.search(text)
        or _BKR_NEG_START_RE.search(text.strip())
    )


def is_liturgical_fragment(sentence: str, lemmas: str = "") -> bool:
    """True for Selah / psalm-acrostic headings that are not speech acts."""
    text = re.sub(r"[.!?]+$", "", (sentence or "").strip().lower())
    if text in _LITURGICAL_RECORD:
        return True
    toks = {t.strip(".,;:!?") for t in (lemmas or "").lower().split() if t}
    return bool(toks) and toks <= _LITURGICAL_RECORD


def apply_intention_fallback(
    intention: str,
    sentence: str,
    lemmas: str = "",
    *,
    has_question: bool = False,
) -> str:
    """Fill a bare ``unclassified`` intention from surface cues, else declaring.

    Past-tense narrative already falls back to ``record`` earlier in
    ``classify_q_skinner``. What remains is mostly present-tense gnomic
    prose, missed BKR prohibitions, and liturgical fragments.
    """
    if intention != "unclassified":
        return intention
    if has_bkr_prohibitive_surface(sentence):
        return "commanding"
    if is_liturgical_fragment(sentence, lemmas):
        return "record"
    if has_question:
        return "unclassified"
    if _KDOZ_START_RE.match((sentence or "").strip()):
        return "declaring"
    return "declaring"


def derive_locution(intention: str, lemmas: str = "", sentence: str = "") -> str:
    """Map an intention onto one of the ten Czech locution labels."""
    lemma_set = {t.lower() for t in (lemmas or "").split()}
    if intention == "commanding":
        if (
            has_bkr_prohibitive_surface(sentence)
            or lemma_set & {x.lower() for x in COMMANDING_PROHIBITION_LEMMAS}
        ):
            return "přímý příkaz"
        if lemma_set & {x.lower() for x in COMMANDING_NORMATIVE_LEMMAS}:
            return "právní předpis"
        return "výzva k poslušnosti"
    if intention == "promising":
        return "zaslíbení"
    if intention == "praising":
        return "chvála"
    if intention in {"warning", "condemning"}:
        if lemma_set & {"plakat", "nářek", "bědovat", "běda", "lament"}:
            return "nářek"
        return "prorocké zvolání"
    if intention in {"record", "narrative"}:
        return "narativní popis"
    if intention == "legitimation":
        return "výrok o Bohu"
    if intention in {"declaring", "justifying"}:
        if lemma_set & {x.lower() for x in AUTHORITY_DIVINE_LEMMAS}:
            return "výrok o Bohu"
        return "teologické tvrzení"
    if intention in {"persuading", "mobilizing"}:
        return "výzva k poslušnosti"
    if intention in {"questioning", "intervention", "ideological_contestation"}:
        return "teologické tvrzení"
    return "narativní popis"


def refresh_stored_skinner_row(row: dict) -> dict:
    """Recompute locution; fill unclassified intention from surface cues."""
    old_int = row.get("primary_intention") or "unclassified"
    sentence = row.get("sentence") or ""
    lemmas = row.get("lemmas") or ""
    new_int = apply_intention_fallback(
        old_int,
        sentence,
        lemmas,
        has_question="?" in sentence,
    )
    out = dict(row)
    out["primary_intention"] = new_int
    out["locution"] = derive_locution(new_int, lemmas, sentence)
    if new_int != old_int:
        out["illocutionary_force"] = get_illocutionary_force(new_int)
        out["primary_strategy"] = apply_strategy_fallback(
            new_int, row.get("primary_strategy") or "unclassified"
        )
        out["convention"] = CONVENTION_MAP.get(
            new_int, row.get("convention") or "undetermined"
        )
        out["reason"] = (
            f"{new_int}: surface fallback for previously unclassified intention."
        )
        out["confidence"] = 0.55
    return out


def _derive_convention(
    primary_intention: str,
    primary_strategy: str,
    feature: SentenceFeatures,
) -> str:
    if primary_intention == "legitimation":
        if rules.has_any_lemma(feature, LEGITIMATION_ROYAL_LEMMAS):
            return "royal_legitimation_formula"
        return "theophanic_self_presentation"

    if primary_intention == "commanding":
        if rules.has_any_lemma(feature, THREAT_CONDITION_LEMMAS):
            return "casuistic_law"
        if rules.has_any_lemma(feature, COMMANDING_PROHIBITION_LEMMAS):
            return "apodictic_prohibition"
        return "apodictic_law"

    if primary_intention == "promising":
        if rules.has_any_lemma(feature, PROMISING_OATH_LEMMAS):
            return "divine_oath_formula"
        if rules.has_any_lemma(feature, REWARD_BEATITUDE_LEMMAS):
            return "beatitude_formula"
        return "covenant_promise"

    if primary_intention == "praising":
        if rules.has_any_lemma(feature, PRAISING_HYMNIC_LEMMAS):
            return "hymnic_praise"
        if rules.has_any_lemma(feature, PRAISING_DOXOLOGY_LEMMAS):
            return "doxological_formula"
        if rules.has_any_lemma(feature, PRAISING_CONFESSION_LEMMAS):
            return "confessional_creed"
        return "attributive_praise"

    if primary_intention == "condemning":
        if rules.has_any_lemma(feature, CONDEMNING_PROPHETIC_LEMMAS):
            return "woe_oracle"
        return "prophetic_judgment_speech"

    if primary_intention == "justifying":
        if primary_strategy == "appeal_to_scripture":
            return "scriptural_warrant"
        return "theological_rationale"

    if primary_intention == "declaring":
        if primary_strategy == "appeal_to_authority":
            return "theophanic_declaration"
        if rules.has_any_lemma(feature, DECLARING_UNIVERSAL_LEMMAS):
            return "universal_truth_claim"
        return "declarative_assertion"

    return _CONVENTION_MAP.get(primary_intention, "undetermined")


# Terms whose modern semantic range risks anachronistic reading of BKR
_ANACHRONISM_RISK_LEMMAS: dict[str, str] = {
    "zákon":        "tórah/nómos = covenantal instruction, not modern legal code",
    "svoboda":      "eleutheria = freedom from sin/bondage, not political emancipation",
    "národ":        "'am/ethnos = covenant people, not modern nation-state",
    "právo":        "mishpat = divine judgment/ordinance, not subjective rights",
    "spravedlnost": "tsedaqah/dikaiosynē = covenant faithfulness, not social justice",
    "lid":          "'am = covenant community, not populist 'the people'",
    "moc":          "exousia/dynamis = divine authorization, not political power",
    "smlouva":      "berith = relational covenant, not contractual agreement",
    "vláda":        "malkuth = divine reign, not modern governance apparatus",
    "stát":         "no Hebrew/Greek equivalent; BKR polity is kingdom or tribe",
}


def _derive_anti_anachronism(
    primary_intention: str,
    feature: SentenceFeatures,
) -> str:
    lemma_set = set(feature.lemmas.split())
    flagged = []
    for lemma, note in _ANACHRONISM_RISK_LEMMAS.items():
        if lemma not in lemma_set:
            continue
        if primary_intention == "commanding" and lemma == "zákon":
            flagged.append(
                f"{lemma}: tórah is instructional covenant, not Mosaic legislation in modern sense"
            )
        else:
            flagged.append(f"{lemma}: {note}")
    return "; ".join(flagged) if flagged else "none_flagged"


# Semantic categories for political vocabulary interpretation
_POLITICAL_VOCAB_CATEGORIES: dict[str, str] = {
    "zákon": "covenant_law", "přikázání": "divine_command", "ustanovení": "divine_ordinance",
    "nařízení": "divine_ordinance", "smlouva": "covenant", "zaslíbení": "covenant_promise",
    "svědectví": "covenant_testimony", "soud": "divine_judgment", "úsudek": "divine_judgment",
    "král": "royal_power", "království": "royal_reign", "panovník": "sovereign_ruler",
    "vládce": "sovereign_ruler", "vláda": "governance", "trůn": "royal_authority",
    "žezlo": "royal_authority", "panství": "dominion",
    "kněz": "priestly_authority", "velekněz": "high_priestly", "levita": "levitical_service",
    "oběť": "cultic_sacrifice", "chrám": "sacred_space", "svatyně": "sacred_space",
    "lid": "covenant_community", "národ": "ethnic_community", "kmen": "tribal_identity",
    "pokolení": "generational_lineage", "dům": "household_community",
    "spravedlnost": "covenantal_justice", "právo": "divine_right", "pravda": "divine_truth",
    "milost": "covenant_grace", "milosrdenství": "steadfast_love",
    "moc": "divine_power", "síla": "divine_strength", "sláva": "divine_glory", "čest": "honor",
    "nepřítel": "opposition", "pohané": "gentile_otherness", "cizinec": "foreigner",
    "válka": "warfare", "meč": "military_power", "boj": "conflict",
    "prorok": "prophetic_office", "mesiáš": "messianic_title", "spasitel": "soteriological",
    "spása": "soteriological", "vykoupení": "redemption",
}


def _interpret_political_vocabulary(feature: SentenceFeatures) -> str:
    hits = [l for l in feature.lemmas.split() if l in POLITICAL_VOCABULARY_LEMMAS]
    if not hits:
        return ""
    return ", ".join(
        f"{l}[{_POLITICAL_VOCAB_CATEGORIES.get(l, 'political_term')}]"
        for l in hits
    )


_INTENTION_REGISTER: dict[str, str] = {
    "commanding":               "directive",
    "mobilizing":               "exhortative",
    "warning":                  "admonitory",
    "condemning":               "prophetic_denunciatory",
    "promising":                "promissory",
    "praising":                 "doxological",
    "justifying":               "argumentative_causal",
    "declaring":                "assertoric",
    "questioning":              "interrogative",
    "persuading":               "deliberative_rhetorical",
    "legitimation":             "theophanic",
    "ideological_contestation": "antithetical_polemical",
    "intervention":             "dialogic_controversial",
    "record":                   "narrative_chronistic",
    "narrative":                "enumerative",
    "unclassified":             "indeterminate",
}

_STRATEGY_REGISTER: dict[str, str] = {
    "direct_address":       "direct_address",
    "rhetorical_question":  "rhetorical_interrogation",
    "appeal_to_authority":  "authoritative_citation",
    "appeal_to_scripture":  "scriptural_appeal",
    "appeal_to_tradition":  "traditional_precedent",
    "conditional_threat":   "conditional_threat_structure",
    "promise_of_reward":    "reward_motivation",
    "contrast":             "contrastive_framing",
    "repetition":           "formulaic_repetition",
    "narrative_example":    "analogical_exemplum",
}


def _derive_linguistic_context(
    primary_intention: str,
    primary_strategy: str,
    feature: SentenceFeatures,
) -> str:
    register = _INTENTION_REGISTER.get(primary_intention, "indeterminate")

    if feature.is_imperative_like:
        construction = "imperative"
    elif feature.has_question:
        construction = "interrogative"
    elif feature.local_pattern == "copular_description":
        construction = "copular"
    elif feature.root_tense == "Past":
        construction = "past_narration"
    else:
        construction = "declarative"

    strategy_label = _STRATEGY_REGISTER.get(primary_strategy, "")

    parts = [f"{register}_register", f"{construction}_construction"]
    if strategy_label:
        parts.append(strategy_label)
    return "; ".join(parts)


# ==========================================================
# IQ4. DATACLASS
# ==========================================================

@dataclass
class QSkinnerDecision:

    # identifikácia
    sentence_id: int
    sentence: str
    source: str
    file_name: str

    # --- Layer 1: ilokučná a rétoricko-ideologická rovina ---

    # ilokučná sila výroku (speech act)
    illocutionary_force: str

    # primárny a sekundárny zámer hovoriaceho
    primary_intention: str
    secondary_intention: Optional[str]

    # primárna a sekundárna rétoricka stratégia
    primary_strategy: str
    secondary_strategy: Optional[str]

    # --- Layer 2: lingvisticko-historická rovina ---

    # doslovný obsah výroku (čo sa hovorí)
    locution: str

    # sociálna konvencia alebo žáner, na ktorý výrok apeluje
    convention: str

    # jazykový kontext (rétorika, register, adresát)
    linguistic_context: str

    # kľúčové politické / teologické pojmy vo výroku
    political_vocabulary: str

    # poznámka k historickej špecifickosti — varovanie pred anachronizmom
    anti_anachronism: str

    # zamýšľaný efekt výroku na čitateľa/poslucháča (perlokvencia)
    perlocutionary_effect: str

    # cross-validačná poznámka: napätie medzi detegovaným diskurzívnym módом a zámerom
    context_note: str

    # --- metaúdaje ---
    confidence: float
    reason: str

    # --- lingvistické príznaky zo SentenceFeatures ---
    type_token_ratio: float
    has_coordination: bool
    dative_present: bool
    indirect_object_present: bool
    adjective_count: int
    adverb_count: int
    pronoun_count: int


@dataclass
class CotextSummary:
    source: str
    total_sentences: int
    dominant_intention: str
    dominant_strategy: str
    rhetorical_density: float
    convention_profile: str
    intention_distribution: dict
    strategy_distribution: dict
    intention_sequence: str


# Module-level check registries used by classify_q_skinner and validate_intention_priority
_INTENTION_CHECKS: list[tuple] = [
    (has_intervention_pattern,             "intervention"),
    (has_ideological_contestation_pattern, "ideological_contestation"),
    (has_legitimation_pattern,             "legitimation"),
    (has_warning_pattern,                  "warning"),
    (has_mobilizing_pattern,               "mobilizing"),
    (has_commanding_pattern,               "commanding"),
    (has_promising_pattern,                "promising"),
    (has_condemning_pattern,               "condemning"),
    (has_persuading_pattern,               "persuading"),
    (has_questioning_pattern,              "questioning"),
    (has_justifying_pattern,               "justifying"),
    (has_praising_pattern,                 "praising"),
    (has_declaring_pattern,                "declaring"),
    (has_record_pattern,                   "record"),
    (has_narrative_pattern,                "narrative"),
]

_STRATEGY_CHECKS: list[tuple] = [
    (has_appeal_to_authority_pattern, "appeal_to_authority"),
    (has_appeal_to_scripture_pattern, "appeal_to_scripture"),
    (has_appeal_to_tradition_pattern, "appeal_to_tradition"),
    (has_direct_address_pattern,      "direct_address"),
    (has_rhetorical_question_pattern, "rhetorical_question"),
    (has_conditional_threat_pattern,  "conditional_threat"),
    (has_promise_of_reward_pattern,   "promise_of_reward"),
    (has_contrast_pattern,            "contrast"),
    (has_repetition_pattern,          "repetition"),
    (has_narrative_example_pattern,   "narrative_example"),
]


# ==========================================================
# IQ5. KLASIFIKÁCIA
# ==========================================================

def classify_q_skinner(
    feature: SentenceFeatures,
    semantic: SemanticFeatures,
    text_input: TextInput,
    linguistic_context: str = "",
    context: Optional[DiscursiveContext] = None,
    profile: Optional[ContextProfile] = None,
) -> QSkinnerDecision:

    # KROK 1 — primary_intention: uses module-level _INTENTION_CHECKS

    # KROK 0 — minulý čas: naratívna predvolba
    # Predikát v minulom čase (Tense=Past) bez imperatívu a otázky opisuje minulú
    # udalosť. Direktívne/komisívne/expresívne vzory nie sú aplikovateľné —
    # "přišel, umřel, udělal" sú naratívne záznamy, nie ilokučné akty.
    _PAST_TENSE_SUPPRESS = frozenset({
        "commanding", "mobilizing", "promising",
        "condemning", "praising", "warning",
    })
    _past_root = (
        feature.root_tense == "Past"
        and not feature.is_imperative_like
        and not feature.has_question
    )
    _active_checks = [
        (fn, label) for fn, label in _INTENTION_CHECKS
        if not (_past_root and label in _PAST_TENSE_SUPPRESS)
    ]

    primary_intention = "unclassified"
    _primary_label: Optional[str] = None
    for fn, label in _active_checks:
        if fn(feature):
            primary_intention = label
            _primary_label = label
            break

    # Fallback: ak past-tense veta neprešla žiadnym vzorom → record
    # Potlačené pre argumentatívno-epistoliárne texty (suppress_past_tense_fallback)
    # kde minulý čas nie je chronistický záznam ale rétoricko-naratívny argument.
    # Aktivuje sa z DiscursiveContext (dynamický) alebo ContextProfile (statický prior).
    _suppress_fallback = (
        (context.suppress_past_tense_fallback if context else False)
        or (profile.suppress_past_tense_fallback if profile else False)
    )
    if _past_root and primary_intention == "unclassified" and not _suppress_fallback:
        primary_intention = "record"
        _primary_label = "record"

    if primary_intention == "unclassified":
        primary_intention = apply_intention_fallback(
            primary_intention,
            feature.sentence,
            feature.lemmas,
            has_question=feature.has_question,
        )
        if primary_intention != "unclassified":
            _primary_label = primary_intention

    # KROK 2 — secondary_intention
    secondary_intention: Optional[str] = None
    for fn, label in _active_checks:
        if label == _primary_label:
            continue
        if fn(feature):
            secondary_intention = label
            break

    # KROK 3 — primary_strategy: uses module-level _STRATEGY_CHECKS

    primary_strategy = "unclassified"
    primary_strat_idx = -1
    for i, (fn, label) in enumerate(_STRATEGY_CHECKS):
        if fn(feature):
            primary_strategy = label
            primary_strat_idx = i
            break
    primary_strategy = apply_strategy_fallback(primary_intention, primary_strategy)

    # KROK 4 — secondary_strategy
    secondary_strategy: Optional[str] = None
    for i, (fn, label) in enumerate(_STRATEGY_CHECKS):
        if i == primary_strat_idx:
            continue
        if fn(feature):
            secondary_strategy = label
            break

    # KROK 5 — illocutionary_force
    illocutionary_force = get_illocutionary_force(primary_intention)

    # confidence + reason
    _CONFIDENCE_FNS = {
        "warning":    _warning_confidence,
        "promising":  _promising_confidence,
        "praising":   _praising_confidence,
        "mobilizing": _mobilizing_confidence,
        "condemning": _condemning_confidence,
        "declaring":  _declaring_confidence,
        "justifying": _justifying_confidence,
        "questioning": _questioning_confidence,
        "persuading": _persuading_confidence,
        "commanding": _commanding_confidence,
        "record":     lambda f: (0.70, "Record: narrative statement without illocutionary content."),
        "narrative":  lambda f: (0.65, "Narrative: noun-heavy enumeration or list structure."),
    }
    if primary_intention in _CONFIDENCE_FNS:
        confidence, reason = _CONFIDENCE_FNS[primary_intention](feature)
    elif primary_intention == "unclassified":
        confidence = 0.30
        reason = "unclassified: no matching pattern found."
    else:
        confidence = 0.75
        reason = f"{primary_intention}: detected via pattern function."

    # VPLYV 2a — DiscursiveContext: dynamické váhy z textu samotného
    if context:
        _delta = context.intention_boosts.get(primary_intention, 0.0)
        if _delta:
            confidence = min(max(confidence + _delta, 0.0), 0.95)

    # VPLYV 2b — ContextProfile: statický prior + škálovaný IDF
    # intention_delta = additive prior podľa typu textu
    # compute_profile_idf_delta = korekcia confidence podľa špecifickosti lemiem v profile
    if profile:
        _pdelta   = profile.intention_delta.get(primary_intention, 0.0)
        _idfdelta = compute_profile_idf_delta(feature, profile)
        _combined = _pdelta + _idfdelta
        if _combined:
            confidence = min(max(confidence + _combined, 0.0), 0.95)

    # KROK 6 — Layer 2: convention, linguistic_context, anti_anachronism, political_vocabulary, perlocution
    _political_vocab = _interpret_political_vocabulary(feature)
    _convention = _derive_convention(primary_intention, primary_strategy, feature)
    _anti_anachronism = _derive_anti_anachronism(primary_intention, feature)
    _linguistic_context = _derive_linguistic_context(primary_intention, primary_strategy, feature)
    _perlocutionary = derive_perlocutionary_effect(feature, primary_intention)

    # VPLYV 3 — cross-validácia: napätie medzi diskurzívnym módом a zámerom vety
    _context_note = context.cross_validate_sentence(primary_intention) if context else ""

    return QSkinnerDecision(
        sentence_id=feature.sentence_id,
        sentence=feature.sentence,
        source=text_input.context.source,
        file_name="",
        illocutionary_force=illocutionary_force,
        primary_intention=primary_intention,
        secondary_intention=secondary_intention,
        primary_strategy=primary_strategy,
        secondary_strategy=secondary_strategy,
        locution=derive_locution(primary_intention, feature.lemmas, feature.sentence),
        convention=_convention,
        linguistic_context=_linguistic_context,
        political_vocabulary=_political_vocab,
        anti_anachronism=_anti_anachronism,
        perlocutionary_effect=_perlocutionary,
        context_note=_context_note,
        confidence=confidence,
        reason=reason,
        type_token_ratio=feature.type_token_ratio,
        has_coordination=feature.has_coordination,
        dative_present=feature.dative_present,
        indirect_object_present=feature.indirect_object_present,
        adjective_count=feature.adjective_count,
        adverb_count=feature.adverb_count,
        pronoun_count=feature.pronoun_count,
    )


# ==========================================================
# IQ6. PIPELINE
# ==========================================================

def apply_q_skinner(
    text_input: TextInput,
    linguistic_context: str = "unknown",
    file_name: str = "",
) -> List[QSkinnerDecision]:
    preprocessed = preprocess_text(text_input)
    features = extract_features(preprocessed)
    disc_context = resolve_discursive_context(features, file_name)
    semantics = semantic_enrichment(features)
    return [
        classify_q_skinner(feat, sem, text_input, context=disc_context)
        for feat, sem in zip(features, semantics)
    ]


def validate_intention_priority(
    features: List[SentenceFeatures],
) -> List[dict]:
    """
    For each check in _INTENTION_CHECKS report firing statistics.
    capture_ratio = primary_fires / total_fires — how often a check wins when it fires.
    Low capture_ratio means higher-priority checks are absorbing its cases.
    """
    n = len(features)
    fire_sets: dict[str, set] = {label: set() for _, label in _INTENTION_CHECKS}
    primary_counts: Counter = Counter()

    for i, feat in enumerate(features):
        first_hit = True
        for fn, label in _INTENTION_CHECKS:
            if fn(feat):
                fire_sets[label].add(i)
                if first_hit:
                    primary_counts[label] += 1
                    first_hit = False

    results = []
    for rank, (fn, label) in enumerate(_INTENTION_CHECKS):
        fires = len(fire_sets[label])
        primary = primary_counts[label]
        results.append({
            "rank":          rank,
            "check":         label,
            "total_fires":   fires,
            "primary_fires": primary,
            "fire_rate":     round(fires / n, 3) if n else 0.0,
            "primary_rate":  round(primary / n, 3) if n else 0.0,
            "capture_ratio": round(primary / fires, 3) if fires else 0.0,
        })

    return sorted(results, key=lambda x: x["total_fires"], reverse=True)


def analyze_cotext(decisions: List[QSkinnerDecision]) -> CotextSummary:
    if not decisions:
        return CotextSummary(
            source="", total_sentences=0, dominant_intention="unknown",
            dominant_strategy="unknown", rhetorical_density=0.0,
            convention_profile="unknown",
            intention_distribution={}, strategy_distribution={},
            intention_sequence="",
        )

    source = decisions[0].source
    total = len(decisions)

    int_counts: Counter = Counter(d.primary_intention for d in decisions)
    strat_counts: Counter = Counter(d.primary_strategy for d in decisions)
    conv_counts: Counter = Counter(d.convention for d in decisions)

    dominant_intention = int_counts.most_common(1)[0][0]
    dominant_strategy = strat_counts.most_common(1)[0][0]
    dominant_convention = conv_counts.most_common(1)[0][0]

    non_narrative = sum(
        c for label, c in int_counts.items()
        if label not in {"record", "narrative", "unclassified"}
    )
    rhetorical_density = round(non_narrative / total, 3)

    _ABBREV = {
        "intervention": "Iv", "ideological_contestation": "Ic",
        "legitimation": "Lg", "warning": "Wn", "mobilizing": "Mb",
        "commanding": "Cm", "promising": "Pm", "condemning": "Cd",
        "persuading": "Ps", "questioning": "Qu", "justifying": "Jf",
        "praising": "Pr", "declaring": "Dc", "record": "Rc",
        "narrative": "Nv", "unclassified": "??",
    }
    seq = "·".join(_ABBREV.get(d.primary_intention, "??") for d in decisions[:12])
    if len(decisions) > 12:
        seq += "…"

    return CotextSummary(
        source=source,
        total_sentences=total,
        dominant_intention=dominant_intention,
        dominant_strategy=dominant_strategy,
        rhetorical_density=rhetorical_density,
        convention_profile=dominant_convention,
        intention_distribution=dict(int_counts.most_common()),
        strategy_distribution=dict(strat_counts.most_common()),
        intention_sequence=seq,
    )


# ==========================================================
# IQ4. EXPORT
# ==========================================================

def export_q_skinner_csv(
    decisions: List[QSkinnerDecision],
    output_path: str,
) -> None:

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = [asdict(d) for d in decisions]

    if not rows:
        raise ValueError("No QSkinnerDecision rows to export.")

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


# ==========================================================
# __main__
# ==========================================================

if __name__ == "__main__":
    import sys

    _corpus_mode = "--corpus" in sys.argv
    _limit_idx = sys.argv.index("--limit") if "--limit" in sys.argv else -1
    _limit = int(sys.argv[_limit_idx + 1]) if _limit_idx >= 0 else None

    if _corpus_mode:
        from a_paths import list_bible_files
        from c_input import create_input_from_file
        from j0_context_profile import get_builtin_profile
        from j0_discursive_context import resolve_discursive_context

        _bkr_profile = get_builtin_profile("biblical_czech_bkr")

        files = list_bible_files(limit=_limit)

        print(f"Processing {len(files)} kníh ...", flush=True)

        all_decisions: List[QSkinnerDecision] = []
        all_feats: List[SentenceFeatures] = []
        book_summaries = []

        for idx, fp in enumerate(files, 1):
            print(f"  [{idx:>2}/{len(files)}] {fp.name}", end="  ", flush=True)
            ti = create_input_from_file(
                file_path=str(fp),
                source="written_record",
                interaction="monologue",
                stimulus="unknown",
                speaker="unknown",
                addressee="unknown",
            )
            preprocessed = preprocess_text(ti)
            feats = extract_features(preprocessed)
            sems = semantic_enrichment(feats)
            disc_context = resolve_discursive_context(feats, fp.name)

            book_decisions = []
            for f, s in zip(feats, sems):
                if f.root_lemma is None:
                    continue
                d = classify_q_skinner(f, s, ti,
                                       context=disc_context,
                                       profile=_bkr_profile)
                d.file_name = fp.name
                book_decisions.append(d)
                all_feats.append(f)

            print(f"{len(book_decisions)} viet", flush=True)
            all_decisions.extend(book_decisions)
            book_summaries.append((fp.name, analyze_cotext(book_decisions)))

        # Export CSV
        out_csv = "output/q_skinner_analytics/q_skinner_corpus_full.csv"
        export_q_skinner_csv(all_decisions, out_csv)
        print(f"\nExported {len(all_decisions)} riadkov -> {out_csv}")

        # Per-book co-text summaries
        print(f"\n{'CORPUS CO-TEXT SUMMARIES':─<78}")
        print(f"  {'book':<26} {'n':>6} {'rhet%':>6} {'dom_intention':<24} {'top_conv':<24}")
        print(f"  {'─'*26} {'─'*6} {'─'*6} {'─'*24} {'─'*24}")
        for book_name, cs in book_summaries:
            short = book_name.replace("bible_BKR_", "").replace(".txt", "")
            print(
                f"  {short:<26} {cs.total_sentences:>6} "
                f"{cs.rhetorical_density:>5.1%} "
                f"{cs.dominant_intention:<24} {cs.convention_profile:<24}"
            )

        # Corpus-level distributions
        total = len(all_decisions)
        int_counts = Counter(d.primary_intention for d in all_decisions)
        print(f"\n{'CORPUS PRIMARY INTENTION DISTRIBUTION':─<56}")
        for label, count in int_counts.most_common():
            bar = "█" * (count * 36 // total)
            print(f"  {label:<30} {count:>7}  {count/total:>5.1%}  {bar}")

        force_counts = Counter(d.illocutionary_force for d in all_decisions)
        print(f"\n{'CORPUS ILLOCUTIONARY FORCE DISTRIBUTION':─<56}")
        for label, count in force_counts.most_common():
            bar = "█" * (count * 36 // total)
            print(f"  {label:<30} {count:>7}  {count/total:>5.1%}  {bar}")

        # Priority validation on full corpus
        validation = validate_intention_priority(all_feats)
        print(f"\n{'PRIORITY VALIDATION — plny korpus':─<74}")
        print(f"  {'rnk':<4} {'check':<32} {'fires':>8} {'prim':>7} {'fire%':>6} {'cap%':>6}")
        print(f"  {'─'*4} {'─'*32} {'─'*8} {'─'*7} {'─'*6} {'─'*6}")
        for v in validation:
            print(
                f"  {v['rank']:<4} {v['check']:<32} "
                f"{v['total_fires']:>8} {v['primary_fires']:>7} "
                f"{v['fire_rate']:>5.1%} {v['capture_ratio']:>5.1%}"
            )

        print(f"\nTotal: {total} viet, {len(files)} knih")

    else:
        from c_input import TextInput, InputContext

        SAMPLE = (
            "Hospodin řekl Mojžíšovi: Já jsem Hospodin Bůh tvůj. "
            "Nebudete-li činiti pokání, všickni podobně zahynete. "
            "Blahoslavení čistého srdce, nebo oni Boha viděti budou. "
            "Běda vám, zákoníci a farizeové, pokrytci. "
            "Jděte do všeho světa a kažte evangelium. "
            "Jakož psáno jest: Hospodin spravedlivý jest. "
            "Neboť tak Bůh miloval svět. "
            "Milujte nepřátele své a modlete se za ty, kteříž vás pronásledují. "
            "Kdo zachová zákon celý, ale pochybí v jednom, provinil se proti všem. "
            "Království nebeské podobno jest člověku, který zasel dobré símě na poli svém."
        )

        ti = TextInput(text=SAMPLE, context=InputContext(source="sample"))
        preprocessed = preprocess_text(ti)
        feats = extract_features(preprocessed)
        sems = semantic_enrichment(feats)
        results = [
            classify_q_skinner(f, s, ti, "biblical_cs")
            for f, s in zip(feats, sems)
        ]

        W_SENT   = 52
        W_FORCE  = 14
        W_PINT   = 24
        W_SINT   = 24
        W_PSTRAT = 22
        W_SSTRAT = 22
        W_PVOC   = 34

        header = (
            f"{'#':<3} "
            f"{'SENTENCE':<{W_SENT}} "
            f"{'FORCE':<{W_FORCE}} "
            f"{'P_INT':<{W_PINT}} "
            f"{'S_INT':<{W_SINT}} "
            f"{'P_STRAT':<{W_PSTRAT}} "
            f"{'S_STRAT':<{W_SSTRAT}} "
            f"{'POLITICAL_VOC':<{W_PVOC}}"
        )
        print(header)
        print("-" * len(header))

        for d in results:
            sent_short = (d.sentence[:W_SENT - 1] + "…") if len(d.sentence) > W_SENT else d.sentence
            pvoc = d.political_vocabulary or "—"
            pvoc_short = (pvoc[:W_PVOC - 1] + "…") if len(pvoc) > W_PVOC else pvoc
            print(
                f"{d.sentence_id:<3} "
                f"{sent_short:<{W_SENT}} "
                f"{d.illocutionary_force:<{W_FORCE}} "
                f"{d.primary_intention:<{W_PINT}} "
                f"{str(d.secondary_intention):<{W_SINT}} "
                f"{d.primary_strategy:<{W_PSTRAT}} "
                f"{str(d.secondary_strategy):<{W_SSTRAT}} "
                f"{pvoc_short}"
            )

        print(f"\n{'LAYER 2 — CONVENTION + ANTI_ANACHRONISM':─<72}")
        for d in results:
            anti = "—" if d.anti_anachronism == "none_flagged" else d.anti_anachronism[:56]
            print(f"  {d.sentence_id:<3} {d.convention:<32} {anti}")

        cotext = analyze_cotext(results)
        print(f"\n{'CO-TEXT SUMMARY (sample)':─<50}")
        print(f"  dominant_intention : {cotext.dominant_intention}")
        print(f"  dominant_strategy  : {cotext.dominant_strategy}")
        print(f"  rhetorical_density : {cotext.rhetorical_density:.1%}")
        print(f"  convention_profile : {cotext.convention_profile}")
        print(f"  sequence           : {cotext.intention_sequence}")

        int_counts = Counter(d.primary_intention for d in results)
        print(f"\n{'PRIMARY INTENTION DISTRIBUTION':─<50}")
        for label, count in int_counts.most_common():
            print(f"  {label:<30} {count:>3}  {'█' * count}")

        force_counts = Counter(d.illocutionary_force for d in results)
        print(f"\n{'ILLOCUTIONARY FORCE DISTRIBUTION':─<50}")
        for label, count in force_counts.most_common():
            print(f"  {label:<30} {count:>3}  {'█' * count}")

        validation = validate_intention_priority(feats)
        print(f"\n{'PRIORITY VALIDATION — _INTENTION_CHECKS':─<72}")
        print(f"  {'rnk':<4} {'check':<32} {'fires':>6} {'prim':>5} {'fire%':>6} {'cap%':>6}")
        print(f"  {'─'*4} {'─'*32} {'─'*6} {'─'*5} {'─'*6} {'─'*6}")
        for v in validation:
            print(
                f"  {v['rank']:<4} {v['check']:<32} "
                f"{v['total_fires']:>6} {v['primary_fires']:>5} "
                f"{v['fire_rate']:>5.1%} {v['capture_ratio']:>5.1%}"
            )

        print(f"\nTotal sentences: {len(results)}")
