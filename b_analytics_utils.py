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


def filter_by_abbrevs(df, abbrev_set, *, col: str, abbr_of):
    """Keep rows whose *col* maps to an abbreviation in *abbrev_set*.

    ``abbrev_set is None`` means no filter (whole corpus).
    """
    if abbrev_set is None or df is None or col not in getattr(df, "columns", ()):
        return df
    return df[df[col].map(abbr_of).isin(abbrev_set)]


def value_counts_df(series, *, exclude=(), raw_col="_raw", count_col="count"):
    """``value_counts`` as a two-column DataFrame, optionally dropping labels."""
    import pandas as pd

    vc = series.value_counts()
    drop = [x for x in exclude if x in vc.index]
    if drop:
        vc = vc.drop(labels=drop)
    return vc.rename_axis(raw_col).reset_index(name=count_col)


def export_rows(rows, output_path, fieldnames):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
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
