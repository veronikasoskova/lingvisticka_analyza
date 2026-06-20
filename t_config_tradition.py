from __future__ import annotations
import math


# ==========================================================
# 1. UNIVERSAL RELIGIOUS ELEMENTS
# ==========================================================

MONOTHEISM = frozenset({
    "bůh", "hospodin", "pán", "alláh", "jehova",
    "god", "lord", "adonai", "yhwh", "jediný",
    "stvořitel", "creator", "almighty",
})

DIVINE_HIERARCHY = frozenset({
    "anděl", "archanděl", "cherub", "seraf",
    "angel", "archangel", "seraph", "cherubim",
    "duch", "spirit", "džinn", "devas",
})

RITUAL_SACRIFICE = frozenset({
    "oběť", "oltář", "kněz", "beránek", "krev",
    "kadidlo", "zápalný", "posvětit", "zasvětit",
    "kněží", "olej", "kozel", "volek", "roucho",
    "skopec", "kadidlnice", "mouka", "tuk",
    "ledvinka", "branice", "slabiny", "šarlat",
    "efod", "náprsník",
    "čerevec", "červec",
    "sacrifice", "altar", "priest", "offering",
    "ritual", "oblation", "libation",
})

COVENANT_LAW = frozenset({
    "smlouva", "zákon", "přikázání", "ustanovení",
    "covenant", "law", "commandment", "torah",
    "šaría", "šaria", "dharma", "vinaya",
    "svědectví", "testimony", "ordinance",
})

MYSTICAL_UNION = frozenset({
    "jednota", "sjednocení", "extáze", "vytržení",
    "union", "unio", "mystika", "mystical",
    "fana", "samádhi", "nirvána", "nirvana",
    "mokša", "moksha", "osvícení", "enlightenment",
})

ESOTERIC_KNOWLEDGE = frozenset({
    "tajemství", "skrytý", "zasvěcení", "gnóze",
    "mystery", "hidden", "initiation", "gnosis",
    "kabala", "kabbalah", "hermetismus", "hermetism",
    "okultní", "occult", "esoterický", "esoteric",
})

PROPHETIC_SPEECH = frozenset({
    "prorok", "proroctví", "vidění", "zjevení",
    "prophet", "prophecy", "vision", "revelation",
    "praví", "hospodinovo", "oracle", "thus saith",
    "wahj", "nubuwwa",
})

ESCHATOLOGY = frozenset({
    "poslední", "soud", "vzkříšení", "vzkřísit", "věčnost", "věčný",
    "nebe", "peklo", "skonání", "konec",
    "přijít", "čas", "den",
    "last", "judgment", "resurrection", "eternity",
    "apokalypsa", "apocalypse", "qiyama", "mahdi",
    "mesiáš", "messiah", "parúsie", "parousia",
})

SACRED_SPACE = frozenset({
    "chrám", "svatyně", "oltář", "hora",
    "temple", "sanctuary", "shrine", "holy mountain",
    "mešita", "mosque", "synagoga", "synagogue",
    "pagoda", "mandir", "kaaba", "stupa",
})

GENEALOGY_LINEAGE = frozenset({
    "syn", "otec", "rod", "pokolení", "předek",
    "zplodit", "narodit", "porodit", "rodokmen",
    "potomek", "dům", "prvorozený",
    "son", "father", "lineage", "tribe", "ancestor",
    "nasab", "gotra", "kmen", "klan", "clan",
})

BUDDHIST_ELEMENTS = frozenset({
    "buddha", "dharma", "sangha", "nirvana",
    "karma", "samsara", "bodhi", "bodhisattva",
    "dukkha", "anicca", "anatta", "pali",
    "sutra", "vinaya", "abhidhamma", "zen",
})

HINDU_ELEMENTS = frozenset({
    "brahman", "atman", "vishnu", "shiva",
    "krishna", "rama", "devi", "shakti",
    "vedas", "upanishad", "bhagavad", "gita",
    "yoga", "puja", "mantra", "moksha",
})

