"""
lexicons_common.py — shared stop-lemma sets and semantic opposition poles.

Replaces:
  q_text_patterns.BASE_CZECH_STOPWORDS + THEOLOGICAL_STOPWORDS  (surface forms)
  g_skinner_rules._REPEATED_STOP_LEMMAS                          (lemma forms)
  f_semantics.OPPOSITIONS / w_opposition_networks.OPPOSITION_PAIRS (duplicated)

All tokens here are LEMMA forms as produced by Stanza cs-pdt / sk-snk / en-ewt,
plus frequent BKR surface leftovers that demo rows and cs-pdt keep un-lemmatised.

Surface-form → lemma mapping (items removed or consolidated):
  jest/jsou/jsi/jsem/jsme/jste/není/bude/budou/byl/byla/bylo/byli/by/bych/bys → být
  abys/abych → aby
  što/což → co
  kterýž/kteráž/kteréž/kteříž → který
  jakž/jakož → jak / jakož (kept: jakož is a distinct conjunction)
  neb → nebo
  protož → proto  (archaic; Stanza lemmatizuje na proto)
  ze → z,  ve → v,  ke → k  (prepositional variants, lemma = base form)
  mne/mně/mi/mého/mou → já   (genitive/dative/accusative of já)
  tobě → ty
  vás/vámi/vám → vy
  nás → my
  toho/tom/toto/těch/těm → ten
  svého/svou/svých/svým → svůj
  hospodina/hospodinu/hospodinem → hospodin  (inflected forms of proper noun)
  boha/bohu/bohem → bůh;  boží is a separate adjective lemma
"""

from __future__ import annotations

from typing import Iterable, NamedTuple


# ── Czech function-word lemmas ────────────────────────────────────────────────
_CS_FUNCTION_LEMMAS: frozenset = frozenset({
    # Coordinating conjunctions
    "a", "ale", "ani", "aneb", "nebo", "nýbrž", "však",
    # Subordinating conjunctions / particles
    "aby", "jak", "jako", "jakož", "že", "byť", "přitom",
    "proto", "tedy", "tak", "také", "již", "pak", "ještě", "jen",
    "čili", "totiž", "neb", "neboť", "poněvadž", "zajisté",
    "tehdy", "když", "pakli", "jestliže", "až", "protož",
    # Interrogative/relative pronouns and adverbs
    "co", "čím", "či", "kdo", "který", "jenž",
    # BKR archaic relatives / particles (surface forms kept by demo rows)
    "kterýž", "kteráž", "kteréž", "kteříž", "kteréžto", "kterýžto",
    "kterouž", "kteréhož", "kterémuž", "kterýchž", "kterýmž",
    "jež", "ješto", "ježto", "an", "aj", "též", "taktéž",
    # Prepositions (lemma = base prepositional form)
    "v", "na", "do", "z", "s", "k", "pro", "při",
    "po", "za", "před", "o", "od", "u", "nad", "pod", "mezi", "bez",
    "proti", "skrze", "dle",
    # Pronouns (lemma forms)
    "já", "ty", "my", "vy", "on", "ona", "ono", "oni",
    "ten", "tento", "onen", "svůj", "můj", "tvůj", "náš", "váš",
    "jeho", "její", "jejich",
    # BKR inflected / clitic pronoun leftovers
    "jich", "jim", "jej", "něho", "němu", "něm", "jemu", "jemuž",
    "vám", "nám", "vámi", "námi", "vás", "nás",
    "mne", "mně", "mi", "tě", "ti", "tebe", "tobě",
    "sebe", "sobě", "si",
    # Copula + auxiliaries — lemma AND BKR surface leftovers
    "být",
    "jest", "jsou", "jsem", "jsi", "jsme", "jste", "není",
    "bude", "budou", "byl", "byla", "bylo", "byli", "byly",
    "by", "bych", "bys",
    # Frequent adverbs / discourse particles
    "velmi", "také", "ještě", "jen", "již", "pak", "tedy",
    "vždycky", "vždy", "nyní", "jižť", "takto",
    "všickni", "všichni", "všecko", "všechen", "vše",
    "této", "tomto", "tohoto", "tomu", "těchto",
    # BKR preposition / possessive leftovers
    "podlé", "podle",
    "svého", "svou", "své", "svých", "svým", "svými",
    "našeho", "našem", "naši", "naší", "naše",
})

