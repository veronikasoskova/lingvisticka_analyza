from pathlib import Path
import csv
from collections import Counter, defaultdict


def export_counter(counter, output_path, key_name):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[key_name, "count"])
        writer.writeheader()
        for key, count in counter.most_common():
            writer.writerow({key_name: key, "count": count})


def export_rows(rows, output_path, fieldnames):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def compute_ratio_by_book(rows, field, books=None):
    counts = defaultdict(Counter)
    for row in rows:
        counts[row["file_name"]][row[field]] += 1

    all_values = sorted({row[field] for row in rows})
    all_books  = sorted(books) if books else sorted(counts)

    out_rows = []
    for file_name in all_books:
        counter = counts.get(file_name, Counter())
        total   = sum(counter.values())
        out_row = {"file_name": file_name, "total": total}
        for val in all_values:
            n = counter.get(val, 0)
            out_row[val]              = n
            out_row[f"{val}_ratio"]   = round(n / total, 3) if total else 0.0
        out_rows.append(out_row)

    return out_rows