ISLAMIC_ELEMENTS = frozenset({
    "alláh", "muhammad", "islám", "korán",
    "allah", "quran", "islam", "salat",
    "zakat", "sawm", "hajj", "shahada",
    "sunna", "hadith", "umma", "jihad",
})

LEGAL_ELEMENTS = frozenset({
    "zákon", "přikázání", "ustanovení", "soud",
    "smlouva", "svědectví", "právo", "spravedlnost",
    "trest", "přestoupit", "nařízení",
    "soudce", "rozsudek", "svědek", "vina",
    "potrestat", "statut", "řád",
})

ROYAL_POWER_ELEMENTS = frozenset({
    "král", "království", "trůn", "stolice",
    "kníže", "vládnout", "panovat",
})

KINSHIP_ELEMENTS = frozenset({
    "otec", "syn", "dcera", "matka",
    "bratr", "žena", "muž", "rod",
})

LIFE_DEATH_ELEMENTS = frozenset({
    "život", "živý", "smrt", "mrtvý",
    "zemřít", "vzkříšení", "věčný",
})

WISDOM_ELEMENTS = frozenset({
    "moudrost", "poznání", "rozumnost",
    "učení", "zákon", "slovo", "rada",
})

WAR_CONFLICT_ELEMENTS = frozenset({
    "boj", "bitva", "meč", "kopí",
    "vojsko", "nepřítel", "zabít", "pobít", "válka",
})

DIVINE_ELEMENTS = frozenset({
    "bůh", "hospodin", "pán", "duch", "svatý",
    "kristus", "ježíš", "sláva", "milost",
    "hospodinův", "víra", "spása", "stvořit",
    "spasit", "odpustit", "modlit", "modlitba",
})

MORAL_ELEMENTS = frozenset({
    "dobrý", "zlý", "spravedlivý", "bezbožný",
    "pravda", "lež", "hřích", "nepravost",
    "milovat", "nenávidět",
})

THEOLOGICAL_LEMMAS = DIVINE_ELEMENTS
MORAL_LEMMAS = MORAL_ELEMENTS


# ==========================================================
# 2. PHILOSOPHICAL INFLUENCES
# ==========================================================

PLATONIC_INFLUENCE = frozenset({
    "idea", "forma", "duše", "tělo", "nesmrtelnost",
    "soul", "body", "immortality", "form", "ideal",
    "demiurg", "demiurge", "logos", "dobro", "good",
})

NEOPLATONIC_INFLUENCE = frozenset({
    "jedno", "emanace", "intelekt", "noús",
    "one", "emanation", "intellect", "nous",
    "plotínos", "plotinus", "proklos", "proclus",
    "hypostaze", "hypostasis",
})

STOIC_INFLUENCE = frozenset({
    "logos", "ctnost", "příroda", "osud",
    "virtue", "nature", "fate", "reason",
    "apatheia", "apathy", "pneuma", "hegemonikon",
    "providentia", "providence",
})

GNOSTIC_INFLUENCE = frozenset({
    "gnóze", "gnosis", "demiurg", "demiurge",
    "archón", "archon", "pleroma", "kenoma",
    "sophia", "aeon", "světlo", "tma",
    "světelný", "spark", "jiskra",
})

ARISTOTELIAN_INFLUENCE = frozenset({
    "forma", "látka", "příčina", "substance",
    "form", "matter", "cause", "substance",
    "entelechia", "entelecheia", "kategorie",
    "category", "potence", "actuality",
})

PYTHAGOREAN_INFLUENCE = frozenset({
    "číslo", "harmonie", "proporce", "duše",
    "number", "harmony", "proportion", "soul",
    "tetraktys", "monad", "dyad", "kosmos",
    "metempsychosis", "stěhování duší",
})

