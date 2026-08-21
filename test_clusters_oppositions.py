"""Concept clusters and semantic opposition coverage."""
from __future__ import annotations

import unittest

from f_semantics import opposition_present
from lexicons_common import (
    CLUSTER_NOISE_LEMMAS,
    OPPOSITION_GROUPS,
    OPPOSITION_PAIRS,
    OPPOSITIONS,
    SEMANTIC_STOP_LEMMAS,
    matching_opposition_keys,
    opposition_present_in,
)
from r_word_network import CLUSTER_SEEDS, _get_tokens, assign_clusters
from t_config_tradition import canonicalize_lemma
from w_opposition_networks import (
    count_oppositions_in_lemma_windows,
    find_opposition_polarity,
    find_oppositions,
)


GN_ROWS = [
    {
        "file_name": "bible_BKR_Gn.txt",
        "sentence": "Na počátku stvořil Bůh nebe a zemi.",
        "lemmas": "počátek stvořit bůh nebe země",
    },
    {
        "file_name": "bible_BKR_Gn.txt",
        "sentence": "Země pak byla nesličná a pustá, a tma byla nad propastí.",
        "lemmas": "země tma propast duch bůh voda",
    },
    {
        "file_name": "bible_BKR_Gn.txt",
        "sentence": "I řekl Bůh: Buď světlo! I bylo světlo.",
        "lemmas": "říci bůh světlo",
    },
    {
        "file_name": "bible_BKR_Gn.txt",
        "sentence": "A viděl Bůh světlo, že bylo dobré; i oddělil Bůh světlo od tmy.",
        "lemmas": "vidět bůh světlo dobrý oddělit tmy",
    },
]


class OppositionLexiconTests(unittest.TestCase):
    def test_groups_cover_core_biblical_pairs(self):
        keys = {g.key for g in OPPOSITION_GROUPS}
        for key in (
            "světlo | tma",
            "život | smrt",
            "nebe | země",
            "dobrý | zlý",
            "víra | skutek",
            "milost | zákon",
            "duch | tělo",
            "moudrost | bláznovství",
            "požehnání | zlořečení",
        ):
            self.assertIn(key, keys)

    def test_single_source_matches_pair_list(self):
        derived = {(g.key.split(" | ")[0], g.key.split(" | ")[1]) for g in OPPOSITION_GROUPS}
        self.assertEqual(set(OPPOSITION_PAIRS), derived)
        self.assertTrue(set(OPPOSITIONS) <= {p[0] for p in derived})

    def test_synonym_poles_share_a_key(self):
        self.assertEqual(
            matching_opposition_keys({"světlo", "temnota"}),
            ["světlo | tma"],
        )
        self.assertEqual(
            matching_opposition_keys({"světlo", "tma"}),
            ["světlo | tma"],
        )

    def test_aliases_feed_opposition_matching(self):
        tokens = {canonicalize_lemma(w) for w in "oddělit bůh světlo tmy".split()}
        self.assertIn("světlo | tma", matching_opposition_keys(tokens))

    def test_sentence_level_helper_uses_groups(self):
        self.assertTrue(opposition_present(["světlo", "tmy"]))
        self.assertTrue(opposition_present_in({"život", "smrt"}))
        self.assertFalse(opposition_present(["světlo", "voda"]))


class OppositionDetectionTests(unittest.TestCase):
    def test_genesis_window_finds_light_dark_and_heaven_earth(self):
        counts, examples = find_oppositions(GN_ROWS, window=3)
        self.assertGreaterEqual(counts["světlo | tma"], 1)
        self.assertGreaterEqual(counts["nebe | země"], 1)
        self.assertTrue(examples["světlo | tma"])

    def test_polarity_uses_canonical_labels(self):
        _, directed = find_opposition_polarity(GN_ROWS, window=3)
        labels = {src for src, _ in directed} | {tgt for _, tgt in directed}
        self.assertTrue({"světlo", "tma"} <= labels or {"nebe", "země"} <= labels)

    def test_live_window_helper_agrees_with_row_detector(self):
        live = count_oppositions_in_lemma_windows(
            [r["lemmas"] for r in GN_ROWS], window=3,
        )
        counts, _ = find_oppositions(GN_ROWS, window=3)
        self.assertEqual(live, counts)


class ConceptClusterTests(unittest.TestCase):
    def test_seed_inventory_covers_new_biblical_fields(self):
        expected = {
            "cultic_cluster", "royal_cluster", "kinship_cluster",
            "war_cluster", "theological_cluster", "wisdom_cluster",
            "covenant_cluster", "judgment_cluster", "salvation_cluster",
            "creation_cluster", "prophetic_cluster", "moral_cluster",
        }
        self.assertEqual(set(CLUSTER_SEEDS), expected)
        for name, seeds in CLUSTER_SEEDS.items():
            self.assertGreaterEqual(len(seeds), 6, name)

    def test_tokens_strip_punctuation_and_canonicalize(self):
        tokens = _get_tokens({
            "lemmas": "světlo tmy boha, kteréž řekl",
            "sentence": "",
        })
        self.assertIn("světlo", tokens)
        self.assertIn("tma", tokens)
        self.assertIn("bůh", tokens)
        self.assertNotIn("kteréž", tokens)
        self.assertNotIn("řekl", tokens)
        self.assertNotIn("boha,", tokens)

    def test_stop_and_noise_lists_catch_bkr_function_words(self):
        self.assertIn("kteréž", SEMANTIC_STOP_LEMMAS)
        self.assertIn("jich", SEMANTIC_STOP_LEMMAS)
        self.assertIn("vám", SEMANTIC_STOP_LEMMAS)
        self.assertIn("řekl", CLUSTER_NOISE_LEMMAS)
        self.assertIn("stalo", CLUSTER_NOISE_LEMMAS)
        self.assertIn("jest", SEMANTIC_STOP_LEMMAS)
        self.assertIn("jsem", SEMANTIC_STOP_LEMMAS)
        self.assertIn("podlé", SEMANTIC_STOP_LEMMAS)

    def test_assign_clusters_keeps_seed_neighbours_drops_speech_verbs(self):
        relations = [
            {"word1": "král", "word2": "trůn", "pair_count": 8, "pmi": 6.1},
            {"word1": "král", "word2": "řekl", "pair_count": 12, "pmi": 5.0},
            {"word1": "oltář", "word2": "krev", "pair_count": 7, "pmi": 8.2},
        ]
        edges = assign_clusters(relations)
        royal_partners = {
            (r["word1"], r["word2"]) for r in edges["royal_cluster"]
        }
        self.assertIn(("král", "trůn"), royal_partners)
        self.assertNotIn(("král", "řekl"), royal_partners)
        self.assertTrue(edges["cultic_cluster"])


if __name__ == "__main__":
    unittest.main()
