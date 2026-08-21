from pathlib import Path
import csv
import re
from collections import Counter, defaultdict

from t_config_tradition import (
    get_active_elements,
    detect_tradition,
    detect_tradition_from_lemmas,
    PHILOSOPHICAL_INFLUENCES,
    BKR_PHILOSOPHICAL_INFLUENCES,
    SHARED_MOTIFS,
    TRADITION_DIAGNOSTIC,
    canonicalize_lemma,
    field_hits,
    motif_hits,
    lexicon_hits,
)
from a_paths import OUTPUT_DIR as ROOT_OUTPUT
from n_db import load_rows as _db_load, TABLE_REFINED


OUTPUT_DIR = ROOT_OUTPUT / "religious_elements"

TRADITION = "christian_czech"


# ==========================================================
# LOAD
# ==========================================================

def load_rows():
    return _db_load(TABLE_REFINED)


def get_lemma_list(row):
    return [canonicalize_lemma(w) for w in row.get("lemmas", "").split() if w]


def get_lemmas(row):
    return set(get_lemma_list(row))


# ==========================================================
# SYNTAKTICKÁ ROLA — váhovanie podľa pozície/dep_tree
# ==========================================================

def _parse_dep_roles(dep_tree: str) -> tuple[set, set]:
    """
    Parse nsubj and obj lemmas from dep_tree string.
    Format: "root(nsubj:lemma, obj:lemma, obl:lemma, ...)"
    Returns (nsubj_set, obj_set).
    Used when dep_tree is available in the row (future schema).
    """
    nsubj = set(re.findall(r'nsubj[^:]*:\s*(\w+)', dep_tree))
    obj   = set(re.findall(r'\bobj:\s*(\w+)', dep_tree))
    return nsubj, obj


