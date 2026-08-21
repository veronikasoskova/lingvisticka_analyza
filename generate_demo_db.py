"""
generate_demo_db.py
===================
Creates output/bible_analysis.db with a representative sample of the
biblical corpus so that the "Biblický korpus" tab renders immediately
without requiring a full Stanza-based pipeline run.

This script uses only the Bible .txt files already present in the repo
and assigns synthetic (but statistically plausible) classification values
based on known distributions of the BKR biblical corpus.

Usage
-----
    python generate_demo_db.py          # all books, ~10 verses each
    python generate_demo_db.py --full   # all books, all verses (slower)
"""

from __future__ import annotations

import ast
import random
import re
import sqlite3
import sys
from collections import Counter
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────────
SRC = Path(__file__).parent
sys.path.insert(0, str(SRC))

from a_paths import BIBLE_FOLDER, OUTPUT_DIR
from t_config_tradition import canonicalize_lemma

DB_PATH = OUTPUT_DIR / "bible_analysis.db"
RUN_ID  = "2024-01-01T00:00:00"        # fixed run_id for demo data

# ── classification vocabularies ────────────────────────────────────────────
INTENTIONS = [
    "legitimation", "commanding", "warning", "record", "praising",
    "declaring", "promising", "condemning", "justifying", "intervention",
    "mobilizing", "ideological_contestation",
]

INTENTION_WEIGHTS = [
    0.14, 0.13, 0.12, 0.11, 0.10, 0.09, 0.08, 0.07, 0.06, 0.05, 0.03, 0.02,
]

STRATEGIES = {
    "legitimation":             "theophanic_self_presentation",
    "commanding":               "apodictic_law",
    "warning":                  "prophetic_admonition",
    "record":                   "narrative_chronicle",
    "praising":                 "doxological_hymn",
    "declaring":                "declarative_assertion",
    "promising":                "covenant_promise",
    "condemning":               "woe_oracle",
    "justifying":               "theological_rationale",
    "intervention":             "dialogic_controversy",
    "mobilizing":               "missionary_commission",
    "ideological_contestation": "antithetical_disputation",
}

FORCES = {
    "legitimation":             "assertive",
    "commanding":               "directive",
    "warning":                  "directive",
    "record":                   "assertive",
    "praising":                 "expressive",
    "declaring":                "declarative_assertion",
    "promising":                "commissive",
    "condemning":               "expressive",
    "justifying":               "assertive",
    "intervention":             "assertive",
    "mobilizing":               "directive",
    "ideological_contestation": "assertive",
}

RELATION_TYPES = [
    "reported_speech", "command_obedience", "lyrical", "narrative",
    "doctrinal", "prophetic", "wisdom",
]
RELATION_WEIGHTS = [0.22, 0.18, 0.15, 0.20, 0.12, 0.08, 0.05]

DESCRIPTION_TYPES = [
    "divine_speech", "prophetic_oracle", "narrative_event",
    "legal_injunction", "wisdom_saying", "doxological_praise",
    "covenant_formula", "lament", "blessing_formula", "theological_statement",
]
DESC_WEIGHTS = [0.18, 0.15, 0.14, 0.12, 0.10, 0.09, 0.08, 0.07, 0.05, 0.02]

SEMANTIC_CLUSTERS = [
    "divine_authority", "covenant_relationship", "moral_command",
    "historical_narrative", "eschatological_warning", "worship",
    "wisdom_instruction", "prophetic_judgment",
]

LOCUTION_TMPL = [
    "výrok o Bohu", "přímý příkaz", "zaslíbení", "výzva k poslušnosti",
    "narativní popis", "prorocké zvolání", "chvála", "nářek",
    "právní předpis", "teologické tvrzení",
]

CONVENTION_TMPL = [
    "právní formule", "prorocký žánr", "narativní žánr", "hymnický žánr",
    "mudroslovný žánr", "doxologie", "smlouva", "zákon",
]

POLITICAL_VOCAB_TMPL = [
    "zákon, smlouva", "Hospodin, lid", "spravedlnost, soud",
    "milost, věrnost", "", "", "",  # many sentences have no political vocab
]


rng = random.Random(42)     # deterministic seed for reproducibility


# ── helpers ─────────────────────────────────────────────────────────────────

def _weighted_choice(options, weights, rng=rng):
    return rng.choices(options, weights=weights, k=1)[0]


