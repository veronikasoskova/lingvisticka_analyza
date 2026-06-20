from pathlib import Path
import csv

from n_db import count_table_rows, DB_PATH, TABLE_SKINNER, TABLE_RELATIONS, TABLE_REFINED


OUTPUT_DIR = Path(
    "output/final_summary"
)

# Primary tables stored in SQLite (key → table name)
DB_TABLES = {
    "q_skinner_analysis":   TABLE_SKINNER,
    "verbal_relations":     TABLE_RELATIONS,
    "refined_descriptions": TABLE_REFINED,
}

# Derived analytics outputs still written as CSV
INPUT_FILES = {
    "weighted_centrality":   Path("output/weighted_centrality/weighted_semantic_centrality.csv"),
    "religious_density":     Path("output/religious_elements/density_by_book.csv"),
    "religious_fields":      Path("output/religious_elements/field_summary.csv"),
    "philosophy_by_book":    Path("output/religious_elements/philosophy_by_book.csv"),
    "religious_combined":    Path("output/religious_elements/combined_density_by_book.csv"),
    "religious_fields_wide": Path("output/religious_elements/fields_by_book_wide.csv"),
    "concept_clusters":      Path("output/concept_clusters/cluster_summary.csv"),
    "opposition_networks":   Path("output/opposition_networks/opposition_counts.csv"),
    "style_authorship":      Path("output/style_authorship/book_style_clusters.csv"),
    "dependency_counts":     Path("output/dependency_hierarchy/dependency_counts.csv"),
    "q_intention_counts":    Path("output/q_skinner_analytics/q_intention_counts.csv"),
    "taxonomy_analytics":    Path("output/taxonomy_analytics/skinner_class_counts.csv"),
}


def count_rows(path):

    if not path.exists():
        return None

    with path.open(
        "r",
        encoding="utf-8"
    ) as f:

        reader = csv.reader(f)

        try:
            next(reader)
        except StopIteration:
            return 0

        return sum(
            1
            for _
            in reader
        )


def build_summary():

    summary = []

    # Primary pipeline data from SQLite
    for name, table in DB_TABLES.items():
        n = count_table_rows(table)
        summary.append({
            "module": name,
            "exists": n is not None,
            "rows": n,
            "file_path": f"sqlite:{DB_PATH.name}:{table}",
        })

    # Derived analytics from CSV files
    for name, path in INPUT_FILES.items():
        exists = path.exists()
        summary.append({
            "module": name,
            "exists": exists,
            "rows": count_rows(path) if exists else None,
            "file_path": str(path),
        })

    return summary


def export_csv(summary):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    output_file = (
        OUTPUT_DIR /
        "pipeline_summary.csv"
    )

    with output_file.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=[
                "module",
                "exists",
                "rows",
                "file_path"
            ]
        )

        writer.writeheader()
        writer.writerows(summary)


def export_txt(summary):

    output_file = (
        OUTPUT_DIR /
        "pipeline_report.txt"
    )

    with output_file.open(
        "w",
        encoding="utf-8"
    ) as f:

        f.write(
            "SKINNER PIPELINE FINAL REPORT\n"
        )

        f.write(
            "=" * 40 + "\n\n"
        )

        for row in summary:

            f.write(
                f"MODULE: {row['module']}\n"
            )

            f.write(
                f"EXISTS: {row['exists']}\n"
            )

            f.write(
                f"ROWS: {row['rows']}\n"
            )

            f.write(
                f"PATH: {row['file_path']}\n"
            )

            f.write(
                "-" * 40 + "\n"
            )


def main():

    summary = build_summary()

    export_csv(
        summary
    )

    export_txt(
        summary
    )

    print("\nDONE")
    print(
        f"Output folder: {OUTPUT_DIR}"
    )

    for row in summary:

        print(
            row["module"],
            row["exists"],
            row["rows"]
        )


if __name__ == "__main__":
    main()