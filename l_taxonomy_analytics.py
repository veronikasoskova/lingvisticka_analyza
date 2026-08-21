from pathlib import Path
import csv
import math
from collections import Counter, defaultdict

from a_paths import OUTPUT_DIR as ROOT_OUTPUT
from b_analytics_utils import export_counter, export_rows
from n_db import load_rows as _db_load, TABLE_SKINNER, TABLE_REFINED


OUTPUT_DIR   = ROOT_OUTPUT / "taxonomy_analytics"
Q_OUTPUT_DIR = ROOT_OUTPUT / "q_skinner_analytics"


# ==========================================================
# K1. LOAD
# ==========================================================

def load_rows():
    return _db_load(TABLE_SKINNER)


# ==========================================================
# K3. GLOBAL OVERVIEWS
# ==========================================================

# DISCONNECTED: needs remapping to q_skinner_bible_analysis.csv schema
# def skinner_class_overview(rows):
#
#     export_counter(
#         Counter(r["skinner_class"] for r in rows),
#         OUTPUT_DIR / "skinner_class_counts.csv",
#         "skinner_class",
#     )


# DISCONNECTED: needs remapping to q_skinner_bible_analysis.csv schema
# def proxy_subtype_overview(rows):
#
#     export_counter(
#         Counter(r["proxy_subtype"] for r in rows),
#         OUTPUT_DIR / "proxy_subtype_counts.csv",
#         "proxy_subtype",
#     )


# DISCONNECTED: needs remapping to q_skinner_bible_analysis.csv schema
# def control_role_overview(rows):
#
#     export_counter(
#         Counter(r["control_role"] for r in rows),
#         OUTPUT_DIR / "control_role_counts.csv",
#         "control_role",
#     )


# ==========================================================
# K4. PER-BOOK: skinner_class distribution
# ==========================================================

# DISCONNECTED: needs remapping to q_skinner_bible_analysis.csv schema
# def skinner_class_by_book(rows):
#
#     counts = defaultdict(Counter)
#     for r in rows:
#         counts[r["file_name"]][r["skinner_class"]] += 1
#
#     all_classes = sorted({r["skinner_class"] for r in rows})
#
#     out_rows = []
#     for file_name, counter in sorted(counts.items()):
#         total = sum(counter.values())
#         out_rows.append({
#             "file_name": file_name,
#             **{c: counter.get(c, 0) for c in all_classes},
#             "total": total,
#         })
#
#     export_rows(
#         out_rows,
#         OUTPUT_DIR / "skinner_class_by_book.csv",
#         ["file_name", *all_classes, "total"],
#     )


# ==========================================================
# K5. PER-BOOK: proxy_subtype distribution
# ==========================================================

# DISCONNECTED: needs remapping to q_skinner_bible_analysis.csv schema
# def proxy_subtype_by_book(rows):
#
#     counts = defaultdict(Counter)
#     for r in rows:
#         counts[r["file_name"]][r["proxy_subtype"]] += 1
#
#     all_subtypes = sorted({r["proxy_subtype"] for r in rows})
#
#     out_rows = []
#     for file_name, counter in sorted(counts.items()):
#         total = sum(counter.values())
#         out_rows.append({
#             "file_name": file_name,
#             **{s: counter.get(s, 0) for s in all_subtypes},
#             "total": total,
#         })
#
#     export_rows(
#         out_rows,
#         OUTPUT_DIR / "proxy_subtype_by_book.csv",
#         ["file_name", *all_subtypes, "total"],
#     )


# ==========================================================
# K6. PER-BOOK: control_role ratio
# ==========================================================

# DISCONNECTED: needs remapping to q_skinner_bible_analysis.csv schema
# def control_role_by_book(rows):
#
#     counts = defaultdict(Counter)
#     for r in rows:
#         counts[r["file_name"]][r["control_role"]] += 1
#
#     roles = ["response", "stimulus", "record"]
#
#     out_rows = []
#     for file_name, counter in sorted(counts.items()):
#         total = sum(counter.values())
#         row = {"file_name": file_name, "total": total}
#         for role in roles:
#             n = counter.get(role, 0)
#             row[role] = n
#             row[f"{role}_ratio"] = round(n / total, 3) if total else 0.0
#         out_rows.append(row)
#
#     export_rows(
#         out_rows,
#         OUTPUT_DIR / "control_role_by_book.csv",
#         ["file_name", *roles, *[f"{r}_ratio" for r in roles], "total"],
#     )


