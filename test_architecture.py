"""Architectural cleanliness invariants.

These tests lock in path centralization, DB null handling, Bible-file glob
safety, and demo/production vocabulary alignment.  They do not require Stanza.
"""
from __future__ import annotations

import sqlite3
import unittest
from pathlib import Path

from a_paths import BIBLE_GLOB, DB_PATH, PROJECT_ROOT, list_bible_files
import n_db
from n_db import TABLE_SKINNER


class BibleFileDiscoveryTests(unittest.TestCase):
    def test_list_bible_files_excludes_requirements_txt(self):
        files = list_bible_files()
        names = {f.name for f in files}
        self.assertTrue(files, "expected bible_BKR_*.txt files in the repo")
        self.assertNotIn("requirements.txt", names)
        self.assertTrue(all(n.startswith("bible_BKR_") and n.endswith(".txt") for n in names))
        self.assertEqual(BIBLE_GLOB, "bible_BKR_*.txt")
        self.assertEqual(len(files), 66)

    def test_pipeline_modules_do_not_glob_all_txt(self):
        offenders = []
        for name in (
            "k_apply_all_to_bible.py",
            "x_style_authorship.py",
            "q_text_patterns.py",
            "y_dependency_hierarchy.py",
            "setup_fasttext_model.py",
            "j_q_skinner_taxonomy.py",
            "generate_demo_db.py",
        ):
            src = (PROJECT_ROOT / name).read_text(encoding="utf-8")
            if 'glob("*.txt")' in src or "glob('*.txt')" in src:
                offenders.append(name)
        self.assertEqual(offenders, [], f"generic *.txt glob still present in {offenders}")


class PathCanonicalizationTests(unittest.TestCase):
    def test_single_db_path(self):
        self.assertEqual(n_db.DB_PATH, DB_PATH)
        self.assertEqual(DB_PATH, PROJECT_ROOT / "output" / "bible_analysis.db")

    def test_process_unit_copies_lemmas_onto_skinner_rows(self):
        src = (PROJECT_ROOT / "k_pipeline_core.py").read_text(encoding="utf-8")
        self.assertIn('sk_row["lemmas"]', src)


class DatabaseNullHandlingTests(unittest.TestCase):
    def test_none_stored_as_sql_null(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "test.db"
            original = n_db.DB_PATH
            n_db.DB_PATH = db_path
            try:
                n_db.insert_rows(
                    TABLE_SKINNER,
                    [{
                        "sentence": "x",
                        "primary_intention": "record",
                        "secondary_intention": None,
                        "secondary_strategy": None,
                    }],
                    "run1",
                )
                conn = sqlite3.connect(db_path)
                raw = conn.execute(
                    "SELECT secondary_intention, secondary_strategy FROM skinner_analysis"
                ).fetchone()
                conn.close()
                self.assertIsNone(raw[0])
                self.assertIsNone(raw[1])

                rows = n_db.load_rows(TABLE_SKINNER, "run1")
                self.assertEqual(len(rows), 1)
                self.assertIsNone(rows[0]["secondary_intention"])
                self.assertIsNone(rows[0]["secondary_strategy"])
            finally:
                n_db.DB_PATH = original

    def test_legacy_none_string_normalized_on_read(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "legacy.db"
            original = n_db.DB_PATH
            n_db.DB_PATH = db_path
            try:
                conn = sqlite3.connect(db_path)
                conn.execute(
                    'CREATE TABLE skinner_analysis '
                    '(id INTEGER PRIMARY KEY AUTOINCREMENT, '
                    'secondary_intention TEXT, run_id TEXT)'
                )
                conn.execute(
                    'INSERT INTO skinner_analysis (secondary_intention, run_id) '
                    'VALUES (?, ?)',
                    ("None", "legacy"),
                )
                conn.commit()
                conn.close()
                rows = n_db.load_rows(TABLE_SKINNER, "legacy")
                self.assertEqual(len(rows), 1)
                self.assertIsNone(rows[0]["secondary_intention"])
            finally:
                n_db.DB_PATH = original

    def test_bool_flags_stored_as_zero_one(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "flags.db"
            original = n_db.DB_PATH
            n_db.DB_PATH = db_path
            try:
                n_db.insert_rows(
                    TABLE_SKINNER,
                    [{
                        "sentence": "x",
                        "has_coordination": True,
                        "dative_present": False,
                    }],
                    "run1",
                )
                conn = sqlite3.connect(db_path)
                raw = conn.execute(
                    "SELECT has_coordination, dative_present FROM skinner_analysis"
                ).fetchone()
                conn.close()
                self.assertEqual(raw[0], "1")
                self.assertEqual(raw[1], "0")
            finally:
                n_db.DB_PATH = original

    def test_coerce_numeric_columns_handles_true_false_text(self):
        import pandas as pd

        df = pd.DataFrame({
            "has_coordination": ["True", "False", "1", "0"],
            "confidence": ["0.73", "0.4", "0.9", "0.3"],
        })
        n_db.coerce_numeric_columns(df, ("has_coordination", "confidence"))
        self.assertEqual(list(df["has_coordination"]), [1.0, 0.0, 1.0, 0.0])
        self.assertAlmostEqual(df["has_coordination"].mean(), 0.5)
        self.assertAlmostEqual(float(df["confidence"].mean()), 0.5825)


class DemoVocabularyTests(unittest.TestCase):
    def test_demo_vocab_matches_production_classifiers(self):
        from generate_demo_db import (
            INTENTION_WEIGHTS,
            RELATION_WEIGHTS,
            DESC_WEIGHTS,
            assert_demo_vocab_aligned,
        )
        assert_demo_vocab_aligned()
        self.assertAlmostEqual(sum(INTENTION_WEIGHTS), 1.0, places=9)
        self.assertAlmostEqual(sum(RELATION_WEIGHTS), 1.0, places=9)
        self.assertAlmostEqual(sum(DESC_WEIGHTS), 1.0, places=9)


class ContextConsistencyTests(unittest.TestCase):
    def test_consistent_written_monologue_is_clean(self):
        from c_input import context_inconsistency_codes
        self.assertEqual(
            context_inconsistency_codes("written_record", "monologue", "unknown"),
            [],
        )

    def test_qa_stimulus_requires_dialogue(self):
        from c_input import CONTEXT_ISSUE_QA_MONO, context_inconsistency_codes, create_input_from_text
        self.assertEqual(
            context_inconsistency_codes("written_record", "monologue", "question_prompt"),
            [CONTEXT_ISSUE_QA_MONO],
        )
        with self.assertRaises(ValueError) as ctx:
            create_input_from_text(
                text="Otázka?",
                source="written_record",
                interaction="monologue",
                stimulus="question_prompt",
            )
        self.assertIn("dialogue", str(ctx.exception))

    def test_written_source_rejects_auditory_stimulus(self):
        from c_input import CONTEXT_ISSUE_AUDIO_WRITTEN, context_inconsistency_codes
        self.assertEqual(
            context_inconsistency_codes(
                "uploaded_document", "unknown", "auditory_verbal_stimulus"
            ),
            [CONTEXT_ISSUE_AUDIO_WRITTEN],
        )


if __name__ == "__main__":
    unittest.main()
