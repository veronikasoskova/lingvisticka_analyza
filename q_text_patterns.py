"""
q_text_patterns.py — N-gram, co-occurrence, and TF-IDF text pattern analysis.

Three analytical layers:
  File level  — one document per biblical book (existing behaviour)
  Chapter level — one document per chapter (new; parsed from raw BKR files)
  Statistical   — PMI-weighted co-occurrence + LLR bigram significance (new)
"""

from __future__ import annotations

import ast
import csv
import math
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer

from a_paths import BIBLE_FOLDER
from b_analytics_utils import export_counter, export_rows
from n_db import load_rows as _db_load, TABLE_REFINED
from lexicons_common import STYLE_STOP_LEMMAS as STYLE_STOPWORDS, SEMANTIC_STOP_LEMMAS as SEMANTIC_STOPWORDS

OUTPUT_DIR = Path("output/text_patterns")


# DEAD: presunuté do lexicons_common.py (lemmatizované formy nahradzujú povrchové tvary)
# BASE_CZECH_STOPWORDS = { "jest", "jsou", "bude", ... }  — surface forms
# THEOLOGICAL_STOPWORDS = { "hospodina", "hospodinu", ... }  — surface forms
# STYLE_STOPWORDS    = BASE_CZECH_STOPWORDS | THEOLOGICAL_STOPWORDS
# SEMANTIC_STOPWORDS = BASE_CZECH_STOPWORDS


# ==========================================================
# RAW FILE HELPERS
# ==========================================================

def _parse_bkr_file(path: Path) -> dict[str, str]:
    """
    Parse a BKR bible file → {verse_key: verse_text}.

    BKR files are Python dicts serialised as text:
        {'Gn 1:1': 'Na počátku stvořil Bůh…', 'Gn 1:2': '…', …}

    Returns an empty dict on parse error.
    """
    raw = path.read_text(encoding="utf-8").strip()
    if raw.startswith("{") and raw.endswith("}"):
        try:
            return ast.literal_eval(raw)
        except (SyntaxError, ValueError):
            pass
    return {}


def _chapter_from_key(verse_key: str) -> str:
    """
    Extract chapter number from a verse key.

    "Gn 1:1" → "1"
    "1Kr 12:3" → "12"
    """
    try:
        return verse_key.split()[1].split(":")[0]
    except (IndexError, ValueError):
        return "0"


def _tokenize_raw(text: str) -> list[str]:
    cleaned = (
        text.lower()
        .replace(".", " ").replace(",", " ")
        .replace(";", " ").replace(":", " ")
        .replace("?", " ").replace("!", " ")
        .replace("\n", " ")
    )
    return [t for t in cleaned.split() if len(t) > 2]


# ==========================================================
# DOCUMENT LOADERS
# ==========================================================

def load_documents() -> list[dict]:
    """
    Load lemma tokens from the refined_descriptions DB grouped by file_name.
    Falls back to raw-text tokenisation when the DB is empty.
    Returns list of {file_name, tokens}.
    """
    db_rows = _db_load(TABLE_REFINED)

    if db_rows:
        by_file: dict[str, list] = {}
        for row in db_rows:
            fname  = row.get("file_name", "")
            lemmas = row.get("lemmas", "")
            if not fname:
                continue
            by_file.setdefault(fname, []).extend(
                t for t in lemmas.split() if len(t) > 2
            )
        return [
            {"file_name": fname, "tokens": tokens}
            for fname, tokens in sorted(by_file.items())
        ]

    # Fallback — raw text
    files = sorted(BIBLE_FOLDER.glob("*.txt"))[:10]
    if not files:
        raise FileNotFoundError(f"No txt files found: {BIBLE_FOLDER}")

    return [
        {"file_name": p.name, "tokens": _tokenize_raw(_parse_bkr_file(p)
                                                       and " ".join(_parse_bkr_file(p).values())
                                                       or p.read_text(encoding="utf-8"))}
        for p in files
    ]


