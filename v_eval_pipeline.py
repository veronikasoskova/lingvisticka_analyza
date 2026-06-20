"""
v_eval_pipeline.py — Pipeline quality evaluation

Reads from SQLite DB (falls back to legacy CSVs if DB is empty).
Produces a text report + structured CSVs in output/eval/.

Usage:
    python v_eval_pipeline.py
"""

import csv
import math
import random
import statistics
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path

from genre_maps import BOOK_GENRES as GENRE_MAP  # canonical file-keyed map

from n_db import (
    load_rows as _db_load,
    insert_rows, get_conn, list_runs, count_table_rows,
    DB_PATH, TABLE_SKINNER, TABLE_RELATIONS, TABLE_REFINED,
)

# ==========================================================
# V1. CONFIG
# ==========================================================

OUTPUT_DIR = Path("output/eval")

LABEL_FIELD      = "illocutionary_force"
BOOK_FIELD       = "file_name"
CONF_FIELD       = "confidence"
LEMMA_FIELD      = "root_lemma"

UNKNOWN_VALUES   = {"unknown", "unclassified", "none", ""}
LOW_CONF         = 0.30
CONF_THRESHOLD   = 0.50
DOMINANT_THRESH  = 0.50   # warn if one class > 50 %
SAMPLE_SIZE      = 20
TOP_LEMMAS       = 20

LEGACY_CSV = {
    TABLE_SKINNER:   Path("output/q_skinner_bible_analysis.csv"),
    TABLE_RELATIONS: Path("output/verbal_relations_bible.csv"),
    TABLE_REFINED:   Path("output/refined_descriptions_bible.csv"),
}

# Gold standard annotation file (two-annotator CSV)
GOLD_STANDARD_PATH = Path("data/annotated_q_intentions.csv")
GOLD_STANDARD_FIELDS = [
    "sentence_id", "file_name", "sentence",
    "system_label",        # filled by generate_annotation_template()
    "human_label_1",       # Annotator A
    "human_label_2",       # Annotator B (optional — for IAA)
    "notes",
]
GOLD_TEMPLATE_N = 200   # stratified sample size for annotation template

# DEAD: presunuté do genre_maps.py (importované vyššie ako GENRE_MAP)
# GENRE_MAP: dict[str, str] = { "bible_BKR_Gn.txt": "narrative_pentateuch", ... }


# ==========================================================
# V2. DATA LOADING  (DB → CSV fallback)
# ==========================================================

def _load_csv(path: Path) -> list:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_data(table: str) -> tuple:
    """
    Returns (rows, source) where source is 'db' or 'csv'.
    Falls back to legacy CSV when the DB table is empty.
    """
    rows = _db_load(table)
    if rows:
        return rows, "db"
    rows = _load_csv(LEGACY_CSV[table])
    return rows, "csv" if rows else "empty"


def _conf(row: dict) -> float:
    try:
        return float(row.get(CONF_FIELD, -1))
    except (ValueError, TypeError):
        return -1.0


def _label(row: dict) -> str:
    return row.get(LABEL_FIELD, "").strip().lower()


def _is_unknown(row: dict) -> bool:
    return _label(row) in UNKNOWN_VALUES


# ==========================================================
# V3. COVERAGE  — classified vs unknown
# ==========================================================

def coverage_stats(rows: list) -> dict:
    total = len(rows)
    if not total:
        return {"total": 0}

    classified = sum(1 for r in rows if not _is_unknown(r))
    by_book    = defaultdict(lambda: {"total": 0, "classified": 0})

    for r in rows:
        book = r.get(BOOK_FIELD, "unknown")
        by_book[book]["total"] += 1
        if not _is_unknown(r):
            by_book[book]["classified"] += 1

    book_rows = []
    for book, d in sorted(by_book.items()):
        pct = round(100 * d["classified"] / d["total"], 1) if d["total"] else 0
        book_rows.append({"book": book, "total": d["total"],
                          "classified": d["classified"], "coverage_pct": pct})

    return {
        "total":        total,
        "classified":   classified,
        "unknown":      total - classified,
        "coverage_pct": round(100 * classified / total, 1),
        "by_book":      book_rows,
    }


# ==========================================================
# V4. CONSISTENCY  — same root_lemma → same label
# ==========================================================

def consistency_stats(sk_rows: list, ref_rows: list) -> dict:
    """
    Joins skinner_analysis (illocutionary_force) with refined_descriptions
    (root_lemma) by sentence_id to check: same lemma → same label.
    """
    # Build (sentence_id, file_name) → label map — sentence_id resets per book
    id_to_label: dict = {}
    for r in sk_rows:
        sid  = r.get("sentence_id", "")
        fn   = r.get("file_name", "")
        lab  = _label(r)
        if sid and lab not in UNKNOWN_VALUES:
            id_to_label[(sid, fn)] = lab

    # Aggregate lemma → set of labels using refined_descriptions for lemmas
    lemma_labels: dict = defaultdict(set)
    for r in ref_rows:
        sid = r.get("sentence_id", "")
        fn  = r.get("file_name", "")
        lem = r.get(LEMMA_FIELD, "").strip()
        lab = id_to_label.get((sid, fn))
        if lem and lab:
            lemma_labels[lem].add(lab)

    total      = len(lemma_labels)
    consistent = sum(1 for ls in lemma_labels.values() if len(ls) == 1)
    ambiguous  = sorted(
        [(lem, sorted(ls)) for lem, ls in lemma_labels.items() if len(ls) > 1],
        key=lambda x: len(x[1]),
        reverse=True,
    )

    return {
        "unique_lemmas":   total,
        "consistent":      consistent,
        "ambiguous":       total - consistent,
        "consistency_pct": round(100 * consistent / total, 1) if total else 0,
        "top_ambiguous":   ambiguous[:20],
        "source":          "cross-table (skinner × refined_descriptions)",
    }


