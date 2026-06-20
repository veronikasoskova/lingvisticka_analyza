from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import g_skinner_rules as rules
from e_extraction import SentenceFeatures
from i_q_skinner_lexicons import (
    LEMMA_IDF_CROSS,
    PRAISING_HYMNIC_LEMMAS, PRAISING_DIRECT_LEMMAS, PRAISING_DOXOLOGY_LEMMAS,
    PRAISING_ATTRIBUTE_LEMMAS, PRAISING_CONFESSION_LEMMAS,
    CONDEMNING_PROPHETIC_LEMMAS, CONDEMNING_JUDGMENT_LEMMAS,
    CONDEMNING_ACCUSATION_LEMMAS, CONDEMNING_LABEL_LEMMAS,
    WARNING_CONDITION_LEMMAS, WARNING_OUTCOME_LEMMAS, WARNING_PREVENTIVE_LEMMAS,
    REPETITION_FORMULA_LEMMAS, REPETITION_ANAPHORIC_LEMMAS, REPETITION_EMPHATIC_LEMMAS,
    JUSTIFYING_CAUSAL_LEMMAS, JUSTIFYING_THEOLOGICAL_LEMMAS, JUSTIFYING_EXPLANATORY_LEMMAS,
    DECLARING_ABSTRACT_LEMMAS, DECLARING_UNIVERSAL_LEMMAS, DECLARING_IDENTITY_LEMMAS,
    COMMANDING_LEMMAS, COMMANDING_PROHIBITION_LEMMAS, COMMANDING_DEONTIC_LEMMAS,
    COMMANDING_NORMATIVE_LEMMAS,
    AUTHORITY_DIVINE_LEMMAS, AUTHORITY_PROPHETIC_LEMMAS, AUTHORITY_APOSTOLIC_LEMMAS,
    SCRIPTURE_CITATION_LEMMAS, SCRIPTURE_FULFILLMENT_LEMMAS, SCRIPTURE_FORMULA_LEMMAS,
    TRADITION_COVENANT_LEMMAS, TRADITION_ANCESTORS_LEMMAS, TRADITION_CONTINUITY_LEMMAS,
    THREAT_DIVINE_WRATH_LEMMAS, THREAT_CONDITION_LEMMAS, THREAT_URGENCY_LEMMAS,
    REWARD_ESCHATOLOGICAL_LEMMAS, REWARD_BEATITUDE_LEMMAS, REWARD_DIRECT_LEMMAS,
    MOBILIZING_MISSIONARY_LEMMAS, MOBILIZING_URGENCY_LEMMAS,
    PERSUADING_CONNECTOR_LEMMAS, PERSUADING_ANALOGY_LEMMAS,
    EMOTIVE_WONDER_LEMMAS, EMOTIVE_FEAR_LEMMAS,
    EMOTIVE_HOPE_LEMMAS, EMOTIVE_GUILT_LEMMAS,
    READER_ADDRESS_LEMMAS,
    DIRECT_ADDRESS_PRONOUN_LEMMAS, DIRECT_ADDRESS_VOCATIVE_LEMMAS,
)

PROFILES_DIR = Path(__file__).parent / "profiles"


# ==========================================================
# JP1. INVERZNÝ INDEX: lemma → skupiny lexikónov
# Precomputed pri importe — O(1) lookup per lemma v _scaled_idf.
# Riziko identifikované v návrhu: bez tohto by škálovanie
# muselo prechádzať cez všetky skupiny per-sentence → výkon.
# ==========================================================