# ── English function-word lemmas ─────────────────────────────────────────────
_EN_FUNCTION_LEMMAS: frozenset = frozenset({
    "the", "a", "an", "and", "or", "but", "in", "of", "to", "for",
    "on", "at", "by", "with", "from", "as", "this", "that",
    "he", "she", "it", "they", "we", "you", "i",
    "his", "her", "its", "their", "my", "our", "your",
    "which", "who", "what",
    "be", "have", "do", "will", "shall", "would", "may", "can", "could",
})

# ── Theological high-frequency lemmas (suppress in style/PMI analysis) ───────
THEOLOGICAL_STOP_LEMMAS: frozenset = frozenset({
    "hospodin", "bůh", "boží",
})

# Formulaic / speech lemmas that pollute concept-cluster neighbour lists.
# Not global stopwords — they stay in style/TF-IDF — but they are not concepts.
CLUSTER_NOISE_LEMMAS: frozenset = frozenset({
    "říci", "říct", "pravit", "praví", "řekl", "řekla", "řekli",
    "dí", "díti", "mluvit", "odpovědět", "odpověděti", "promluvit",
    "řka", "řkouc",
    "stát", "státi", "stalo", "stálo", "stane",
    "načteno", "psáti", "psát", "napsat",
})

# ── Combined sets (public API) ────────────────────────────────────────────────

# Unified stop-lemma set — use for PMI, TF-IDF, repeated-content detection
STOP_LEMMAS: frozenset = _CS_FUNCTION_LEMMAS | _EN_FUNCTION_LEMMAS

# Style analysis: also suppress high-frequency theological terms
STYLE_STOP_LEMMAS: frozenset = STOP_LEMMAS | THEOLOGICAL_STOP_LEMMAS

# Semantic analysis: keep theological terms (they are semantically significant)
SEMANTIC_STOP_LEMMAS: frozenset = STOP_LEMMAS


# ==========================================================
# Biblical semantic opposition poles
# ==========================================================
# Each group is one rhetorical opposition.  Synonyms and BKR variants live
# inside the pole sets so "světlo/temnota" and "světlo/tma" count as the same
# pair.  The canonical key is always "{positive} | {negative}".

class OppositionGroup(NamedTuple):
    key: str
    positive: frozenset[str]
    negative: frozenset[str]


def _g(pos: str, neg: str, extra_pos: tuple[str, ...] = (), extra_neg: tuple[str, ...] = ()) -> OppositionGroup:
    return OppositionGroup(
        key=f"{pos} | {neg}",
        positive=frozenset((pos, *extra_pos)),
        negative=frozenset((neg, *extra_neg)),
    )


