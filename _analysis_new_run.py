"""
Post-run analysis script — runs after full pipeline completes.

Compare a new run against a previous one.  Defaults to the historical
baseline ``2026-06-04T20:27:40``; override with ``--old-run`` or the
``ANALYSIS_OLD_RUN`` environment variable.

Usage:
    python _analysis_new_run.py
    python _analysis_new_run.py --old-run 2026-06-04T20:27:40
"""
import os
import sqlite3
import sys
from collections import Counter, defaultdict

from a_paths import DB_PATH, PROJECT_ROOT

DB = DB_PATH
OLD_RUN = os.environ.get("ANALYSIS_OLD_RUN", "2026-06-04T20:27:40")
if "--old-run" in sys.argv:
    _idx = sys.argv.index("--old-run")
    if _idx + 1 < len(sys.argv):
        OLD_RUN = sys.argv[_idx + 1]

conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

def q(sql, params=()):
    return [dict(r) for r in conn.execute(sql, params)]

# ── Identify new run ──────────────────────────────────────────────────────────
_row = conn.execute(
    "SELECT run_id FROM skinner_analysis WHERE run_id NOT LIKE 'upload_%'"
    " ORDER BY rowid DESC LIMIT 1"
).fetchone()
if _row is None:
    print("ERROR: no analysis run found in skinner_analysis", file=sys.stderr)
    sys.exit(1)
new_run = _row[0]
print(f"OLD run : {OLD_RUN}")
print(f"NEW run : {new_run}")
print()

# ── 2a. Books and row counts ──────────────────────────────────────────────────
print("=" * 60)
print("1. BOOK COVERAGE")
print("=" * 60)
books_new = q("SELECT file_name, COUNT(*) n FROM skinner_analysis WHERE run_id=? GROUP BY file_name ORDER BY file_name", (new_run,))
print(f"Books in new run: {len(books_new)}")
zero = [b for b in books_new if b["n"] == 0]
print(f"Books with 0 rows: {zero if zero else 'none'}")
print()

# ── 2b. dep_tree coverage ─────────────────────────────────────────────────────
print("=" * 60)
print("2a. DEP_TREE COVERAGE PER BOOK")
print("=" * 60)
dep_rows = q("""
    SELECT file_name,
           COUNT(*) total,
           SUM(CASE WHEN dep_tree IS NOT NULL AND dep_tree != '' THEN 1 ELSE 0 END) nonempty
    FROM refined_descriptions WHERE run_id=?
    GROUP BY file_name ORDER BY file_name
""", (new_run,))
under95 = []
for r in dep_rows:
    pct = r["nonempty"] / r["total"] * 100 if r["total"] else 0
    if pct < 95:
        under95.append((r["file_name"], pct, r["nonempty"], r["total"]))
if under95:
    print("Books under 95% dep_tree fill:")
    for fname, pct, ne, tot in under95:
        print(f"  {fname:<30} {pct:.1f}%  ({ne}/{tot})")
else:
    total_all = sum(r["total"] for r in dep_rows)
    nonempty_all = sum(r["nonempty"] for r in dep_rows)
    print(f"All books ≥ 95%  (corpus total: {nonempty_all}/{total_all} = {nonempty_all/total_all*100:.1f}%)")
print()

# ── 2c. rst_relation presence + coherence density ────────────────────────────
print("=" * 60)
print("2b. RST_RELATION — coherence_density per book")
print("=" * 60)
rst_rows = q("""
    SELECT file_name,
           COUNT(*) total,
           SUM(CASE WHEN rst_relation IS NOT NULL AND rst_relation != '' THEN 1 ELSE 0 END) has_rst,
           SUM(CASE WHEN rst_relation != 'continuation' THEN 1 ELSE 0 END) non_cont
    FROM skinner_analysis WHERE run_id=?
    GROUP BY file_name ORDER BY file_name
""", (new_run,))

missing_rst = [r for r in rst_rows if r["has_rst"] < r["total"]]
print(f"Rows missing rst_relation: {sum(r['total']-r['has_rst'] for r in missing_rst)}")

densities = []
for r in rst_rows:
    if r["total"] > 0:
        densities.append((r["file_name"], r["non_cont"] / r["total"]))

densities.sort(key=lambda x: -x[1])
print("\nTop 5 coherence_density (most non-continuation):")
for fname, d in densities[:5]:
    short = fname.replace("bible_BKR_","").replace(".txt","")
    print(f"  {short:<8} {d:.3f}")
