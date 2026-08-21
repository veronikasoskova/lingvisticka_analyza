from __future__ import annotations

import math
from collections import Counter
from typing import Iterable


# ==========================================================
# Design
# ----------------------------------------------------------
# Three layers that must not be mixed:
#
# 1. THEMATIC FIELDS  — what a text talks about (sacrifice, kinship…).
#    Used for density charts inside a known corpus (e.g. the Bible).
#
# 2. TRADITION-DIAGNOSTIC LEXICONS  — high-precision terms that identify
#    *which* religion/philosophy a text belongs to (buddha, akáša, sefírot).
#    Generic biblical words never belong here.
#
# 3. SHARED / POLYVALENT MOTIFS  — lemmas that appear in the Bible in their
#    own theological register and were later reused by other traditions
#    (světlo/tma, duše/tělo, slovo, tajemství).  Reported as overlap, never
#    as proof that the Bible is Gnostic, Platonic, Theosophical, etc.
# ==========================================================


def _W(*words: str) -> frozenset[str]:
    """Lower-cased lemma set."""
    return frozenset(w.strip().lower() for w in words if w.strip())


# ==========================================================
# POLYVALENT lemmas — never count as foreign-tradition evidence
# ==========================================================

POLYVALENT_BIBLICAL_LEMMAS = _W(
    # light / darkness — Gn 1, J 1, 1J; later Gnostic / Zoroastrian / New Age
    "světlo", "tma", "temnota", "temný", "světelný",
    "light", "darkness", "dark", "bright",
    # soul / body — biblical anthropology; later Platonism
    "duše", "tělo", "soul", "body",
    # spirit — ruach / pneuma; later shamanic / theosophical / New Age
    "duch", "duchovní", "spirit", "spiritual",
    # word / logos — J 1 (BKR: Slovo, not "logos")
    "slovo", "word",
    # mystery — Pauline μυστήριον, not Gnostic gnosis
    "tajemství", "skrytý", "mystery", "hidden",
    # love — NT agape; later Sufi readings of "love/wine"
    "láska", "milovat", "love", "víno", "vino", "wine",
    # good / one / unity — biblical moral and Shema/John 17 language
    "dobro", "dobrý", "good", "jedno", "jediný", "jednota", "one", "union",
    "sjednocení",
    # virtue / nature / fate — NT arete + creation language; later Stoic
    "ctnost", "příroda", "osud", "virtue", "nature", "fate", "reason",
    # number / harmony — Revelation; later Pythagorean / Kabbalistic
    "číslo", "harmonie", "number", "harmony", "proportion",
    # pleasure / pain / rest — pastoral NT; later Epicurean
    "slast", "bolest", "klid", "náhoda", "pleasure", "pain", "tranquility",
    "chance",
    # cause / matter — ordinary Czech; later Aristotelian
    "příčina", "látka", "cause", "matter", "substance", "forma", "form",
    "idea", "ideal",
    # immortality / eternity — NT; later Platonic
    "nesmrtelnost", "immortality",
    # New Age / Jungian generics that also appear in ordinary Czech/Bible
    "vědomí", "consciousness", "energie", "energy", "probuzení", "awakening",
    "plán", "plan", "stín", "shadow", "komplex", "complex",
    "kmen", "tribe", "rituál", "ritual", "příroda",
    "kolektivní", "collective",
    "mystický", "mystical", "mystika",
    "osvícení", "enlightenment",
)


def distinctive(words: Iterable[str]) -> frozenset[str]:
    """Drop polyvalent biblical lemmas so they cannot attribute a foreign tradition."""
    return frozenset(w.strip().lower() for w in words if w.strip()) - POLYVALENT_BIBLICAL_LEMMAS


# ==========================================================
# 1. THEMATIC RELIGIOUS FIELDS
#    Tradition-specific terms (dharma, mešita, nirvana…) do NOT belong here.
# ==========================================================

MONOTHEISM = _W(
    "bůh", "hospodin", "alláh", "allah", "jehova", "jahve",
    "god", "adonai", "yhwh", "yhwh",
    "stvořitel", "creator", "almighty", "všemohoucí",
    # "pán" / "lord" / "jediný" omitted: too many human-lord and "only" hits
)

DIVINE_HIERARCHY = _W(
    "anděl", "archanděl", "cherub", "cherubín", "seraf", "serafín",
    "angel", "archangel", "seraph", "cherubim", "seraphim",
    "džinn", "jinn", "devas", "deva",
    # "duch" / "spirit" omitted: Holy Spirit is DIVINE, shamanic false positive
)

RITUAL_SACRIFICE = _W(
    "oběť", "oltář", "kněz", "kněží", "velekněz",
    "beránek", "kozel", "volek", "skopec",
    "kadidlo", "kadidlnice", "zápalný",
    "posvětit", "zasvětit", "efod", "náprsník",
    "čerevec", "červec",
    "sacrifice", "altar", "priest", "offering",
    "oblation", "libation",
    "krev",  # cultic blood; still noisy but central to Leviticus / NT
    # removed generic food/cloth: olej, mouka, tuk, ledvinka, branice,
    # slabiny, šarlat, roucho
)

COVENANT_LAW = _W(
    "smlouva", "zákon", "přikázání", "ustanovení", "desatero", "dekalog",
    "covenant", "commandment", "torah", "tóra",
    # "svědectví" omitted: NT "witness", not Sinai tablets
    # dharma / vinaya / šaría belong in their diagnostic lexicons
)

