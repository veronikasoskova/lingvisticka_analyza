"""
lexicons_common.py — single source for stop-lemma sets and token cleaning.

Replaces:
  q_text_patterns.BASE_CZECH_STOPWORDS + THEOLOGICAL_STOPWORDS  (surface forms)
  g_skinner_rules._REPEATED_STOP_LEMMAS                          (lemma forms)

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
from typing import Iterable, Optional


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
    "tak", "také", "též", "takto",
    "již", "už", "pak", "ještě", "jen",
    "čili", "totiž",
    "když", "kdyžto", "poněvadž", "poněvadz",
    "jestliže", "jestli",
    "ač", "ačkoli", "ačkoliv", "až", "než", "nežli",
    "an", "ano",
    # Interrogative / relative pronouns and adverbs
    "co", "což", "čím", "či", "kdo", "kdož",
    "který", "kterýž", "kteříž", "kteréž", "kteráž",
    "kteréhož", "kterémuž", "kterýmž", "kterýmiž",
    "kteréžto", "kterýžto", "kteřížto",
    "jenž", "jež", "ježto", "anžto",
    # Prepositions (lemma + vocalised / BKR variants)
    "v", "ve", "na", "do", "z", "ze", "s", "se", "k", "ke", "ku",
    "pro", "při", "po", "za", "před", "o", "od", "u", "nad", "pod",
    "mezi", "bez", "skrze", "proti",
    "podlé", "podle", "vedlé", "vedle", "dle",
    "přes", "mimo", "kromě", "krom", "místo",
    # Pronouns — lemmas + frequent BKR inflected / archaic forms
    "já", "ty", "my", "vy", "on", "ona", "ono", "oni", "ony",
    "ten", "ta", "to", "ti", "tento", "tato", "toto", "tito",
    "tom", "tomu", "toho", "těch", "těm", "těmi", "té", "tu", "tím",
    "svůj", "svá", "své", "svou", "svého", "svému", "svých", "svým", "svými",
    "můj", "má", "mé", "moje", "mou", "mého", "mému",
    "tvůj", "tvá", "tvé", "tvou",
    "náš", "naše", "našeho", "našemu", "našich", "našim", "našimi",
    "váš", "vaše", "vašeho",
    "jeho", "její", "jejich", "jich", "jim", "jimi",
    "jemu", "jej", "ji", "jí", "ho", "mu",
    "vám", "vás", "vámi", "nás", "nám", "námi",
    "mě", "mne", "mi", "mně", "tebe", "tobě",
    "sebe", "sobě",
    "sám", "sama", "samo", "sami",
    "nich", "nim", "nimi", "něj", "něho", "němu", "ní",
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

# ── Combined sets (public API) ────────────────────────────────────────────────

# Unified stop-lemma set — use for PMI, TF-IDF, repeated-content detection
STOP_LEMMAS: frozenset = _CS_FUNCTION_LEMMAS | _EN_FUNCTION_LEMMAS

# Style analysis: also suppress high-frequency theological terms
STYLE_STOP_LEMMAS: frozenset = STOP_LEMMAS | THEOLOGICAL_STOP_LEMMAS

# Semantic analysis: keep theological terms (they are semantically significant)
SEMANTIC_STOP_LEMMAS: frozenset = STOP_LEMMAS
