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
    python generate_demo_db.py          # all books, 40 verses each
    python generate_demo_db.py --full   # all books, all verses (slower)
"""

from __future__ import annotations

import ast
import random
import sys
from collections import Counter
from pathlib import Path

# ── paths ──────────────────────────────────────────────────────────────────
SRC = Path(__file__).parent
sys.path.insert(0, str(SRC))

from a_paths import BIBLE_FOLDER, OUTPUT_DIR, DB_PATH, list_bible_files
from n_db import insert_rows, TABLE_SKINNER, TABLE_RELATIONS, TABLE_REFINED
from t_config_tradition import canonicalize_lemma
from lexicons_common import clean_surface_token
from i_q_skinner_lexicons import ILLOCUTIONARY_FORCE_MAP, RHETORICAL_STRATEGY_VALUES
from j_q_skinner_taxonomy import CONVENTION_MAP
from m_verbal_relations import RELATION_TYPE_VALUES
from p_refine_descriptions import DESCRIPTION_TYPE_VALUES

RUN_ID  = "2024-01-01T00:00:00"        # fixed run_id for demo data

# Vocabularies are the production classifier labels so the demo DB is
# schema-compatible with a real k_apply_all_to_bible run.  Weights are
# synthetic (statistically plausible for BKR), not empirical.
INTENTIONS = [
    "legitimation", "commanding", "warning", "record", "praising",
    "declaring", "promising", "condemning", "justifying", "intervention",
    "mobilizing", "ideological_contestation", "persuading", "questioning",
    "narrative",
]

INTENTION_WEIGHTS = [
    0.13, 0.12, 0.11, 0.10, 0.09,
    0.08, 0.07, 0.06, 0.05, 0.04,
    0.03, 0.02, 0.03, 0.03, 0.04,
]

# Intention → typical rhetorical strategy (RHETORICAL_STRATEGY_VALUES).
# Convention names belong in the `convention` column, not primary_strategy.
STRATEGIES = {
    "legitimation":             "appeal_to_authority",
    "commanding":               "direct_address",
    "warning":                  "conditional_threat",
    "record":                   "narrative_example",
    "praising":                 "repetition",
    "declaring":                "appeal_to_authority",
    "promising":                "promise_of_reward",
    "condemning":               "contrast",
    "justifying":               "appeal_to_scripture",
    "intervention":             "rhetorical_question",
    "mobilizing":               "direct_address",
    "ideological_contestation": "contrast",
    "persuading":               "appeal_to_tradition",
    "questioning":              "rhetorical_question",
    "narrative":                "narrative_example",
}

RELATION_TYPES = [
    "reported_speech", "request_relation", "lyrical_relation",
    "historical_event_relation", "descriptive_relation",
    "prophetic_relation", "wisdom_relation", "genealogical_relation",
    "autoclitic_relation",
]
RELATION_WEIGHTS = [0.20, 0.14, 0.13, 0.16, 0.12, 0.08, 0.07, 0.06, 0.04]

DESCRIPTION_TYPES = [
    "theological_statement", "prophetic_announcement", "general_narrative",
    "legal_normative", "wisdom_maxim", "ritual_liturgical",
    "moral_statement", "social_relation", "creation_narrative",
    "genealogical_record", "eschatological", "attribute_description",
    "state_description",
]
DESC_WEIGHTS = [0.14, 0.12, 0.13, 0.10, 0.09, 0.08, 0.08, 0.07, 0.05, 0.05, 0.04, 0.03, 0.02]

SEMANTIC_CLUSTERS = [
    "description", "neutral", "request", "negation", "uncertainty",
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
    force     = ILLOCUTIONARY_FORCE_MAP.get(intention, "unknown")
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
        "convention":            CONVENTION_MAP.get(intention, "undetermined"),
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
        "lemmas":                "",
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
    # Strip punctuation from every token, then keep all unique lemmas in the
    # verse (not a 8-token cap). Function-word filtering happens at analysis
    # time in r_word_network / q_text_patterns.
    words = []
    for raw in str(sentence or "").split():
        tok = clean_surface_token(raw)
        if tok:
            words.append(canonicalize_lemma(tok))
    lemmas = " ".join(dict.fromkeys(words))
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
# Writes go through n_db.insert_rows so demo and production share one schema.


def _load_bible_files(limit_per_book: int | None) -> list[tuple[str, list[str]]]:
    """Return list of (file_name, sentences) from bible_BKR_*.txt files."""
    files = list_bible_files()
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

def assert_demo_vocab_aligned() -> None:
    """Guard: demo labels must be a subset of production classifier vocabularies."""
    unknown_strategies = set(STRATEGIES.values()) - RHETORICAL_STRATEGY_VALUES
    if unknown_strategies:
        raise ValueError(f"Demo strategies not in production vocab: {unknown_strategies}")
    unknown_relations = set(RELATION_TYPES) - RELATION_TYPE_VALUES
    if unknown_relations:
        raise ValueError(f"Demo relation types not in production vocab: {unknown_relations}")
    unknown_descriptions = set(DESCRIPTION_TYPES) - DESCRIPTION_TYPE_VALUES
    if unknown_descriptions:
        raise ValueError(f"Demo description types not in production vocab: {unknown_descriptions}")
    unknown_forces = {
        ILLOCUTIONARY_FORCE_MAP[i]
        for i in INTENTIONS
        if i in ILLOCUTIONARY_FORCE_MAP
    } - {"assertive", "directive", "commissive", "expressive", "declarative"}
    if unknown_forces:
        raise ValueError(f"Demo forces not in production vocab: {unknown_forces}")


def main(full: bool = False):
    assert_demo_vocab_aligned()
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
            sk = _make_skinner_row(sent_id, verse, file_name)
            rel = _make_relation_row(sent_id, verse, file_name)
            ref = _make_refined_row(sent_id, verse, file_name)
            sk["lemmas"] = ref["lemmas"]
            skinner_rows.append(sk)
            relation_rows.append(rel)
            refined_rows.append(ref)
            sent_id += 1

    print(f"  {sent_id - 1:,} sentences across {len(books)} books")
    print(f"Writing to: {DB_PATH}")

    DB_PATH.unlink(missing_ok=True)
    insert_rows(TABLE_SKINNER, skinner_rows, RUN_ID)
    insert_rows(TABLE_RELATIONS, relation_rows, RUN_ID)
    insert_rows(TABLE_REFINED, refined_rows, RUN_ID)
    print("  DB written.")

    # Analytics modules resolve output via a_paths.OUTPUT_DIR (cwd-independent).
    print("\nGenerating analytics CSV files…")

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
