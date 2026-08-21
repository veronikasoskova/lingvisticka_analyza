"""
Verifikácia dep_tree + rst_relation po poslednom kole zmien.
Spúšťa sa na jedinej knihe (Abd) cez _process_book().
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from a_paths import BIBLE_FOLDER
from collections import Counter

ABD = BIBLE_FOLDER / "bible_BKR_Abd.txt"

# ── 1. Run pipeline on Abd ─────────────────────────────────────────────────
print("=" * 60)
print("1. PIPELINE RUN — bible_BKR_Abd.txt")
print("=" * 60)

from k_apply_all_to_bible import _process_book
sk_rows, rel_rows, ref_rows = _process_book(ABD)
print(f"   skinner_rows : {len(sk_rows)}")
print(f"   relation_rows: {len(rel_rows)}")
print(f"   refined_rows : {len(ref_rows)}")

# ── 2D. dep_tree — refined_rows ────────────────────────────────────────────
print()
print("=" * 60)
print("2. DEP_TREE VERIFICATION")
print("=" * 60)

# a) stĺpec prítomný?
has_col = all("dep_tree" in r for r in ref_rows)
print(f"\n2a) 'dep_tree' key in all ref_rows: {has_col}")

# b) % neprázdnych
non_empty = [r for r in ref_rows if r.get("dep_tree", "").strip()]
pct = len(non_empty) / len(ref_rows) * 100 if ref_rows else 0
print(f"2b) Non-empty dep_tree: {len(non_empty)}/{len(ref_rows)}  ({pct:.1f} %)")

# c) 5 ukážok
print("2c) 5 sample dep_tree values:")
for r in non_empty[:5]:
    print(f"    sentence_id={r.get('sentence_id', '?')} | {r['dep_tree'][:80]}")

# d) upstream check — features dep_tree
print("\n2d) Upstream check — feature.dep_tree on raw extraction:")
from c_input import create_input_from_file
from d_preprocessing import preprocess_text
from e_extraction import extract_features

text_input   = create_input_from_file(ABD) if hasattr(__import__('c_input'), 'create_input_from_file') else open(ABD).read()
preprocessed = preprocess_text(text_input)
features     = extract_features(preprocessed)

feat_non_empty = [f for f in features if getattr(f, "dep_tree", "").strip()]
print(f"   features with non-empty dep_tree: {len(feat_non_empty)}/{len(features)}")
if feat_non_empty:
    print(f"   sample: {feat_non_empty[0].dep_tree[:80]}")
else:
    print("   *** dep_tree is EMPTY on all feature objects — loss is in e_extraction ***")

# ── 3. RST VERIFICATION ────────────────────────────────────────────────────
print()
print("=" * 60)
print("3. RST_RELATION VERIFICATION")
print("=" * 60)

# a) stĺpec prítomný?
has_rst = all("rst_relation" in r for r in sk_rows)
print(f"\n3a) 'rst_relation' key in all sk_rows: {has_rst}")

# b) distribúcia + coherence_density
from j0_rst_relations import rst_profile
labels = [r["rst_relation"] for r in sk_rows]
profile = rst_profile(labels)
cnt = Counter(labels)
print("3b) Distribution:")
for rel, n in sorted(cnt.items(), key=lambda x: -x[1]):
    print(f"    {rel:<20} {n:>4}  ({n/len(labels)*100:.1f} %)")
print(f"    coherence_density = {profile['coherence_density']}")

# c) Sanity-check zarovnania konektorov
print("\n3c) Connector alignment sanity-check:")
CONNECTORS = {
    "ale": "contrast", "však": "contrast", "nýbrž": "contrast", "naopak": "contrast",
    "neboť": "cause",  "protože": "cause",  "protož": "cause",  "tedy": "cause",
    "jestliže": "condition", "kdyby": "condition", "pakliť": "condition",
}
hits = 0
for r in sk_rows:
    sentence = r.get("sentence", "").lower()
    first_word = sentence.split()[0].rstrip(",.;:") if sentence.split() else ""
    if first_word in CONNECTORS:
        expected = CONNECTORS[first_word]
        actual   = r["rst_relation"]
        ok = "OK" if actual == expected else f"MISMATCH (expected {expected})"
        print(f"    [{ok}] sid={r.get('sentence_id','?')} first='{first_word}' rst='{actual}' | {r['sentence'][:60]}")
        hits += 1
    if hits >= 3:
        break
if hits == 0:
    print("    (no connector-initial sentences found in Abd — check with longer book)")

# d) count match
print(f"\n3d) sk_rows count ({len(sk_rows)}) — each has rst_relation: {has_rst}")
missing_rst = [r for r in sk_rows if "rst_relation" not in r]
print(f"    rows missing rst_relation: {len(missing_rst)}")

print()
print("=" * 60)
print("DONE")
print("=" * 60)