print("Bottom 5:")
for fname, d in densities[-5:]:
    short = fname.replace("bible_BKR_","").replace(".txt","")
    print(f"  {short:<8} {d:.3f}")
print()

# ── 2d. u_religious_elements TEMP counter ────────────────────────────────────
print("=" * 60)
print("2c. ROLE_WEIGHT COUNTER (dep_tree vs positional) — full corpus")
print("=" * 60)
conn.close()

import importlib, sys
sys.path.insert(0, str(PROJECT_ROOT))

# Reset counter before run
import u_religious_elements as ure
ure._ROLE_WEIGHT_COUNTER["dep_tree"] = 0
ure._ROLE_WEIGHT_COUNTER["positional"] = 0

from n_db import load_rows, TABLE_REFINED
from t_config_tradition import get_active_elements
active = get_active_elements("christian_czech")
rows = load_rows(TABLE_REFINED)
ure.compute_density_by_book(rows, active)
c = ure._ROLE_WEIGHT_COUNTER
total_c = c["dep_tree"] + c["positional"]
print(f"Total _role_weight() calls: {total_c}")
if total_c:
    print(f"  dep_tree branch  : {c['dep_tree']:>7}  ({c['dep_tree']/total_c*100:.1f}%)")
    print(f"  positional branch: {c['positional']:>7}  ({c['positional']/total_c*100:.1f}%)")
print()

# Re-open conn for diff analysis
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row

# ── 3a. primary_intention diff ────────────────────────────────────────────────
print("=" * 60)
print("3a. PRIMARY_INTENTION DIFF (old vs new)")
print("=" * 60)

def intent_dist(run):
    rows = q("SELECT primary_intention, COUNT(*) n FROM skinner_analysis WHERE run_id=? GROUP BY primary_intention", (run,))
    total = sum(r["n"] for r in rows)
    return {r["primary_intention"]: r["n"] for r in rows}, total

old_dist, old_total = intent_dist(OLD_RUN)
new_dist, new_total = intent_dist(new_run)
all_intents = sorted(set(old_dist) | set(new_dist))

print(f"{'Intention':<30} {'Old':>8} {'Old%':>7} {'New':>8} {'New%':>7} {'Δpp':>8}")
print("-" * 72)
for intent in sorted(all_intents, key=lambda x: -new_dist.get(x,0)):
    o = old_dist.get(intent, 0); n = new_dist.get(intent, 0)
    op = o/old_total*100; np_ = n/new_total*100
    print(f"{intent:<30} {o:>8} {op:>6.2f}% {n:>8} {np_:>6.2f}% {np_-op:>+7.2f}pp")

print()
old_unc = old_dist.get("unclassified", 0) / old_total * 100
new_unc = new_dist.get("unclassified", 0) / new_total * 100
print(f"unclassified: {old_unc:.2f}% → {new_unc:.2f}%  (Δ {new_unc-old_unc:+.2f}pp)")
print()

# ── 3a.2 Per-genre intention shift ───────────────────────────────────────────
print("Per-genre (coarse) primary_intention distribution — new run:")
from genre_maps import detect_book_genre
genre_rows = q("SELECT file_name, primary_intention, COUNT(*) n FROM skinner_analysis WHERE run_id=? GROUP BY file_name, primary_intention", (new_run,))
by_genre = defaultdict(Counter)
for r in genre_rows:
    genre = detect_book_genre(r["file_name"], coarse=True)
    by_genre[genre][r["primary_intention"]] += r["n"]

for genre in sorted(by_genre):
    total_g = sum(by_genre[genre].values())
    top3 = by_genre[genre].most_common(3)
    parts = ", ".join(f"{k}={v/total_g*100:.0f}%" for k, v in top3)
    print(f"  {genre:<14} n={total_g:>6}  {parts}")
print()

# ── 3b. Changed sentences ─────────────────────────────────────────────────────
print("=" * 60)
print("3b. CHANGED primary_intention sentences")
print("=" * 60)
# Join on sentence_id + file_name (both runs must have same books)
changed = q("""
    SELECT o.file_name, o.sentence_id,
           o.primary_intention old_int,
           n.primary_intention new_int,
           COUNT(*) OVER () total_changed
    FROM skinner_analysis o
    JOIN skinner_analysis n ON o.sentence_id = n.sentence_id AND o.file_name = n.file_name
    WHERE o.run_id=? AND n.run_id=? AND o.primary_intention != n.primary_intention
""", (OLD_RUN, new_run))

