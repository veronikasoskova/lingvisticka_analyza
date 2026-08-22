"""Displayed-data language form: every stored classifier key has a CS/SK/EN label."""
from __future__ import annotations

import ast
import sqlite3
import unittest

from a_paths import DB_PATH, PROJECT_ROOT
from generate_demo_db import RUN_ID as DEMO_RUN_ID


def _load_assign(name: str):
    src = (PROJECT_ROOT / "app.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    for node in tree.body:
        if isinstance(node, ast.AnnAssign):
            target = node.target
            value = node.value
        elif isinstance(node, ast.Assign) and node.targets:
            target = node.targets[0]
            value = node.value
        else:
            continue
        if isinstance(target, ast.Name) and target.id == name:
            return ast.literal_eval(value)
    raise AssertionError(f"{name} not found as a literal in app.py")


VALUE_LABELS = _load_assign("VALUE_LABELS")
BOOK_NAMES = _load_assign("BOOK_NAMES")


class BookNameFormTests(unittest.TestCase):
    def test_slovak_epistle_names_use_slovak_dative(self):
        self.assertEqual(BOOK_NAMES["R"]["sk"], "Rimanom")
        self.assertEqual(BOOK_NAMES["1K"]["sk"], "1. Korinťanom")
        self.assertEqual(BOOK_NAMES["2K"]["sk"], "2. Korinťanom")
        self.assertEqual(BOOK_NAMES["Ko"]["sk"], "Kolosanom")
        self.assertEqual(BOOK_NAMES["Ju"]["sk"], "Júdov")
        self.assertEqual(BOOK_NAMES["Sd"]["sk"], "Sudcovia")
        self.assertEqual(BOOK_NAMES["1Pa"]["sk"], "1. kniha kroník")
        self.assertEqual(BOOK_NAMES["2Pa"]["sk"], "2. kniha kroník")

    def test_every_book_has_cs_sk_en(self):
        for abbr, names in BOOK_NAMES.items():
            self.assertEqual(set(names), {"cs", "sk", "en"}, abbr)


class DemoDbDisplayLabelTests(unittest.TestCase):
    COL_TO_MAP = {
        "illocutionary_force": "force",
        "primary_intention": "intention",
        "secondary_intention": "intention",
        "primary_strategy": "strategy",
        "convention": "convention",
        "locution": "locution",
        "relation_type": "verbal_type",
        "semantic_cluster": "semantic_cluster",
        "description_type": "description_type",
    }

    def test_demo_db_categorical_values_have_ui_labels(self):
        from a_paths import ensure_bible_db
        ensure_bible_db()
        self.assertTrue(DB_PATH.exists(), "bible_analysis.db must unpack from .db.gz")
        conn = sqlite3.connect(DB_PATH)
        missing = []
        tables = {
            "skinner_analysis": (
                "illocutionary_force", "primary_intention", "secondary_intention",
                "primary_strategy", "convention", "locution",
            ),
            "verbal_relations": ("relation_type", "semantic_cluster"),
            "refined_descriptions": ("description_type", "semantic_cluster"),
        }
        for table, cols in tables.items():
            for col in cols:
                mapping_name = self.COL_TO_MAP[col]
                for lang in ("cs", "sk", "en"):
                    labels = VALUE_LABELS[mapping_name][lang]
                    rows = conn.execute(
                        f'SELECT DISTINCT "{col}" FROM "{table}" '
                        f'WHERE run_id = ? AND "{col}" IS NOT NULL AND "{col}" != ""',
                        (DEMO_RUN_ID,),
                    )
                    for (raw,) in rows:
                        if str(raw) not in labels:
                            missing.append(f"{lang}:{table}.{col}={raw}")
        conn.close()
        self.assertEqual(missing, [], f"untranslated displayed values: {missing[:40]}")

    def test_legacy_and_production_relation_keys_covered(self):
        sk = VALUE_LABELS["verbal_type"]["sk"]
        for key in (
            "command_obedience", "doctrinal", "narrative", "lyrical",
            "prophetic", "wisdom", "reported_speech",
            "descriptive_relation", "request_relation",
        ):
            self.assertIn(key, sk, key)
            self.assertNotIn("_", sk[key], f"{key} still looks like a raw key: {sk[key]}")

    def test_live_run_classifier_keys_have_ui_labels(self):
        from a_paths import ensure_bible_db
        from n_db import latest_bible_run_id, TABLE_SKINNER, TABLE_RELATIONS

        ensure_bible_db()
        if not DB_PATH.exists():
            self.skipTest("no bible DB")
        run_id = latest_bible_run_id(TABLE_SKINNER)
        if run_id is None or run_id == DEMO_RUN_ID:
            self.skipTest("no live bible run")
        conn = sqlite3.connect(DB_PATH)
        missing = []
        for lang in ("cs", "sk", "en"):
            labels = VALUE_LABELS["convention"][lang]
            for (raw,) in conn.execute(
                'SELECT DISTINCT convention FROM skinner_analysis '
                'WHERE run_id = ? AND convention IS NOT NULL AND convention != ""',
                (run_id,),
            ):
                if str(raw) not in labels:
                    missing.append(f"{lang}:convention={raw}")
            loc_labels = VALUE_LABELS["locution"][lang]
            for (raw,) in conn.execute(
                'SELECT DISTINCT locution FROM skinner_analysis '
                'WHERE run_id = ? AND locution IS NOT NULL AND locution != ""',
                (run_id,),
            ):
                if str(raw) not in loc_labels:
                    missing.append(f"{lang}:locution={raw}")
            vlabels = VALUE_LABELS["verbal_type"][lang]
            for (raw,) in conn.execute(
                'SELECT DISTINCT subtype FROM verbal_relations '
                'WHERE run_id = ? AND subtype IS NOT NULL AND subtype != ""',
                (run_id,),
            ):
                if str(raw) not in vlabels:
                    missing.append(f"{lang}:subtype={raw}")
        conn.close()
        self.assertEqual(missing, [], f"untranslated live keys: {missing[:40]}")


if __name__ == "__main__":
    unittest.main()