EPICUREAN_INFLUENCE = frozenset({
    "slast", "bolest", "klid", "ataraxia",
    "pleasure", "pain", "tranquility", "ataraxia",
    "aponia", "epikuros", "epicurus", "atom",
    "náhoda", "chance", "clinamen",
})

HERMETIC_INFLUENCE = frozenset({
    "hermes", "trismegistos", "trismegistus",
    "smaragd", "emerald", "kybalion",
    "mentalismus", "mentalism",
    "korespondence", "correspondence",
    "alchymie", "alchemy", "hermetic", "hermetický",
})

SUFI_INFLUENCE = frozenset({
    "rúmí", "rumi", "súfismus", "sufism",
    "faná", "fana", "baqa",
    "taríqa", "tariqa", "zikr",
    "dervíš", "dervish",
    "mystický", "mystical", "mystika",
    "láska", "wine", "vino",
})

KABBALISTIC_INFLUENCE = frozenset({
    "kabala", "kabbalah",
    "sefírot", "sephirot",
    "tóra", "torah",
    "zohar",
    "tikun", "tikkun",
    "cimcum", "tzimtzum",
    "ein sof", "ain sof",
    "sefirot", "sefirah",
})

THEOSOPHICAL_INFLUENCE = frozenset({
    "blavatská", "blavatsky",
    "steiner",
    "teosofie", "theosophy",
    "antroposofie", "anthroposophy",
    "akáša", "akasha",
    "kořenová rasa", "root race",
    "logos", "plán",
})

JUNGIAN_INFLUENCE = frozenset({
    "archetyp", "archetype",
    "nevědomí", "unconscious",
    "kolektivní", "collective",
    "stín", "shadow",
    "anima", "animus",
    "individuace", "individuation",
    "mandala", "synchronicita", "synchronicity",
    "komplex", "complex",
})

NEW_AGE_INFLUENCE = frozenset({
    "čakra", "chakra",
    "aura",
    "vibrace", "vibration",
    "manifestace", "manifestation",
    "probuzení", "awakening",
    "vědomí", "consciousness",
    "energie", "energy",
    "léčení", "healing",
    "kvantový", "quantum",
})

SHAMANIC_INFLUENCE = frozenset({
    "animismus", "animism",
    "totem",
    "šaman", "shaman",
    "duch", "spirit",
    "příroda", "nature",
    "duchovní", "spiritual",
    "kmen", "tribe",
    "rituál", "ritual",
    "trance",
})

TANTRIC_INFLUENCE = frozenset({
    "tantra", "tantric",
    "mantra",
    "čakra", "chakra",
    "kundaliní", "kundalini",
    "mudra",
    "yantra",
    "šakti", "shakti",
    "šiva", "shiva",
    "energie", "energy",
})


# ==========================================================
# 3. TRADITIONS
# ==========================================================

UNIVERSAL_RELIGIOUS_ELEMENTS = {
    "monotheism":         MONOTHEISM,
    "divine_hierarchy":   DIVINE_HIERARCHY,
    "ritual_sacrifice":   RITUAL_SACRIFICE,
    "covenant_law":       COVENANT_LAW,
    "mystical_union":     MYSTICAL_UNION,
    "esoteric_knowledge": ESOTERIC_KNOWLEDGE,
    "prophetic_speech":   PROPHETIC_SPEECH,
    "eschatology":        ESCHATOLOGY,
    "sacred_space":       SACRED_SPACE,
    "genealogy_lineage":  GENEALOGY_LINEAGE,
    "buddhist_elements":  BUDDHIST_ELEMENTS,
    "hindu_elements":     HINDU_ELEMENTS,
    "islamic_elements":   ISLAMIC_ELEMENTS,
    "legal":              LEGAL_ELEMENTS,
    "royal_power":        ROYAL_POWER_ELEMENTS,
    "kinship":            KINSHIP_ELEMENTS,
    "life_death":         LIFE_DEATH_ELEMENTS,
    "wisdom":             WISDOM_ELEMENTS,
    "war_conflict":       WAR_CONFLICT_ELEMENTS,
    "divine":             DIVINE_ELEMENTS,
    "moral":              MORAL_ELEMENTS,
}