# Explicitná mapa kľúč skupiny → frozenset lemiem
# Kľúče zodpovedajú názvom používaným v idf_group_multipliers profilov.
_GROUP_LEXICONS: dict[str, frozenset] = {
    "PRAISING_HYMNIC":        PRAISING_HYMNIC_LEMMAS,
    "PRAISING_DIRECT":        PRAISING_DIRECT_LEMMAS,
    "PRAISING_DOXOLOGY":      PRAISING_DOXOLOGY_LEMMAS,
    "PRAISING_ATTRIBUTE":     PRAISING_ATTRIBUTE_LEMMAS,
    "PRAISING_CONFESSION":    PRAISING_CONFESSION_LEMMAS,
    "CONDEMNING_PROPHETIC":   CONDEMNING_PROPHETIC_LEMMAS,
    "CONDEMNING_JUDGMENT":    CONDEMNING_JUDGMENT_LEMMAS,
    "CONDEMNING_ACCUSATION":  CONDEMNING_ACCUSATION_LEMMAS,
    "CONDEMNING_LABEL":       CONDEMNING_LABEL_LEMMAS,
    "WARNING_CONDITION":      WARNING_CONDITION_LEMMAS,
    "WARNING_OUTCOME":        WARNING_OUTCOME_LEMMAS,
    "WARNING_PREVENTIVE":     WARNING_PREVENTIVE_LEMMAS,
    "REPETITION_FORMULA":     REPETITION_FORMULA_LEMMAS,
    "REPETITION_ANAPHORIC":   REPETITION_ANAPHORIC_LEMMAS,
    "REPETITION_EMPHATIC":    REPETITION_EMPHATIC_LEMMAS,
    "JUSTIFYING_CAUSAL":      JUSTIFYING_CAUSAL_LEMMAS,
    "JUSTIFYING_THEOLOGICAL": JUSTIFYING_THEOLOGICAL_LEMMAS,
    "JUSTIFYING_EXPLANATORY": JUSTIFYING_EXPLANATORY_LEMMAS,
    "DECLARING_ABSTRACT":     DECLARING_ABSTRACT_LEMMAS,
    "DECLARING_UNIVERSAL":    DECLARING_UNIVERSAL_LEMMAS,
    "DECLARING_IDENTITY":     DECLARING_IDENTITY_LEMMAS,
    "COMMANDING":             COMMANDING_LEMMAS,
    "COMMANDING_PROHIBITION": COMMANDING_PROHIBITION_LEMMAS,
    "COMMANDING_DEONTIC":     COMMANDING_DEONTIC_LEMMAS,
    "COMMANDING_NORMATIVE":   COMMANDING_NORMATIVE_LEMMAS,
    "AUTHORITY_DIVINE":       AUTHORITY_DIVINE_LEMMAS,
    "AUTHORITY_PROPHETIC":    AUTHORITY_PROPHETIC_LEMMAS,
    "AUTHORITY_APOSTOLIC":    AUTHORITY_APOSTOLIC_LEMMAS,
    "SCRIPTURE_CITATION":     SCRIPTURE_CITATION_LEMMAS,
    "SCRIPTURE_FULFILLMENT":  SCRIPTURE_FULFILLMENT_LEMMAS,
    "SCRIPTURE_FORMULA":      SCRIPTURE_FORMULA_LEMMAS,
    "TRADITION_COVENANT":     TRADITION_COVENANT_LEMMAS,
    "TRADITION_ANCESTORS":    TRADITION_ANCESTORS_LEMMAS,
    "TRADITION_CONTINUITY":   TRADITION_CONTINUITY_LEMMAS,
    "THREAT_DIVINE_WRATH":    THREAT_DIVINE_WRATH_LEMMAS,
    "THREAT_CONDITION":       THREAT_CONDITION_LEMMAS,
    "THREAT_URGENCY":         THREAT_URGENCY_LEMMAS,
    "REWARD_ESCHATOLOGICAL":  REWARD_ESCHATOLOGICAL_LEMMAS,
    "REWARD_BEATITUDE":       REWARD_BEATITUDE_LEMMAS,
    "REWARD_DIRECT":          REWARD_DIRECT_LEMMAS,
    "MOBILIZING_MISSIONARY":  MOBILIZING_MISSIONARY_LEMMAS,
    "MOBILIZING_URGENCY":     MOBILIZING_URGENCY_LEMMAS,
    "PERSUADING_CONNECTOR":   PERSUADING_CONNECTOR_LEMMAS,
    "PERSUADING_ANALOGY":     PERSUADING_ANALOGY_LEMMAS,
    "EMOTIVE_WONDER":         EMOTIVE_WONDER_LEMMAS,
    "EMOTIVE_FEAR":           EMOTIVE_FEAR_LEMMAS,
    "EMOTIVE_HOPE":           EMOTIVE_HOPE_LEMMAS,
    "EMOTIVE_GUILT":          EMOTIVE_GUILT_LEMMAS,
    "READER_ADDRESS":         READER_ADDRESS_LEMMAS,
    "DIRECT_ADDRESS_PRONOUN": DIRECT_ADDRESS_PRONOUN_LEMMAS,
    "DIRECT_ADDRESS_VOCATIVE":DIRECT_ADDRESS_VOCATIVE_LEMMAS,
}


