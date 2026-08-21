from pathlib import Path
import csv
from collections import Counter, defaultdict

from c_input import create_input_from_file
from d_preprocessing import preprocess_text
from a_paths import BIBLE_FOLDER, OUTPUT_DIR as ROOT_OUTPUT, list_bible_files

OUTPUT_DIR = ROOT_OUTPUT / "dependency_hierarchy"


def analyze_file(file_path):

    text_input = create_input_from_file(
        file_path=str(file_path),
        source="written_record",
        interaction="monologue",
        stimulus="unknown",
        speaker="unknown",
        addressee="unknown",
        notes=f"Bible file: {file_path.name}"
    )

    preprocessed = preprocess_text(text_input)
    rows = []

    for sent_idx, sentence in enumerate(preprocessed.sentences):
        for token_idx, token in enumerate(sentence.tokens):
            rows.append({
                "file_name": file_path.name,
                "sent_idx":  sent_idx,
                "token_idx": token_idx,
                "sentence":  sentence.text,
                "token":     token.text,
                "lemma":     token.lemma,
                "pos":       token.pos,
                "dep":       token.dep,
                "head":      token.head,
            })

    return rows


def collect_dependency_rows():

    all_rows = []

    files = list_bible_files(limit=10)

    if not files:
        raise FileNotFoundError(
            f"No bible_BKR_*.txt files found: {BIBLE_FOLDER}"
        )

    for file_path in files:

        print(f"Processing: {file_path.name}")

        rows = analyze_file(
            file_path
        )

        all_rows.extend(
            rows
        )

    return all_rows


def export_token_dependency_rows(rows, max_rows=50000):

    if len(rows) > max_rows:
        print(f"  Truncating token_dependencies.csv to {max_rows} rows (total: {len(rows)})")
        rows = rows[:max_rows]

    output_file = OUTPUT_DIR / "token_dependencies.csv"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with output_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "file_name", "sent_idx", "token_idx",
            "sentence", "token", "lemma", "pos", "dep", "head",
        ])
        writer.writeheader()
        writer.writerows(rows)


def export_dependency_counts(rows):

    counter = Counter(
        row["dep"]
        for row in rows
    )

    output_file = OUTPUT_DIR / "dependency_counts.csv"

    with output_file.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=[
                "dependency",
                "count"
            ]
        )

        writer.writeheader()

        for dep, count in counter.most_common():
            writer.writerow({
                "dependency": dep,
                "count": count
            })


def export_head_lemma_counts(rows):

    counter = Counter(
        row["lemma"].lower()
        for row in rows
        if row["head"].lower() != "root"
    )

    output_file = OUTPUT_DIR / "head_lemma_counts.csv"

    with output_file.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        writer = csv.DictWriter(
            f,
            fieldnames=[
                "head",
                "count"
            ]
        )

        writer.writeheader()

        for head, count in counter.most_common(500):
            writer.writerow({
                "head": head,
                "count": count
            })


CLAUSE_DEPS = {"advcl", "relcl", "acl", "csubj", "ccomp", "xcomp", "parataxis"}


def _tree_depth(sentence_token_rows: list) -> int:
    """Max dependency chain length from ROOT for one sentence."""
    dep_map = {r["token"]: (r["dep"], r["head"]) for r in sentence_token_rows}

    def depth_of(token: str, visited: set) -> int:
        if token in visited or token not in dep_map:
            return 0
        visited.add(token)
        dep, head = dep_map[token]
        if dep.lower() == "root" or head == token or head.lower() == "root":
            return 0
        return 1 + depth_of(head, visited)

    return max((depth_of(r["token"], set()) for r in sentence_token_rows), default=0)


def _clause_count(sentence_token_rows: list) -> int:
    return sum(1 for r in sentence_token_rows if r["dep"] in CLAUSE_DEPS)


def compute_complexity_rows(token_rows: list) -> list:
    groups: dict = defaultdict(list)
    for r in token_rows:
        groups[(r["file_name"], r["sentence"])].append(r)

    out = []
    for (file_name, sentence), tokens in groups.items():
        out.append({
            "file_name":    file_name,
            "sentence":     sentence,
            "tree_depth":   _tree_depth(tokens),
            "clause_count": _clause_count(tokens),
        })
    return out


def export_sentence_complexity(complexity_rows: list) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_file = OUTPUT_DIR / "sentence_complexity.csv"
    with output_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["file_name", "sentence", "tree_depth", "clause_count"],
        )
        writer.writeheader()
        writer.writerows(complexity_rows)