PHILOSOPHICAL_INFLUENCES = {
    "platonic":      PLATONIC_INFLUENCE,
    "neoplatonic":   NEOPLATONIC_INFLUENCE,
    "stoic":         STOIC_INFLUENCE,
    "gnostic":       GNOSTIC_INFLUENCE,
    "aristotelian":  ARISTOTELIAN_INFLUENCE,
    "pythagorean":   PYTHAGOREAN_INFLUENCE,
    "epicurean":     EPICUREAN_INFLUENCE,
    "hermetic":      HERMETIC_INFLUENCE,
    "sufi":          SUFI_INFLUENCE,
    "kabbalistic":   KABBALISTIC_INFLUENCE,
    "theosophical":  THEOSOPHICAL_INFLUENCE,
    "jungian":       JUNGIAN_INFLUENCE,
    "new_age":       NEW_AGE_INFLUENCE,
    "shamanic":      SHAMANIC_INFLUENCE,
    "tantric":       TANTRIC_INFLUENCE,
}

# BKR-filtered philosophical lexicons.
# Most post-biblical philosophical terms are absent from 16th-century Czech
# Bible translations: "demiurg", "hypostaze", "emanace", "noús", "pleroma",
# "entelechia", "tetraktys", "ataraxia" and all English terms never appear
# in Králická Bible (1613).  This dict retains only Czech lemmas with
# documented presence in BKR.  Traditions with no BKR-plausible vocabulary
# (hermetic, sufi, kabbalistic, theosophical, jungian, new_age, shamanic,
# tantric) are excluded entirely.
BKR_PHILOSOPHICAL_INFLUENCES: dict[str, frozenset] = {
    "platonic": frozenset({
        "duše", "tělo", "nesmrtelnost", "dobro",
    }),
    "neoplatonic": frozenset({
        "jedno",        # "the One" as abstract concept; emanace/noús/hypostaze absent
    }),
    "stoic": frozenset({
        "ctnost",       # ἀρετή / virtus — Fp 4:8, 2P 1:5
        "příroda",      # φύσις — rare
        "osud",
        "příčina",
    }),
    "gnostic": frozenset({
        "tajemství",    # μυστήριον — common in Paul
        "skrytý",       # κρυπτός
        "světlo",       # φῶς — but also standard biblical metaphor
        "tma",          # σκότος
    }),
    "aristotelian": frozenset({
        "příčina",      # αἰτία
        "látka",        # ὕλη — rare in BKR
    }),
    "pythagorean": frozenset({
        "číslo",        # ἀριθμός — symbolic use in Rv
        "harmonie",
    }),
    "epicurean": frozenset({
        "slast",        # ἡδονή — 2Tm 3:4, Jk 4:1
        "bolest",
        "klid",
        "náhoda",
    }),
}