total_new_rows = new_total
pct_changed = len(changed) / total_new_rows * 100 if total_new_rows else 0
print(f"Changed: {len(changed)} / {total_new_rows} = {pct_changed:.2f}%")

transitions = Counter((r["old_int"], r["new_int"]) for r in changed)
print("Top 5 transitions (old → new):")
for (old_i, new_i), cnt in transitions.most_common(5):
    print(f"  {old_i:<30} → {new_i:<30} {cnt:>5}")
print()

# ── 3c. Ilokučná sila ─────────────────────────────────────────────────────────
print("=" * 60)
print("3c. ILLOCUTIONARY_FORCE DIFF")
print("=" * 60)
def force_dist(run):
    rows = q("SELECT illocutionary_force, COUNT(*) n FROM skinner_analysis WHERE run_id=? GROUP BY illocutionary_force", (run,))
    total = sum(r["n"] for r in rows)
    return {r["illocutionary_force"]: r["n"] for r in rows}, total

of_dist, of_total = force_dist(OLD_RUN)
nf_dist, nf_total = force_dist(new_run)
all_forces = sorted(set(of_dist) | set(nf_dist))
print(f"{'Force':<20} {'Old%':>8} {'New%':>8} {'Δpp':>8}")
print("-" * 48)
for f in sorted(all_forces, key=lambda x: -nf_dist.get(x,0)):
    op = of_dist.get(f,0)/of_total*100; np_ = nf_dist.get(f,0)/nf_total*100
    print(f"{f:<20} {op:>7.2f}% {np_:>7.2f}% {np_-op:>+7.2f}pp")
print()

# ── 3d. m_verbal relation_type diff ──────────────────────────────────────────
print("=" * 60)
print("3d. VERBAL RELATION_TYPE DIFF")
print("=" * 60)
def rel_dist(run):
    rows = q("SELECT relation_type, COUNT(*) n, AVG(CAST(confidence AS REAL)) avg_conf FROM verbal_relations WHERE run_id=? GROUP BY relation_type", (run,))
    total = sum(r["n"] for r in rows)
    return {r["relation_type"]: (r["n"], r["avg_conf"]) for r in rows}, total

or_dist, or_total = rel_dist(OLD_RUN)
nr_dist, nr_total = rel_dist(new_run)
all_rels = sorted(set(or_dist) | set(nr_dist))
print(f"{'RelType':<30} {'Old%':>8} {'New%':>8} {'Δpp':>8}  {'OldConf':>8}  {'NewConf':>8}")
print("-" * 78)
for rel in sorted(all_rels, key=lambda x: -nr_dist.get(x,(0,0))[0]):
    on, oc = or_dist.get(rel, (0, 0.0)); nn, nc = nr_dist.get(rel, (0, 0.0))
    op = on/or_total*100; np_ = nn/nr_total*100
    flag = " ← NOTE" if abs(np_-op) > 1 else ""
    print(f"{rel:<30} {op:>7.2f}% {np_:>7.2f}% {np_-op:>+7.2f}pp  {oc or 0:>8.3f}  {nc or 0:>8.3f}{flag}")

# Per-genre avg confidence new run
print("\nPer-genre avg confidence (new run):")
genre_conf = q("""
    SELECT v.file_name, AVG(CAST(v.confidence AS REAL)) avg_conf, COUNT(*) n
    FROM verbal_relations v WHERE v.run_id=?
    GROUP BY v.file_name
""", (new_run,))
by_genre_conf = defaultdict(list)
for r in genre_conf:
    g = detect_book_genre(r["file_name"], coarse=True)
    by_genre_conf[g].append((r["avg_conf"], r["n"]))
print(f"  {'Genre':<14} {'AvgConf':>9}  {'Sentences':>10}")
for g in sorted(by_genre_conf):
    total_n = sum(n for _,n in by_genre_conf[g])
    wavg = sum(c*n for c,n in by_genre_conf[g]) / total_n if total_n else 0
    print(f"  {g:<14} {wavg:>9.3f}  {total_n:>10}")

conn.close()
print("\nDONE")