MYSTICAL_UNION = distinctive((
    "extáze", "ecstasy", "unio", "mystika",
    "fana", "faná", "samádhi", "samadhi",
    "nirvána", "nirvana", "nibbána", "nibbana",
    "mokša", "moksha", "henosis",
))

ESOTERIC_KNOWLEDGE = distinctive((
    "zasvěcení", "initiation", "gnóze", "gnosis",
    "kabala", "kabbalah", "hermetismus", "hermetism", "hermetic",
    "okultní", "occult", "esoterický", "esoteric",
    "tajná doktrína",
))

PROPHETIC_SPEECH = _W(
    "prorok", "proroctví", "prorokyně", "vidění", "zjevení",
    "prophet", "prophecy", "vision", "revelation",
    "hospodinovo",  # "slovo Hospodinovo"
    "oracle", "wahj", "nubuwwa", "výrok",
    # "praví" omitted: ordinary "says"
)

ESCHATOLOGY = _W(
    "vzkříšení", "vzkřísit", "věčnost",
    "peklo", "sheol", "gehenna", "hades",
    "apokalypsa", "apocalypse", "parúsie", "parousia",
    "mesiáš", "messiah",
    "antikrist", "antichrist", "armagedon", "armageddon",
    "qiyama", "mahdi",
    "poslední",  # "poslední hodina / den"
    # removed generic: přijít, čas, den, konec, nebe, soud
)

SACRED_SPACE = _W(
    "chrám", "svatyně", "oltář",
    "temple", "sanctuary", "shrine",
    # "hora" omitted: ordinary mountain
    # mosque / pagoda / kaaba / stupa belong in diagnostic lexicons
)

GENEALOGY_LINEAGE = _W(
    "pokolení", "předek", "zplodit", "rodokmen",
    "potomek", "prvorozený", "rod",
    "lineage", "ancestor", "genealogy",
    "nasab", "gotra",
    # syn / otec / dům / narodit belong in kinship (too common for genealogy)
)

LEGAL_ELEMENTS = _W(
    "zákon", "přikázání", "ustanovení", "soud",
    "smlouva", "právo", "spravedlnost",
    "trest", "přestoupit", "nařízení",
    "soudce", "rozsudek", "svědek", "vina",
    "potrestat", "statut", "řád",
)

ROYAL_POWER_ELEMENTS = _W(
    "král", "království", "trůn", "stolice",
    "kníže", "vládnout", "panovat",
)

KINSHIP_ELEMENTS = _W(
    "otec", "syn", "dcera", "matka",
    "bratr", "sestra", "žena", "muž", "rod",
)

LIFE_DEATH_ELEMENTS = _W(
    "život", "živý", "smrt", "mrtvý",
    "zemřít", "vzkříšení", "věčný",
)

WISDOM_ELEMENTS = _W(
    "moudrost", "poznání", "rozumnost",
    "učení", "rada", "přísloví", "poučení", "naučení",
    # "zákon" / "slovo" omitted: legal + every "word"
)

WAR_CONFLICT_ELEMENTS = _W(
    "boj", "bitva", "meč", "kopí",
    "vojsko", "nepřítel", "zabít", "pobít", "válka",
)

DIVINE_ELEMENTS = _W(
    "bůh", "hospodin", "pán", "svatý",
    "kristus", "ježíš", "jezukristus", "jezis",
    "sláva", "milost",
    "hospodinův", "víra", "spása", "stvořit",
    "spasit", "odpustit", "modlit", "modlitba",
    "duch",  # Holy Spirit / Spirit of God — thematic, not shamanic diagnostic
)

MORAL_ELEMENTS = _W(
    "dobrý", "zlý", "spravedlivý", "bezbožný",
    "pravda", "lež", "hřích", "nepravost",
    "milovat", "nenávidět",
)

THEOLOGICAL_LEMMAS = DIVINE_ELEMENTS
MORAL_LEMMAS = MORAL_ELEMENTS


THEMATIC_ELEMENTS: dict[str, frozenset] = {
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
    "legal":              LEGAL_ELEMENTS,
    "royal_power":        ROYAL_POWER_ELEMENTS,
    "kinship":            KINSHIP_ELEMENTS,
    "life_death":         LIFE_DEATH_ELEMENTS,
    "wisdom":             WISDOM_ELEMENTS,
    "war_conflict":       WAR_CONFLICT_ELEMENTS,
    "divine":             DIVINE_ELEMENTS,
    "moral":              MORAL_ELEMENTS,
}


# ==========================================================
# 2. TRADITION-DIAGNOSTIC LEXICONS  (high precision)
# ==========================================================

CHRISTIAN_ELEMENTS = distinctive((
    "kristus", "ježíš", "jezukristus", "jezis", "ježíšův",
    "christ", "jesus", "christus",
    "evangelium", "gospel", "evangelista",
    "církev", "cirkev", "church", "ekklésia", "ecclesia",
    "kříž", "kriz", "ukřižovat", "ukřižování", "cross", "crucify",
    "apoštol", "apostle", "apoštolský",
    "křest", "křtít", "křtění", "baptism", "baptize",
    "eucharistie", "eucharist",
    "trojice", "trinity", "trinitarian",
    "hospodin",
    "spasitel", "saviour", "savior", "vykupitel", "redeemer",
    "farizej", "saducej", "pharisee", "sadducee",
    "letnice", "pentecost",
    "inkarnace", "vtělení", "incarnation",
    "evangelijní",
))