# ==========================================================
# UD DEPENDENCY TRIGRAMS  (nsubj → VERB → obj)
# ==========================================================

_SUBJ_DEPS = frozenset({"nsubj", "nsubj:pass", "csubj"})
_OBJ_DEPS  = frozenset({"obj", "iobj", "obl", "obl:arg"})
_VERB_POS  = frozenset({"VERB", "AUX"})


def _extract_trigrams_from_sentence(sentence_tokens: list[dict]) -> list[tuple[str, str, str]]:
    """
    Extract (subj_lemma, verb_lemma, obj_lemma) triples from one sentence.
    Matches: token with dep in _SUBJ_DEPS whose head == VERB token text,
             and token with dep in _OBJ_DEPS whose head == same VERB token text.
    Uses first-occurrence text matching for head resolution.
    """
    # text → first token in this sentence (for head resolution)
    text_to_token: dict[str, dict] = {}
    for t in sentence_tokens:
        if t["token"] not in text_to_token:
            text_to_token[t["token"]] = t

    # head_text → list of dependents
    head_to_deps: dict = defaultdict(list)
    for t in sentence_tokens:
        head_to_deps[t["head"]].append(t)

    trigrams = []
    for tok in sentence_tokens:
        if tok["pos"] not in _VERB_POS:
            continue
        verb_text  = tok["token"]
        verb_lemma = tok["lemma"]
        deps = head_to_deps.get(verb_text, [])

        subjs = [d for d in deps if d["dep"] in _SUBJ_DEPS]
        objs  = [d for d in deps if d["dep"] in _OBJ_DEPS]

        for s in subjs:
            for o in objs:
                trigrams.append((s["lemma"], verb_lemma, o["lemma"]))

    return trigrams


def extract_all_trigrams(token_rows: list[dict]) -> list[dict]:
    """
    Extract trigrams from all token rows, grouped by sentence.
    Returns list of {subj, verb, obj, count, file_name} dicts.
    """
    # Group by (file_name, sent_idx) — sent_idx disambiguates repeated sentence texts
    groups: dict = defaultdict(list)
    for r in token_rows:
        key = (r["file_name"], r.get("sent_idx", r["sentence"]))
        groups[key].append(r)

    # Count per book
    global_counter: Counter = Counter()
    book_counter: dict = defaultdict(Counter)

    for (file_name, _), tokens in groups.items():
        for tri in _extract_trigrams_from_sentence(tokens):
            global_counter[tri] += 1
            book_counter[file_name][tri] += 1

    out_rows = []
    for tri, count in global_counter.most_common():
        subj, verb, obj = tri
        out_rows.append({
            "subj": subj, "verb": verb, "obj": obj,
            "count_total": count,
        })
    return out_rows