def _make_skinner_row(sentence_id: int, sentence: str, file_name: str) -> dict:
    intention = _weighted_choice(INTENTIONS, INTENTION_WEIGHTS)
    secondary = rng.choices(
        INTENTIONS + [None],
        weights=INTENTION_WEIGHTS + [0.40],
        k=1,
    )[0]
    if secondary == intention:
        secondary = None

    strategy  = STRATEGIES[intention]
    force     = FORCES[intention]
    conf      = round(rng.gauss(0.62, 0.15), 3)
    conf      = max(0.10, min(0.99, conf))

    words = sentence.split()
    ttr   = round(len(set(words)) / max(len(words), 1), 3)
    adj_c = rng.randint(0, 4)
    adv_c = rng.randint(0, 3)
    pro_c = rng.randint(0, 5)

    return {
        "sentence_id":           sentence_id,
        "sentence":              sentence,
        "source":                "written_record",
        "file_name":             file_name,
        "unit_id":               file_name,
        "corpus_id":             "bible_bkr",
        "display_name":          file_name.replace("bible_BKR_", "").replace(".txt", ""),
        "illocutionary_force":   force,
        "primary_intention":     intention,
        "secondary_intention":   secondary,
        "primary_strategy":      strategy,
        "secondary_strategy":    None,
        "locution":              rng.choice(LOCUTION_TMPL),
        "convention":            rng.choice(CONVENTION_TMPL),
        "linguistic_context":    "biblical_czech_bkr",
        "political_vocabulary":  rng.choice(POLITICAL_VOCAB_TMPL),
        "anti_anachronism":      "",
        "perlocutionary_effect": "",
        "context_note":          "",
        "confidence":            conf,
        "reason":                f"demo-{intention}",
        "type_token_ratio":      ttr,
        "has_coordination":      int(rng.random() < 0.25),
        "dative_present":        int(rng.random() < 0.15),
        "indirect_object_present": int(rng.random() < 0.12),
        "adjective_count":       adj_c,
        "adverb_count":          adv_c,
        "pronoun_count":         pro_c,
        "rst_relation":          rng.choice(["elaboration", "contrast", "cause", "sequence", "background"]),
    }


def _make_relation_row(sentence_id: int, sentence: str, file_name: str) -> dict:
    rel = _weighted_choice(RELATION_TYPES, RELATION_WEIGHTS)
    return {
        "sentence_id":   sentence_id,
        "sentence":      sentence,
        "file_name":     file_name,
        "unit_id":       file_name,
        "corpus_id":     "bible_bkr",
        "display_name":  file_name.replace("bible_BKR_", "").replace(".txt", ""),
        "relation_type": rel,
        "subtype":       rel,
        "confidence":    round(rng.gauss(0.60, 0.14), 3),
        "explanation":   f"demo-{rel}",
        "root_lemma":    sentence.split()[0].lower() if sentence else "",
        "local_pattern": f"V+{rel[:3]}",
        "semantic_cluster": rng.choice(SEMANTIC_CLUSTERS),
    }


def _make_refined_row(sentence_id: int, sentence: str, file_name: str) -> dict:
    dtype = _weighted_choice(DESCRIPTION_TYPES, DESC_WEIGHTS)
    raw_words = sentence.lower().split()
    words = []
    for token in raw_words:
        token = re.sub(r"[^\wáéíóúýěščřžďťňůäöüľĺŕ]+", "", token, flags=re.UNICODE)
        if token:
            words.append(canonicalize_lemma(token))
    lemmas = " ".join(dict.fromkeys(words[:8]))   # pseudo-lemmas + BKR aliases
    return {
        "sentence_id":    sentence_id,
        "sentence":       sentence,
        "file_name":      file_name,
        "unit_id":        file_name,
        "corpus_id":      "bible_bkr",
        "display_name":   file_name.replace("bible_BKR_", "").replace(".txt", ""),
        "description_type": dtype,
        "confidence":     round(rng.gauss(0.58, 0.13), 3),
        "explanation":    f"demo-{dtype}",
        "root_lemma":     words[0] if words else "",
        "semantic_cluster": rng.choice(SEMANTIC_CLUSTERS),
        "lemmas":         lemmas,
        "dep_tree":       "",
    }


# ── DB writer ────────────────────────────────────────────────────────────────

def _insert_rows(conn: sqlite3.Connection, table: str, rows: list[dict],
                 run_id: str):
    if not rows:
        return
    cols = list(rows[0].keys()) + ["run_id"]
    placeholders = ", ".join("?" * len(cols))
    col_sql = ", ".join(f'"{c}"' for c in cols)
    # Create table if absent (auto-schema from first row)
    col_defs = ", ".join(
        f'"{c}" TEXT' if isinstance(rows[0].get(c, ""), str) else f'"{c}"'
        for c in cols
    )
    conn.execute(
        f'CREATE TABLE IF NOT EXISTS "{table}" '
        f'(id INTEGER PRIMARY KEY AUTOINCREMENT, {col_defs})'
    )
    conn.executemany(
        f'INSERT INTO "{table}" ({col_sql}) VALUES ({placeholders})',
        [list(r.values()) + [run_id] for r in rows],
    )


