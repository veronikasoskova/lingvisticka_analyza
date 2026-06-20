from pathlib import Path
import csv
from collections import Counter, defaultdict

from b_analytics_utils import export_counter, export_rows
from n_db import load_rows as _db_load, TABLE_RELATIONS


OUTPUT_DIR = Path(
    "output/verbal_relations_analytics"
)


def load_rows():
    return _db_load(TABLE_RELATIONS)


def relation_type_counts(rows):
    counter = Counter(
        row["relation_type"]
        for row in rows
    )

    export_counter(
        counter,
        OUTPUT_DIR / "relation_type_counts.csv",
        "relation_type"
    )


def subtype_counts(rows):
    counter = Counter(
        row["subtype"]
        for row in rows
    )

    export_counter(
        counter,
        OUTPUT_DIR / "subtype_counts.csv",
        "subtype"
    )


def relations_by_book(rows):
    counts = defaultdict(Counter)

    for row in rows:
        file_name = row["file_name"]
        relation_type = row["relation_type"]
        counts[file_name][relation_type] += 1

    all_relation_types = sorted({
        row["relation_type"]
        for row in rows
    })

    output_path = OUTPUT_DIR / "relations_by_book.csv"
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as f:
        fieldnames = [
            "file_name",
            *all_relation_types,
            "total"
        ]

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        writer.writeheader()

        for file_name, counter in counts.items():
            total = sum(counter.values())

            row = {
                "file_name": file_name,
                "total": total
            }

            for relation_type in all_relation_types:
                row[relation_type] = counter.get(
                    relation_type,
                    0
                )

            writer.writerow(row)


def confidence_by_relation(rows):
    values = defaultdict(list)

    for row in rows:
        values[row["relation_type"]].append(
            float(row["confidence"])
        )

    output_path = OUTPUT_DIR / "confidence_by_relation.csv"
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "relation_type",
                "count",
                "avg_confidence",
                "min_confidence",
                "max_confidence"
            ]
        )

        writer.writeheader()

        for relation_type, scores in values.items():
            writer.writerow({
                "relation_type": relation_type,
                "count": len(scores),
                "avg_confidence": round(
                    sum(scores) / len(scores),
                    3
                ),
                "min_confidence": min(scores),
                "max_confidence": max(scores),
            })


def examples_by_relation(rows, max_examples=20):
    examples = defaultdict(list)

    for row in rows:
        relation_type = row["relation_type"]

        if len(examples[relation_type]) < max_examples:
            examples[relation_type].append(row)

    output_path = OUTPUT_DIR / "examples_by_relation.csv"
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "relation_type",
                "subtype",
                "sentence",
                "file_name",
                "confidence"
            ]
        )

        writer.writeheader()

        for relation_type, relation_examples in examples.items():
            for row in relation_examples:
                writer.writerow({
                    "relation_type": relation_type,
                    "subtype": row["subtype"],
                    "sentence": row["sentence"],
                    "file_name": row["file_name"],
                    "confidence": row["confidence"],
                })


def relations_ratio_by_book(rows):
    counts = defaultdict(Counter)
    for row in rows:
        counts[row["file_name"]][row["relation_type"]] += 1

    all_types = sorted({row["relation_type"] for row in rows})

    out_rows = []
    for file_name, counter in sorted(counts.items()):
        total = sum(counter.values())
        row = {"file_name": file_name, "total": total}
        for rt in all_types:
            n = counter.get(rt, 0)
            row[rt] = n
            row[f"{rt}_ratio"] = round(n / total, 3) if total else 0.0
        out_rows.append(row)

    fieldnames = ["file_name", "total"]
    for rt in all_types:
        fieldnames += [rt, f"{rt}_ratio"]

    output_path = OUTPUT_DIR / "relations_ratio_by_book.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)


def low_confidence_relations(rows):
    fields = ["sentence", "relation_type", "subtype", "confidence", "file_name"]
    low = [
        {f: row.get(f, "") for f in fields}
        for row in rows
        if float(row.get("confidence", 1)) < 0.6
    ]

    output_path = OUTPUT_DIR / "low_confidence_relations.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(low)


def descriptive_fallback_ratio(rows):
    totals     = Counter()
    fallback_n = Counter()

    for row in rows:
        book = row["file_name"]
        totals[book] += 1
        if row["relation_type"] == "descriptive_relation":
            fallback_n[book] += 1

    total_all    = sum(totals.values())
    fallback_all = sum(fallback_n.values())

    print(f"\n{'DESCRIPTIVE FALLBACK RATIO PER BOOK':─<50}")
    print(f"  {'BOOK':<28} {'fallback':>8}  {'total':>7}  {'ratio':>7}")
    print(f"  {'-'*52}")
    for book in sorted(totals):
        total = totals[book]
        n = fallback_n[book]
        ratio = n / total if total else 0.0
        bar = "█" * int(ratio * 20)
        print(f"  {book:<28} {n:>8}  {total:>7}  {ratio:>6.1%}  {bar}")
    print(f"  {'─'*52}")
    print(f"  {'TOTAL':<28} {fallback_all:>8}  {total_all:>7}  {fallback_all/total_all:>6.1%}")


def main():
    rows = load_rows()

    print(
        f"Loaded rows: {len(rows)}"
    )

    descriptive_fallback_ratio(rows)
    relation_type_counts(rows)
    subtype_counts(rows)
    relations_by_book(rows)
    confidence_by_relation(rows)
    examples_by_relation(rows)
    relations_ratio_by_book(rows)
    low_confidence_relations(rows)

    print("\nDONE")
    print(
        f"Output folder: {OUTPUT_DIR}"
    )


if __name__ == "__main__":
    main()