# ==========================================================
# K7. PER-BOOK: dialogická hustota
#     (intraverbal sentences / total)
# ==========================================================

def dialogue_density_by_book(rows):
    # "directive" illocutionary force = addressed/dialogic speech;
    # replaces old proxy_subtype intraverbal/dialogue_chain check.
    totals   = Counter()
    dialogue = Counter()

    for r in rows:
        book = r["file_name"]
        totals[book] += 1
        if r.get("illocutionary_force") == "directive":
            dialogue[book] += 1

    out_rows = []
    for book in sorted(totals):
        total = totals[book]
        d = dialogue[book]
        out_rows.append({
            "file_name":        book,
            "dialogue_sentences": d,
            "total":            total,
            "dialogue_density": round(d / total, 3) if total else 0.0,
        })

    export_rows(
        out_rows,
        OUTPUT_DIR / "dialogue_density_by_book.csv",
        ["file_name", "dialogue_sentences", "total", "dialogue_density"],
    )


# ==========================================================
# K8. PER-BOOK: tact vs autoclitic pomer
# ==========================================================

def tact_vs_autoclitic_by_book(rows):
    # New schema mapping:
    #   tact      → illocutionary_force == "assertive"  (describes/reports reality)
    #   autoclitic → illocutionary_force == "declarative" (modifies verbal context)
    totals = Counter()
    tact_n = Counter()
    auto_n = Counter()

    for r in rows:
        book  = r["file_name"]
        force = r.get("illocutionary_force", "")
        totals[book] += 1
        if force == "assertive":
            tact_n[book] += 1
        elif force == "declarative":
            auto_n[book] += 1

    out_rows = []
    for book in sorted(totals):
        total     = totals[book]
        t         = tact_n[book]
        a         = auto_n[book]
        denominator = t + a
        out_rows.append({
            "file_name":          book,
            "tact":               t,
            "autoclitic":         a,
            "tact_ratio":         round(t / total,       3) if total       else 0.0,
            "autoclitic_ratio":   round(a / total,       3) if total       else 0.0,
            "tact_vs_autoclitic": round(t / denominator, 3) if denominator else None,
            "total":              total,
        })

    export_rows(
        out_rows,
        OUTPUT_DIR / "tact_vs_autoclitic_by_book.csv",
        [
            "file_name", "tact", "autoclitic",
            "tact_ratio", "autoclitic_ratio",
            "tact_vs_autoclitic", "total",
        ],
    )


# ==========================================================
# K9. PER-BOOK: confidence distribúcia
# ==========================================================

def confidence_by_book(rows):

    values = defaultdict(list)
    for r in rows:
        values[r["file_name"]].append(float(r["confidence"]))

    out_rows = []
    for book in sorted(values):
        vs = values[book]
        out_rows.append({
            "file_name": book,
            "count": len(vs),
            "avg_confidence": round(sum(vs) / len(vs), 3),
            "min_confidence": min(vs),
            "max_confidence": max(vs),
        })

    export_rows(
        out_rows,
        OUTPUT_DIR / "confidence_by_book.csv",
        ["file_name", "count", "avg_confidence", "min_confidence", "max_confidence"],
    )


# DISCONNECTED: needs remapping to q_skinner_bible_analysis.csv schema
# def confidence_by_class(rows):
#
#     values = defaultdict(list)
#     for r in rows:
#         values[r["skinner_class"]].append(float(r["confidence"]))
#
#     out_rows = []
#     for cls in sorted(values):
#         vs = values[cls]
#         out_rows.append({
#             "skinner_class": cls,
#             "count": len(vs),
#             "avg_confidence": round(sum(vs) / len(vs), 3),
#             "min_confidence": min(vs),
#             "max_confidence": max(vs),
#         })
#
#     export_rows(
#         out_rows,
#         OUTPUT_DIR / "confidence_by_class.csv",
#         ["skinner_class", "count", "avg_confidence", "min_confidence", "max_confidence"],
#     )