TRADITIONS: dict[str, dict[str, frozenset]] = {
    "christian_czech": {
        "monotheism":        MONOTHEISM,
        "divine_hierarchy":  DIVINE_HIERARCHY,
        "ritual_sacrifice":  RITUAL_SACRIFICE,
        "covenant_law":      COVENANT_LAW,
        "prophetic_speech":  PROPHETIC_SPEECH,
        "eschatology":       ESCHATOLOGY,
        "sacred_space":      SACRED_SPACE,
        "genealogy_lineage": GENEALOGY_LINEAGE,
        "legal":             LEGAL_ELEMENTS,
        "royal_power":       ROYAL_POWER_ELEMENTS,
        "kinship":           KINSHIP_ELEMENTS,
        "life_death":        LIFE_DEATH_ELEMENTS,
        "wisdom":            WISDOM_ELEMENTS,
        "war_conflict":      WAR_CONFLICT_ELEMENTS,
        "divine":            DIVINE_ELEMENTS,
        "moral":             MORAL_ELEMENTS,
    },
    "christian_english": {
        "monotheism":        MONOTHEISM,
        "divine_hierarchy":  DIVINE_HIERARCHY,
        "ritual_sacrifice":  RITUAL_SACRIFICE,
        "covenant_law":      COVENANT_LAW,
        "prophetic_speech":  PROPHETIC_SPEECH,
        "eschatology":       ESCHATOLOGY,
        "sacred_space":      SACRED_SPACE,
        "genealogy_lineage": GENEALOGY_LINEAGE,
    },
    "jewish_hebrew": {
        "monotheism":        MONOTHEISM,
        "covenant_law":      COVENANT_LAW,
        "ritual_sacrifice":  RITUAL_SACRIFICE,
        "prophetic_speech":  PROPHETIC_SPEECH,
        "sacred_space":      SACRED_SPACE,
        "genealogy_lineage": GENEALOGY_LINEAGE,
        "eschatology":       ESCHATOLOGY,
    },
    "jewish_czech": {
        "monotheism":        MONOTHEISM,
        "covenant_law":      COVENANT_LAW,
        "ritual_sacrifice":  RITUAL_SACRIFICE,
        "prophetic_speech":  PROPHETIC_SPEECH,
        "sacred_space":      SACRED_SPACE,
        "genealogy_lineage": GENEALOGY_LINEAGE,
    },
    "islamic_arabic": {
        "monotheism":        MONOTHEISM,
        "islamic_elements":  ISLAMIC_ELEMENTS,
        "covenant_law":      COVENANT_LAW,
        "prophetic_speech":  PROPHETIC_SPEECH,
        "sacred_space":      SACRED_SPACE,
        "eschatology":       ESCHATOLOGY,
    },
    "islamic_czech": {
        "monotheism":        MONOTHEISM,
        "islamic_elements":  ISLAMIC_ELEMENTS,
        "covenant_law":      COVENANT_LAW,
        "prophetic_speech":  PROPHETIC_SPEECH,
        "eschatology":       ESCHATOLOGY,
    },
    "hermetic_english": {
        "hermetic":           HERMETIC_INFLUENCE,
        "esoteric_knowledge": ESOTERIC_KNOWLEDGE,
        "mystical_union":     MYSTICAL_UNION,
        "divine_hierarchy":   DIVINE_HIERARCHY,
        "neoplatonic":        NEOPLATONIC_INFLUENCE,
        "gnostic":            GNOSTIC_INFLUENCE,
        "platonic":           PLATONIC_INFLUENCE,
    },
    "hermetic_czech": {
        "hermetic":           HERMETIC_INFLUENCE,
        "esoteric_knowledge": ESOTERIC_KNOWLEDGE,
        "mystical_union":     MYSTICAL_UNION,
        "divine_hierarchy":   DIVINE_HIERARCHY,
        "neoplatonic":        NEOPLATONIC_INFLUENCE,
        "gnostic":            GNOSTIC_INFLUENCE,
    },
    "buddhist_pali": {
        "buddhist_elements":  BUDDHIST_ELEMENTS,
        "mystical_union":     MYSTICAL_UNION,
        "eschatology":        ESCHATOLOGY,
        "sacred_space":       SACRED_SPACE,
    },
    "buddhist_czech": {
        "buddhist_elements":  BUDDHIST_ELEMENTS,
        "mystical_union":     MYSTICAL_UNION,
        "esoteric_knowledge": ESOTERIC_KNOWLEDGE,
    },
    "hindu_sanskrit": {
        "hindu_elements":     HINDU_ELEMENTS,
        "mystical_union":     MYSTICAL_UNION,
        "genealogy_lineage":  GENEALOGY_LINEAGE,
        "sacred_space":       SACRED_SPACE,
        "eschatology":        ESCHATOLOGY,
        "pythagorean":        PYTHAGOREAN_INFLUENCE,
    },
    "hindu_czech": {
        "hindu_elements":     HINDU_ELEMENTS,
        "mystical_union":     MYSTICAL_UNION,
        "esoteric_knowledge": ESOTERIC_KNOWLEDGE,
    },
    "sufi_arabic": {
        "sufi":              SUFI_INFLUENCE,
        "mystical_union":    MYSTICAL_UNION,
        "islamic_elements":  ISLAMIC_ELEMENTS,
        "monotheism":        MONOTHEISM,
        "prophetic_speech":  PROPHETIC_SPEECH,
    },
    "sufi_czech": {
        "sufi":              SUFI_INFLUENCE,
        "mystical_union":    MYSTICAL_UNION,
        "esoteric_knowledge": ESOTERIC_KNOWLEDGE,
    },
    "kabbalistic_hebrew": {
        "kabbalistic":       KABBALISTIC_INFLUENCE,
        "monotheism":        MONOTHEISM,
        "covenant_law":      COVENANT_LAW,
        "esoteric_knowledge": ESOTERIC_KNOWLEDGE,
        "prophetic_speech":  PROPHETIC_SPEECH,
    },
    "kabbalistic_czech": {
        "kabbalistic":       KABBALISTIC_INFLUENCE,
        "esoteric_knowledge": ESOTERIC_KNOWLEDGE,
        "mystical_union":    MYSTICAL_UNION,
    },
    "theosophical_english": {
        "theosophical":      THEOSOPHICAL_INFLUENCE,
        "esoteric_knowledge": ESOTERIC_KNOWLEDGE,
        "mystical_union":    MYSTICAL_UNION,
        "divine_hierarchy":  DIVINE_HIERARCHY,
        "jungian":           JUNGIAN_INFLUENCE,
    },
    "new_age_english": {
        "new_age":           NEW_AGE_INFLUENCE,
        "mystical_union":    MYSTICAL_UNION,
        "esoteric_knowledge": ESOTERIC_KNOWLEDGE,
        "jungian":           JUNGIAN_INFLUENCE,
    },
    "new_age_czech": {
        "new_age":           NEW_AGE_INFLUENCE,
        "esoteric_knowledge": ESOTERIC_KNOWLEDGE,
        "mystical_union":    MYSTICAL_UNION,
    },
    "shamanic_english": {
        "shamanic":          SHAMANIC_INFLUENCE,
        "mystical_union":    MYSTICAL_UNION,
        "divine_hierarchy":  DIVINE_HIERARCHY,
        "sacred_space":      SACRED_SPACE,
        "prophetic_speech":  PROPHETIC_SPEECH,
    },
    "shamanic_czech": {
        "shamanic":          SHAMANIC_INFLUENCE,
        "mystical_union":    MYSTICAL_UNION,
        "esoteric_knowledge": ESOTERIC_KNOWLEDGE,
    },
    "tantric_sanskrit": {
        "tantric":           TANTRIC_INFLUENCE,
        "hindu_elements":    HINDU_ELEMENTS,
        "mystical_union":    MYSTICAL_UNION,
        "ritual_sacrifice":  RITUAL_SACRIFICE,
        "sacred_space":      SACRED_SPACE,
    },
    "tantric_czech": {
        "tantric":           TANTRIC_INFLUENCE,
        "mystical_union":    MYSTICAL_UNION,
        "esoteric_knowledge": ESOTERIC_KNOWLEDGE,
    },
}


