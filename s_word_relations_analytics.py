from pathlib import Path
import csv
from collections import Counter, defaultdict

from a_paths import OUTPUT_DIR as ROOT_OUTPUT
from b_analytics_utils import export_counter, export_rows


INPUT_FILE = ROOT_OUTPUT / "word_relations" / "semantic_relations.csv"
OUTPUT_DIR = ROOT_OUTPUT / "word_relations_analytics"


def load_rows():

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing file: {INPUT_FILE}"
        )

    with INPUT_FILE.open(
        "r",
        encoding="utf-8"
    ) as f:

        reader = csv.DictReader(f)
        return list(reader)


def strongest_relations(rows, output_path=None):

    sorted_rows = sorted(
        rows,
        key=lambda r: float(r["pmi"]),
        reverse=True
    )

    if output_path is None:
        output_path = OUTPUT_DIR / "top_pmi_relations.csv"

    export_rows(
        sorted_rows[:200],
        output_path,
        ["word1", "word2", "pair_count", "pmi"]
    )


def most_connected_words(rows):

    counter = Counter()

    for row in rows:
        counter[row["word1"]] += 1
        counter[row["word2"]] += 1

    output_rows = [
        {
            "word": word,
            "connection_count": count
        }
        for word, count in counter.most_common(200)
    ]

    export_rows(
        output_rows,
        OUTPUT_DIR / "most_connected_words.csv",
        ["word", "connection_count"]
    )


def strongest_neighbors(rows, output_path=None):

    neighbors = defaultdict(list)

    for row in rows:
        word1 = row["word1"]
        word2 = row["word2"]
        pmi = float(row["pmi"])

        neighbors[word1].append(
            (word2, pmi)
        )
        neighbors[word2].append(
            (word1, pmi)
        )

    output_rows = []

    for word, items in neighbors.items():

        top_items = sorted(
            items,
            key=lambda x: x[1],
            reverse=True
        )[:10]

        output_rows.append({
            "word": word,
            "top_neighbors": "; ".join(
                f"{neighbor}:{round(score, 3)}"
                for neighbor, score in top_items
            )
        })

    if output_path is None:
        output_path = OUTPUT_DIR / "strongest_neighbors.csv"

    export_rows(
        output_rows,
        output_path,
        ["word", "top_neighbors"]
    )


PER_TYPE_FILES = {
    "theological": Path(
        "output/word_relations/pmi_theological.csv"
    ),
    "moral": Path(
        "output/word_relations/pmi_moral.csv"
    ),
    "social": Path(
        "output/word_relations/pmi_social.csv"
    ),
}


def load_type_rows(path):

    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def compare_types(type_rows_map):

    all_pairs = {}

    for type_name, rows in type_rows_map.items():
        top20 = sorted(
            rows,
            key=lambda r: float(r["pmi"]),
            reverse=True
        )[:20]
        for row in top20:
            pair = (row["word1"], row["word2"])
            if pair not in all_pairs:
                all_pairs[pair] = {
                    "word1": row["word1"],
                    "word2": row["word2"],
                }
            all_pairs[pair][f"pmi_{type_name}"] = row["pmi"]
            all_pairs[pair][f"n_{type_name}"] = row["pair_count"]

    type_names = list(type_rows_map.keys())

    output_rows = []
    for pair, data in all_pairs.items():
        present_in = [
            t for t in type_names
            if f"pmi_{t}" in data
        ]
        data["present_in"] = "|".join(present_in)
        data["unique_to"] = (
            present_in[0]
            if len(present_in) == 1
            else ""
        )
        output_rows.append(data)

    output_rows.sort(
        key=lambda r: r["present_in"],
        reverse=True
    )

    fieldnames = ["word1", "word2", "present_in", "unique_to"]
    for t in type_names:
        fieldnames += [f"pmi_{t}", f"n_{t}"]

    export_rows(
        output_rows,
        OUTPUT_DIR / "type_comparison.csv",
        fieldnames
    )


def main():

    rows = load_rows()

    print(f"Loaded relations: {len(rows)}")

    strongest_relations(rows)
    most_connected_words(rows)
    strongest_neighbors(rows)

    type_rows_map = {}

    for type_name, path in PER_TYPE_FILES.items():
        type_rows = load_type_rows(path)

        if not type_rows:
            print(f"  [{type_name}] skipped — file missing")
            continue

        print(f"\n[{type_name}] {len(type_rows)} pairs")

        strongest_relations(
            type_rows,
            OUTPUT_DIR / f"{type_name}_top_pmi.csv"
        )
        strongest_neighbors(
            type_rows,
            OUTPUT_DIR / f"{type_name}_neighbors.csv"
        )

        type_rows_map[type_name] = type_rows

    if type_rows_map:
        compare_types(type_rows_map)
        print(f"\ntype_comparison.csv written")

    print(f"\nDONE — Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()