JEWISH_ELEMENTS = distinctive((
    "tóra", "torah", "talmud", "mišna", "mishnah", "gemara",
    "halacha", "halakhah", "agada", "aggadah",
    "šabat", "sabat", "shabbat", "sabbath",
    "košer", "kosher", "kašrut", "kashrut",
    "tefilin", "tefillin", "mezuza", "mezuzah",
    "jahve", "yhwh", "adonai", "elohim",
    "rabi", "rabbi", "rabín",
    "midraš", "midrash", "tanach", "tanakh",
    "menora", "menorah", "chanuka", "hanukkah", "pesach", "sukot", "sukkot",
    "synagoga", "synagogue",
))

ISLAMIC_ELEMENTS = distinctive((
    "alláh", "allah", "muhammad", "mohamed", "mohammed",
    "islám", "islam", "korán", "quran", "qur'an",
    "salat", "salát", "zakat", "zakát", "sawm", "saum",
    "hajj", "hadždž", "shahada", "šaháda",
    "sunna", "hadith", "hadís", "umma", "ummah",
    "jihad", "džihád",
    "mešita", "mosque", "imám", "imam",
    "súra", "sura", "ája", "ayah",
    "ramadán", "ramadan", "šaría", "šaria", "sharia",
    "kaaba", "ka'ba", "mekka", "mecca", "medina",
))

BUDDHIST_ELEMENTS = distinctive((
    "buddha", "buddhismus", "buddhistický", "buddhism", "buddhist",
    "dharma", "dhamma", "sangha", "saṅgha",
    "nirvana", "nirvána", "nibbana", "nibbána",
    "karma", "karman",
    "samsara", "sansára", "samsára",
    "bodhi", "bódhi", "bodhisattva", "bódhisattva",
    "dukkha", "anicca", "anatta", "anattá", "anātman",
    "sutra", "sútra", "sutta", "vinaya",
    "abhidhamma", "abhidharma",
    "zen", "čchan", "chan", "satori", "kóan", "koan",
    "vipassana", "vipassaná", "samatha", "metta",
    "theravada", "theraváda", "mahayana", "mahájána",
    "vajrayana", "vadžrajána", "hinayana", "hinajána",
    "arhat", "arahant", "tathagata", "tathágata",
    "stupa", "stúpa", "pagoda",
    "dalajlama", "dalajláma", "lama",
    "sunyata", "šúnjatá", "skandha", "khandha",
    "pratitya", "pratítja",
    "osmidílná", "eightfold", "madhjamaka", "madhyamaka",
    "jogačára", "yogacara", "pali", "páli",
))

HINDU_ELEMENTS = distinctive((
    "brahman", "brahmá", "brahma", "atman", "átman",
    "vishnu", "višnu", "shiva", "šiva",
    "krishna", "kršna", "krišna",
    "devi", "déví", "shakti", "šakti",
    "kali", "kálí", "durga",
    "vedas", "védy", "véda", "upanishad", "upanišad", "upanišady",
    "bhagavad", "gita", "gíta", "bhagavadgíta",
    "yoga", "jóga", "puja", "púdža", "mantra",
    "moksha", "mókša", "mokša",
    "avatar", "avatár",
    "indra", "agni", "soma", "sóma",
    "vedanta", "védánta", "advaita", "samkhya", "sánkhja",
    "om", "aum", "pranayama", "pránájáma",
    "varna", "bráhmana", "kšatrija", "vaišja", "šúdra",
    "kaliyuga", "yuga", "juga",
    "purana", "purána", "mahabharata", "mahábhárata", "ramayana", "rámájana",
    "mandir",
))

HERMETIC_ELEMENTS = distinctive((
    "hermes", "trismegistos", "trismegistus",
    "hermetismus", "hermetism", "hermetic", "hermetický",
    "smaragd", "emerald", "kybalion",
    "alchymie", "alchemy", "alchymista",
    "poimandres", "poimandrès", "corpus hermeticum",
    "mentalismus", "mentalism",
    "korespondence", "correspondence",
))

SUFI_ELEMENTS = distinctive((
    "súfismus", "sufism", "súfí", "sufi", "súfijský",
    "rúmí", "rumi", "rumiho",
    "faná", "fana", "baqa", "baqá",
    "taríqa", "tariqa", "zikr", "dhikr",
    "dervíš", "dervish",
    "halládž", "hallaj", "ibn arabí", "ibn arabi",
    "gazálí", "ghazali",
    "wahdat", "qawwali",
))

KABBALISTIC_ELEMENTS = distinctive((
    "kabala", "kabbalah", "kabbalist", "kabalista",
    "sefírot", "sephirot", "sefirot", "sefirah", "sephirah",
    "zohar", "tikun", "tikkun",
    "cimcum", "tzimtzum",
    "ein sof", "ain sof",
    "merkabah", "merkava", "merkavah",
    "klipot", "qlippoth", "qliphoth",
    "adam kadmon",
    "shekhinah", "šechina", "shechinah",
))

THEOSOPHICAL_ELEMENTS = distinctive((
    "blavatská", "blavatsky", "hpb", "olcott",
    "besant", "leadbeater", "sinnett",
    "teosofie", "teozofie", "theosophy", "theosophical", "teosofický", "teozofický",
    "antroposofie", "anthroposophy", "steiner", "goetheanum",
    "akáša", "akasha", "akášický", "akashic",
    "mahátma", "mahatma", "morya", "koot", "hoomi",
    "dzyan", "shambhala", "šambala", "shambala",
    "lemurie", "lemuria", "hyperborea",
    "astrální", "astral", "káuzální", "causal",
    "buddhi", "sanat", "kumara",
    "alice bailey", "bailey", "lucis",
    "kořenová", "root-race", "rootrace",
    "tajná doktrína", "secret doctrine",
    "isis unveiled",
))