# ==========================================================
# 4. IDF weights — elements shared by many traditions score lower
# ==========================================================

def _compute_element_idf() -> dict:
    N  = len(TRADITIONS)
    df: dict = {}
    for active in TRADITIONS.values():
        for el in active:
            df[el] = df.get(el, 0) + 1
    # log(N/df): elements unique to 1 tradition → log(N), ubiquitous → 0
    return {el: math.log(N / count) for el, count in df.items()}

_ELEMENT_IDF: dict = _compute_element_idf()

# Union lexicon per tradition (used by detect_tradition_from_lemmas to avoid
# double-counting lemmata shared by multiple elements of the same tradition).
_TRADITION_UNION: dict[str, frozenset] = {
    name: frozenset().union(*elements.values())
    for name, elements in TRADITIONS.items()
}

def _compute_lemma_idf() -> dict:
    """IDF at the lemma level: how many traditions contain each lemma."""
    N = len(TRADITIONS)
    df: dict = {}
    for lexicon in _TRADITION_UNION.values():
        for lemma in lexicon:
            df[lemma] = df.get(lemma, 0) + 1
    return {lemma: math.log(N / count) for lemma, count in df.items()}

_LEMMA_IDF: dict = _compute_lemma_idf()


# ==========================================================
# 5. detect_tradition()
# ==========================================================

