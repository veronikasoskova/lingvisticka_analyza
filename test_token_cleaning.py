"""Token cleaning for semantic centrality / PMI.

Locks in: punctuation is stripped from surface tokens before stop-word
matching, and BKR function words (jsem, kterýž, protož, jich, vám, takto…)
never enter the content-token stream.
"""
from __future__ import annotations

import unittest

from lexicons_common import (
    STOP_LEMMAS,
    STYLE_STOP_LEMMAS,
    SEMANTIC_STOP_LEMMAS,
    clean_surface_token,
    content_tokens,
)
from r_word_network import _get_tokens, _tokenize


class CleanSurfaceTokenTests(unittest.TestCase):
    def test_strips_comma_and_colon(self):
        self.assertEqual(clean_surface_token("zástupů:"), "zástupů")
        self.assertEqual(clean_surface_token("jejich,"), "jejich")
        self.assertEqual(clean_surface_token("hospodin:"), "hospodin")
        self.assertEqual(clean_surface_token("vám,"), "vám")
        self.assertEqual(clean_surface_token("jsem:"), "jsem")

    def test_strips_quotes_brackets_and_period(self):
        self.assertEqual(clean_surface_token('"krista,"'), "krista")
        self.assertEqual(clean_surface_token("(nebo"), "nebo")
        self.assertEqual(clean_surface_token("jich."), "jich")

    def test_drops_hyphenated_bkr_enclitic(self):
        self.assertEqual(clean_surface_token("díme-li,"), "díme")
        self.assertEqual(clean_surface_token("však-ž"), "však")


class ContentTokenFilterTests(unittest.TestCase):
    def test_function_words_dropped_even_with_punctuation(self):
        text = (
            "Takto praví Hospodin: jsem s vámi, protož když kteříž "
            "jich jejich, vám, kteriz, kdyz."
        )
        tokens = content_tokens(text, stop=STYLE_STOP_LEMMAS)
        for bad in (
            "takto", "jsem", "vám", "vámi", "protož", "když",
            "kteříž", "jich", "jejich", "hospodin",
        ):
            self.assertNotIn(bad, tokens, f"{bad!r} leaked into content tokens")
        self.assertIn("praví", tokens)

    def test_content_word_with_colon_is_kept(self):
        tokens = content_tokens("zástupů: přišel", stop=SEMANTIC_STOP_LEMMAS)
        self.assertIn("zástupů", tokens)
        self.assertIn("přišel", tokens)

    def test_short_particle_with_comma_is_dropped(self):
        # "se," / "aj," used to pass len>=3 because of the comma
        tokens = content_tokens("řekl se, aj, lidu", stop=STOP_LEMMAS)
        self.assertNotIn("se", tokens)
        self.assertNotIn("aj", tokens)
        self.assertIn("řekl", tokens)
        self.assertIn("lidu", tokens)

    def test_user_reported_forms_are_stops(self):
        for form in (
            "jsem", "takto", "vám", "vam", "protož", "protoz", "jich", "jejich",
            "když", "kdyz", "kterýž", "kteriz", "kteříž", "jest", "skrze",
        ):
            self.assertIn(form, STOP_LEMMAS, f"{form} missing from STOP_LEMMAS")


class WordNetworkTokenTests(unittest.TestCase):
    def test_get_tokens_cleans_dirty_lemmas(self):
        row = {
            "lemmas": "takto hospodin: jejich, zástupů: jsem vám, protož",
            "sentence": "",
        }
        tokens = _get_tokens(row)
        self.assertEqual(tokens, ["hospodin", "zástupů"])

    def test_tokenize_raw_sentence_drops_function_words(self):
        tokens = _tokenize("Když jsem k vám přišel, protož jich neviděl.")
        self.assertNotIn("když", tokens)
        self.assertNotIn("jsem", tokens)
        self.assertNotIn("vám", tokens)
        self.assertNotIn("protož", tokens)
        self.assertNotIn("jich", tokens)
        self.assertIn("přišel", tokens)
        self.assertIn("neviděl", tokens)


if __name__ == "__main__":
    unittest.main()
