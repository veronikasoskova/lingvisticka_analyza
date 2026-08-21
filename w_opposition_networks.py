from pathlib import Path
import csv
from collections import Counter, defaultdict

from a_paths import OUTPUT_DIR as ROOT_OUTPUT
from n_db import load_rows as _db_load, TABLE_REFINED


OUTPUT_DIR = ROOT_OUTPUT / "opposition_networks"


OPPOSITION_PAIRS = {
    ("život", "smrt"),
    ("světlo", "tma"),
    ("dobrý", "zlý"),
    ("spravedlivý", "bezbožný"),
    ("pravda", "lež"),
    ("duch", "tělo"),
    ("čistý", "nečistý"),
    ("víra", "skutek"),
    ("milost", "zákon"),
    ("bůh", "modla"),
    ("hospodin", "baal"),
    ("moudrost", "bláznovství"),
    ("požehnání", "zlořečení"),
    ("nebe", "země"),
    ("den", "noc"),
    ("pravice", "levice"),
    ("chudý", "bohatý"),
    ("pokoj", "boj"),
    ("dobrý", "špatný"),
    ("požehnat", "proklat"),
    ("zákon", "milosrdenství"),
    ("spravedlnost", "nepravost"),
    ("víra", "nevěra"),
}

# Semantically "positive" pole for each word that appears in OPPOSITION_PAIRS.
# Used to label direction in the oriented network.
POSITIVE_WORDS: frozenset = frozenset({
    "život", "světlo", "dobrý", "spravedlivý", "pravda", "duch", "čistý",
    "víra", "milost", "bůh", "hospodin", "moudrost", "požehnání", "požehnat",
    "nebe", "den", "pravice", "chudý", "pokoj", "milosrdenství", "spravedlnost",
})

NEGATION_LEMMAS: frozenset = frozenset({
    "ne", "ani", "nikdy", "nikde", "nic", "žádný", "bez", "nelze",
})


def load_rows():
    return _db_load(TABLE_REFINED)


# ──────────────────────────────────────────────────────────────────────────────
# CORE DETECTION
# ──────────────────────────────────────────────────────────────────────────────

def _dominant_pole(anchor_tokens: set, word1: str, word2: str) -> str:
    """Return which pole (word1 / word2 / 'both') is present in anchor tokens."""
    has1 = word1 in anchor_tokens
    has2 = word2 in anchor_tokens
    if has1 and not has2:
        return word1
    if has2 and not has1:
        return word2
    return "both"


def find_oppositions(rows, window: int = 3):
    """Detect opposition pairs within a ±window sentence context per book."""

    pair_counter = Counter()
    examples = defaultdict(list)

    by_file: dict = defaultdict(list)
    for row in rows:
        by_file[row["file_name"]].append(row)

    for file_name, file_rows in by_file.items():
        n = len(file_rows)
        for i, anchor in enumerate(file_rows):
            lo = max(0, i - window)
            hi = min(n, i + window + 1)
            window_tokens: set = set()
            for j in range(lo, hi):
                window_tokens |= set(file_rows[j].get("lemmas", "").split())

            for word1, word2 in OPPOSITION_PAIRS:
                if word1 in window_tokens and word2 in window_tokens:
                    key = f"{word1} | {word2}"
                    pair_counter[key] += 1
                    if len(examples[key]) < 10:
                        examples[key].append({
                            "opposition_pair": key,
                            "sentence": anchor["sentence"],
                            "file_name": file_name,
                        })

    return pair_counter, examples