def _role_weight_position(lemma: str, lemma_list: list[str]) -> float:
    """
    Position-based heuristic for syntactic role in BKR Czech (SVO order).
    First third of lemmas → likely subject zone (agent, actor): 1.3×
    Last third             → likely object/adverbial zone: 0.8×
    Middle                 → neutral: 1.0×

    This is a fallback for rows where dep_tree is unavailable.
    """
    n = len(lemma_list)
    if n == 0:
        return 1.0
    try:
        pos = lemma_list.index(lemma)
    except ValueError:
        return 1.0
    if pos < n // 3:
        return 1.3
    if pos > 2 * (n // 3):
        return 0.8
    return 1.0


_ROLE_WEIGHT_COUNTER = {"dep_tree": 0, "positional": 0}
# Debug counters consumed by _analysis_new_run.py after a full-Bible run.


def _role_weight(lemma: str, row: dict) -> float:
    """
    Returns syntactic-role weight for a lemma in a given row.
    Uses dep_tree if available, else position heuristic.
    Subject: 1.3–1.5×, Object: 0.7–0.8×, Other: 1.0×
    """
    dep_tree = row.get("dep_tree", "")
    if dep_tree:
        _ROLE_WEIGHT_COUNTER["dep_tree"] += 1
        nsubj, obj = _parse_dep_roles(dep_tree)
        if lemma in nsubj:
            return 1.5
        if lemma in obj:
            return 0.7
        return 1.0
    # Fallback: position heuristic
    _ROLE_WEIGHT_COUNTER["positional"] += 1
    lemma_list = get_lemma_list(row)
    return _role_weight_position(lemma, lemma_list)


# ==========================================================
# 3. DENSITY ANALYSIS per kniha
# ==========================================================

def compute_density_by_book(rows, active_elements):

    by_book = defaultdict(lambda: defaultdict(lambda: {
        "matched_sentences": 0,
        "matched_lemmas":    0,
        "total_sentences":   0,
        "total_lemmas":      0,
        "role_score":        0.0,
        "top_words":         Counter(),
    }))

    for row in rows:
        fname  = row["file_name"]
        lemmas = get_lemmas(row)

        for element_name, lexicon in active_elements.items():
            hits = field_hits(lemmas, element_name, lexicon)
            s    = by_book[fname][element_name]
            s["total_sentences"] += 1
            s["total_lemmas"]    += len(lemmas)
            s["matched_lemmas"]  += len(hits)
            s["top_words"].update(hits)
            if hits:
                s["matched_sentences"] += 1
                # Role-weighted score: subject hits count more, object hits less
                s["role_score"] += sum(_role_weight(h, row) for h in hits)

    out_rows = []
    for fname in sorted(by_book):
        for element_name, s in sorted(by_book[fname].items()):
            total_l = s["total_lemmas"]
            total_s = s["total_sentences"]
            out_rows.append({
                "file_name":            fname,
                "element":              element_name,
                "matched_sentences":    s["matched_sentences"],
                "sentence_count":       total_s,
                "sentence_density":     round(
                    s["matched_sentences"] / total_s, 5
                ) if total_s else 0.0,
                "matched_lemmas":       s["matched_lemmas"],
                "total_lemmas":         total_l,
                "token_density":        round(
                    s["matched_lemmas"] / total_l, 5
                ) if total_l else 0.0,
                "role_weighted_score":  round(s["role_score"], 3),
                "role_weighted_density": round(
                    s["role_score"] / total_s, 5
                ) if total_s else 0.0,
                "top_words": "; ".join(
                    f"{w}:{n}"
                    for w, n in s["top_words"].most_common(10)
                ),
            })

    return out_rows


# ==========================================================
# 4. FIELD ANALYSIS per veta
# ==========================================================

def compute_fields_by_sentence(rows, active_elements):

    sentence_rows = []
    summary       = Counter()
    books_per_el  = defaultdict(set)
    examples      = defaultdict(list)

    for row in rows:
        lemmas    = get_lemmas(row)
        matched   = {}

        for element_name, lexicon in active_elements.items():
            hits = field_hits(lemmas, element_name, lexicon)
            if hits:
                matched[element_name] = hits

        if matched:
            sentence_rows.append({
                "sentence_id": row["sentence_id"],
                "file_name":   row["file_name"],
                "elements":    "; ".join(sorted(matched.keys())),
                "matched_words": "; ".join(
                    sorted(w for hits in matched.values() for w in hits)
                ),
                "sentence":    row["sentence"],
            })

            for element_name, hits in matched.items():
                summary[element_name] += 1
                books_per_el[element_name].add(row["file_name"])
                if len(examples[element_name]) < 20:
                    examples[element_name].append({
                        "element":       element_name,
                        "matched_words": "; ".join(sorted(hits)),
                        "sentence":      row["sentence"],
                        "file_name":     row["file_name"],
                    })

    summary_rows = [
        {
            "element":        el,
            "sentence_count": count,
            "book_count":     len(books_per_el[el]),
        }
        for el, count in summary.most_common()
    ]

    example_rows = [
        ex
        for el in summary
        for ex in examples[el]
    ]

    return sentence_rows, summary_rows, example_rows


# ==========================================================
# 5. PHILOSOPHICAL INFLUENCE DETECTION per kniha
# ==========================================================

def compute_philosophy_by_book(rows, bkr_filter: bool = True):
    """
    Detect distinctive philosophical lexicon hits per book.

    Only high-precision terms count (gnóze, platón, akáša, nirvána…).
    Polyvalent biblical words (světlo, duše, tajemství) are tracked
    separately as shared motifs — they are not evidence of Platonism
    or Gnosticism in the Bible.

    bkr_filter=True (default): BKR_PHILOSOPHICAL_INFLUENCES (distinctive
    terms only; expected empty on Kralická Bible).
    bkr_filter=False: full PHILOSOPHICAL_INFLUENCES for uploaded texts.
    """
    lexicons = BKR_PHILOSOPHICAL_INFLUENCES if bkr_filter else PHILOSOPHICAL_INFLUENCES

    by_book = defaultdict(lambda: defaultdict(lambda: {
        "matched_count": 0,
        "top_words":     Counter(),
    }))

    for row in rows:
        fname  = row["file_name"]
        lemmas = get_lemmas(row)

        for phil_name, lexicon in lexicons.items():
            if not lexicon:
                continue
            hits = lexicon_hits(lemmas, lexicon)
            if hits:
                by_book[fname][phil_name]["matched_count"] += 1
                by_book[fname][phil_name]["top_words"].update(hits)

    out_rows = []
    for fname in sorted(by_book):
        for phil_name, s in sorted(by_book[fname].items()):
            if s["matched_count"] == 0:
                continue
            out_rows.append({
                "file_name":     fname,
                "philosophy":    phil_name,
                "matched_count": s["matched_count"],
                "bkr_filter":    bkr_filter,
                "hit_kind":      "distinctive",
                "top_words":     "; ".join(
                    f"{w}:{n}"
                    for w, n in s["top_words"].most_common(5)
                ),
            })

    return out_rows


def compute_shared_motifs_by_book(rows):
    """
    Polyvalent motifs that exist in the Bible and were later reused
    by other traditions.  These are NOT tradition attributions.
    """
    by_book = defaultdict(lambda: defaultdict(lambda: {
        "matched_count": 0,
        "top_words":     Counter(),
    }))

    for row in rows:
        fname  = row["file_name"]
        lemmas = get_lemmas(row)
        for motif_name, meta in SHARED_MOTIFS.items():
            hits = motif_hits(lemmas, meta)
            if hits:
                by_book[fname][motif_name]["matched_count"] += 1
                by_book[fname][motif_name]["top_words"].update(hits)

    out_rows = []
    for fname in sorted(by_book):
        for motif_name, s in sorted(by_book[fname].items()):
            if s["matched_count"] == 0:
                continue
            meta = SHARED_MOTIFS[motif_name]
            out_rows.append({
                "file_name":         fname,
                "motif":             motif_name,
                "matched_count":     s["matched_count"],
                "hit_kind":          "shared_polyvalent",
                "biblical_home":     meta["biblical_home"],
                "later_traditions":  "; ".join(meta["later_traditions"]),
                "top_words":         "; ".join(
                    f"{w}:{n}"
                    for w, n in s["top_words"].most_common(5)
                ),
            })
    return out_rows


def compute_tradition_diagnostics_by_book(rows):
    """
    High-precision tradition identifiers (buddha, akáša, alláh, sefírot…).
    On a Christian Bible corpus this should be empty or nearly empty,
    except for YHWH names (hospodin) and NT christological terms (kristus).
    """
    by_book = defaultdict(lambda: defaultdict(lambda: {
        "matched_count": 0,
        "top_words":     Counter(),
    }))

    for row in rows:
        fname  = row["file_name"]
        lemmas = get_lemmas(row)
        for trad_name, lexicon in TRADITION_DIAGNOSTIC.items():
            hits = lexicon_hits(lemmas, lexicon)
            if hits:
                by_book[fname][trad_name]["matched_count"] += 1
                by_book[fname][trad_name]["top_words"].update(hits)

    out_rows = []
    for fname in sorted(by_book):
        for trad_name, s in sorted(by_book[fname].items()):
            if s["matched_count"] == 0:
                continue
            out_rows.append({
                "file_name":     fname,
                "tradition":     trad_name,
                "matched_count": s["matched_count"],
                "hit_kind":      "distinctive",
                "top_words":     "; ".join(
                    f"{w}:{n}"
                    for w, n in s["top_words"].most_common(5)
                ),
            })
    return out_rows


# ==========================================================
# EXPORT
# ==========================================================

def _write_csv(rows, path, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def export_wide_pivot(density_rows):
    by_book = defaultdict(dict)
    for row in density_rows:
        by_book[row["file_name"]][row["element"]] = row["matched_sentences"]

    all_elements = sorted({row["element"] for row in density_rows})

    out_rows = []
    for fname in sorted(by_book):
        counts  = by_book[fname]
        out_row = {"file_name": fname}
        for el in all_elements:
            out_row[el] = counts.get(el, 0)
        out_row["total_field_hits"] = sum(counts.values())
        out_rows.append(out_row)

    _write_csv(
        out_rows,
        OUTPUT_DIR / "fields_by_book_wide.csv",
        ["file_name", *all_elements, "total_field_hits"],
    )


def export_combined_density(density_rows):
    by_book = defaultdict(dict)
    for row in density_rows:
        el = row["element"]
        by_book[row["file_name"]][f"{el}_token_density"]    = row["token_density"]
        by_book[row["file_name"]][f"{el}_sentence_density"] = row["sentence_density"]

    all_elements = sorted({row["element"] for row in density_rows})

    fieldnames = ["file_name"]
    for el in all_elements:
        fieldnames += [f"{el}_token_density", f"{el}_sentence_density"]

    out_rows = []
    for fname in sorted(by_book):
        out_row = {"file_name": fname, **by_book[fname]}
        out_rows.append(out_row)

    _write_csv(
        out_rows,
        OUTPUT_DIR / "combined_density_by_book.csv",
        fieldnames,
    )


def export_all(density_rows, sentence_rows,
               summary_rows, example_rows, phil_rows,
               shared_rows=None, diagnostic_rows=None):

    _write_csv(
        density_rows,
        OUTPUT_DIR / "density_by_book.csv",
        ["file_name", "element", "matched_sentences", "sentence_count",
         "sentence_density", "matched_lemmas", "total_lemmas", "token_density",
         "role_weighted_score", "role_weighted_density", "top_words"],
    )

    _write_csv(
        sentence_rows,
        OUTPUT_DIR / "fields_by_sentence.csv",
        ["sentence_id", "file_name", "elements", "matched_words", "sentence"],
    )

    _write_csv(
        summary_rows,
        OUTPUT_DIR / "field_summary.csv",
        ["element", "sentence_count", "book_count"],
    )

    _write_csv(
        example_rows,
        OUTPUT_DIR / "field_examples.csv",
        ["element", "matched_words", "sentence", "file_name"],
    )

    _write_csv(
        phil_rows,
        OUTPUT_DIR / "philosophy_by_book.csv",
        ["file_name", "philosophy", "matched_count", "bkr_filter",
         "hit_kind", "top_words"],
    )

    _write_csv(
        shared_rows or [],
        OUTPUT_DIR / "shared_motifs_by_book.csv",
        ["file_name", "motif", "matched_count", "hit_kind",
         "biblical_home", "later_traditions", "top_words"],
    )

    _write_csv(
        diagnostic_rows or [],
        OUTPUT_DIR / "tradition_diagnostics_by_book.csv",
        ["file_name", "tradition", "matched_count", "hit_kind", "top_words"],
    )

    catalog_rows = [
        {
            "motif":            name,
            "biblical_home":    meta["biblical_home"],
            "later_traditions": "; ".join(meta["later_traditions"]),
            "lemmas":           "; ".join(sorted(meta["lemmas"])),
        }
        for name, meta in SHARED_MOTIFS.items()
    ]
    _write_csv(
        catalog_rows,
        OUTPUT_DIR / "shared_motifs_catalog.csv",
        ["motif", "biblical_home", "later_traditions", "lemmas"],
    )

    export_wide_pivot(density_rows)
    export_combined_density(density_rows)


# ==========================================================
# MAIN
# ==========================================================

def main(tradition=TRADITION):

    rows = load_rows()
    print(f"Loaded rows: {len(rows)}")

    active_elements = get_active_elements(tradition)
    print(f"Tradition:   {tradition}")
    print(f"Elements:    {sorted(active_elements.keys())}")

    density_rows = compute_density_by_book(rows, active_elements)

    element_totals = {}
    for r in density_rows:
        el = r["element"]
        element_totals[el] = element_totals.get(el, 0) + r["matched_sentences"]
    detected = detect_tradition(element_totals)
    print(f"Detekovaná tradícia: {detected}")

    sentence_rows, summary_rows, example_rows = compute_fields_by_sentence(
        rows, active_elements
    )

    phil_rows = compute_philosophy_by_book(rows)
    shared_rows = compute_shared_motifs_by_book(rows)
    diagnostic_rows = compute_tradition_diagnostics_by_book(rows)

    lemma_counts = Counter()
    for row in rows:
        lemma_counts.update(get_lemmas(row))
    detected_from_lemmas = detect_tradition_from_lemmas(lemma_counts)
    print(f"Detekovaná tradícia (diagnostické lemy): {detected_from_lemmas}")

    export_all(
        density_rows, sentence_rows,
        summary_rows, example_rows, phil_rows,
        shared_rows=shared_rows,
        diagnostic_rows=diagnostic_rows,
    )

    # ── top 3 elementy per kniha ──────────────────────────
    print(f"\nTop 3 elementy per kniha (sentence_density):")
    top_by_book = defaultdict(list)
    for r in density_rows:
        top_by_book[r["file_name"]].append(
            (r["element"], r["sentence_density"])
        )

    for fname in sorted(top_by_book):
        book  = fname.replace("bible_BKR_", "").replace(".txt", "")
        top3  = sorted(
            top_by_book[fname], key=lambda x: -x[1]
        )[:3]
        parts = "  ".join(
            f"{el}={d:.3f}" for el, d in top3
        )
        print(f"  {book:<6} {parts}")

    # ── filozofické vplyvy (len diagnostické termíny) ─────
    phil_detected = sorted({r["philosophy"] for r in phil_rows})
    print(f"\nDiagnostické filozofické vplyvy ({len(phil_detected)}):")
    if not phil_rows:
        print("  (žiadne — očakávané pri biblickom korpuse)")
    phil_totals = Counter()
    for r in phil_rows:
        phil_totals[r["philosophy"]] += r["matched_count"]
    for phil, total in phil_totals.most_common():
        print(f"  {phil:<20} {total:>6} matched sentences")

    shared_totals = Counter()
    for r in shared_rows:
        shared_totals[r["motif"]] += r["matched_count"]
    print(f"\nZdieľané / polyvalentné motívy ({len(shared_totals)}):")
    for motif, total in shared_totals.most_common():
        later = SHARED_MOTIFS[motif]["later_traditions"]
        print(f"  {motif:<22} {total:>6}  (neskôr aj: {', '.join(later)})")

    diag_totals = Counter()
    for r in diagnostic_rows:
        diag_totals[r["tradition"]] += r["matched_count"]
    print(f"\nDiagnostické tradície ({len(diag_totals)}):")
    if not diag_totals:
        print("  (žiadne cudzie diagnostické termíny)")
    for trad, total in diag_totals.most_common():
        print(f"  {trad:<20} {total:>6} matched sentences")

    print(f"\nDONE — Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
