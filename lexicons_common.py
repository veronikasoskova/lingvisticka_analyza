"""
lexicons_common.py — single source for stop-lemma sets.

Replaces:
  q_text_patterns.BASE_CZECH_STOPWORDS + THEOLOGICAL_STOPWORDS  (surface forms)
  g_skinner_rules._REPEATED_STOP_LEMMAS                          (lemma forms)

All tokens here are LEMMA forms as produced by Stanza cs-pdt / sk-snk / en-ewt.

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

# ── Czech function-word lemmas ────────────────────────────────────────────────
_CS_FUNCTION_LEMMAS: frozenset = frozenset({
    # Coordinating conjunctions
    "a", "ale", "ani", "aneb", "nebo", "nýbrž", "však",
    # Subordinating conjunctions / particles
    "aby", "jak", "jako", "jakož", "že", "byť", "přitom",
    "proto", "tedy", "tak", "také", "již", "pak", "ještě", "jen",
    "čili", "totiž",
    # Interrogative/relative pronouns and adverbs
    "co", "čím", "či", "kdo", "který", "jenž",
    # Prepositions (lemma = base prepositional form)
    "v", "na", "do", "z", "s", "k", "pro", "při",
    "po", "za", "před", "o", "od", "u", "nad", "pod", "mezi", "bez",
    # Pronouns (lemma forms)
    "já", "ty", "my", "vy", "on", "ona", "ono", "oni",
    "ten", "tento", "svůj", "můj", "tvůj", "náš", "váš",
    "jeho", "její", "jejich",
    # Copula + auxiliaries — THE KEY ADDITION missing from old surface-form list
    "být",
    # Frequent adverbs / discourse particles
    "velmi", "také", "ještě", "jen", "již", "pak", "tedy",
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