JUNGIAN_ELEMENTS = distinctive((
    "archetyp", "archetype", "archetypový",
    "nevědomí", "unconscious",
    "anima", "animus",
    "individuace", "individuation",
    "mandala", "synchronicita", "synchronicity",
    "jung", "jungian", "jungiánský",
    # "stín" / "komplex" / "kolektivní" omitted: too generic
))

NEW_AGE_ELEMENTS = distinctive((
    "čakra", "chakra", "aura",
    "vibrace", "vibration",
    "manifestace", "manifestation",
    "kvantový", "quantum",
    "indigo", "starseed", "lightworker",
    "holistický", "holistic",
    "ascended master", "ascended",
    # "vědomí" / "energie" / "probuzení" / "léčení" omitted
))

SHAMANIC_ELEMENTS = distinctive((
    "animismus", "animism", "totem", "totemismus",
    "šaman", "shaman", "šamanský", "shamanic", "šamanismus", "shamanism",
    "ayahuasca", "ayahuasca", "icaro",
    "trance", "trans",
    # "duch" / "příroda" / "kmen" / "rituál" omitted
))

TANTRIC_ELEMENTS = distinctive((
    "tantra", "tantric", "tantrický", "tantrismus",
    "kundaliní", "kundalini",
    "mudra", "mudrá", "yantra", "jantra",
    "šakti", "shakti", "šiva", "shiva",
    "čakra", "chakra", "mantra",
    # "energie" omitted
))

GNOSTIC_ELEMENTS = distinctive((
    "gnóze", "gnosis", "gnostik", "gnostic", "gnosticismus",
    "demiurg", "demiurge",
    "archón", "archon", "archont",
    "pleroma", "pléróma", "kenoma", "kénoma",
    "aeon", "aión", "aion",
    "yaldabaoth", "ialdabaoth",
    "valentinos", "valentinus", "basilides", "sethian", "sethiánský",
    "nag hammadi", "hammadi",
    "jiskra", "spark",
    # "sophia" kept as loanword; Czech "moudrost" is biblical Hokhmah
    "sophia",
    # "světlo" / "tma" omitted — Johannine, not Gnostic evidence
))

ZOROASTRIAN_ELEMENTS = distinctive((
    "zoroaster", "zarathustra", "zarathuštra", "zoroastrismus", "zoroastrian",
    "ahura", "mazda", "ahuramazda",
    "ahriman", "angra", "mainyu",
    "asha", "aša", "druj",
    "avesta", "gatha", "gáthy", "zend",
    "mithra", "mitra", "faravahar",
    "magi", "mágové",
))

TAOIST_ELEMENTS = distinctive((
    "tao", "dao", "taocismus", "taoismus", "taoist", "taoistický",
    "daodejing", "tao te", "laozi", "lao-c'", "lao c'", "laotse",
    "zhuangzi", "čuang", "qi", "čchi", "chi",
    "yin", "yang", "jin", "jang", "yin-yang",
    "wuwei", "wu-wei", "nesmrtelní",
    "taiji", "tchai-ťi", "qigong", "čchi-kung",
))


TRADITION_DIAGNOSTIC: dict[str, frozenset] = {
    "christian":     CHRISTIAN_ELEMENTS,
    "jewish":        JEWISH_ELEMENTS,
    "islamic":       ISLAMIC_ELEMENTS,
    "buddhist":      BUDDHIST_ELEMENTS,
    "hindu":         HINDU_ELEMENTS,
    "hermetic":      HERMETIC_ELEMENTS,
    "sufi":          SUFI_ELEMENTS,
    "kabbalistic":   KABBALISTIC_ELEMENTS,
    "theosophical":  THEOSOPHICAL_ELEMENTS,
    "jungian":       JUNGIAN_ELEMENTS,
    "new_age":       NEW_AGE_ELEMENTS,
    "shamanic":      SHAMANIC_ELEMENTS,
    "tantric":       TANTRIC_ELEMENTS,
    "gnostic":       GNOSTIC_ELEMENTS,
    "zoroastrian":   ZOROASTRIAN_ELEMENTS,
    "taoist":        TAOIST_ELEMENTS,
}


# ==========================================================
# 3. PHILOSOPHICAL INFLUENCES  — distinctive only
# ==========================================================

PLATONIC_INFLUENCE = distinctive((
    "platón", "platon", "plato", "platónský", "platonic", "platonismus",
    "anamnéza", "anamnesis", "anamnesis",
    "eidos", "kalokagathia",
    "sókratés", "socrates", "sokratés",
    "faidón", "phaedo", "symposion", "symposium",
    "demiurg", "demiurge",
    # duše / tělo / dobro / idea / forma / nesmrtelnost are polyvalent
))

NEOPLATONIC_INFLUENCE = distinctive((
    "plotínos", "plotinus", "proklos", "proclus",
    "iamblichos", "iamblichus", "porfyrios", "porphyry",
    "emanace", "emanation",
    "noús", "nous", "hypostaze", "hypostasis",
    "henosis", "neoplatonismus", "neoplatonic",
    "intelekt", "intellect",
    # "jedno" omitted: ordinary Czech "one"
))