def _load_bible_files(limit_per_book: int | None) -> list[tuple[str, list[str]]]:
    """Return list of (file_name, sentences) from bible_BKR_*.txt files."""
    files = sorted(BIBLE_FOLDER.glob("bible_BKR_*.txt"))
    if not files:
        raise FileNotFoundError(
            f"No bible_BKR_*.txt files in {BIBLE_FOLDER}. "
            "Check that BIBLE_FOLDER is set correctly in a_paths.py."
        )
    result = []
    for f in files:
        try:
            raw = f.read_text(encoding="utf-8").strip()
            data = ast.literal_eval(raw)
            verses = list(data.values()) if isinstance(data, dict) else []
        except Exception as exc:
            print(f"  WARN: could not parse {f.name}: {exc}")
            continue
        if limit_per_book is not None:
            verses = verses[:limit_per_book]
        result.append((f.name, verses))
    return result


# ── main ─────────────────────────────────────────────────────────────────────

def main(full: bool = False):
    limit = None if full else 40   # verses per book in demo mode

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Loading Bible files from: {BIBLE_FOLDER}")
    books = _load_bible_files(limit)
    print(f"  {len(books)} books found")

    skinner_rows: list[dict] = []
    relation_rows: list[dict] = []
    refined_rows:  list[dict] = []

    sent_id = 1
    for file_name, verses in books:
        for verse in verses:
            verse = verse.strip()
            if not verse:
                continue
            skinner_rows.append(_make_skinner_row(sent_id, verse, file_name))
            relation_rows.append(_make_relation_row(sent_id, verse, file_name))
            refined_rows.append(_make_refined_row(sent_id, verse, file_name))
            sent_id += 1

    print(f"  {sent_id - 1:,} sentences across {len(books)} books")
    print(f"Writing to: {DB_PATH}")

    DB_PATH.unlink(missing_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")

    _insert_rows(conn, "skinner_analysis",   skinner_rows,  RUN_ID)
    _insert_rows(conn, "verbal_relations",   relation_rows, RUN_ID)
    _insert_rows(conn, "refined_descriptions", refined_rows, RUN_ID)

    conn.commit()
    conn.close()
    print("  DB written.")

    # ── generate analytics CSVs ───────────────────────────────────────────
    print("\nGenerating analytics CSV files…")
    import os
    os.chdir(SRC)   # analytics scripts use relative "output/" paths

    try:
        from l_taxonomy_analytics import main as _tax_main
        _tax_main()
        print("  l_taxonomy_analytics done.")
    except Exception as exc:
        print(f"  WARN: l_taxonomy_analytics failed: {exc}")

    try:
        from o_verbal_relations_analytics import main as _vrel_main
        _vrel_main()
        print("  o_verbal_relations_analytics done.")
    except Exception as exc:
        print(f"  WARN: o_verbal_relations_analytics failed: {exc}")

    try:
        from s_word_relations_analytics import main as _word_main
        _word_main()
        print("  s_word_relations_analytics done.")
    except Exception as exc:
        print(f"  WARN: s_word_relations_analytics failed: {exc}")

    try:
        from u_religious_elements import main as _rel_main
        _rel_main()
        print("  u_religious_elements done.")
    except Exception as exc:
        print(f"  WARN: u_religious_elements failed: {exc}")

    try:
        from w_opposition_networks import main as _opp_main
        _opp_main()
        print("  w_opposition_networks done.")
    except Exception as exc:
        print(f"  WARN: w_opposition_networks failed: {exc}")

    try:
        from x_style_authorship import main as _style_main
        _style_main()
        print("  x_style_authorship done.")
    except Exception as exc:
        print(f"  WARN: x_style_authorship failed: {exc}")

    try:
        from y_dependency_hierarchy import main as _dep_main
        _dep_main()
        print("  y_dependency_hierarchy done.")
    except Exception as exc:
        print(f"  WARN: y_dependency_hierarchy failed: {exc}")

    try:
        from r_word_network import main as _net_main
        _net_main()
        print("  r_word_network done.")
    except Exception as exc:
        print(f"  WARN: r_word_network failed: {exc}")

    print(f"\nDone. DB = {DB_PATH}")
    intent_dist = Counter(r["primary_intention"] for r in skinner_rows)
    print("\nTop intentions:")
    for intent, count in intent_dist.most_common(5):
        print(f"  {intent:<30} {count:>5}")


if __name__ == "__main__":
    full = "--full" in sys.argv
    main(full=full)