# ==========================================================
# K11. LOAD Q. SKINNER
# ==========================================================

def load_q_rows():
    return _db_load(TABLE_SKINNER)


# ==========================================================
# K12. Q. SKINNER GLOBAL OVERVIEWS
# ==========================================================

def q_intention_overview(rows):

    export_counter(
        Counter(r["primary_intention"] for r in rows),
        Q_OUTPUT_DIR / "q_intention_counts.csv",
        "primary_intention",
    )


def q_illocutionary_force_overview(rows):

    export_counter(
        Counter(r["illocutionary_force"] for r in rows),
        Q_OUTPUT_DIR / "q_illocutionary_force_counts.csv",
        "illocutionary_force",
    )


def q_strategy_overview(rows):

    export_counter(
        Counter(r["primary_strategy"] for r in rows),
        Q_OUTPUT_DIR / "q_strategy_counts.csv",
        "primary_strategy",
    )


# ==========================================================
# K13. Q. SKINNER PER-BOOK
# ==========================================================

def _per_book_wide(rows, field, output_path, key_name):
    counts = defaultdict(Counter)
    for r in rows:
        counts[r["file_name"]][r[field]] += 1

    all_values = sorted({r[field] for r in rows})

    out_rows = []
    for file_name, counter in sorted(counts.items()):
        total = sum(counter.values())
        out_rows.append({
            "file_name": file_name,
            **{v: counter.get(v, 0) for v in all_values},
            "total": total,
        })

    export_rows(out_rows, output_path, ["file_name", *all_values, "total"])


def q_intention_by_book(rows):
    _per_book_wide(
        rows, "primary_intention",
        Q_OUTPUT_DIR / "q_intention_by_book.csv",
        "primary_intention",
    )


def q_illocutionary_force_by_book(rows):
    _per_book_wide(
        rows, "illocutionary_force",
        Q_OUTPUT_DIR / "q_illocutionary_force_by_book.csv",
        "illocutionary_force",
    )


def q_strategy_by_book(rows):
    _per_book_wide(
        rows, "primary_strategy",
        Q_OUTPUT_DIR / "q_strategy_by_book.csv",
        "primary_strategy",
    )


# ==========================================================
# K13a. NORMALIZOVANÉ SADZBY PER KNIHA (rate = count / total)
# ==========================================================

def _per_book_normalized(rows, field, output_path):
    counts = defaultdict(Counter)
    for r in rows:
        counts[r["file_name"]][r[field]] += 1

    all_values = sorted({r[field] for r in rows})

    out_rows = []
    for file_name, counter in sorted(counts.items()):
        total = sum(counter.values())
        row = {"file_name": file_name, "total": total}
        for v in all_values:
            n = counter.get(v, 0)
            row[v] = n
            row[f"{v}_rate"] = round(n / total, 4) if total else 0.0
        out_rows.append(row)

    export_rows(
        out_rows,
        output_path,
        ["file_name", "total", *all_values, *[f"{v}_rate" for v in all_values]],
    )


def q_intention_rates_by_book(rows):
    _per_book_normalized(
        rows, "primary_intention",
        Q_OUTPUT_DIR / "q_intention_rates_by_book.csv",
    )


def q_force_rates_by_book(rows):
    _per_book_normalized(
        rows, "illocutionary_force",
        Q_OUTPUT_DIR / "q_force_rates_by_book.csv",
    )


def q_strategy_rates_by_book(rows):
    _per_book_normalized(
        rows, "primary_strategy",
        Q_OUTPUT_DIR / "q_strategy_rates_by_book.csv",
    )


def q_convention_rates_by_book(rows):
    if not any(r.get("convention") for r in rows):
        return
    _per_book_normalized(
        rows, "convention",
        Q_OUTPUT_DIR / "q_convention_rates_by_book.csv",
    )


# ==========================================================
# K14. Q. SKINNER KĽÚČOVÉ POMERY PER KNIHA
# ==========================================================