def _build_lemma_to_groups() -> dict[str, list[str]]:
    idx: dict[str, list[str]] = {}
    for group_key, lemma_set in _GROUP_LEXICONS.items():
        for lemma in lemma_set:
            idx.setdefault(lemma, []).append(group_key)
    return idx


# Precomputed at import — never recomputed per-sentence.
_LEMMA_TO_GROUPS: dict[str, list[str]] = _build_lemma_to_groups()

_IDF_MAX: float = max(LEMMA_IDF_CROSS.values()) if LEMMA_IDF_CROSS else 1.0


# ==========================================================
# JP2. ŠKÁLOVANÝ IDF
# ==========================================================

def _scaled_idf(
    base_idf: dict[str, float],
    idf_group_multipliers: dict[str, float],
) -> dict[str, float]:
    """
    Scale base_idf values based on which lexicon group each lemma belongs to.
    Multiplier = max over all groups the lemma appears in.
    Lemmas not in any tracked group retain their base weight (multiplier = 1.0).
    """
    result: dict[str, float] = {}
    for lemma, base_weight in base_idf.items():
        groups = _LEMMA_TO_GROUPS.get(lemma, [])
        multiplier = max(
            (idf_group_multipliers.get(g, 1.0) for g in groups),
            default=1.0,
        )
        result[lemma] = base_weight * multiplier
    return result


# ==========================================================
# JP3. CONTEXT PROFILE DATACLASS
# ==========================================================

