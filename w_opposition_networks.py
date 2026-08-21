from pathlib import Path
import csv
from collections import Counter, defaultdict

from a_paths import OUTPUT_DIR as ROOT_OUTPUT
from n_db import load_rows as _db_load, TABLE_REFINED
from t_config_tradition import canonicalize_lemma
from lexicons_common import (
    OPPOSITION_GROUPS,
    OPPOSITION_PAIRS,  # re-exported for app.py live / PDF callers
    POSITIVE_WORDS,
    dominant_opposition_pole,
    matching_opposition_groups,
)


OUTPUT_DIR = ROOT_OUTPUT / "opposition_networks"


NEGATION_LEMMAS: frozenset = frozenset({
    "ne", "ani", "nikdy", "nikde", "nic", "žádný", "bez", "nelze",
})


def load_rows():
    return _db_load(TABLE_REFINED)


def _token_set(lemmas: str) -> set[str]:
    return {
        canonicalize_lemma(t)
        for t in str(lemmas or "").split()
        if t
    }


# ──────────────────────────────────────────────────────────────────────────────
# CORE DETECTION
# ──────────────────────────────────────────────────────────────────────────────

def find_oppositions(rows, window: int = 3):
    """Detect opposition groups within a ±window sentence context per book."""

    pair_counter = Counter()
    examples = defaultdict(list)

    by_file: dict = defaultdict(list)
    for row in rows:
        by_file[row["file_name"]].append(row)

    for file_name, file_rows in by_file.items():
        n = len(file_rows)
        tokenised = [_token_set(r.get("lemmas", "")) for r in file_rows]
        for i, anchor in enumerate(file_rows):
            lo = max(0, i - window)
            hi = min(n, i + window + 1)
            window_tokens: set = set()
            for j in range(lo, hi):
                window_tokens |= tokenised[j]

            for group in matching_opposition_groups(window_tokens):
                pair_counter[group.key] += 1
                if len(examples[group.key]) < 10:
                    examples[group.key].append({
                        "opposition_pair": group.key,
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
        tokenised = [_token_set(r.get("lemmas", "")) for r in file_rows]
        for i, anchor in enumerate(file_rows):
            anchor_tokens = tokenised[i]

            lo = max(0, i - window)
            hi = min(n, i + window + 1)
            window_tokens: set = set()
            for j in range(lo, hi):
                window_tokens |= tokenised[j]

            has_negation = bool(anchor_tokens & NEGATION_LEMMAS)

            for group in matching_opposition_groups(window_tokens):
                key = group.key
                pos_label, neg_label = key.split(" | ")
                dominant = dominant_opposition_pole(anchor_tokens, group)

                if dominant == "both":
                    polarity_stats[key]["both"] += 1
                    continue

                dominant_is_positive = dominant in POSITIVE_WORDS
                if has_negation:
                    dominant_is_positive = not dominant_is_positive

                if dominant_is_positive:
                    polarity_stats[key]["positive"] += 1
                else:
                    polarity_stats[key]["negative"] += 1

                subordinate = neg_label if dominant == pos_label else pos_label
                directed_counts[(dominant, subordinate)] += 1

    return dict(polarity_stats), directed_counts


def count_oppositions_in_lemma_windows(lemma_strings: list[str], window: int = 3) -> Counter:
    """
    Count opposition groups over a linear list of lemma strings (live UI / PDF).
    Each item is a space-separated lemma string for one sentence.
    """
    tokenised = [_token_set(ls) for ls in lemma_strings]
    counts: Counter = Counter()
    n = len(tokenised)
    for i in range(n):
        lo = max(0, i - window)
        hi = min(n, i + window + 1)
        window_tokens: set = set()
        for j in range(lo, hi):
            window_tokens |= tokenised[j]
        counts.update(g.key for g in matching_opposition_groups(window_tokens))
    return counts


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
    print(f"Opposition groups: {len(OPPOSITION_GROUPS)}")

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
    if pair_counter:
        print("Top pairs:")
        for key, n in pair_counter.most_common(12):
            print(f"  {key:<28} {n}")


if __name__ == "__main__":
    main()