STOIC_INFLUENCE = distinctive((
    "stoicismus", "stoicism", "stoik", "stoic", "stoický",
    "apatheia", "hegemonikon",
    "zénón", "zeno", "seneca", "epiktétos", "epictetus",
    "marcus aurelius", "aurelius",
    "providentia", "providence",
    "pneuma",  # technical Stoic; BKR uses "duch"
    "logos",   # technical loanword; BKR translates J 1 as "slovo"
    # ctnost / příroda / osud omitted
))

GNOSTIC_INFLUENCE = GNOSTIC_ELEMENTS  # already distinctive

ARISTOTELIAN_INFLUENCE = distinctive((
    "aristotelés", "aristotle", "aristotelismus", "aristotelian",
    "entelechia", "entelecheia",
    "kategorie", "category",
    "potence", "actuality", "energeia",
    "hyle", "morfé", "lykeion", "lyceum", "organon",
    "metafyzika", "metaphysics",
    # forma / látka / příčina / substance omitted
))

PYTHAGOREAN_INFLUENCE = distinctive((
    "pýthagorás", "pythagoras", "pythagorejský", "pythagorean",
    "tetraktys", "monad", "dyad", "monáda", "dyáda",
    "metempsychosis", "metempsychóza", "stěhování duší",
    "kosmos",
    # číslo / harmonie omitted
))

EPICUREAN_INFLUENCE = distinctive((
    "epikuros", "epicurus", "epikureismus", "epicurean", "epikurejský",
    "ataraxia", "aponia", "clinamen", "atom", "atomismus",
    # slast / bolest / klid / náhoda omitted
))

HERMETIC_INFLUENCE = HERMETIC_ELEMENTS
SUFI_INFLUENCE = SUFI_ELEMENTS
KABBALISTIC_INFLUENCE = KABBALISTIC_ELEMENTS
THEOSOPHICAL_INFLUENCE = THEOSOPHICAL_ELEMENTS
JUNGIAN_INFLUENCE = JUNGIAN_ELEMENTS
NEW_AGE_INFLUENCE = NEW_AGE_ELEMENTS
SHAMANIC_INFLUENCE = SHAMANIC_ELEMENTS
TANTRIC_INFLUENCE = TANTRIC_ELEMENTS