OPPOSITION_GROUPS: tuple[OppositionGroup, ...] = (
    # Cosmic merisms
    _g("světlo", "tma", ("světlý", "osvítit", "osvětlit"), ("temnota", "temnost", "temný")),
    _g("nebe", "země", ("nebesa", "nebeský"), ()),
    _g("den", "noc", (), ()),
    _g("pravice", "levice", ("pravý",), ("levý",)),
    # Moral polarity
    _g("dobrý", "zlý", ("dobro",), ("zlo", "špatný")),
    _g("spravedlivý", "bezbožný", (), ("hříšník", "nešlechetný")),
    _g("spravedlnost", "nepravost", (), ("hřích", "vina")),
    _g("pravda", "lež", (), ("klam", "faleš")),
    _g("čistý", "nečistý", (), ()),
    _g("láska", "nenávist", ("milovat", "milující"), ("nenávidět",)),
    _g("pokora", "pýcha", ("pokorný",), ("pyšný", "domýšlivý")),
    _g("věrný", "nevěrný", ("věrnost",), ("nevěra", "nevěrnost")),
    # Blessing / curse
    _g("požehnání", "zlořečení", ("požehnat", "požehnaný"), ("proklít", "proklat", "zlořečit", "kletba")),
    # Life / death / salvation
    _g("život", "smrt", ("živý", "žít", "žíti"), ("mrtvý", "zemřít", "umřít", "umříti")),
    _g("spása", "zahynutí", ("spasení", "spasit", "zachránit"), ("zahynout", "zahubit", "zatracení")),
    _g("věčný", "časný", ("věčnost",), ()),
    # Anthropology
    _g("duch", "tělo", ("duchovní",), ("tělesný",)),
    _g("duše", "tělo", (), ()),
    # Covenant / Pauline
    _g("víra", "skutek", (), ("skutky",)),
    _g("víra", "nevěra", ("věřící",), ("nevěřící", "pochybnost")),
    _g("milost", "zákon", (), ()),
    _g("milosrdenství", "zákon", (), ()),
    _g("milosrdenství", "soud", (), ("hněv",)),
    # Divine vs idolatry
    _g("bůh", "modla", (), ("modlář", "modlářství")),
    _g("hospodin", "baal", (), ()),
    # Wisdom
    _g("moudrost", "bláznovství", ("moudrý",), ("blázen", "bláznivý")),
    # Social
    _g("chudý", "bohatý", ("chudoba",), ("bohatství",)),
    _g("svoboda", "otroctví", ("svobodný",), ("otrok",)),
    _g("izrael", "pohan", (), ("pohané",)),
    # Peace / war
    _g("pokoj", "boj", (), ("válka", "meč")),
    # Sacred / apocalyptic
    _g("svatý", "obecný", (), ("profánní",)),
    _g("beránek", "šelma", (), ()),
    _g("kristus", "antikrist", (), ()),
    _g("jeruzalém", "babylon", ("sion",), ("bábel",)),
    # Other biblical rhetoric
    _g("první", "poslední", ("prvý", "prvorozený"), ()),
    _g("sláva", "hanba", ("čest",), ("potupa", "pohana")),
    _g("přítel", "nepřítel", (), ()),
    _g("poslušnost", "vzpurnost", ("poslušný",), ("vzpurný", "neposlušný")),
    _g("oběť", "milosrdenství", (), ()),
)


# Canonical pair list — positive pole first.  Kept for callers that iterate
# exact (word1, word2) tuples; prefer matching_opposition_keys() for recall.
OPPOSITION_PAIRS: frozenset[tuple[str, str]] = frozenset(
    (g.key.split(" | ")[0], g.key.split(" | ")[1]) for g in OPPOSITION_GROUPS
)

# Backward-compatible dict used by f_semantics.opposition_present (one direction).
OPPOSITIONS: dict[str, str] = {
    g.key.split(" | ")[0]: g.key.split(" | ")[1] for g in OPPOSITION_GROUPS
}

POSITIVE_WORDS: frozenset[str] = frozenset(
    w for g in OPPOSITION_GROUPS for w in g.positive
)
NEGATIVE_WORDS: frozenset[str] = frozenset(
    w for g in OPPOSITION_GROUPS for w in g.negative
)


def matching_opposition_groups(tokens: Iterable[str]) -> list[OppositionGroup]:
    """Return opposition groups whose both poles occur in `tokens`."""
    lowered = {str(t).lower() for t in tokens if t}
    return [
        g for g in OPPOSITION_GROUPS
        if (lowered & g.positive) and (lowered & g.negative)
    ]


def matching_opposition_keys(tokens: Iterable[str]) -> list[str]:
    return [g.key for g in matching_opposition_groups(tokens)]


def opposition_present_in(tokens: Iterable[str]) -> bool:
    return bool(matching_opposition_groups(tokens))


def dominant_opposition_pole(anchor_tokens: Iterable[str], group: OppositionGroup) -> str:
    """
    Which pole of `group` is present in the anchor sentence.

    Returns the canonical positive label, the canonical negative label, or "both".
    """
    lowered = {str(t).lower() for t in anchor_tokens if t}
    has_pos = bool(lowered & group.positive)
    has_neg = bool(lowered & group.negative)
    pos_label, neg_label = group.key.split(" | ")
    if has_pos and not has_neg:
        return pos_label
    if has_neg and not has_pos:
        return neg_label
    return "both"