@dataclass
class ContextProfile:
    # Identifikácia
    name: str
    language: str                     # "cs" | "en" | budúce "la", "de", "ar"
    era: str                          # "16th_century" | "early_20th" | "contemporary"
    tradition: str                    # "protestant_czech" | "esoteric_christian" | ...

    # Dimenzia A — additive delta na base_conf per intention
    intention_delta: dict[str, float]

    # Dimenzia B — IDF group multipliers (kľúče z _GROUP_LEXICONS)
    idf_group_multipliers: dict[str, float]

    # Dimenzia C — ktorý jazykový variant lexikónu použiť
    lexicon_lang: str                 # "cs" | "en"

    # Dimenzia D — potlačenie past-tense→record fallback (pre ne-naratívne eng. texty)
    suppress_past_tense_fallback: bool

    # Precomputed pri __post_init__ — nikdy neukladané do JSON
    scaled_idf: dict[str, float] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        self.scaled_idf = _scaled_idf(LEMMA_IDF_CROSS, self.idf_group_multipliers)

    def to_dict(self) -> dict:
        return {
            "name":                       self.name,
            "language":                   self.language,
            "era":                        self.era,
            "tradition":                  self.tradition,
            "intention_delta":            self.intention_delta,
            "idf_group_multipliers":      self.idf_group_multipliers,
            "lexicon_lang":               self.lexicon_lang,
            "suppress_past_tense_fallback": self.suppress_past_tense_fallback,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ContextProfile":
        return cls(
            name=d["name"],
            language=d["language"],
            era=d["era"],
            tradition=d["tradition"],
            intention_delta=d["intention_delta"],
            idf_group_multipliers=d["idf_group_multipliers"],
            lexicon_lang=d["lexicon_lang"],
            suppress_past_tense_fallback=d["suppress_past_tense_fallback"],
        )


# ==========================================================
# JP4. IDF DELTA — vplyv škálovaného IDF na confidence
# ==========================================================

def compute_profile_idf_delta(
    feature: SentenceFeatures,
    profile: ContextProfile,
    max_effect: float = 0.08,
) -> float:
    """
    Compute the additional confidence delta from using the profile's scaled IDF
    vs. the base LEMMA_IDF_CROSS. Applied as an additive correction after
    the standard confidence_boost().

    Logic:
      - Collect all lemmas in the sentence that have a known IDF score.
      - Compare mean(base_idf) vs. mean(scaled_idf) for those lemmas.
      - Map the difference onto [-max_effect, +max_effect].

    Capped at ±0.08 so profile IDF never overrides the base classification signal.
    """
    lemma_set = rules.lemma_set_of(feature)
    if not lemma_set or _IDF_MAX == 0:
        return 0.0

    base_vals   = [LEMMA_IDF_CROSS[l]     for l in lemma_set if l in LEMMA_IDF_CROSS]
    scaled_vals = [profile.scaled_idf[l]  for l in lemma_set if l in profile.scaled_idf]

    if not base_vals:
        return 0.0

    base_norm   = min(sum(base_vals)   / len(base_vals)   / _IDF_MAX, 1.0)
    scaled_norm = min(sum(scaled_vals) / len(scaled_vals) / _IDF_MAX, 1.0) if scaled_vals else base_norm

    return max(-max_effect, min((scaled_norm - base_norm) * 0.12, max_effect))


# ==========================================================
# JP5. ULOŽENIE A NAČÍTANIE
# ==========================================================

def save_profile(profile: ContextProfile, profiles_dir: Path = PROFILES_DIR) -> Path:
    profiles_dir.mkdir(parents=True, exist_ok=True)
    path = profiles_dir / f"{profile.name}.json"
    path.write_text(json.dumps(profile.to_dict(), ensure_ascii=False, indent=2))
    return path


def load_profile(name_or_path: str, profiles_dir: Path = PROFILES_DIR) -> ContextProfile:
    """
    Load a ContextProfile from JSON.
    Accepts a full path string or a bare profile name (looks in PROFILES_DIR).
    """
    p = Path(name_or_path)
    if not p.suffix:
        p = profiles_dir / f"{name_or_path}.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    return ContextProfile.from_dict(d)


def load_profile_or_none(name: str, profiles_dir: Path = PROFILES_DIR) -> Optional[ContextProfile]:
    try:
        return load_profile(name, profiles_dir)
    except (FileNotFoundError, KeyError):
        return None


# ==========================================================
# JP6. BUILT-IN PROFILY
# Uložia sa ako JSON pri prvom zavolaní save_builtin_profiles().
# ==========================================================

_BUILTIN_PROFILE_DATA: dict[str, dict] = {
    "biblical_czech_bkr": {
        "name": "biblical_czech_bkr",
        "language": "cs",
        "era": "16th_century",
        "tradition": "protestant_czech",
        "intention_delta": {
            "praising":   0.06,
            "warning":    0.05,
            "commanding": 0.04,
            "record":    -0.03,
        },
        "idf_group_multipliers": {
            # BKR-špecifické formulaické signály zosilnené:
            # haleluja/amen/zpívat sú v BKR diagnostické, v iných textoch zriedkavé
            "PRAISING_HYMNIC":        1.3,
            "REPETITION_FORMULA":     1.4,
            "REPETITION_ANAPHORIC":   1.3,
            # Prorocký a varovný register — BKR je plný oboch
            "CONDEMNING_PROPHETIC":   1.2,
            "WARNING_CONDITION":      1.2,
            # Zmluvné a citačné formuly sú jadrom BKR diskurzu
            "SCRIPTURE_CITATION":     1.2,
            "TRADITION_COVENANT":     1.2,
        },
        "lexicon_lang": "cs",
        "suppress_past_tense_fallback": False,
    },
    "esoteric_christian_en": {
        "name": "esoteric_christian_en",
        "language": "en",
        "era": "early_20th",
        "tradition": "esoteric_christian",
        "intention_delta": {
            # Waite deklaruje a vysvetľuje — neodsudzuje ani neprikazuje
            "declaring":   0.07,
            "justifying":  0.05,
            "praising":    0.04,
            "commanding": -0.05,
            "condemning": -0.08,
        },
        "idf_group_multipliers": {
            # Mystické a úžasové registre sú diagnostické pre ezoterickú angličtinu
            "EMOTIVE_WONDER":         1.8,
            "READER_ADDRESS":         1.6,
            "DECLARING_ABSTRACT":     1.5,
            "JUSTIFYING_THEOLOGICAL": 1.4,
            "AUTHORITY_DIVINE":       1.3,
            # Prorocký zákazový register je v ezoterických textoch vzácny
            "CONDEMNING_PROPHETIC":   0.3,
            "COMMANDING_PROHIBITION": 0.4,
        },
        "lexicon_lang": "en",
        "suppress_past_tense_fallback": True,
    },
}


def get_builtin_profile(name: str) -> ContextProfile:
    if name not in _BUILTIN_PROFILE_DATA:
        raise KeyError(f"Unknown built-in profile: {name!r}. Available: {list(_BUILTIN_PROFILE_DATA)}")
    return ContextProfile.from_dict(_BUILTIN_PROFILE_DATA[name])


def save_builtin_profiles(profiles_dir: Path = PROFILES_DIR) -> list[Path]:
    return [
        save_profile(ContextProfile.from_dict(d), profiles_dir)
        for d in _BUILTIN_PROFILE_DATA.values()
    ]