PHILOSOPHICAL_INFLUENCES: dict[str, frozenset] = {
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

# Kralická Bible (1613) contains none of the distinctive post-biblical
# philosophical lemmas.  Generic biblical words are tracked as SHARED_MOTIFS.
BKR_PHILOSOPHICAL_INFLUENCES: dict[str, frozenset] = {
    name: distinctive(lexicon)
    for name, lexicon in PHILOSOPHICAL_INFLUENCES.items()
}


# ==========================================================
# 4. SHARED / POLYVALENT MOTIFS  (explanation layer, not attribution)
# ==========================================================

SHARED_MOTIFS: dict[str, dict] = {
    "light_darkness": {
        "lemmas": _W("světlo", "tma", "temnota", "temný", "světelný",
                     "light", "darkness", "dark"),
        "biblical_home": "Gn 1; J 1; 1J — stvoření a janovský dualismus",
        "later_traditions": ("gnostic", "zoroastrian", "new_age"),
    },
    "soul_body": {
        "lemmas": _W("duše", "tělo", "soul", "body"),
        "biblical_home": "hebr. nefeš / gr. psyché — antropológia, nie platónsky dualizmus",
        "later_traditions": ("platonic", "neoplatonic", "pythagorean"),
    },
    "spirit": {
        "lemmas": _W("duch", "duchovní", "spirit", "spiritual"),
        "biblical_home": "hebr. rúach / gr. pneuma — Duch Boží, nie šamanizmus",
        "later_traditions": ("shamanic", "new_age", "theosophical", "stoic"),
    },
    "logos_word": {
        "lemmas": _W("slovo", "word"),
        "biblical_home": "J 1: BKR prekladá λόγος ako Slovo, nie ako 'logos'",
        "later_traditions": ("stoic", "neoplatonic", "theosophical"),
    },
    "mystery": {
        "lemmas": _W("tajemství", "skrytý", "mystery", "hidden"),
        "biblical_home": "Pavlov μυστήριον — skrytý plán spásy, nie gnostická gnóza",
        "later_traditions": ("gnostic", "hermetic", "kabbalistic"),
    },
    "love": {
        "lemmas": _W("láska", "milovat", "love"),
        "biblical_home": "NT agapé — zmluva a prikázanie, nie súfijský 'wine/love'",
        "later_traditions": ("sufi",),
    },
    "one_unity": {
        "lemmas": _W("jedno", "jediný", "jednota", "one"),
        "biblical_home": "Shema / J 17 — jedinosť Boha, nie novoplatónske Jedno",
        "later_traditions": ("neoplatonic",),
    },
    "immortality": {
        "lemmas": _W("nesmrtelnost", "immortality", "věčný", "věčnost"),
        "biblical_home": "NZ vzkriesenie a večný život, nie platónska nesmrteľnosť duše",
        "later_traditions": ("platonic",),
    },
    "number_harmony": {
        "lemmas": _W("číslo", "harmonie", "number", "harmony"),
        "biblical_home": "symbolika v Zjavení, nie pythagorejská náuka o čísle",
        "later_traditions": ("pythagorean", "kabbalistic"),
    },
    "virtue_nature_fate": {
        "lemmas": _W("ctnost", "příroda", "osud", "virtue", "nature", "fate"),
        "biblical_home": "NZ areté / stvorenie, nie stoická fyzika",
        "later_traditions": ("stoic",),
    },
    "pleasure_pain": {
        "lemmas": _W("slast", "bolest", "klid", "pleasure", "pain"),
        "biblical_home": "pastorálne listy a žalmy, nie epikurejská ataraxia",
        "later_traditions": ("epicurean",),
    },
}


# ==========================================================
# 5. TRADITIONS  (thematic fields + own diagnostic lexicon)
# ==========================================================

_CS_THEMATIC = {
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
}

_EN_CORE = {
    "monotheism":        MONOTHEISM,
    "divine_hierarchy":  DIVINE_HIERARCHY,
    "ritual_sacrifice":  RITUAL_SACRIFICE,
    "covenant_law":      COVENANT_LAW,
    "prophetic_speech":  PROPHETIC_SPEECH,
    "eschatology":       ESCHATOLOGY,
    "sacred_space":      SACRED_SPACE,
    "genealogy_lineage": GENEALOGY_LINEAGE,
}

TRADITIONS: dict[str, dict[str, frozenset]] = {
    "christian_czech": {
        **_CS_THEMATIC,
        "christian_elements": CHRISTIAN_ELEMENTS,
    },
    "christian_english": {
        **_EN_CORE,
        "christian_elements": CHRISTIAN_ELEMENTS,
        "divine": DIVINE_ELEMENTS,
        "moral": MORAL_ELEMENTS,
    },
    "jewish_hebrew": {
        "monotheism":        MONOTHEISM,
        "covenant_law":      COVENANT_LAW,
        "ritual_sacrifice":  RITUAL_SACRIFICE,
        "prophetic_speech":  PROPHETIC_SPEECH,
        "sacred_space":      SACRED_SPACE,
        "genealogy_lineage": GENEALOGY_LINEAGE,
        "eschatology":       ESCHATOLOGY,
        "jewish_elements":   JEWISH_ELEMENTS,
    },
    "jewish_czech": {
        "monotheism":        MONOTHEISM,
        "covenant_law":      COVENANT_LAW,
        "ritual_sacrifice":  RITUAL_SACRIFICE,
        "prophetic_speech":  PROPHETIC_SPEECH,
        "sacred_space":      SACRED_SPACE,
        "genealogy_lineage": GENEALOGY_LINEAGE,
        "jewish_elements":   JEWISH_ELEMENTS,
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
        "gnostic":            GNOSTIC_INFLUENCE,
        "platonic":           PLATONIC_INFLUENCE,
        "neoplatonic":        NEOPLATONIC_INFLUENCE,
    },
    "hermetic_czech": {
        "hermetic":           HERMETIC_INFLUENCE,
        "esoteric_knowledge": ESOTERIC_KNOWLEDGE,
        "mystical_union":     MYSTICAL_UNION,
        "divine_hierarchy":   DIVINE_HIERARCHY,
        "gnostic":            GNOSTIC_INFLUENCE,
        "neoplatonic":        NEOPLATONIC_INFLUENCE,
    },
    "buddhist_pali": {
        "buddhist_elements":  BUDDHIST_ELEMENTS,
        "mystical_union":     MYSTICAL_UNION,
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
        "sufi":               SUFI_INFLUENCE,
        "mystical_union":     MYSTICAL_UNION,
        "esoteric_knowledge": ESOTERIC_KNOWLEDGE,
    },
    "kabbalistic_hebrew": {
        "kabbalistic":        KABBALISTIC_INFLUENCE,
        "monotheism":         MONOTHEISM,
        "covenant_law":       COVENANT_LAW,
        "esoteric_knowledge": ESOTERIC_KNOWLEDGE,
        "prophetic_speech":   PROPHETIC_SPEECH,
        "jewish_elements":    JEWISH_ELEMENTS,
    },
    "kabbalistic_czech": {
        "kabbalistic":        KABBALISTIC_INFLUENCE,
        "esoteric_knowledge": ESOTERIC_KNOWLEDGE,
        "mystical_union":     MYSTICAL_UNION,
    },
    "theosophical_english": {
        "theosophical":       THEOSOPHICAL_INFLUENCE,
        "esoteric_knowledge": ESOTERIC_KNOWLEDGE,
        "mystical_union":     MYSTICAL_UNION,
        "hindu_elements":     HINDU_ELEMENTS,
        "buddhist_elements":  BUDDHIST_ELEMENTS,
    },
    "theosophical_czech": {
        "theosophical":       THEOSOPHICAL_INFLUENCE,
        "esoteric_knowledge": ESOTERIC_KNOWLEDGE,
        "mystical_union":     MYSTICAL_UNION,
        "hindu_elements":     HINDU_ELEMENTS,
        "buddhist_elements":  BUDDHIST_ELEMENTS,
    },
    "new_age_english": {
        "new_age":            NEW_AGE_INFLUENCE,
        "mystical_union":     MYSTICAL_UNION,
        "esoteric_knowledge": ESOTERIC_KNOWLEDGE,
        "jungian":            JUNGIAN_INFLUENCE,
    },
    "new_age_czech": {
        "new_age":            NEW_AGE_INFLUENCE,
        "esoteric_knowledge": ESOTERIC_KNOWLEDGE,
        "mystical_union":     MYSTICAL_UNION,
    },
    "shamanic_english": {
        "shamanic":          SHAMANIC_INFLUENCE,
        "mystical_union":    MYSTICAL_UNION,
        "divine_hierarchy":  DIVINE_HIERARCHY,
        "sacred_space":      SACRED_SPACE,
        "prophetic_speech":  PROPHETIC_SPEECH,
    },
    "shamanic_czech": {
        "shamanic":           SHAMANIC_INFLUENCE,
        "mystical_union":     MYSTICAL_UNION,
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
        "tantric":            TANTRIC_INFLUENCE,
        "mystical_union":     MYSTICAL_UNION,
        "esoteric_knowledge": ESOTERIC_KNOWLEDGE,
    },
    "gnostic_czech": {
        "gnostic":            GNOSTIC_INFLUENCE,
        "esoteric_knowledge": ESOTERIC_KNOWLEDGE,
        "mystical_union":     MYSTICAL_UNION,
        "platonic":           PLATONIC_INFLUENCE,
    },
    "gnostic_english": {
        "gnostic":            GNOSTIC_INFLUENCE,
        "esoteric_knowledge": ESOTERIC_KNOWLEDGE,
        "mystical_union":     MYSTICAL_UNION,
        "platonic":           PLATONIC_INFLUENCE,
    },
    "zoroastrian_czech": {
        "zoroastrian":       ZOROASTRIAN_ELEMENTS,
        "monotheism":        MONOTHEISM,
        "eschatology":       ESCHATOLOGY,
        "prophetic_speech":  PROPHETIC_SPEECH,
    },
    "zoroastrian_english": {
        "zoroastrian":       ZOROASTRIAN_ELEMENTS,
        "monotheism":        MONOTHEISM,
        "eschatology":       ESCHATOLOGY,
        "prophetic_speech":  PROPHETIC_SPEECH,
    },
    "taoist_czech": {
        "taoist":             TAOIST_ELEMENTS,
        "mystical_union":     MYSTICAL_UNION,
        "esoteric_knowledge": ESOTERIC_KNOWLEDGE,
    },
    "taoist_english": {
        "taoist":             TAOIST_ELEMENTS,
        "mystical_union":     MYSTICAL_UNION,
        "esoteric_knowledge": ESOTERIC_KNOWLEDGE,
    },
}


UNIVERSAL_RELIGIOUS_ELEMENTS: dict[str, frozenset] = {
    **THEMATIC_ELEMENTS,
    "buddhist_elements":  BUDDHIST_ELEMENTS,
    "hindu_elements":     HINDU_ELEMENTS,
    "islamic_elements":   ISLAMIC_ELEMENTS,
    "christian_elements": CHRISTIAN_ELEMENTS,
    "jewish_elements":    JEWISH_ELEMENTS,
    "zoroastrian":        ZOROASTRIAN_ELEMENTS,
    "taoist":             TAOIST_ELEMENTS,
    "gnostic":            GNOSTIC_ELEMENTS,
    "theosophical":       THEOSOPHICAL_ELEMENTS,
    "hermetic":           HERMETIC_ELEMENTS,
    "sufi":               SUFI_ELEMENTS,
    "kabbalistic":        KABBALISTIC_ELEMENTS,
    "shamanic":           SHAMANIC_ELEMENTS,
    "tantric":            TANTRIC_ELEMENTS,
    "jungian":            JUNGIAN_ELEMENTS,
    "new_age":            NEW_AGE_ELEMENTS,
}


# ==========================================================
# 6. IDF weights
# ==========================================================

def _compute_element_idf() -> dict:
    n = len(TRADITIONS)
    df: dict = {}
    for active in TRADITIONS.values():
        for el in active:
            df[el] = df.get(el, 0) + 1
    return {el: math.log(n / count) for el, count in df.items()}


_ELEMENT_IDF: dict = _compute_element_idf()

_TRADITION_UNION: dict[str, frozenset] = {
    name: frozenset().union(*elements.values())
    for name, elements in TRADITIONS.items()
}


def _family_of(tradition_name: str) -> str:
    for sfx in (
        "_czech", "_english", "_arabic", "_hebrew", "_pali", "_sanskrit",
    ):
        if tradition_name.endswith(sfx):
            return tradition_name[: -len(sfx)]
    return tradition_name


_TRADITION_DIAGNOSTIC_UNION: dict[str, frozenset] = {}
for _tname in TRADITIONS:
    _fam = _family_of(_tname)
    _diag = TRADITION_DIAGNOSTIC.get(_fam, frozenset())
    _own = TRADITIONS[_tname].get(f"{_fam}_elements", frozenset())
    _TRADITION_DIAGNOSTIC_UNION[_tname] = frozenset(_diag | _own)


def _compute_lemma_idf(unions: dict[str, frozenset]) -> dict:
    n = len(unions)
    df: dict = {}
    for lexicon in unions.values():
        for lemma in lexicon:
            df[lemma] = df.get(lemma, 0) + 1
    return {lemma: math.log(n / count) for lemma, count in df.items()}


_LEMMA_IDF: dict = _compute_lemma_idf(_TRADITION_UNION)
_DIAG_LEMMA_IDF: dict = _compute_lemma_idf(_TRADITION_DIAGNOSTIC_UNION)
_FAMILY_LEMMA_IDF: dict = _compute_lemma_idf(TRADITION_DIAGNOSTIC)


# ==========================================================
# 7. Detection + scoring
# ==========================================================

def detect_tradition(element_scores: dict) -> str:
    """
    Most likely tradition from thematic/element scores (TF-IDF).
    Shared thematic fields have low IDF so they do not dominate.
    """
    best_tradition = "unknown"
    best_score = -1.0
    for tradition, active in TRADITIONS.items():
        score = sum(
            element_scores.get(element, 0) * _ELEMENT_IDF.get(element, 1.0)
            for element in active
        )
        if score > best_score:
            best_score = score
            best_tradition = tradition
    return best_tradition


def detect_tradition_from_lemmas(lemma_counts: dict) -> str:
    """
    Detect tradition family from diagnostic lemmas only.

    Polyvalent biblical words (světlo, duše, duch, tajemství…) are excluded
    from diagnostic lexicons, so a Bible-like bag of words does not get
    labelled Gnostic / Platonic / Theosophical / Shamanic.
    Returns 'unknown' when there is no distinctive evidence.
    """
    best_tradition = "unknown"
    best_score = 0.0
    for family, lexicon in TRADITION_DIAGNOSTIC.items():
        score = sum(
            lemma_counts.get(lemma, 0) * _FAMILY_LEMMA_IDF.get(lemma, 1.0)
            for lemma in lexicon
        )
        if score > best_score:
            best_score = score
            best_tradition = family
    return best_tradition


def _intersect(lemmas: set[str], lexicon: frozenset) -> set[str]:
    return {w for w in lemmas if w in lexicon}


def analyze_lemma_set(lemmas: Iterable[str]) -> dict:
    """
    Score a bag of lemmas on all four layers.

    Returns dict with keys:
      thematic, tradition_diagnostic, philosophical, shared_motifs,
      detected_tradition
    Each of the first four maps name → set of matching lemmas (non-empty only).
    """
    lemma_set = {str(w).lower() for w in lemmas if str(w).strip()}
    thematic = {
        k: hits for k, v in THEMATIC_ELEMENTS.items()
        if (hits := _intersect(lemma_set, v))
    }
    diagnostic = {
        k: hits for k, v in TRADITION_DIAGNOSTIC.items()
        if (hits := _intersect(lemma_set, v))
    }
    philosophical = {
        k: hits for k, v in PHILOSOPHICAL_INFLUENCES.items()
        if (hits := _intersect(lemma_set, v))
    }
    shared = {
        k: hits for k, meta in SHARED_MOTIFS.items()
        if (hits := _intersect(lemma_set, meta["lemmas"]))
    }
    counts = Counter(lemma_set)
    return {
        "thematic": thematic,
        "tradition_diagnostic": diagnostic,
        "philosophical": philosophical,
        "shared_motifs": shared,
        "detected_tradition": detect_tradition_from_lemmas(counts),
    }


def get_active_elements(tradition: str) -> dict:
    if tradition not in TRADITIONS:
        raise KeyError(
            f"Unknown tradition: '{tradition}'. "
            f"Available: {sorted(TRADITIONS)}"
        )
    return dict(TRADITIONS[tradition])


def get_thematic_elements() -> dict[str, frozenset]:
    """Universal thematic fields (no tradition-diagnostic bleed)."""
    return dict(THEMATIC_ELEMENTS)


# ==========================================================
# 8. OVERLAP DIAGNOSTICS
# ==========================================================

def get_lexicon_overlaps(tradition_name: str) -> dict[str, list[str]]:
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
    overlaps = get_lexicon_overlaps(tradition_name)
    matrix = get_element_overlap_matrix(tradition_name)
    if not overlaps:
        return {"total_overlapping_lemmas": 0}
    worst_lemma = max(overlaps, key=lambda l: len(overlaps[l]))
    worst_pair = next(iter(matrix)) if matrix else ("—", "—")
    return {
        "tradition":                tradition_name,
        "total_overlapping_lemmas": len(overlaps),
        "max_element_count":        max(len(v) for v in overlaps.values()),
        "most_shared_lemma":        f"{worst_lemma} → {overlaps[worst_lemma]}",
        "worst_element_pair":       (
            f"{worst_pair[0]} ∩ {worst_pair[1]} = {matrix.get(worst_pair, 0)} lemmas"
        ),
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
    print(f"Thematic elements:        {len(THEMATIC_ELEMENTS)}")
    print(f"Diagnostic families:      {len(TRADITION_DIAGNOSTIC)}")
    print(f"Shared motifs:            {len(SHARED_MOTIFS)}")

    bible_like = {
        "bůh", "hospodin", "světlo", "tma", "duše", "tělo",
        "slovo", "tajemství", "duch", "láska", "zákon",
    }
    scored = analyze_lemma_set(bible_like)
    print(f"\nBible-like diagnostic: {sorted(scored['tradition_diagnostic'])}")
    print(f"Bible-like philosophy: {sorted(scored['philosophical'])}")
    print(f"Bible-like shared:     {sorted(scored['shared_motifs'])}")
    print(f"Bible-like detected:   {scored['detected_tradition']}")

    theo = analyze_lemma_set({"akáša", "blavatská", "teosofie", "duše", "světlo"})
    print(f"\nTheosophy detected:    {theo['detected_tradition']}")
    print(f"Theosophy diagnostic:  {sorted(theo['tradition_diagnostic'])}")

    budd = analyze_lemma_set({"buddha", "nirvána", "sangha", "dukkha"})
    print(f"Buddhist detected:     {budd['detected_tradition']}")

    scores = {
        "monotheism":        10,
        "covenant_law":       8,
        "prophetic_speech":   6,
        "ritual_sacrifice":   4,
        "genealogy_lineage":  3,
        "christian_elements": 12,
    }
    detected = detect_tradition(scores)
    print(f"\ndetect_tradition(test scores) → '{detected}'")

    active = get_active_elements("christian_czech")
    print(f"get_active_elements('christian_czech') → {sorted(active.keys())}")

    print(f"\n{'LEXICON OVERLAP DIAGNOSTICS — christian_czech':─<60}")
    summary = overlap_summary("christian_czech")
    for k, v in summary.items():
        print(f"  {k:<30} {v}")