def q_key_ratios_by_book(rows):

    totals     = Counter()
    legit      = Counter()
    ideo       = Counter()
    interv     = Counter()
    directive  = Counter()
    assertive  = Counter()

    for r in rows:
        book = r["file_name"]
        totals[book] += 1
        if r["primary_intention"] == "legitimation":
            legit[book] += 1
        if r["primary_intention"] == "ideological_contestation":
            ideo[book] += 1
        if r["primary_intention"] == "intervention":
            interv[book] += 1
        if r["illocutionary_force"] == "directive":
            directive[book] += 1
        if r["illocutionary_force"] == "assertive":
            assertive[book] += 1

    out_rows = []
    for book in sorted(totals):
        total = totals[book]
        d = directive[book]
        a = assertive[book]
        da_denom = d + a
        out_rows.append({
            "file_name":                    book,
            "total":                        total,
            "legitimation":                 legit[book],
            "legitimation_ratio":           round(legit[book]  / total, 3) if total else 0.0,
            "ideological_contestation":     ideo[book],
            "ideological_contestation_ratio": round(ideo[book] / total, 3) if total else 0.0,
            "intervention":                 interv[book],
            "intervention_ratio":           round(interv[book] / total, 3) if total else 0.0,
            "directive":                    d,
            "assertive":                    a,
            "directive_vs_assertive":       round(d / da_denom, 3) if da_denom else None,
        })

    export_rows(
        out_rows,
        Q_OUTPUT_DIR / "q_key_ratios_by_book.csv",
        [
            "file_name", "total",
            "legitimation", "legitimation_ratio",
            "ideological_contestation", "ideological_contestation_ratio",
            "intervention", "intervention_ratio",
            "directive", "assertive", "directive_vs_assertive",
        ],
    )


# ==========================================================
# K14b. ŠTATISTICKÉ POROVNANIE MEDZI KNIHAMI
#   Long-format output: (field_value, file_name, count, rate, corpus_mean,
#   corpus_std, zscore, rank) — filtrovateľné per zámer/knihu
# ==========================================================

def _comparison_stats_for_field(rows, field, output_path):
    book_totals = Counter(r["file_name"] for r in rows)
    value_by_book = defaultdict(Counter)
    for r in rows:
        value_by_book[r[field]][r["file_name"]] += 1

    all_books = sorted(book_totals)
    all_values = sorted(value_by_book)

    out_rows = []
    for val in all_values:
        rates = [
            round(value_by_book[val][b] / book_totals[b], 4) if book_totals[b] else 0.0
            for b in all_books
        ]
        n = len(rates)
        corpus_mean = sum(rates) / n if n else 0.0
        corpus_std = (
            math.sqrt(sum((r - corpus_mean) ** 2 for r in rates) / (n - 1))
            if n > 1 else 0.0
        )
        ranked = sorted(range(n), key=lambda i: rates[i], reverse=True)
        rank_of = {idx: pos + 1 for pos, idx in enumerate(ranked)}

        for i, book in enumerate(all_books):
            zscore = (rates[i] - corpus_mean) / corpus_std if corpus_std else 0.0
            out_rows.append({
                field:          val,
                "file_name":    book,
                "count":        value_by_book[val][book],
                "total":        book_totals[book],
                "rate":         rates[i],
                "corpus_mean":  round(corpus_mean, 4),
                "corpus_std":   round(corpus_std, 4),
                "zscore":       round(zscore, 3),
                "rank":         rank_of[i],
            })

    export_rows(
        out_rows,
        output_path,
        [field, "file_name", "count", "total", "rate",
         "corpus_mean", "corpus_std", "zscore", "rank"],
    )


def q_comparison_stats(rows):
    _comparison_stats_for_field(
        rows, "primary_intention",
        Q_OUTPUT_DIR / "q_intention_comparison.csv",
    )
    _comparison_stats_for_field(
        rows, "illocutionary_force",
        Q_OUTPUT_DIR / "q_force_comparison.csv",
    )