def detect_tradition(element_scores: dict) -> str:
    """
    Vráti najpravdepodobnejšiu tradíciu na základe
    TF-IDF váhovaného skóre aktívnych elementov.

    element_scores: {"element_name": count_or_score, ...}
    Elementy zdieľané viacerými tradíciami majú nižší IDF → nižšiu váhu.
    """
    best_tradition = "unknown"
    best_score     = -1.0

    for tradition, active in TRADITIONS.items():
        score = sum(
            element_scores.get(element, 0) * _ELEMENT_IDF.get(element, 1.0)
            for element in active
        )
        if score > best_score:
            best_score     = score
            best_tradition = tradition

    return best_tradition


def detect_tradition_from_lemmas(lemma_counts: dict) -> str:
    """
    Variant of detect_tradition() that takes raw lemma → count mapping
    instead of element-level aggregates.

    Avoids double-counting lemmata that appear in multiple elements of the
    same tradition (e.g. 'zákon' in covenant_law + legal + wisdom all within
    christian_czech would otherwise contribute 3× to that tradition's score).

    Each lemma is counted once per tradition, weighted by _LEMMA_IDF
    (how many traditions contain that lemma).

    lemma_counts: {"zákon": 5, "bůh": 12, ...}
    """
    best_tradition = "unknown"
    best_score     = -1.0

    for tradition, union_lexicon in _TRADITION_UNION.items():
        score = sum(
            lemma_counts.get(lemma, 0) * _LEMMA_IDF.get(lemma, 1.0)
            for lemma in union_lexicon
        )
        if score > best_score:
            best_score     = score
            best_tradition = tradition

    return best_tradition


# ==========================================================
# 6. get_active_elements()
# ==========================================================

def get_active_elements(tradition: str) -> dict:
    """
    Vráti dict {element_name: frozenset} aktívnych
    lexikónov pre danú tradíciu.
    """
    if tradition not in TRADITIONS:
        raise KeyError(
            f"Unknown tradition: '{tradition}'. "
            f"Available: {sorted(TRADITIONS)}"
        )

    return dict(TRADITIONS[tradition])


# ==========================================================
# 7. OVERLAP DIAGNOSTICS  (nedisjunktnosť lexikónov)
# ==========================================================

def get_lexicon_overlaps(tradition_name: str) -> dict[str, list[str]]:
    """
    Returns {lemma: [element_names]} for every lemma that appears in 2+
    elements within the given tradition.  Used to diagnose non-disjointness.

    Example: 'zákon' → ['covenant_law', 'legal', 'wisdom'] for christian_czech
    means a single lemma contributes to 3 elements — triple-counting in naive
    element-level scoring (fixed by detect_tradition_from_lemmas).
    """
    if tradition_name not in TRADITIONS:
        raise KeyError(f"Unknown tradition: '{tradition_name}'")
    elements = TRADITIONS[tradition_name]
    lemma_to_els: dict[str, list[str]] = {}
    for el_name, lexicon in elements.items():
        for lemma in lexicon:
            lemma_to_els.setdefault(lemma, []).append(el_name)
    return {
        lemma: sorted(els)
        for lemma, els in sorted(lemma_to_els.items())
        if len(els) >= 2
    }