def find_opposition_polarity(rows, window: int = 3):
    """
    For each detected opposition window, determine which pole dominates
    in the anchor sentence and build directed-edge counts.

    Returns:
        polarity_stats: dict  pair_key → {"positive": n, "negative": n, "both": n}
        directed_counts: Counter  (source, target) → n
            direction convention: dominant_pole → subordinate_pole
    """
    polarity_stats: dict = defaultdict(lambda: {"positive": 0, "negative": 0, "both": 0})
    directed_counts: Counter = Counter()

    by_file: dict = defaultdict(list)
    for row in rows:
        by_file[row["file_name"]].append(row)

    for file_name, file_rows in by_file.items():
        n = len(file_rows)
        for i, anchor in enumerate(file_rows):
            anchor_tokens: set = set(anchor.get("lemmas", "").split())

            lo = max(0, i - window)
            hi = min(n, i + window + 1)
            window_tokens: set = set()
            for j in range(lo, hi):
                window_tokens |= set(file_rows[j].get("lemmas", "").split())

            has_negation = bool(anchor_tokens & NEGATION_LEMMAS)

            for word1, word2 in OPPOSITION_PAIRS:
                if not (word1 in window_tokens and word2 in window_tokens):
                    continue

                key = f"{word1} | {word2}"
                dominant = _dominant_pole(anchor_tokens, word1, word2)

                # Determine semantic label: positive / negative / both
                if dominant == "both":
                    polarity_stats[key]["both"] += 1
                    # No clear direction for directed graph
                    continue

                dominant_is_positive = dominant in POSITIVE_WORDS
                # Flip if anchor has negation (negated positive → negative context)
                if has_negation:
                    dominant_is_positive = not dominant_is_positive

                if dominant_is_positive:
                    polarity_stats[key]["positive"] += 1
                else:
                    polarity_stats[key]["negative"] += 1

                # Directed edge: dominant → subordinate
                subordinate = word2 if dominant == word1 else word1
                directed_counts[(dominant, subordinate)] += 1

    return dict(polarity_stats), directed_counts


# ──────────────────────────────────────────────────────────────────────────────
# EXPORT
# ──────────────────────────────────────────────────────────────────────────────

def export_counts(pair_counter):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "opposition_counts.csv"
    with output_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["opposition_pair", "count"])
        writer.writeheader()
        for pair, count in pair_counter.most_common():
            writer.writerow({"opposition_pair": pair, "count": count})


def export_examples(examples):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "opposition_examples.csv"
    with output_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["opposition_pair", "sentence", "file_name"]
        )
        writer.writeheader()
        for pair, rows in examples.items():
            for row in rows:
                writer.writerow(row)


def export_polarity(polarity_stats: dict, pair_counter: Counter):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "opposition_polarity.csv"
    with output_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "opposition_pair", "total",
                "positive", "negative", "both",
                "polarity_ratio",
            ],
        )
        writer.writeheader()
        for pair, stats in sorted(
            polarity_stats.items(),
            key=lambda x: -pair_counter.get(x[0], 0),
        ):
            pos = stats["positive"]
            neg = stats["negative"]
            both = stats["both"]
            total = pos + neg + both
            denom = pos + neg
            writer.writerow({
                "opposition_pair": pair,
                "total":           total,
                "positive":        pos,
                "negative":        neg,
                "both":            both,
                "polarity_ratio":  round(pos / denom, 3) if denom else None,
            })


def export_directed_edges(directed_counts: Counter, top_n: int = 60):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "opposition_directed_edges.csv"
    with output_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["source", "target", "weight"])
        writer.writeheader()
        for (src, tgt), weight in directed_counts.most_common(top_n):
            writer.writerow({"source": src, "target": tgt, "weight": weight})


# ──────────────────────────────────────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────────────────────────────────────

def main():
    rows = load_rows()
    print(f"Loaded rows: {len(rows)}")

    pair_counter, examples = find_oppositions(rows)
    export_counts(pair_counter)
    export_examples(examples)

    polarity_stats, directed_counts = find_opposition_polarity(rows)
    export_polarity(polarity_stats, pair_counter)
    export_directed_edges(directed_counts)

    print("\nDONE")
    print(f"Opposition pairs found: {len(pair_counter)}")
    print(f"Polarity stats:         {len(polarity_stats)} pairs")
    print(f"Directed edges:         {len(directed_counts)} unique edges")
    print(f"Output folder: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