def q_book_profiles(rows):
    book_totals = Counter(r["file_name"] for r in rows)
    all_books = sorted(book_totals)
    all_intentions = sorted({r["primary_intention"] for r in rows})

    intent_by_book = defaultdict(Counter)
    strat_by_book  = defaultdict(Counter)
    conf_by_book   = defaultdict(list)
    for r in rows:
        b = r["file_name"]
        intent_by_book[b][r["primary_intention"]] += 1
        strat_by_book[b][r.get("primary_strategy", "")] += 1
        conf_by_book[b].append(float(r.get("confidence", 0)))

    # Corpus mean rate per intention
    corpus_mean = {}
    for intent in all_intentions:
        rates = [
            intent_by_book[b][intent] / book_totals[b]
            for b in all_books if book_totals[b]
        ]
        corpus_mean[intent] = sum(rates) / len(rates) if rates else 0.0

    out_rows = []
    for book in all_books:
        total = book_totals[book]
        rates = {
            i: round(intent_by_book[book][i] / total, 4) if total else 0.0
            for i in all_intentions
        }
        rhet_n = sum(
            intent_by_book[book][i] for i in all_intentions
            if i not in {"record", "narrative", "unclassified"}
        )
        top3 = sorted(all_intentions, key=lambda i: rates[i], reverse=True)[:3]
        top3_str = " > ".join(f"{i}({rates[i]:.3f})" for i in top3)
        dom_strat = strat_by_book[book].most_common(1)[0][0] if strat_by_book[book] else ""
        vs = conf_by_book[book]

        out_rows.append({
            "file_name":          book,
            "total_sentences":    total,
            "rhetorical_density": round(rhet_n / total, 3) if total else 0.0,
            "dominant_strategy":  dom_strat,
            "avg_confidence":     round(sum(vs) / len(vs), 3) if vs else 0.0,
            "top3_intentions":    top3_str,
            **{f"{i}_rate":     rates[i] for i in all_intentions},
            **{f"{i}_vs_mean":  round(rates[i] - corpus_mean[i], 4) for i in all_intentions},
        })

    fieldnames = [
        "file_name", "total_sentences", "rhetorical_density",
        "dominant_strategy", "avg_confidence", "top3_intentions",
        *[f"{i}_rate"    for i in all_intentions],
        *[f"{i}_vs_mean" for i in all_intentions],
    ]
    export_rows(out_rows, Q_OUTPUT_DIR / "q_book_profiles.csv", fieldnames)


# ==========================================================
# K15. POLITICAL VOCABULARY
# ==========================================================

def q_political_vocabulary_counts(rows):
    # Strips category annotation if present: "zákon[covenant_law]" → "zákon"
    term_counter = Counter()
    for r in rows:
        raw = r.get("political_vocabulary", "").strip()
        if raw:
            for term in raw.split(", "):
                bare = term.strip().split("[")[0]
                if bare:
                    term_counter[bare] += 1

    export_counter(
        term_counter,
        Q_OUTPUT_DIR / "q_political_vocabulary_counts.csv",
        "term",
    )


def q_political_vocabulary_by_book(rows):
    book_totals = Counter(r["file_name"] for r in rows)
    term_by_book = defaultdict(Counter)

    for r in rows:
        raw = r.get("political_vocabulary", "").strip()
        if not raw:
            continue
        book = r["file_name"]
        for term in raw.split(", "):
            bare = term.strip().split("[")[0]
            if bare:
                term_by_book[book][bare] += 1

    all_terms = sorted({t for cnt in term_by_book.values() for t in cnt})
    if not all_terms:
        return

    out_rows = []
    for book in sorted(book_totals):
        total = book_totals[book]
        row = {"file_name": book, "total": total}
        for t in all_terms:
            n = term_by_book[book][t]
            row[t] = n
            row[f"{t}_rate"] = round(n / total, 4) if total else 0.0
        out_rows.append(row)

    fieldnames = ["file_name", "total",
                  *[col for t in all_terms for col in (t, f"{t}_rate")]]
    export_rows(out_rows, Q_OUTPUT_DIR / "q_political_vocabulary_by_book.csv", fieldnames)


