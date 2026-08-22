import os
import re
import unicodedata

from dataclasses import dataclass
from typing import List, Dict

from c_input import TextInput


# ==========================================================
# MULTILANG NLP PIPELINE CACHE
# ==========================================================

_NLP_CACHE = {}

_PIPELINE_CONFIGS = {
    "cs": dict(
        lang="cs",
        package="pdt",
        processors="tokenize,mwt,pos,lemma,depparse",
    ),
    "sk": dict(
        lang="sk",
        package="snk",
        processors="tokenize,pos,lemma,depparse",
    ),
    "en": dict(
        lang="en",
        package="ewt",
        processors="tokenize,pos,lemma,depparse",
    ),
}


def get_nlp(lang: str = "cs"):
    import stanza

    if lang not in _NLP_CACHE:
        cfg = _PIPELINE_CONFIGS.get(lang)
        if cfg is None:
            raise ValueError(
                f"Unsupported language '{lang}'. "
                f"Available: {sorted(_PIPELINE_CONFIGS)}"
            )
        _NLP_CACHE[lang] = stanza.Pipeline(
            **cfg,
            use_gpu=False,
            download_method=None,
        )

    return _NLP_CACHE[lang]


PIPELINE_LANG = os.getenv("PIPELINE_LANG", "cs")


# ==========================================================
# BKR CZECH NORMALIZATION
# ==========================================================

# Hyphenated enclitic particles in Králická Bible (BKR):
#   -li  conditional / interrogative  ("přijdeš-li", "bude-li", "jest-li")
#   -ž   emphatic particle            ("však-ž", "vše-ž")
#   -ť   emphatic particle            ("vsak-ť", "on-ť")
# Stanza cs-pdt is trained on modern newspaper Czech (PDT) and will
# typically misanalyse these hyphenated forms. Splitting them into two
# space-separated tokens before NLP lets each part be handled correctly.
#
# Note: conjunctions already written as one word ("jestliže", "nicméně")
# never contain a hyphen, so the regex does NOT affect them.
_BKR_ENCLITIC_RE = re.compile(
    r"(\w)-(li|ž|ť)\b",
    re.IGNORECASE | re.UNICODE,
)

# Attached emphatic -ť without hyphen ("nyníť", "neníť", "umíť").
# Do NOT split lexicalised conjunctions (neboť, vždyť, ať, byť).
_BKR_KEEP_T = frozenset({"neboť", "vždyť", "ať", "byť"})
_BKR_ATTACHED_T_RE = re.compile(
    r"\b\w{3,}ť\b",
    re.IGNORECASE | re.UNICODE,
)


def _split_attached_t(text: str) -> str:
    def repl(match: re.Match) -> str:
        token = match.group(0)
        if token.lower() in _BKR_KEEP_T:
            return token
        return token[:-1] + " ť"
    return _BKR_ATTACHED_T_RE.sub(repl, text)