def load_documents_with_chapters(max_files: int | None = None) -> list[dict]:
    """
    Load BKR raw files and split by chapter.

    Returns a list of dicts, one per (file × chapter):
        {file_name, chapter_id, chapter_doc_id, tokens}

    chapter_doc_id is a unique string "bible_BKR_Gn.txt__ch1" used as the
    TF-IDF document identifier.

    Falls back to file-level loading when BKR files are not parseable.

    Parameters
    ----------
    max_files : int, optional
        Limit the number of bible files to process (useful for testing).
    """
    files = sorted(BIBLE_FOLDER.glob("*.txt"))
    if max_files:
        files = files[:max_files]

    chapter_docs: list[dict] = []

    for path in files:
        verse_dict = _parse_bkr_file(path)
        if not verse_dict:
            continue

        # Group verses by chapter
        chapters: dict[str, list[str]] = defaultdict(list)
        for key, text in verse_dict.items():
            ch = _chapter_from_key(key)
            chapters[ch].extend(_tokenize_raw(text))

        for ch_id, tokens in sorted(chapters.items(), key=lambda x: int(x[0])):
            chapter_docs.append({
                "file_name":      path.name,
                "chapter_id":     ch_id,
                "chapter_doc_id": f"{path.stem}__ch{ch_id}",
                "tokens":         tokens,
            })

    return chapter_docs


# ==========================================================
# N-GRAM ANALYSIS
# ==========================================================

def compute_ngrams(documents: list[dict], prefix: str = "") -> None:
    """
    Export raw unigram / bigram / trigram counts.
    Use prefix="chapter_" for chapter-level calls to avoid overwriting file-level output.
    """
    uni = Counter()
    bi  = Counter()
    tri = Counter()

    for doc in documents:
        t = doc["tokens"]
        uni.update(t)
        bi.update(" ".join(p) for p in zip(t, t[1:]))
        tri.update(" ".join(p) for p in zip(t, t[1:], t[2:]))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    export_counter(uni, OUTPUT_DIR / f"{prefix}unigrams.csv",  "unigram")
    export_counter(bi,  OUTPUT_DIR / f"{prefix}bigrams.csv",   "bigram")
    export_counter(tri, OUTPUT_DIR / f"{prefix}trigrams.csv",  "trigram")


# ==========================================================
# STATISTICAL SIGNIFICANCE FOR BIGRAMS (bod 3)
# ==========================================================

def _llr(n11: int, n12: int, n21: int, n22: int) -> float:
    """
    Log-likelihood ratio (G²) for a 2×2 contingency table.

    Dunning (1993) — "Accurate Methods for the Statistics of Surprise and
    Coincidence".  Asymptotically chi-squared with 1 degree of freedom.

    Inputs
    ------
    n11 : count(w1 w2)          — both words co-occur
    n12 : count(w1, NOT w2)     — w1 without w2
    n21 : count(NOT w1, w2)     — w2 without w1
    n22 : count(NOT w1, NOT w2) — neither
    """
    n = n11 + n12 + n21 + n22
    if n == 0:
        return 0.0

    r1, r2 = n11 + n12, n21 + n22
    c1, c2 = n11 + n21, n12 + n22

    def _contrib(obs: int, exp: float) -> float:
        return obs * math.log(obs / exp) if obs > 0 and exp > 0 else 0.0

    e11 = r1 * c1 / n
    e12 = r1 * c2 / n
    e21 = r2 * c1 / n
    e22 = r2 * c2 / n

    return 2.0 * (_contrib(n11, e11) + _contrib(n12, e12) +
                  _contrib(n21, e21) + _contrib(n22, e22))


def _chi2_sf(x: float, df: int = 1) -> float:
    """
    Survival function (1 - CDF) of the chi-squared distribution.

    Uses scipy when available; falls back to a conservative approximation
    (safe_log bound: p ≈ exp(-x/2)) for df=1 when scipy is absent.
    """
    try:
        from scipy.stats import chi2 as _chi2
        return float(_chi2.sf(x, df))
    except ImportError:
        # Conservative approximation for df=1: p ≈ exp(−G²/2) (upper bound)
        return math.exp(-x / 2.0) if x >= 0 else 1.0