def get_element_overlap_matrix(tradition_name: str) -> dict[tuple[str, str], int]:
    """
    Pairwise shared-lemma counts between all element pairs within a tradition.
    Returns {(el1, el2): n_shared} for pairs with n_shared > 0, sorted desc.
    """
    if tradition_name not in TRADITIONS:
        raise KeyError(f"Unknown tradition: '{tradition_name}'")
    elements = TRADITIONS[tradition_name]
    el_names = sorted(elements)
    matrix: dict[tuple[str, str], int] = {}
    for i, el1 in enumerate(el_names):
        for el2 in el_names[i + 1:]:
            shared = len(elements[el1] & elements[el2])
            if shared:
                matrix[(el1, el2)] = shared
    return dict(sorted(matrix.items(), key=lambda kv: -kv[1]))


def overlap_summary(tradition_name: str) -> dict:
    """
    High-level overlap statistics for a tradition.
    Returns: total_overlapping_lemmas, max_element_count_for_a_lemma,
             most_shared_lemma, worst_element_pair.
    """
    overlaps = get_lexicon_overlaps(tradition_name)
    matrix = get_element_overlap_matrix(tradition_name)
    if not overlaps:
        return {"total_overlapping_lemmas": 0}
    worst_lemma = max(overlaps, key=lambda l: len(overlaps[l]))
    worst_pair = next(iter(matrix)) if matrix else ("—", "—")
    return {
        "tradition":               tradition_name,
        "total_overlapping_lemmas": len(overlaps),
        "max_element_count":       max(len(v) for v in overlaps.values()),
        "most_shared_lemma":       f"{worst_lemma} → {overlaps[worst_lemma]}",
        "worst_element_pair":      f"{worst_pair[0]} ∩ {worst_pair[1]} = {matrix.get(worst_pair, 0)} lemmas",
    }


# ==========================================================
# smoke test
# ==========================================================

if __name__ == "__main__":

    print(f"Traditions ({len(TRADITIONS)}):")
    for name, elements in TRADITIONS.items():
        print(f"  {name:<24} → {sorted(elements.keys())}")

    print(f"\nPhilosophical influences: {len(PHILOSOPHICAL_INFLUENCES)}")
    print(f"BKR-filtered phil.:       {len(BKR_PHILOSOPHICAL_INFLUENCES)}")
    print(f"Religious elements:       {len(UNIVERSAL_RELIGIOUS_ELEMENTS)}")

    scores = {
        "monotheism":        10,
        "covenant_law":       8,
        "prophetic_speech":   6,
        "ritual_sacrifice":   4,
        "genealogy_lineage":  3,
    }
    detected = detect_tradition(scores)
    print(f"\ndetect_tradition(test scores) → '{detected}'")

    active = get_active_elements("christian_czech")
    print(f"get_active_elements('christian_czech') → {sorted(active.keys())}")

    # ── Overlap diagnostics ──────────────────────────────
    print(f"\n{'LEXICON OVERLAP DIAGNOSTICS — christian_czech':─<60}")
    summary = overlap_summary("christian_czech")
    for k, v in summary.items():
        print(f"  {k:<30} {v}")

    overlaps = get_lexicon_overlaps("christian_czech")
    print(f"\nShared lemmas ({len(overlaps)}):")
    for lemma, els in list(overlaps.items())[:15]:
        print(f"  {lemma:<22} → {els}")

    matrix = get_element_overlap_matrix("christian_czech")
    print(f"\nTop 10 overlapping element pairs:")
    for (el1, el2), n in list(matrix.items())[:10]:
        print(f"  {el1:<22} ∩ {el2:<22} = {n}")

    print(f"\n{'BKR_PHILOSOPHICAL_INFLUENCES':─<50}")
    for phil, lexicon in BKR_PHILOSOPHICAL_INFLUENCES.items():
        print(f"  {phil:<14} {sorted(lexicon)}")