# ==========================================================
# V5. RANDOM SAMPLE  — stratified by label
# ==========================================================

def random_sample(rows: list, n: int = SAMPLE_SIZE) -> list:
    by_label: dict = defaultdict(list)
    for r in rows:
        by_label[_label(r)].append(r)

    labels = sorted(by_label)
    per_cls = max(1, n // max(len(labels), 1))

    taken_ids: set = set()
    sample: list   = []

    for lab in labels:
        pool = by_label[lab]
        take = min(per_cls, len(pool))
        chosen = random.sample(pool, take)
        sample.extend(chosen)
        taken_ids.update(id(r) for r in chosen)

    # top up if needed
    if len(sample) < n:
        rest = [r for r in rows if id(r) not in taken_ids]
        extra = min(n - len(sample), len(rest))
        if extra:
            sample.extend(random.sample(rest, extra))

    return sample[:n]


# ==========================================================
# V6. FAILURE DETECTION
# ==========================================================

def failure_stats(rows: list, ref_rows: list = None) -> dict:
    total         = len(rows)
    low_conf      = [r for r in rows if 0 <= _conf(r) < LOW_CONF]
    unknown_rows  = [r for r in rows if _is_unknown(r)]

    # root_lemma lives in refined_descriptions, not in QSkinnerDecision
    ref_for_lemma = ref_rows if ref_rows is not None else []
    no_lemma      = [r for r in ref_for_lemma if not r.get(LEMMA_FIELD, "").strip()]

    # Suspicious: unknown rows that have high confidence (≥ 0.5)
    # → suggests unknown is a default label, not a genuine non-match
    high_conf_unknown = [r for r in unknown_rows if _conf(r) >= CONF_THRESHOLD]

    # Top locution patterns in unknown (from QSkinnerDecision.locution)
    unknown_locutions = Counter(r.get("locution", "") for r in unknown_rows)

    return {
        "low_conf_count":        len(low_conf),
        "low_conf_pct":          round(100 * len(low_conf) / total, 1) if total else 0,
        "unknown_count":         len(unknown_rows),
        "high_conf_unknown":     len(high_conf_unknown),
        "no_lemma_count_ref":    len(no_lemma),
        "top_unknown_locutions": unknown_locutions.most_common(10),
        "low_conf_sample":       random.sample(low_conf, min(5, len(low_conf))),
    }


# ==========================================================
# V7. CLASS DISTRIBUTION
# ==========================================================

def distribution_stats(rows: list) -> list:
    counter = Counter(_label(r) for r in rows)
    total   = len(rows)
    result  = []
    for label, count in counter.most_common():
        pct = round(100 * count / total, 1) if total else 0
        result.append({
            "label":    label,
            "count":    count,
            "pct":      pct,
            "dominant": pct > DOMINANT_THRESH * 100,
        })
    return result


# ==========================================================
# V8. BOOK COMPARISON
# ==========================================================

def book_comparison(rows: list) -> tuple:
    by_book: dict     = defaultdict(Counter)
    for r in rows:
        by_book[r.get(BOOK_FIELD, "unknown")][_label(r)] += 1

    all_labels = sorted({_label(r) for r in rows})

    book_stats: dict = {}
    for book, counter in sorted(by_book.items()):
        total = sum(counter.values())
        book_stats[book] = {
            "total":  total,
            "ratios": {
                lab: round(counter[lab] / total, 3) if total else 0.0
                for lab in all_labels
            },
        }

    outliers: list = []
    for label in all_labels:
        ratios = [book_stats[b]["ratios"][label] for b in book_stats]
        if len(ratios) < 2:
            continue
        try:
            mean = statistics.mean(ratios)
            std  = statistics.stdev(ratios)
        except statistics.StatisticsError:
            continue
        if std == 0:
            continue
        for book in book_stats:
            r = book_stats[book]["ratios"][label]
            z = (r - mean) / std
            if abs(z) > 2.0:
                outliers.append({
                    "book": book, "label": label,
                    "ratio": r, "z_score": round(z, 2),
                })

    return book_stats, outliers, all_labels


# ==========================================================
# V9. CONFIDENCE ANALYSIS
# ==========================================================

def confidence_analysis(rows: list) -> tuple:
    by_label: dict = defaultdict(list)
    for r in rows:
        c = _conf(r)
        if c >= 0:
            by_label[_label(r)].append(c)

    bins = {"0.0-0.3": 0, "0.3-0.6": 0, "0.6-1.0": 0}
    stats: dict = {}

    for label, confs in sorted(by_label.items()):
        stats[label] = {
            "n":        len(confs),
            "mean":     round(statistics.mean(confs), 3),
            "median":   round(statistics.median(confs), 3),
            "min":      round(min(confs), 3),
            "max":      round(max(confs), 3),
            "low_pct":  round(
                100 * sum(1 for c in confs if c < CONF_THRESHOLD) / len(confs), 1
            ),
        }
        for c in confs:
            if c < 0.3:
                bins["0.0-0.3"] += 1
            elif c < 0.6:
                bins["0.3-0.6"] += 1
            else:
                bins["0.6-1.0"] += 1

    return stats, bins


# ==========================================================
# V10. LEXICON COVERAGE  — top lemmas per class
# ==========================================================

def lexicon_coverage(rows: list, top_n: int = TOP_LEMMAS) -> dict:
    by_label: dict = defaultdict(Counter)
    for r in rows:
        label = _label(r)
        lemma = r.get(LEMMA_FIELD, "").strip()
        if lemma and label not in UNKNOWN_VALUES:
            by_label[label][lemma] += 1
    return {lab: ctr.most_common(top_n) for lab, ctr in sorted(by_label.items())}


# ==========================================================
# V11. SQLITE VERIFICATION
# ==========================================================

def sqlite_verification() -> dict:
    result: dict = {
        "db_path":    str(DB_PATH),
        "db_exists":  DB_PATH.exists(),
        "tables":     {},
        "legacy_csv": {},
        "append_test": None,
    }

    # Table counts and run history
    for table in [TABLE_SKINNER, TABLE_RELATIONS, TABLE_REFINED]:
        n    = count_table_rows(table)
        runs = list_runs(table)
        result["tables"][table] = {"rows": n, "runs": runs}

    # Legacy CSV counts
    for table, path in LEGACY_CSV.items():
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                csv_rows = sum(1 for _ in csv.reader(f)) - 1
        else:
            csv_rows = None
        result["legacy_csv"][table] = {
            "path":   str(path),
            "exists": path.exists(),
            "rows":   csv_rows,
        }

    # Append test: use a dedicated throw-away table so production tables
    # are never touched and their schema is never polluted by test rows.
    TEST_TABLE = "_eval_append_test"
    TEST_RUN   = "_eval_run_"
    dummy      = [{"value": "TEST"}]

    conn = get_conn()
    conn.execute(f'DROP TABLE IF EXISTS "{TEST_TABLE}"')
    conn.commit()
    conn.close()

    before = count_table_rows(TEST_TABLE) or 0
    insert_rows(TEST_TABLE, dummy, TEST_RUN)
    after  = count_table_rows(TEST_TABLE) or 0
    insert_rows(TEST_TABLE, dummy, TEST_RUN)
    after2 = count_table_rows(TEST_TABLE) or 0

    conn = get_conn()
    conn.execute(f'DROP TABLE IF EXISTS "{TEST_TABLE}"')
    conn.commit()
    conn.close()

    result["append_test"] = {
        "before":        before,
        "after_insert":  after,
        "after_insert2": after2,
        "passed":        (after == 1) and (after2 == 2),
    }

    return result


# ==========================================================
# V12. GENRE-AWARE ERROR ANALYSIS  (no gold standard needed)
# ==========================================================

def genre_error_analysis(rows: list, label_field: str = "primary_intention") -> list:
    """
    Per-genre class distribution — shows genre-specific classification patterns.
    Uses GENRE_MAP; books not in the map get 'unknown_genre'.
    """
    by_genre: dict = defaultdict(Counter)
    for r in rows:
        genre = GENRE_MAP.get(r.get(BOOK_FIELD, ""), "unknown_genre")
        by_genre[genre][r.get(label_field, "").strip().lower()] += 1

    result = []
    for genre in sorted(by_genre):
        counter = by_genre[genre]
        total   = sum(counter.values())
        for label, count in counter.most_common():
            result.append({
                "genre":   genre,
                "label":   label,
                "count":   count,
                "total_in_genre": total,
                "rate":    round(count / total, 4) if total else 0.0,
            })
    return result


def genre_summary(genre_rows: list) -> list:
    """Per-genre dominant label + rhetorical density."""
    by_genre: dict = defaultdict(list)
    for r in genre_rows:
        by_genre[r["genre"]].append(r)

    out = []
    for genre, rows in sorted(by_genre.items()):
        total = rows[0]["total_in_genre"] if rows else 0
        top   = rows[0] if rows else {}
        rhet  = sum(r["count"] for r in rows
                    if r["label"] not in {"record", "narrative", "unclassified"})
        out.append({
            "genre":              genre,
            "total":              total,
            "dominant_label":     top.get("label", "—"),
            "dominant_rate":      top.get("rate", 0.0),
            "rhetorical_density": round(rhet / total, 3) if total else 0.0,
        })
    return out


# ==========================================================
# V13. COHEN'S κ  (inter-annotator agreement)
# ==========================================================

def cohen_kappa(labels_a: list[str], labels_b: list[str]) -> float:
    """
    Cohen's κ for two sequences of nominal labels.
    κ < 0: worse than chance | 0–0.2: slight | 0.2–0.4: fair |
    0.4–0.6: moderate | 0.6–0.8: substantial | 0.8–1.0: almost perfect.
    """
    n = len(labels_a)
    if n == 0 or len(labels_b) != n:
        return float("nan")
    all_labels = sorted(set(labels_a) | set(labels_b))
    p_o = sum(a == b for a, b in zip(labels_a, labels_b)) / n
    ca, cb = Counter(labels_a), Counter(labels_b)
    p_e = sum((ca[l] / n) * (cb[l] / n) for l in all_labels)
    return round((p_o - p_e) / (1 - p_e), 4) if p_e < 1.0 else 1.0


def kappa_interpretation(kappa: float) -> str:
    if math.isnan(kappa):
        return "n/a"
    if kappa < 0:
        return "poor (worse than chance)"
    if kappa < 0.20:
        return "slight"
    if kappa < 0.40:
        return "fair"
    if kappa < 0.60:
        return "moderate"
    if kappa < 0.80:
        return "substantial"
    return "almost perfect"


def per_class_kappa(labels_a: list[str], labels_b: list[str]) -> dict[str, float]:
    """Binary κ per class: class k vs. rest."""
    all_labels = sorted(set(labels_a) | set(labels_b))
    result = {}
    for lab in all_labels:
        bin_a = ["pos" if l == lab else "neg" for l in labels_a]
        bin_b = ["pos" if l == lab else "neg" for l in labels_b]
        result[lab] = cohen_kappa(bin_a, bin_b)
    return result


# ==========================================================
# V14. PRECISION / RECALL / F1 per class
# ==========================================================

def precision_recall_f1(
    y_true: list[str],
    y_pred: list[str],
    labels: list[str] | None = None,
) -> dict:
    """
    Per-class P, R, F1 + macro and weighted averages.
    y_true = gold standard labels, y_pred = system labels.
    """
    if labels is None:
        labels = sorted(set(y_true) | set(y_pred))

    tp: Counter = Counter()
    fp: Counter = Counter()
    fn: Counter = Counter()
    for t, p in zip(y_true, y_pred):
        if t == p:
            tp[t] += 1
        else:
            fp[p] += 1
            fn[t] += 1

    per_class = {}
    for lab in labels:
        prec = tp[lab] / (tp[lab] + fp[lab]) if (tp[lab] + fp[lab]) else 0.0
        rec  = tp[lab] / (tp[lab] + fn[lab]) if (tp[lab] + fn[lab]) else 0.0
        f1   = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        per_class[lab] = {
            "precision": round(prec, 4), "recall": round(rec, 4),
            "f1": round(f1, 4),
            "tp": tp[lab], "fp": fp[lab], "fn": fn[lab],
            "support": tp[lab] + fn[lab],
        }

    n_lab = len(labels)
    macro_p  = sum(per_class[l]["precision"] for l in labels) / n_lab if n_lab else 0.0
    macro_r  = sum(per_class[l]["recall"]    for l in labels) / n_lab if n_lab else 0.0
    macro_f1 = sum(per_class[l]["f1"]        for l in labels) / n_lab if n_lab else 0.0

    total_sup = sum(per_class[l]["support"] for l in labels) or 1
    w_p  = sum(per_class[l]["precision"] * per_class[l]["support"] for l in labels) / total_sup
    w_r  = sum(per_class[l]["recall"]    * per_class[l]["support"] for l in labels) / total_sup
    w_f1 = sum(per_class[l]["f1"]        * per_class[l]["support"] for l in labels) / total_sup

    return {
        "per_class":  per_class,
        "macro":      {"precision": round(macro_p, 4),  "recall": round(macro_r, 4),  "f1": round(macro_f1, 4)},
        "weighted":   {"precision": round(w_p, 4),      "recall": round(w_r, 4),      "f1": round(w_f1, 4)},
        "n_total":    len(y_true),
    }


def confusion_matrix(y_true: list[str], y_pred: list[str], labels: list[str]) -> dict:
    """
    Returns {true_label: {pred_label: count}} confusion matrix.
    Also returns top-N most common errors as (true, pred, count) list.
    """
    matrix: dict = defaultdict(Counter)
    for t, p in zip(y_true, y_pred):
        matrix[t][p] += 1

    errors = sorted(
        [(t, p, matrix[t][p]) for t in labels for p in labels if t != p and matrix[t][p] > 0],
        key=lambda x: -x[2],
    )
    return {"matrix": dict(matrix), "top_errors": errors[:20]}


# ==========================================================
# V15. GOLD STANDARD INFRASTRUCTURE
# ==========================================================

def load_gold_standard(path: Path = GOLD_STANDARD_PATH) -> list[dict]:
    """
    Load annotation CSV. Expected columns: sentence_id, file_name,
    system_label, human_label_1 (+ optional human_label_2).
    Returns [] when file does not exist.
    """
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return [r for r in rows if r.get("human_label_1", "").strip()]


def generate_annotation_template(
    sk_rows: list,
    output_path: Path = Path("data/annotation_template.csv"),
    n: int = GOLD_TEMPLATE_N,
) -> Path:
    """
    Create a stratified annotation template CSV for human labelling.
    Stratified by primary_intention so all classes are represented.
    system_label is pre-filled; human_label_1 / human_label_2 are blank.
    """
    by_label: dict = defaultdict(list)
    for r in sk_rows:
        by_label[r.get("primary_intention", "unclassified")].append(r)

    labels = sorted(by_label)
    per_cls = max(1, n // max(len(labels), 1))

    sample = []
    for lab in labels:
        pool = by_label[lab]
        sample.extend(random.sample(pool, min(per_cls, len(pool))))

    random.shuffle(sample)
    sample = sample[:n]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=GOLD_STANDARD_FIELDS)
        writer.writeheader()
        for r in sample:
            writer.writerow({
                "sentence_id":   r.get("sentence_id", ""),
                "file_name":     r.get("file_name", ""),
                "sentence":      r.get("sentence", r.get("locution", "")),
                "system_label":  r.get("primary_intention", ""),
                "human_label_1": "",
                "human_label_2": "",
                "notes":         "",
            })
    return output_path


def evaluate_against_gold(
    sk_rows: list,
    gold_rows: list,
) -> tuple[dict, dict | None]:
    """
    Match system rows to gold rows by (sentence_id, file_name).
    Returns (prf1_result, kappa_result_or_None).
    kappa_result is computed if human_label_2 is populated.
    """
    gold_lookup = {
        (r["sentence_id"], r["file_name"]): r
        for r in gold_rows
    }

    y_true, y_pred = [], []
    ann1, ann2 = [], []
    has_annotator2 = False

    for r in sk_rows:
        key = (r.get("sentence_id", ""), r.get("file_name", ""))
        if key not in gold_lookup:
            continue
        g = gold_lookup[key]
        y_pred.append(r.get("primary_intention", "").strip().lower())
        y_true.append(g["human_label_1"].strip().lower())
        ann1.append(g["human_label_1"].strip().lower())
        lab2 = g.get("human_label_2", "").strip().lower()
        if lab2:
            ann2.append(lab2)
            has_annotator2 = True
        else:
            ann2.append(g["human_label_1"].strip().lower())  # self-agreement

    if not y_true:
        return {}, None

    labels = sorted(set(y_true) | set(y_pred))
    prf1   = precision_recall_f1(y_true, y_pred, labels)
    prf1["confusion"] = confusion_matrix(y_true, y_pred, labels)

    # IAA (Cohen's κ between the two annotators)
    iaa = None
    if has_annotator2:
        kappa   = cohen_kappa(ann1, ann2)
        per_cls = per_class_kappa(ann1, ann2)
        iaa = {
            "kappa":         kappa,
            "interpretation": kappa_interpretation(kappa),
            "per_class":     per_cls,
            "n_items":       len(ann1),
        }

    return prf1, iaa


# ==========================================================
# V11. EXPORT HELPERS  (was V12 — keeping old section comment)
# ==========================================================

def _write_csv(rows: list, filename: str, fieldnames: list = None) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / filename
    if not rows:
        return path
    fields = fieldnames or list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return path


def _fmt_pct(n, total) -> str:
    if not total:
        return "n/a"
    return f"{100 * n / total:.1f}%"


# ==========================================================
# V13. REPORT BUILDER
# ==========================================================

def build_report(sk_rows: list, sk_source: str, ref_rows: list = None) -> str:
    lines: list = []
    W = 60

    def h1(title):
        lines.append("=" * W)
        lines.append(f"  {title}")
        lines.append("=" * W)

    def h2(title):
        lines.append("")
        lines.append(f"── {title} " + "─" * max(0, W - len(title) - 4))

    def row(k, v):
        lines.append(f"  {k:<30} {v}")

    # ── Header ────────────────────────────────────────────
    h1("SKINNER PIPELINE — QUALITY EVALUATION")
    lines.append(f"  Data source : {sk_source.upper()}")
    lines.append(f"  Total rows  : {len(sk_rows)}")

    ref_rows = ref_rows or []

    if not sk_rows:
        lines.append("")
        lines.append("  NO DATA AVAILABLE.")
        lines.append("  Run k_apply_all_to_bible.py first, then re-run this script.")
        return "\n".join(lines)

    # ── V3. Coverage ─────────────────────────────────────
    cov = coverage_stats(sk_rows)
    h2("COVERAGE (classified vs unknown)")
    row("Total sentences",      cov["total"])
    row("Classified",           f"{cov['classified']}  ({cov['coverage_pct']}%)")
    row("Unknown / unclassified", f"{cov['unknown']}  ({100 - cov['coverage_pct']:.1f}%)")
    lines.append("")
    lines.append(f"  {'Book':<30} {'Total':>6}  {'Classif.':>8}  {'Coverage':>9}")
    lines.append(f"  {'-'*30} {'------':>6}  {'--------':>8}  {'---------':>9}")
    for b in cov["by_book"]:
        lines.append(
            f"  {b['book']:<30} {b['total']:>6}  {b['classified']:>8}  {b['coverage_pct']:>8.1f}%"
        )

    # ── V4. Consistency ───────────────────────────────────
    cons = consistency_stats(sk_rows, ref_rows)
    h2("CONSISTENCY (same lemma → same class)")
    lines.append(f"  Source: {cons['source']}")
    lines.append("")
    row("Unique lemmas analysed",   cons["unique_lemmas"])
    row("Consistently classified",  f"{cons['consistent']}  ({cons['consistency_pct']}%)")
    row("Ambiguous lemmas",         cons["ambiguous"])
    if cons["top_ambiguous"]:
        lines.append("")
        lines.append("  Top ambiguous lemmas:")
        for lem, labs in cons["top_ambiguous"][:10]:
            lines.append(f"    {lem:<20}  →  {', '.join(labs)}")

    # ── V6. Class distribution ────────────────────────────
    dist = distribution_stats(sk_rows)
    h2("CLASS DISTRIBUTION")
    lines.append(f"  {'Class':<30} {'Count':>6}  {'%':>6}  note")
    lines.append(f"  {'-'*30} {'------':>6}  {'------':>6}  ----")
    for d in dist:
        note = "⚠ DOMINANT (>50%)" if d["dominant"] else ""
        lines.append(f"  {d['label']:<30} {d['count']:>6}  {d['pct']:>5.1f}%  {note}")

    # ── V7. Book comparison ───────────────────────────────
    book_stats, outliers, all_labels = book_comparison(sk_rows)
    h2("BOOK COMPARISON — OUTLIERS (|z| > 2)")
    if outliers:
        for o in sorted(outliers, key=lambda x: abs(x["z_score"]), reverse=True)[:15]:
            lines.append(
                f"  {o['book']:<25}  {o['label']:<20}  ratio={o['ratio']:.3f}  z={o['z_score']:+.2f}"
            )
    else:
        lines.append("  No significant outliers found.")

    # ── V8. Confidence ────────────────────────────────────
    conf_stats, bins = confidence_analysis(sk_rows)
    h2("CONFIDENCE ANALYSIS")
    lines.append(f"  {'Class':<30} {'Mean':>6}  {'Med':>6}  {'Min':>6}  {'Max':>6}  {'<0.5':>6}")
    lines.append(f"  {'-'*30} {'------':>6}  {'------':>6}  {'------':>6}  {'------':>6}  {'------':>6}")
    for label, s in conf_stats.items():
        lines.append(
            f"  {label:<30} {s['mean']:>6.3f}  {s['median']:>6.3f}"
            f"  {s['min']:>6.3f}  {s['max']:>6.3f}  {s['low_pct']:>5.1f}%"
        )
    lines.append("")
    n_total = len(sk_rows)
    lines.append("  Confidence bins (all classes):")
    for bin_name, count in bins.items():
        bar = "█" * min(40, count // max(1, n_total // 40))
        lines.append(f"    {bin_name}  {count:>5}  {bar}")

    # ── V9. Failures ──────────────────────────────────────
    fails = failure_stats(sk_rows, ref_rows)
    h2("FAILURE DETECTION")
    row("Low confidence (< 0.30)",   f"{fails['low_conf_count']}  ({fails['low_conf_pct']}%)")
    row("Unknown / unclassified",    fails["unknown_count"])
    row("  of which high-conf (≥0.5)",
        f"{fails['high_conf_unknown']}"
        + ("  ⚠ 'unknown' is likely a default label, not a real miss"
           if fails["high_conf_unknown"] > 0 else ""))
    row("Missing root_lemma (refined)", fails["no_lemma_count_ref"])
    if fails["top_unknown_locutions"]:
        lines.append("")
        lines.append("  Most common locution patterns in unknown class:")
        for loc, cnt in fails["top_unknown_locutions"]:
            lines.append(f"    {loc or '(empty)':<30}  {cnt}x")

    # ── V10. SQLite verification ──────────────────────────
    sv = sqlite_verification()
    h2("SQLITE UPGRADE VERIFICATION")
    row("DB path",    sv["db_path"])
    row("DB exists",  sv["db_exists"])
    lines.append("")
    lines.append("  Table counts:")
    lines.append(f"  {'Table':<28} {'DB rows':>8}  {'CSV rows':>10}  {'CSV path'}")
    lines.append(f"  {'-'*28} {'--------':>8}  {'----------':>10}  {'-'*30}")
    for table in [TABLE_SKINNER, TABLE_RELATIONS, TABLE_REFINED]:
        db_n   = sv["tables"][table]["rows"]
        db_n   = db_n if db_n is not None else "—"
        csv_n  = sv["legacy_csv"][table]["rows"]
        csv_n  = csv_n if csv_n is not None else "—"
        csv_p  = Path(sv["legacy_csv"][table]["path"]).name
        lines.append(f"  {table:<28} {str(db_n):>8}  {str(csv_n):>10}  {csv_p}")

    lines.append("")
    lines.append("  Run history per table:")
    for table, info in sv["tables"].items():
        actual_runs = info["runs"]
        count_label = f"{len(actual_runs)} run(s)" if actual_runs else "0 runs (pipeline not yet run with SQLite)"
        lines.append(f"    {table}: {count_label}")
        for r in actual_runs[-5:]:
            lines.append(f"      {r}")

    at = sv["append_test"]
    lines.append("")
    lines.append("  Append test (insert×1 → count, insert×2 → count):")
    lines.append(f"    After 1st insert : {at['after_insert']} row  (expected 1)")
    lines.append(f"    After 2nd insert : {at['after_insert2']} rows (expected 2)")
    status = "PASSED ✓" if at["passed"] else "FAILED ✗"
    lines.append(f"    Result           : {status}")

    # ── V12. Genre error analysis ────────────────────────────
    genre_rows = genre_error_analysis(sk_rows, "primary_intention")
    genre_sum  = genre_summary(genre_rows)
    h2("GENRE-AWARE ANALYSIS (primary_intention per genre)")
    lines.append(f"  {'Genre':<26} {'Total':>6}  {'Dominant label':<22}  {'Rate':>6}  {'Rhet%':>6}")
    lines.append(f"  {'-'*26} {'------':>6}  {'-'*22}  {'------':>6}  {'------':>6}")
    for g in genre_sum:
        lines.append(
            f"  {g['genre']:<26} {g['total']:>6}  "
            f"{g['dominant_label']:<22}  {g['dominant_rate']:>5.1%}  "
            f"{g['rhetorical_density']:>5.1%}"
        )

    # ── V15. Gold standard evaluation ────────────────────────
    gold_rows = load_gold_standard()
    h2("GOLD STANDARD EVALUATION")
    if not gold_rows:
        lines.append(f"  ⚠ No gold standard found at: {GOLD_STANDARD_PATH}")
        lines.append("  Generate annotation template:")
        lines.append("    python v_eval_pipeline.py --generate-template")
        lines.append("  Then fill human_label_1 (and optionally human_label_2),")
        lines.append("  save as data/annotated_q_intentions.csv, and re-run.")
    else:
        prf1, iaa = evaluate_against_gold(sk_rows, gold_rows)
        n_eval = prf1.get("n_total", 0)
        lines.append(f"  Gold standard: {len(gold_rows)} annotated items  "
                     f"(matched: {n_eval})")
        lines.append("")
        if prf1:
            m = prf1["macro"]
            w = prf1["weighted"]
            lines.append(f"  {'':30} {'P':>7}  {'R':>7}  {'F1':>7}  {'support':>8}")
            lines.append(f"  {'-'*30} {'-------':>7}  {'-------':>7}  {'-------':>7}  {'--------':>8}")
            for lab, s in sorted(prf1["per_class"].items()):
                lines.append(
                    f"  {lab:<30} {s['precision']:>7.4f}  {s['recall']:>7.4f}"
                    f"  {s['f1']:>7.4f}  {s['support']:>8}"
                )
            lines.append(f"  {'─'*60}")
            lines.append(
                f"  {'macro avg':<30} {m['precision']:>7.4f}  {m['recall']:>7.4f}  {m['f1']:>7.4f}")
            lines.append(
                f"  {'weighted avg':<30} {w['precision']:>7.4f}  {w['recall']:>7.4f}  {w['f1']:>7.4f}")

            top_errs = prf1.get("confusion", {}).get("top_errors", [])
            if top_errs:
                lines.append("")
                lines.append("  Top confusion pairs (true → predicted):")
                for t, p, n in top_errs[:8]:
                    lines.append(f"    {t:<24} → {p:<24}  {n}×")

        if iaa:
            lines.append("")
            lines.append(
                f"  IAA Cohen's κ = {iaa['kappa']}  [{iaa['interpretation']}]"
                f"  (n={iaa['n_items']})"
            )
            lines.append("  Per-class κ:")
            for lab, k in sorted(iaa["per_class"].items()):
                interp = kappa_interpretation(k)
                lines.append(f"    {lab:<28}  κ={k:>6.4f}  [{interp}]")

    lines.append("")
    lines.append("=" * W)
    return "\n".join(lines)


# ==========================================================
# V14. MAIN
# ==========================================================

def main():
    random.seed(42)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Load primary data
    sk_rows,  sk_source  = load_data(TABLE_SKINNER)
    ref_rows, _ref_source = load_data(TABLE_REFINED)

    print(f"Skinner source  : {sk_source}  ({len(sk_rows)} rows)")
    print(f"Refined source  : {_ref_source}  ({len(ref_rows)} rows)")

    # ── Text report ───────────────────────────────────────
    report = build_report(sk_rows, sk_source, ref_rows)
    report_path = OUTPUT_DIR / "pipeline_report.txt"
    report_path.write_text(report, encoding="utf-8")
    print(report)

    if not sk_rows:
        return

    # ── CSV exports ───────────────────────────────────────

    # Coverage per book
    cov = coverage_stats(sk_rows)
    _write_csv(cov["by_book"], "coverage_by_book.csv",
               ["book", "total", "classified", "coverage_pct"])

    # Class distribution
    dist = distribution_stats(sk_rows)
    _write_csv(dist, "class_distribution.csv",
               ["label", "count", "pct", "dominant"])

    # Book comparison (wide format)
    book_stats, outliers, all_labels = book_comparison(sk_rows)
    book_rows = []
    for book, info in sorted(book_stats.items()):
        row_d = {"book": book, "total": info["total"]}
        for lab in all_labels:
            row_d[lab] = info["ratios"][lab]
        book_rows.append(row_d)
    _write_csv(book_rows, "book_comparison.csv",
               ["book", "total"] + all_labels)

    _write_csv(outliers, "book_outliers.csv",
               ["book", "label", "ratio", "z_score"])

    # Confidence per class
    conf_stats, _ = confidence_analysis(sk_rows)
    conf_rows = [{"label": lab, **s} for lab, s in conf_stats.items()]
    _write_csv(conf_rows, "confidence_by_class.csv",
               ["label", "n", "mean", "median", "min", "max", "low_pct"])

    # Lexicon coverage (using illocutionary_force labels, lemmas from refined)
    lex_source = ref_rows if ref_rows else sk_rows
    lex_label_field = LABEL_FIELD if not ref_rows else "description_type"
    lex = lexicon_coverage(lex_source if ref_rows else sk_rows)
    lex_rows = []
    for label, top in lex.items():
        for rank, (lemma, count) in enumerate(top, 1):
            lex_rows.append({"label": label, "rank": rank,
                             "lemma": lemma, "count": count})
    _write_csv(lex_rows, "lexicon_by_class.csv",
               ["label", "rank", "lemma", "count"])

    # Random sample for manual inspection
    sample = random_sample(sk_rows)
    sample_fields = ["file_name", LABEL_FIELD, "primary_intention",
                     "confidence", "locution", "sentence"]
    _write_csv(sample, "random_sample.csv", sample_fields)

    # Consistency (ambiguous lemmas)
    cons = consistency_stats(sk_rows, ref_rows)
    amb_rows = [{"lemma": lem, "labels": "|".join(labs), "n_labels": len(labs)}
                for lem, labs in cons["top_ambiguous"]]
    _write_csv(amb_rows, "ambiguous_lemmas.csv",
               ["lemma", "labels", "n_labels"])

    # Genre error analysis
    genre_rows = genre_error_analysis(sk_rows, "primary_intention")
    _write_csv(genre_rows, "genre_distribution.csv",
               ["genre", "label", "count", "total_in_genre", "rate"])
    genre_sum = genre_summary(genre_rows)
    _write_csv(genre_sum, "genre_summary.csv",
               ["genre", "total", "dominant_label", "dominant_rate", "rhetorical_density"])

    # Gold standard evaluation (if available)
    gold_rows = load_gold_standard()
    if gold_rows:
        prf1, iaa = evaluate_against_gold(sk_rows, gold_rows)
        if prf1 and "per_class" in prf1:
            prf1_rows = [
                {"label": lab, **s}
                for lab, s in prf1["per_class"].items()
            ]
            prf1_rows.append({"label": "macro",    **prf1["macro"],    "support": ""})
            prf1_rows.append({"label": "weighted", **prf1["weighted"], "support": ""})
            _write_csv(prf1_rows, "precision_recall_f1.csv",
                       ["label", "precision", "recall", "f1", "tp", "fp", "fn", "support"])
        if iaa:
            kappa_rows = [
                {"label": lab, "kappa": k, "interpretation": kappa_interpretation(k)}
                for lab, k in iaa["per_class"].items()
            ]
            kappa_rows.insert(0, {
                "label": "_overall",
                "kappa": iaa["kappa"],
                "interpretation": iaa["interpretation"],
            })
            _write_csv(kappa_rows, "cohen_kappa_per_class.csv",
                       ["label", "kappa", "interpretation"])
    else:
        print(f"\nNo gold standard → skipping P/R/F1 + κ export.")
        print(f"  Run: python v_eval_pipeline.py --generate-template")

    print(f"\nCSVs written to  {OUTPUT_DIR}/")
    print(f"Report written to {report_path}")


if __name__ == "__main__":
    import sys
    if "--generate-template" in sys.argv:
        random.seed(42)
        sk_rows, _ = load_data(TABLE_SKINNER)
        if not sk_rows:
            print("No data — run k_apply_all_to_bible.py first.")
            sys.exit(1)
        path = generate_annotation_template(sk_rows)
        print(f"Annotation template written: {path}")
        print(f"Fill in 'human_label_1' (and optionally 'human_label_2'),")
        print(f"save as {GOLD_STANDARD_PATH}, then re-run v_eval_pipeline.py")
        print(f"(Note: data/annotated_skinner.csv is reserved for h_classifiers.py — B.F. Skinner proxy_subtype annotation)")
    else:
        main()