def compute_ngram_significance(
    documents: list[dict],
    min_count: int = 3,
    alpha: float = 0.001,
) -> None:
    """
    Compute statistically significant bigrams using the log-likelihood ratio test.

    Only bigrams with count ≥ min_count AND p_value ≤ alpha are exported.
    Output: significant_bigrams.csv with columns
        bigram, count, llr, p_value

    Rationale
    ---------
    Raw bigram counts favour frequent but uninformative collocations like
    "a byl" or "hospodin řekl".  The LLR test asks: does this bigram occur
    more often than expected under word independence?  A high LLR (low p-value)
    means the two words are genuinely attracted to each other beyond frequency.

    Reference: Dunning (1993), Computational Linguistics 19(1).
    """
    unigram: Counter = Counter()
    bigram:  Counter = Counter()
    total_tokens = 0

    for doc in documents:
        t = doc["tokens"]
        unigram.update(t)
        bigram.update(" ".join(p) for p in zip(t, t[1:]))
        total_tokens += len(t)

    total_bigrams = sum(bigram.values())

    rows = []
    for bg_str, n11 in bigram.items():
        if n11 < min_count:
            continue
        w1, w2 = bg_str.split(" ", 1)
        c_w1 = unigram[w1]
        c_w2 = unigram[w2]

        # 2×2 contingency table
        n12 = c_w1 - n11         # w1 not followed by w2
        n21 = c_w2 - n11         # w2 not preceded by w1
        n22 = total_bigrams - n11 - n12 - n21

        if n12 < 0 or n21 < 0 or n22 < 0:
            continue

        llr_val = _llr(n11, n12, n21, n22)
        p_val   = _chi2_sf(llr_val, df=1)

        if p_val <= alpha:
            rows.append({
                "bigram":  bg_str,
                "count":   n11,
                "llr":     round(llr_val, 3),
                "p_value": round(p_val, 6),
            })

    rows.sort(key=lambda r: -r["llr"])
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    export_rows(
        rows,
        OUTPUT_DIR / "significant_bigrams.csv",
        ["bigram", "count", "llr", "p_value"],
    )
    print(f"  Significant bigrams (p≤{alpha}, n≥{min_count}): {len(rows)}")


# ==========================================================
# PMI CO-OCCURRENCE (bod 2)
# ==========================================================

def compute_cooccurrence(documents: list[dict], window_size: int = 5) -> None:
    """
    Raw co-occurrence pair counts (original behaviour, kept for backward compat).
    """
    pair_counter: Counter = Counter()

    for doc in documents:
        tokens = doc["tokens"]
        for i in range(len(tokens)):
            window = tokens[i: i + window_size]
            for pair in combinations(sorted(set(window)), 2):
                pair_counter[" | ".join(pair)] += 1

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    export_counter(pair_counter, OUTPUT_DIR / "cooccurrence_pairs.csv", "pair")


def compute_pmi_cooccurrence(
    documents: list[dict],
    window_size: int = 5,
    min_count: int = 2,
    min_pmi: float = 0.0,
    top_n: int = 2000,
) -> None:
    """
    PMI-weighted co-occurrence: exports pairs sorted by Positive PMI.

    PMI(x, y) = log2( P(x,y) / (P(x) · P(y)) )

    Rationale
    ---------
    Raw co-occurrence counts are dominated by high-frequency words.
    "hospodin" co-occurs with almost everything simply because it is frequent.
    PMI normalises for marginal probabilities: a pair scores high only if
    the two words co-occur more than chance predicts.  Positive PMI (PPMI =
    max(0, PMI)) is used to suppress pairs with negative association.

    Parameters
    ----------
    min_count : minimum co-occurrence count (noise filter)
    min_pmi   : minimum PPMI to include (0.0 = all positive pairs)
    top_n     : maximum rows to export (sorted by PMI descending)

    Output: pmi_cooccurrence.csv — columns: pair, count, pmi, ppmi
    """
    word_count:   Counter = Counter()
    pair_count:   Counter = Counter()
    total_tokens: int = 0

    for doc in documents:
        tokens = doc["tokens"]
        total_tokens += len(tokens)
        word_count.update(tokens)
        for i in range(len(tokens)):
            window = tokens[i: i + window_size]
            for pair in combinations(sorted(set(window)), 2):
                pair_count[" | ".join(pair)] += 1

    total_pairs = sum(pair_count.values())

    rows = []
    for pair_str, c_xy in pair_count.items():
        if c_xy < min_count:
            continue
        w1, w2 = pair_str.split(" | ", 1)
        c_x = word_count[w1]
        c_y = word_count[w2]

        if c_x == 0 or c_y == 0:
            continue

        p_xy = c_xy / total_pairs
        p_x  = c_x  / total_tokens
        p_y  = c_y  / total_tokens

        # Guard against log(0)
        if p_xy <= 0 or p_x <= 0 or p_y <= 0:
            continue

        pmi  = math.log2(p_xy / (p_x * p_y))
        ppmi = max(0.0, pmi)

        if ppmi < min_pmi:
            continue

        rows.append({
            "pair":  pair_str,
            "count": c_xy,
            "pmi":   round(pmi,  4),
            "ppmi":  round(ppmi, 4),
        })

    rows.sort(key=lambda r: -r["ppmi"])
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    export_rows(
        rows[:top_n],
        OUTPUT_DIR / "pmi_cooccurrence.csv",
        ["pair", "count", "pmi", "ppmi"],
    )
    print(f"  PMI pairs exported: {min(len(rows), top_n)} (total above threshold: {len(rows)})")