# ==========================================================
# K16. LEXIKÁLNA HUSTOTA PER KNIHA
# ==========================================================

# DISCONNECTED: needs remapping to q_skinner_bible_analysis.csv schema
# def lexical_density_by_book(rows):
#
#     totals    = Counter()
#     verbum    = Counter()
#     imperative = Counter()
#     negation  = Counter()
#
#     for r in rows:
#         book = r["file_name"]
#         totals[book] += 1
#         if r.get("has_verbum_dicendi") == "True":
#             verbum[book] += 1
#         if r.get("is_imperative_like") == "True":
#             imperative[book] += 1
#         if r.get("has_negation") == "True":
#             negation[book] += 1
#
#     out_rows = []
#     for book in sorted(totals):
#         total = totals[book]
#         out_rows.append({
#             "file_name":            book,
#             "total":                total,
#             "verbum_dicendi":       verbum[book],
#             "verbum_dicendi_ratio": round(verbum[book]    / total, 3) if total else 0.0,
#             "imperative":           imperative[book],
#             "imperative_ratio":     round(imperative[book] / total, 3) if total else 0.0,
#             "negation":             negation[book],
#             "negation_ratio":       round(negation[book]  / total, 3) if total else 0.0,
#         })
#
#     export_rows(
#         out_rows,
#         OUTPUT_DIR / "lexical_density_by_book.csv",
#         ["file_name", "total",
#          "verbum_dicendi", "verbum_dicendi_ratio",
#          "imperative", "imperative_ratio",
#          "negation", "negation_ratio"],
#     )


# ==========================================================
# K17. LOW-CONFIDENCE SENTENCES
# ==========================================================

# DISCONNECTED: needs remapping to q_skinner_bible_analysis.csv schema
# def low_confidence_sentences(rows):
#
#     fields = ["sentence", "skinner_class", "proxy_subtype", "confidence", "file_name"]
#     low = [
#         {f: r.get(f, "") for f in fields}
#         for r in rows
#         if float(r.get("confidence", 1)) < 0.6
#     ]
#
#     export_rows(low, OUTPUT_DIR / "o_low_confidence.csv", fields)


# ==========================================================
# K18. PER-BOOK SUMMARY
# ==========================================================

# DISCONNECTED: needs remapping to q_skinner_bible_analysis.csv schema
# def per_book_summary(rows):
#
#     totals          = Counter()
#     confidence_vals = defaultdict(list)
#     tact_n          = Counter()
#     auto_n          = Counter()
#     dialogue_n      = Counter()
#
#     DIALOGUE_SUBTYPES = {
#         "intraverbal_proxy",
#         "intraverbal_trigger",
#         "dialogue_chain_proxy",
#     }
#
#     for r in rows:
#         book = r["file_name"]
#         totals[book] += 1
#         confidence_vals[book].append(float(r.get("confidence", 0)))
#         if r["skinner_class"] == "tact":
#             tact_n[book] += 1
#         elif r["skinner_class"] == "autoclitic":
#             auto_n[book] += 1
#         if r["proxy_subtype"] in DIALOGUE_SUBTYPES:
#             dialogue_n[book] += 1
#
#     out_rows = []
#     for book in sorted(totals):
#         total = totals[book]
#         vs = confidence_vals[book]
#         out_rows.append({
#             "file_name":        book,
#             "total":            total,
#             "avg_confidence":   round(sum(vs) / len(vs), 3) if vs else 0.0,
#             "tact_ratio":       round(tact_n[book]     / total, 3) if total else 0.0,
#             "autoclitic_ratio": round(auto_n[book]     / total, 3) if total else 0.0,
#             "dialogue_density": round(dialogue_n[book] / total, 3) if total else 0.0,
#         })
#
#     export_rows(
#         out_rows,
#         OUTPUT_DIR / "o_per_book_summary.csv",
#         ["file_name", "total", "avg_confidence",
#          "tact_ratio", "autoclitic_ratio", "dialogue_density"],
#     )


# ==========================================================
# K11. REFINED DESCRIPTIONS INDEX  (absorbed from q_description_index)
# ==========================================================

