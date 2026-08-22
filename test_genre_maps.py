"""Coverage, aliases, and UI wiring for biblical literary genres."""
from __future__ import annotations

import unittest
from pathlib import Path

from a_paths import PROJECT_ROOT, list_bible_files
from c_unit import AnalysisUnit
from genre_maps import (
    BOOK_GENRES,
    COARSE_GENRES,
    FINE_GENRES,
    FINE_TO_COARSE,
    GENRE_LABELS,
    canonical_bkr_filename,
    detect_book_genre,
)
from k_pipeline_core import _with_unit
from m_verbal_relations import _GENRE_ADJ


class GenreMapCoverageTests(unittest.TestCase):
    def test_every_bible_file_has_exactly_one_genre(self):
        files = [f.name for f in list_bible_files()]
        self.assertEqual(len(files), 66)
        self.assertEqual(set(files), set(BOOK_GENRES))
        self.assertEqual(len(BOOK_GENRES), len(set(BOOK_GENRES)))

    def test_no_fine_genre_is_empty_or_unmapped(self):
        used = set(BOOK_GENRES.values())
        self.assertEqual(used, set(FINE_GENRES))
        self.assertTrue(used <= FINE_TO_COARSE.keys())

    def test_every_coarse_genre_has_adj_and_books(self):
        used_coarse = {FINE_TO_COARSE[g] for g in BOOK_GENRES.values()}
        self.assertEqual(used_coarse, set(COARSE_GENRES))
        self.assertTrue(used_coarse <= _GENRE_ADJ.keys())
        self.assertIn("law", used_coarse)
        self.assertIn("lyrical", used_coarse)

    def test_song_of_songs_is_lyrical_not_wisdom(self):
        self.assertEqual(detect_book_genre("bible_BKR_Pis.txt"), "lyrical_poetry")
        self.assertEqual(detect_book_genre("bible_BKR_Pis.txt", coarse=True), "lyrical")
        self.assertEqual(detect_book_genre("bible_BKR_Jb.txt", coarse=True), "wisdom")

    def test_lamentations_stays_lyrical(self):
        self.assertEqual(detect_book_genre("bible_BKR_Pl.txt"), "lyrical_poetry")

    def test_law_books_are_law_not_historical(self):
        self.assertEqual(detect_book_genre("bible_BKR_Lv.txt", coarse=True), "law")
        self.assertEqual(detect_book_genre("bible_BKR_Dt.txt", coarse=True), "law")
        self.assertEqual(detect_book_genre("bible_BKR_Gn.txt", coarse=True), "historical")

    def test_acts_is_historical_not_gospel(self):
        self.assertEqual(detect_book_genre("bible_BKR_Sk.txt"), "narrative_acts")
        self.assertEqual(detect_book_genre("bible_BKR_Sk.txt", coarse=True), "historical")


class GenreLookupTests(unittest.TestCase):
    def test_accepts_path_stem_and_abbrev(self):
        expected = "narrative_pentateuch"
        self.assertEqual(detect_book_genre("bible_BKR_Gn.txt"), expected)
        self.assertEqual(detect_book_genre(Path("/tmp/bible_BKR_Gn.txt")), expected)
        self.assertEqual(detect_book_genre("Gn"), expected)
        self.assertEqual(canonical_bkr_filename("Gn"), "bible_BKR_Gn.txt")

    def test_legacy_abbrev_aliases(self):
        self.assertEqual(detect_book_genre("bible_BKR_Ž.txt", coarse=True), "psalm")
        self.assertEqual(detect_book_genre("Př", coarse=True), "wisdom")
        self.assertEqual(detect_book_genre("Pís"), "lyrical_poetry")
        self.assertEqual(detect_book_genre("Dn"), "prophetic_major")
        self.assertEqual(detect_book_genre("Tt"), "epistle_pastoral")

    def test_unknown_and_empty(self):
        self.assertEqual(detect_book_genre(""), "unknown")
        self.assertEqual(detect_book_genre(None), "unknown")
        self.assertEqual(detect_book_genre("not_a_book.txt"), "unknown")


class GenreLabelTests(unittest.TestCase):
    def test_labels_cover_fine_and_coarse(self):
        for lang in ("cs", "sk", "en"):
            labels = GENRE_LABELS[lang]
            for key in FINE_GENRES | COARSE_GENRES | {"unknown"}:
                self.assertIn(key, labels, f"{lang}:{key}")
                self.assertTrue(labels[key].strip())
                self.assertNotIn("_", labels[key], f"{lang}:{key} still looks like a raw key")

    def test_app_wires_genre_labels_into_ui(self):
        src = (PROJECT_ROOT / "app.py").read_text(encoding="utf-8")
        self.assertIn("from genre_maps import GENRE_LABELS, detect_book_genre", src)
        self.assertIn('VALUE_LABELS["genre"] = GENRE_LABELS', src)
        self.assertIn('T["sec_genre"]', src)
        self.assertIn('T["col_genre"]', src)
        self.assertIn("_book_genre_label", src)


class AnalysisUnitGenreTests(unittest.TestCase):
    def test_bible_unit_auto_fills_genre(self):
        unit = AnalysisUnit(
            corpus_id="bible_bkr",
            unit_id="bible_BKR_Gn.txt",
            unit_type="book",
            display_name="Gn",
            text="Na počátku stvořil Bůh nebe a zemi.",
        )
        self.assertEqual(unit.genre, "narrative_pentateuch")
        row = _with_unit({}, unit)
        self.assertEqual(row["genre"], "narrative_pentateuch")
        self.assertEqual(row["file_name"], "bible_BKR_Gn.txt")

    def test_upload_unit_has_no_biblical_genre(self):
        unit = AnalysisUnit(
            corpus_id="upload_essay_20240101T000000",
            unit_id="chapter_01",
            unit_type="chapter",
            display_name="Kapitola 01",
            text="Nějaký nahraný text.",
        )
        self.assertEqual(unit.genre, "")
        row = _with_unit({}, unit)
        self.assertNotIn("genre", row)

    def test_explicit_genre_is_kept(self):
        unit = AnalysisUnit(
            corpus_id="bible_bkr",
            unit_id="bible_BKR_Pis.txt",
            unit_type="book",
            display_name="Pis",
            text="x",
            genre="lyrical_poetry",
        )
        self.assertEqual(unit.genre, "lyrical_poetry")


class DiscursiveLawModeTests(unittest.TestCase):
    def test_law_has_an_expected_mode(self):
        from j0_discursive_context import _GENRE_EXPECTED_MODE
        self.assertEqual(_GENRE_EXPECTED_MODE["law"], "directive")
        self.assertEqual(_GENRE_EXPECTED_MODE["lyrical"], "hymnic")


if __name__ == "__main__":
    unittest.main()
