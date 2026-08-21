"""
lexicons_common.py — stop-lemma sets, token cleaning, and semantic opposition poles.

Replaces:
  q_text_patterns.BASE_CZECH_STOPWORDS + THEOLOGICAL_STOPWORDS  (surface forms)
  g_skinner_rules._REPEATED_STOP_LEMMAS                          (lemma forms)
  f_semantics.OPPOSITIONS / w_opposition_networks.OPPOSITION_PAIRS (duplicated)

Tokens here include:
  * lemma forms as produced by Stanza cs-pdt / sk-snk / en-ewt
  * BKR / demo surface forms (kterýž, protož, jsem, jich, vám, …)

Demo DB rows and older lemma strings are often unlemmatised Bible Czech
with commas/colons still glued on ("jejich,", "zástupů:").  Semantic
centrality and PMI must strip that punctuation and drop function words
before any scoring — see clean_surface_token() / content_tokens().
"""

from __future__ import annotations

import re
import unicodedata
from typing import Iterable, NamedTuple, Optional


# Hyphenated BKR enclitics glued onto the previous word ("díme-li", "však-ž").
# Allow trailing punctuation so "díme-li," still matches.
_BKR_ENCLITIC_TAIL = re.compile(r"-(li|ž|ť)(?=\W*$)", re.IGNORECASE)


def clean_surface_token(token: str) -> str:
    """
    Prepare one raw token for lexical analytics.

    1. lowercase + strip
    2. drop a trailing BKR enclitic (-li / -ž / -ť)
    3. keep Unicode letters only (commas, colons, quotes, brackets go away)

    "zástupů:" → "zástupů"
    "jejich,"  → "jejich"
    "díme-li," → "díme"
    """
    if not token:
        return ""
    t = str(token).strip().lower()
    t = _BKR_ENCLITIC_TAIL.sub("", t)
    return "".join(ch for ch in t if unicodedata.category(ch).startswith("L"))


def content_tokens(
    text: str,
    *,
    stop: Optional[Iterable[str]] = None,
    min_len: int = 3,
) -> list[str]:
    """
    Tokenise a lemma string or a raw sentence for PMI / centrality / TF-IDF.

    Punctuation is stripped from every token *before* stop-word matching, so
    "jejich," and "vám:" are recognised as the function words jejich / vám.
    """
    if stop is None:
        stop_set: frozenset[str] = STOP_LEMMAS
    else:
        stop_set = stop if isinstance(stop, frozenset) else frozenset(stop)

    out: list[str] = []
    for raw in str(text or "").split():
        tok = clean_surface_token(raw)
        if len(tok) >= min_len and tok not in stop_set:
            out.append(tok)
    return out


# ── Czech function-word lemmas + BKR surface forms ───────────────────────────
_CS_FUNCTION_LEMMAS: frozenset = frozenset({
    # Coordinating conjunctions
    "a", "ale", "ani", "aneb", "anebo", "nebo", "neb", "neboť",
    "nýbrž", "však", "i",
    # Subordinating conjunctions / particles
    "aby", "abych", "abys", "abychom", "abyste",
    "jak", "jako", "jakož", "jakožto", "jakž",
    "že", "byť", "přitom",
    "proto", "protož", "protože", "tedy",
    "tak", "také", "též", "takto", "taktéž",
    "již", "už", "jižť", "pak", "ještě", "jen",
    "čili", "totiž",
    "když", "kdyžto", "poněvadž", "poněvadz",
    "jestliže", "jestli", "pakli",
    "ač", "ačkoli", "ačkoliv", "až", "než", "nežli",
    "an", "ano", "tehdy",
    # Interrogative / relative pronouns and adverbs
    "co", "což", "čím", "či", "kdo", "kdož",
    "který", "kterýž", "kteříž", "kteréž", "kteráž",
    "kteréhož", "kterémuž", "kterýmž", "kterýmiž",
    "kterouž", "kterýchž",
    "kteréžto", "kterýžto", "kteřížto",
    "jenž", "jež", "ješto", "ježto", "anžto",
    # Prepositions (lemma + vocalised / BKR variants)
    "v", "ve", "na", "do", "z", "ze", "s", "se", "k", "ke", "ku",
    "pro", "při", "po", "za", "před", "o", "od", "u", "nad", "pod",
    "mezi", "bez", "skrze", "proti",
    "podlé", "podle", "vedlé", "vedle", "dle",
    "přes", "mimo", "kromě", "krom", "místo",
    # Pronouns — lemmas + frequent BKR inflected / archaic forms
    "já", "ty", "my", "vy", "on", "ona", "ono", "oni", "ony",
    "ten", "ta", "to", "ti", "tento", "tato", "toto", "tito", "onen",
    "tom", "tomu", "toho", "těch", "těm", "těmi", "té", "tu", "tím",
    "této", "tomto", "tohoto", "těchto",
    "svůj", "svá", "své", "svou", "svého", "svému", "svých", "svým", "svými",
    "můj", "má", "mé", "moje", "mou", "mého", "mému",
    "tvůj", "tvá", "tvé", "tvou",
    "náš", "naše", "našeho", "našemu", "našich", "našim", "našimi",
    "našem", "naši", "naší",
    "váš", "vaše", "vašeho",
    "jeho", "její", "jejich", "jich", "jim", "jimi",
    "jemu", "jemuž", "jej", "ji", "jí", "ho", "mu",
    "vám", "vás", "vámi", "nás", "nám", "námi",
    "mě", "mne", "mi", "mně", "tebe", "tobě", "tě", "si",
    "sebe", "sobě",
    "sám", "sama", "samo", "sami",
    "nich", "nim", "nimi", "něj", "něho", "němu", "něm", "ní",
    "všickni", "všichni", "všecko", "všechen", "vše",
    # Copula + auxiliaries — lemma AND BKR/demo surface forms
    # (Stanza maps jsem/jest/byl → být; demo lemmas keep the surface form)
    "být", "býti",
    "jsem", "jsi", "jest", "je", "jsou", "jsme", "jste",
    "není", "nejsem", "nejsou",
    "bude", "budou", "budu", "budeš", "budeme", "budete",
    "byl", "byla", "bylo", "byli", "byly",
    "by", "bych", "bys", "bychom", "byste",
    # Frequent adverbs / discourse particles
    "velmi", "velice", "vždy", "vždycky", "vždyť",
    "nyní", "opět", "zajisté", "jistě", "ovšem",
    "hle", "aj", "ať", "nechť", "koli", "koliv",
    "toť", "totoť",
    # Slovak function-word mirrors (upload pipeline lang=sk)
    "som", "sme", "ste", "sú", "keď", "preto", "ktorý", "ktorí", "ktoré",
    "ich", "kedze", "keďže",
    # ASCII-folded typing of the same BKR function words
    "protoz", "kdyz", "kteriz", "kterizto", "vam",
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