OUTPUT_DIR_REFINED = ROOT_OUTPUT / "description_index"


def load_refined_rows():
    return _db_load(TABLE_REFINED)


def count_description_types(rows):
    export_counter(
        Counter(r["description_type"] for r in rows if r.get("description_type")),
        OUTPUT_DIR_REFINED / "description_type_counts.csv",
        "description_type",
    )


def aggregate_by_cluster(rows):
    values: dict = defaultdict(list)
    for r in rows:
        cluster = r.get("semantic_cluster", "")
        if cluster:
            values[cluster].append(float(r.get("confidence", 0)))

    out_rows = [
        {
            "semantic_cluster": cluster,
            "count":            len(vs),
            "avg_confidence":   round(sum(vs) / len(vs), 3) if vs else 0.0,
        }
        for cluster, vs in sorted(values.items())
    ]
    export_rows(
        out_rows,
        OUTPUT_DIR_REFINED / "cluster_counts.csv",
        ["semantic_cluster", "count", "avg_confidence"],
    )


def refined_per_book_summary(rows):
    book_totals = Counter(r["file_name"] for r in rows)
    type_by_book: dict = defaultdict(Counter)
    conf_by_book: dict = defaultdict(list)

    for r in rows:
        book = r["file_name"]
        dtype = r.get("description_type", "")
        if dtype:
            type_by_book[book][dtype] += 1
        conf_by_book[book].append(float(r.get("confidence", 0)))

    out_rows = []
    for book in sorted(book_totals):
        vs = conf_by_book[book]
        top3 = " > ".join(
            f"{t}({c})" for t, c in type_by_book[book].most_common(3)
        )
        out_rows.append({
            "file_name":              book,
            "total_sentences":        book_totals[book],
            "avg_confidence":         round(sum(vs) / len(vs), 3) if vs else 0.0,
            "top3_description_types": top3,
        })

    export_rows(
        out_rows,
        OUTPUT_DIR_REFINED / "book_summary.csv",
        ["file_name", "total_sentences", "avg_confidence", "top3_description_types"],
    )


# ==========================================================
# K10. MAIN
# ==========================================================

def main():

    rows = load_rows()
    print(f"Loaded rows: {len(rows)}")

    # Per-book operational analytics
    dialogue_density_by_book(rows)
    tact_vs_autoclitic_by_book(rows)
    confidence_by_book(rows)

    # Q. Skinner analytics
    q_rows = load_q_rows()
    print(f"Loaded Q. Skinner rows: {len(q_rows)}")

    # Global overviews
    q_intention_overview(q_rows)
    q_illocutionary_force_overview(q_rows)
    q_strategy_overview(q_rows)

    # Per-book raw counts
    q_intention_by_book(q_rows)
    q_illocutionary_force_by_book(q_rows)
    q_strategy_by_book(q_rows)
    q_key_ratios_by_book(q_rows)

    # Per-book normalizované sadzby (rate = count / total_sentences)
    q_intention_rates_by_book(q_rows)
    q_force_rates_by_book(q_rows)
    q_strategy_rates_by_book(q_rows)
    q_convention_rates_by_book(q_rows)

    # Štatistické porovnanie medzi knihami (z-score + rank)
    q_comparison_stats(q_rows)
    q_book_profiles(q_rows)

    # Political vocabulary
    q_political_vocabulary_counts(q_rows)
    q_political_vocabulary_by_book(q_rows)

    # Refined descriptions
    refined_rows = load_refined_rows()
    print(f"Loaded refined rows: {len(refined_rows)}")
    count_description_types(refined_rows)
    aggregate_by_cluster(refined_rows)
    refined_per_book_summary(refined_rows)

    print("\nDONE")
    print(f"Output folder: {OUTPUT_DIR}")
    print("Files written:")
    for f in sorted(OUTPUT_DIR.glob("*.csv")):
        print(f"  {f.name}")
    print(f"\nQ. Skinner output folder: {Q_OUTPUT_DIR}")
    print("Files written:")
    for f in sorted(Q_OUTPUT_DIR.glob("*.csv")):
        print(f"  {f.name}")


if __name__ == "__main__":
    main()