def export_trigrams(trigram_rows: list[dict]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / "ud_trigrams.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["subj", "verb", "obj", "count_total"])
        writer.writeheader()
        writer.writerows(trigram_rows[:5000])  # top 5k


# ==========================================================
# HEAD-DEPENDENT DISTANCE DISTRIBUTION
# ==========================================================

def compute_head_distances(token_rows: list[dict]) -> list[dict]:
    """
    For each non-ROOT token, compute linear distance to its head within the sentence.
    Groups by (file_name, sent_idx); uses token_idx for position.
    """
    groups: dict = defaultdict(list)
    for r in token_rows:
        key = (r["file_name"], r.get("sent_idx", r["sentence"]))
        groups[key].append(r)

    dist_rows = []
    for (file_name, _), tokens in groups.items():
        # Build token_text → first token_idx in this sentence
        text_to_idx: dict[str, int] = {}
        for t in tokens:
            txt = t["token"]
            if txt not in text_to_idx:
                text_to_idx[txt] = int(t.get("token_idx", 0))

        for t in tokens:
            if t["dep"].lower() in ("root", "punct") or t["head"].lower() == "root":
                continue
            head_idx = text_to_idx.get(t["head"])
            if head_idx is None:
                continue
            tok_idx = int(t.get("token_idx", 0))
            dist = abs(tok_idx - head_idx)
            dist_rows.append({
                "file_name": file_name,
                "dep":       t["dep"],
                "distance":  dist,
                "pos":       t["pos"],
            })
    return dist_rows


def export_head_distance_distribution(dist_rows: list[dict]) -> None:
    """Global distance frequency distribution (count per distance value)."""
    counter: Counter = Counter(r["distance"] for r in dist_rows)
    total = sum(counter.values())
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / "head_distance_distribution.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["distance", "count", "rate"])
        writer.writeheader()
        for dist in sorted(counter):
            writer.writerow({
                "distance": dist,
                "count":    counter[dist],
                "rate":     round(counter[dist] / total, 5) if total else 0.0,
            })


def export_head_distance_by_dep(dist_rows: list[dict]) -> None:
    """Mean/median/std of head-dependent distance per UD dependency type."""
    by_dep: dict = defaultdict(list)
    for r in dist_rows:
        by_dep[r["dep"]].append(r["distance"])

    out_rows = []
    for dep in sorted(by_dep):
        vs = sorted(by_dep[dep])
        n  = len(vs)
        mean = sum(vs) / n
        median = vs[n // 2]
        std = (sum((v - mean) ** 2 for v in vs) / n) ** 0.5 if n > 1 else 0.0
        out_rows.append({
            "dep":    dep,
            "n":      n,
            "mean":   round(mean, 3),
            "median": median,
            "std":    round(std, 3),
            "max":    max(vs),
        })
    out_rows.sort(key=lambda x: -x["n"])

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / "head_distance_by_dep.csv"
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["dep", "n", "mean", "median", "std", "max"])
        writer.writeheader()
        writer.writerows(out_rows)


def export_complexity_by_book(complexity_rows: list) -> None:
    by_book: dict = defaultdict(list)
    for r in complexity_rows:
        by_book[r["file_name"]].append(r)

    out_rows = []
    for file_name in sorted(by_book):
        rs = by_book[file_name]
        depths  = [r["tree_depth"]   for r in rs]
        clauses = [r["clause_count"] for r in rs]
        n = len(rs)
        out_rows.append({
            "file_name":       file_name,
            "sentence_count":  n,
            "avg_tree_depth":  round(sum(depths)  / n, 3) if n else 0.0,
            "max_tree_depth":  max(depths)  if depths  else 0,
            "avg_clause_count": round(sum(clauses) / n, 3) if n else 0.0,
        })

    output_file = OUTPUT_DIR / "complexity_by_book.csv"
    with output_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "file_name", "sentence_count",
                "avg_tree_depth", "max_tree_depth", "avg_clause_count",
            ],
        )
        writer.writeheader()
        writer.writerows(out_rows)


def export_dependency_by_book(rows):

    by_book = defaultdict(Counter)

    for row in rows:
        by_book[row["file_name"]][row["dep"]] += 1

    all_deps = sorted({
        row["dep"]
        for row in rows
    })

    output_file = OUTPUT_DIR / "dependency_by_book.csv"

    with output_file.open(
        "w",
        newline="",
        encoding="utf-8"
    ) as f:

        fieldnames = [
            "file_name",
            *all_deps,
            "total"
        ]

        writer = csv.DictWriter(
            f,
            fieldnames=fieldnames
        )

        writer.writeheader()

        for file_name, counter in by_book.items():

            total = sum(
                counter.values()
            )

            row = {
                "file_name": file_name,
                "total": total
            }

            for dep in all_deps:
                row[dep] = counter.get(
                    dep,
                    0
                )

            writer.writerow(row)


def main():

    rows = collect_dependency_rows()
    print(f"\nTotal dependency rows: {len(rows)}")

    export_token_dependency_rows(rows)
    export_dependency_counts(rows)
    export_head_lemma_counts(rows)
    export_dependency_by_book(rows)

    complexity = compute_complexity_rows(rows)
    print(f"Sentences with complexity metrics: {len(complexity)}")
    export_sentence_complexity(complexity)
    export_complexity_by_book(complexity)

    # ── UD trigrams ───────────────────────────────────────
    print("Extracting UD trigrams (nsubj→VERB→obj) ...")
    trigrams = extract_all_trigrams(rows)
    export_trigrams(trigrams)
    print(f"  Trigrams (unique): {len(trigrams)}")
    print("  Top 10:")
    for r in trigrams[:10]:
        print(f"    {r['subj']:<20} ← {r['verb']:<16} → {r['obj']:<20}  n={r['count_total']}")

    # ── Head-dependent distances ──────────────────────────
    print("Computing head-dependent distances ...")
    dist_rows = compute_head_distances(rows)
    export_head_distance_distribution(dist_rows)
    export_head_distance_by_dep(dist_rows)
    print(f"  Distance rows: {len(dist_rows)}")
    total = len(dist_rows)
    if total:
        mean_d = sum(r["distance"] for r in dist_rows) / total
        print(f"  Mean head distance (all deps): {mean_d:.2f} tokens")

    print(f"\nDONE — Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()