# ==========================================================
# TF-IDF
# ==========================================================

def _compute_tfidf(docs: list[dict], id_field: str, output_file: str,
                   stopwords: set, top_n: int = 50) -> None:
    """
    Shared TF-IDF computation for both file-level and chapter-level documents.

    id_field : key in each doc dict used as the document identifier
               (e.g. "file_name" or "chapter_doc_id")
    """
    ids   = [doc[id_field] for doc in docs]
    texts = [" ".join(doc["tokens"]) for doc in docs]

    vectorizer = TfidfVectorizer(
        lowercase=True,
        ngram_range=(1, 2),
        min_df=2,
        max_df=0.85,
        token_pattern=r"(?u)\b[a-zá-ž]{3,}\b",
        stop_words=list(stopwords),
    )

    try:
        matrix = vectorizer.fit_transform(texts)
    except ValueError:
        print(f"  [TF-IDF] skipped {output_file} — insufficient vocabulary")
        return

    terms = vectorizer.get_feature_names_out()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with (OUTPUT_DIR / output_file).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[id_field, "term", "tfidf_score"])
        writer.writeheader()
        for i, doc_id in enumerate(ids):
            row = matrix.getrow(i)
            top = sorted(zip(row.indices, row.data), key=lambda x: -x[1])[:top_n]
            for term_idx, score in top:
                writer.writerow({
                    id_field:      doc_id,
                    "term":        terms[term_idx],
                    "tfidf_score": round(float(score), 5),
                })


def compute_tfidf(documents: list[dict], output_file_name: str,
                  stopwords: set) -> None:
    """File-level TF-IDF (backward-compatible wrapper)."""
    _compute_tfidf(documents, "file_name", output_file_name, stopwords)


def compute_tfidf_chapters(chapter_docs: list[dict], output_file_name: str,
                            stopwords: set) -> None:
    """
    Chapter-level TF-IDF — one document per (book × chapter).

    Identifies vocabulary characteristic of individual chapters rather than
    whole books.  Useful for detecting compositional shifts within a book
    (e.g., narrative vs. law sections in Leviticus, or oracles vs. laments
    in Jeremiah).

    Uses chapter_doc_id (e.g. "bible_BKR_Gn__ch1") as the document key.
    """
    _compute_tfidf(chapter_docs, "chapter_doc_id", output_file_name, stopwords)


# ==========================================================
# MAIN
# ==========================================================

def main():
    # ── File-level documents (DB lemmas) ────────────────────────────────────
    documents = load_documents()
    print(f"Loaded file-level documents: {len(documents)}")

    compute_ngrams(documents)
    print("N-grams exported.")

    # ── Raw co-occurrence (backward compat) ──────────────────────────────────
    compute_cooccurrence(documents)
    print("Raw co-occurrence exported.")

    # ── PMI-weighted co-occurrence ───────────────────────────────────────────
    compute_pmi_cooccurrence(documents)
    print("PMI co-occurrence exported.")

    # ── Bigram statistical significance (LLR) ────────────────────────────────
    compute_ngram_significance(documents)
    print("Significant bigrams exported.")

    # ── File-level TF-IDF ────────────────────────────────────────────────────
    compute_tfidf(documents, "tfidf_style_mode.csv",    STYLE_STOPWORDS)
    compute_tfidf(documents, "tfidf_semantic_mode.csv", SEMANTIC_STOPWORDS)
    print("TF-IDF (file level) exported.")

    # ── Chapter-level documents (raw BKR files) ──────────────────────────────
    chapter_docs = load_documents_with_chapters()
    print(f"Loaded chapter-level documents: {len(chapter_docs)}")

    if chapter_docs:
        compute_tfidf_chapters(chapter_docs, "tfidf_chapters_style.csv",    STYLE_STOPWORDS)
        compute_tfidf_chapters(chapter_docs, "tfidf_chapters_semantic.csv", SEMANTIC_STOPWORDS)
        print("TF-IDF (chapter level) exported.")

        # Chapter-level n-grams and PMI (smaller scope — useful for dense books)
        compute_ngrams(chapter_docs, prefix="chapter_")
        print("Chapter-level n-grams exported.")

    print("\nDONE")
    print(f"Output folder: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