def _normalize_universal(text: str) -> str:
    """
    Language-agnostic normalization — runs for EVERY pipeline language.

    Steps
    -----
    1. Unicode NFC
    2. Remove/replace invisible and non-standard whitespace:
         U+00AD soft hyphen, U+00A0 NBSP, U+202F narrow NBSP,
         U+200B zero-width space, U+FEFF BOM, U+2009 thin space
    3. Typographic punctuation -> ASCII equivalents:
         em dash -> " - ", en dash -> "-"
         left/right double quotes -> ", left/right single quotes -> '
    4. Collapse redundant whitespace
    """
    text = unicodedata.normalize("NFC", text)

    # Invisible / non-standard characters
    text = text.replace("\xad", "")    # soft hyphen
    text = text.replace("\xa0", " ")   # non-breaking space
    text = text.replace("\u202f", " ") # narrow non-breaking space
    text = text.replace("\u200b", "")  # zero-width space
    text = text.replace("\ufeff", "")  # BOM
    text = text.replace("\u2009", " ") # thin space

    # Typographic punctuation
    text = text.replace("\u2014", " - ")  # em dash
    text = text.replace("\u2013", "-")    # en dash
    text = text.replace("\u201e", '"')    # lower-9 double quote
    text = text.replace("\u201c", '"')    # left double quotation mark
    text = text.replace("\u201d", '"')    # right double quotation mark
    text = text.replace("\u2018", "'")    # left single quotation mark
    text = text.replace("\u2019", "'")    # right single quotation mark

    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def normalize_bkr(text: str) -> str:
    """
    Normalize BKR (Kral\u00edck\u00e1 Bible) Czech text before Stanza processing.

    Steps
    -----
    1-4. Universal normalization via _normalize_universal().
    5.   Czech BKR hyphenated enclitics: "přijdeš-li" -> "přijdeš li".
    6.   Attached emphatic -ť: "nyníť" -> "nyní ť" (not "neboť").
    """
    text = _normalize_universal(text)
    text = _BKR_ENCLITIC_RE.sub(r"\1 \2", text)
    text = _split_attached_t(text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


# ==========================================================
# FEATS STRING → DICT PARSING
# ==========================================================

def parse_feats(feats_str: str) -> Dict[str, str]:
    """
    Parse a Stanza Universal Dependencies feats string into a dict.

    Examples
    --------
    "Animacy=Anim|Case=Nom|Gender=Masc|Number=Sing"
    → {"Animacy": "Anim", "Case": "Nom", "Gender": "Masc", "Number": "Sing"}

    "" or None → {}
    """
    if not feats_str:
        return {}
    result: Dict[str, str] = {}
    for pair in feats_str.split("|"):
        if "=" in pair:
            k, v = pair.split("=", 1)
            result[k] = v
    return result


# ==========================================================
# TOKEN OBJECT
# ==========================================================

@dataclass
class TokenData:

    id: int
    text: str
    lemma: str
    pos: str
    feats: str              # raw UD feats string, e.g. "Case=Nom|Number=Sing"
    feats_dict: Dict[str, str]  # parsed version for attribute-level access
    dep: str
    head: str
    head_id: int


# ==========================================================
# SENTENCE OBJECT
# ==========================================================

@dataclass
class SentenceData:

    text: str
    tokens: List[TokenData]


# ==========================================================
# PREPROCESSING OUTPUT
# ==========================================================

@dataclass
class PreprocessedText:

    original: TextInput
    sentences: List[SentenceData]


# ==========================================================
# TOKEN PARSER
# ==========================================================

def parse_token(
    word,
    sentence_words
) -> TokenData:

    if word.head == 0:
        head_text = "ROOT"
    else:
        head_text = sentence_words[word.head - 1].text

    raw_feats = word.feats or ""

    return TokenData(
        id=word.id,
        text=word.text,
        lemma=word.lemma,
        pos=word.upos,
        feats=raw_feats,
        feats_dict=parse_feats(raw_feats),
        dep=word.deprel,
        head=head_text,
        head_id=word.head,
    )


# ==========================================================
# SENTENCE PARSER
# ==========================================================

def parse_sentence(sentence) -> SentenceData:
    return SentenceData(
        text=sentence.text,
        tokens=[parse_token(word, sentence.words) for word in sentence.words],
    )


# ==========================================================
# MAIN PREPROCESS FUNCTION
# ==========================================================

def preprocess_text(
    text_input: TextInput
) -> PreprocessedText:

    nlp = get_nlp(PIPELINE_LANG)

    raw_text = text_input.text
    if PIPELINE_LANG == "cs":
        raw_text = normalize_bkr(raw_text)
    else:
        raw_text = _normalize_universal(raw_text)

    doc = nlp(raw_text)
    return PreprocessedText(
        original=text_input,
        sentences=[parse_sentence(sent) for sent in doc.sentences],
    )


# ==========================================================
# TEST BLOCK
# ==========================================================

if __name__ == "__main__":

    from c_input import create_input_from_text

    # ── BKR enclitic normalisation smoke-test (no NLP required) ──────────────
    print("=== BKR normalise_bkr() ===")
    _cases = [
        ("Přijdeš-li k nám, budeme rádi.",
         "Přijdeš li k nám, budeme rádi."),
        ("jest-li kdo moudrý",
         "jest li kdo moudrý"),
        ("vsak-ť pravda vítězí",
         "vsak ť pravda vítězí"),
        ("jestliže přijde",          # conjunction — must NOT be split
         "jestliže přijde"),
        ("Nicméně půjdeme.",          # no enclitic — must NOT change
         "Nicméně půjdeme."),
        ("nyníť pravím vám",
         "nyní ť pravím vám"),
        ("neníť to tak",
         "není ť to tak"),
        ("neboť Bůh miloval svět",    # lexicalised — must NOT split
         "neboť Bůh miloval svět"),
        ("vždyť on jest",
         "vždyť on jest"),
    ]
    _ok = True
    for _inp, _expected in _cases:
        _got = normalize_bkr(_inp)
        _status = "OK" if _got == _expected else "FAIL"
        if _status == "FAIL":
            _ok = False
        print(f"  {_status}: {repr(_inp)} → {repr(_got)}")
    print()

    # ── feats parsing smoke-test ──────────────────────────────────────────────
    print("=== parse_feats() ===")
    _ftest = [
        ("Animacy=Anim|Case=Nom|Gender=Masc|Number=Sing",
         {"Animacy": "Anim", "Case": "Nom", "Gender": "Masc", "Number": "Sing"}),
        ("Mood=Imp|Number=Sing|Person=2|VerbForm=Fin",
         {"Mood": "Imp", "Number": "Sing", "Person": "2", "VerbForm": "Fin"}),
        ("",  {}),
        (None, {}),
    ]
    for _raw, _exp in _ftest:
        _got = parse_feats(_raw)
        _status = "OK" if _got == _exp else "FAIL"
        print(f"  {_status}: {repr(_raw)} → {_got}")
    print()

    # ── Stanza cs model ───────────────────────────────────────────────────────
    print("=== Stanza cs — BKR text ===")
    _cs_inp = create_input_from_text(
        text="Přijdeš-li k nám, budeme rádi. Dej mi vodu.",
        source="written_record",
        interaction="monologue",
        stimulus="unknown",
    )
    _cs_result = preprocess_text(_cs_inp)
    for _sent in _cs_result.sentences:
        print(f"\n  SENTENCE: {_sent.text}")
        for _tok in _sent.tokens:
            print(
                f"    {_tok.text:<14} lemma={_tok.lemma:<12} "
                f"pos={_tok.pos:<6} dep={_tok.dep:<10} "
                f"feats_dict={_tok.feats_dict}"
            )
    print()

    # ── Stanza sk model ───────────────────────────────────────────────────────
    print("=== Stanza sk model ===")
    try:
        _sk_orig = PIPELINE_LANG
        PIPELINE_LANG = "sk"
        _sk_inp = create_input_from_text(
            text="Daj mi vodu. Toto je pes.",
            source="written_record",
        )
        _sk_result = preprocess_text(_sk_inp)
        for _sent in _sk_result.sentences:
            print(f"\n  SENTENCE: {_sent.text}")
            for _tok in _sent.tokens:
                print(
                    f"    {_tok.text:<14} lemma={_tok.lemma:<12} "
                    f"pos={_tok.pos:<6} dep={_tok.dep:<10} "
                    f"feats={_tok.feats}"
                )
        PIPELINE_LANG = _sk_orig
    except Exception as _e:
        print(f"  sk model unavailable: {_e}")
    print()

    # ── Stanza en model ───────────────────────────────────────────────────────
    print("=== Stanza en model ===")
    try:
        _en_orig = PIPELINE_LANG
        PIPELINE_LANG = "en"
        _en_inp = create_input_from_text(
            text="Give me water. This is a dog.",
            source="written_record",
        )
        _en_result = preprocess_text(_en_inp)
        for _sent in _en_result.sentences:
            print(f"\n  SENTENCE: {_sent.text}")
            for _tok in _sent.tokens:
                print(
                    f"    {_tok.text:<14} lemma={_tok.lemma:<12} "
                    f"pos={_tok.pos:<6} dep={_tok.dep:<10} "
                    f"feats={_tok.feats}"
                )
        PIPELINE_LANG = _en_orig
    except Exception as _e:
        print(f"  en model unavailable: {_e}")
