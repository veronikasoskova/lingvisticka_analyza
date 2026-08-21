"""Lexical categorisation of religious / philosophical traditions."""
from __future__ import annotations

import unittest
from collections import Counter

from t_config_tradition import (
    ESCHATOLOGY,
    COVENANT_LAW,
    SACRED_SPACE,
    WISDOM_ELEMENTS,
    PROPHETIC_SPEECH,
    DIVINE_HIERARCHY,
    GENEALOGY_LINEAGE,
    BUDDHIST_ELEMENTS,
    HINDU_ELEMENTS,
    THEOSOPHICAL_ELEMENTS,
    GNOSTIC_INFLUENCE,
    PLATONIC_INFLUENCE,
    SHAMANIC_INFLUENCE,
    SUFI_INFLUENCE,
    NEW_AGE_INFLUENCE,
    STOIC_INFLUENCE,
    POLYVALENT_BIBLICAL_LEMMAS,
    PHILOSOPHICAL_INFLUENCES,
    SHARED_MOTIFS,
    analyze_lemma_set,
    detect_tradition_from_lemmas,
    distinctive,
)


BIBLE_CORE = {
    "bůh", "hospodin", "světlo", "tma", "duše", "tělo",
    "slovo", "tajemství", "duch", "láska", "zákon",
    "syn", "otec", "den", "čas", "nebe", "soud",
}


class ThematicCleanupTests(unittest.TestCase):
    def test_eschatology_drops_generic_time_words(self):
        for w in ("den", "čas", "přijít", "konec", "nebe", "soud"):
            self.assertNotIn(w, ESCHATOLOGY)

    def test_eschatology_keeps_real_terms(self):
        for w in ("vzkříšení", "peklo", "mesiáš", "antikrist"):
            self.assertIn(w, ESCHATOLOGY)

    def test_covenant_law_does_not_absorb_other_religions(self):
        for w in ("dharma", "vinaya", "šaría", "šaria", "svědectví"):
            self.assertNotIn(w, COVENANT_LAW)

    def test_dharma_lives_in_buddhist_and_not_covenant(self):
        self.assertIn("dharma", BUDDHIST_ELEMENTS)

    def test_sacred_space_drops_generic_mountain(self):
        self.assertNotIn("hora", SACRED_SPACE)

    def test_wisdom_drops_generic_word(self):
        self.assertNotIn("slovo", WISDOM_ELEMENTS)
        self.assertNotIn("zákon", WISDOM_ELEMENTS)

    def test_prophetic_drops_ordinary_says(self):
        self.assertNotIn("praví", PROPHETIC_SPEECH)

    def test_divine_hierarchy_drops_spirit(self):
        self.assertNotIn("duch", DIVINE_HIERARCHY)
        self.assertNotIn("spirit", DIVINE_HIERARCHY)

    def test_genealogy_drops_everyday_kinship(self):
        for w in ("syn", "otec", "dům"):
            self.assertNotIn(w, GENEALOGY_LINEAGE)


class PolyvalentIsolationTests(unittest.TestCase):
    def test_polyvalent_lemmas_stripped_from_distinctive(self):
        leaked = distinctive(POLYVALENT_BIBLICAL_LEMMAS)
        self.assertEqual(leaked, frozenset())

    def test_bible_core_is_not_foreign_philosophy(self):
        scored = analyze_lemma_set(BIBLE_CORE)
        self.assertEqual(scored["philosophical"], {})
        for fam in ("gnostic", "platonic", "theosophical", "shamanic",
                    "sufi", "new_age", "buddhist", "hindu", "tantric"):
            self.assertNotIn(fam, scored["tradition_diagnostic"])

    def test_bible_core_is_shared_motifs_not_gnostic(self):
        scored = analyze_lemma_set(BIBLE_CORE)
        self.assertIn("light_darkness", scored["shared_motifs"])
        self.assertIn("soul_body", scored["shared_motifs"])
        self.assertIn("mystery", scored["shared_motifs"])
        self.assertNotIn("světlo", GNOSTIC_INFLUENCE)
        self.assertNotIn("tma", GNOSTIC_INFLUENCE)
        self.assertNotIn("duše", PLATONIC_INFLUENCE)
        self.assertNotIn("tělo", PLATONIC_INFLUENCE)
        self.assertNotIn("duch", SHAMANIC_INFLUENCE)
        self.assertNotIn("láska", SUFI_INFLUENCE)
        self.assertNotIn("vědomí", NEW_AGE_INFLUENCE)
        self.assertNotIn("logos", {w for w in BIBLE_CORE})

    def test_philosophical_influences_exclude_polyvalent(self):
        for name, lexicon in PHILOSOPHICAL_INFLUENCES.items():
            leak = lexicon & POLYVALENT_BIBLICAL_LEMMAS
            self.assertEqual(
                leak, frozenset(),
                f"{name} still contains polyvalent lemmas: {sorted(leak)}",
            )


class DiagnosticDetectionTests(unittest.TestCase):
    def test_theosophy_detected_by_distinctive_terms(self):
        lemmas = {"akáša", "blavatská", "teosofie", "duše", "světlo"}
        scored = analyze_lemma_set(lemmas)
        self.assertEqual(scored["detected_tradition"], "theosophical")
        self.assertIn("theosophical", scored["tradition_diagnostic"])
        self.assertIn("akáša", scored["tradition_diagnostic"]["theosophical"])
        # polyvalent words still reported as shared, not as theosophy
        self.assertIn("soul_body", scored["shared_motifs"])

    def test_buddhism_detected(self):
        lemmas = {"buddha", "nirvána", "sangha", "dukkha", "karma"}
        scored = analyze_lemma_set(lemmas)
        self.assertEqual(scored["detected_tradition"], "buddhist")
        self.assertIn("buddha", BUDDHIST_ELEMENTS)

    def test_hindu_detected(self):
        lemmas = {"kršna", "bhagavad", "upanišad", "védánta"}
        self.assertEqual(
            detect_tradition_from_lemmas(Counter(lemmas)),
            "hindu",
        )

    def test_bible_like_is_christian_or_unknown_not_gnostic(self):
        # hospodin is a Christian/Jewish diagnostic; světlo is not
        detected = detect_tradition_from_lemmas(Counter(BIBLE_CORE))
        self.assertIn(detected, {"christian", "unknown"})
        self.assertNotEqual(detected, "gnostic")
        self.assertNotEqual(detected, "theosophical")
        self.assertNotEqual(detected, "buddhist")

    def test_stoic_logos_loanword_is_distinctive_but_absent_from_bkr(self):
        self.assertIn("logos", STOIC_INFLUENCE)
        self.assertNotIn("slovo", STOIC_INFLUENCE)

    def test_shared_motif_catalog_covers_false_friends(self):
        for motif in ("light_darkness", "soul_body", "spirit",
                      "logos_word", "mystery"):
            self.assertIn(motif, SHARED_MOTIFS)
            self.assertTrue(SHARED_MOTIFS[motif]["later_traditions"])
            self.assertTrue(SHARED_MOTIFS[motif]["biblical_home"])


class TheosophyKeywordTests(unittest.TestCase):
    def test_expected_theosophical_keywords_present(self):
        for w in ("teosofie", "teozofie", "blavatská", "akáša", "mahátma",
                  "antroposofie", "steiner", "dzyan"):
            self.assertIn(w, THEOSOPHICAL_ELEMENTS)

    def test_czech_false_friends_not_diagnostic(self):
        # "sama" = Czech "herself"; Sufi samā' must not use that token
        # "ráma" = biblical Ramah; Hindu Rama must not use that token alone
        self.assertNotIn("sama", SUFI_INFLUENCE)
        from t_config_tradition import HINDU_ELEMENTS as H
        self.assertNotIn("ráma", H)
        self.assertNotIn("rama", H)
        scored = analyze_lemma_set({"sama", "ráma", "bůh"})
        self.assertNotIn("sufi", scored["tradition_diagnostic"])
        self.assertNotIn("hindu", scored["tradition_diagnostic"])
        self.assertIn("jóga", HINDU_ELEMENTS)
        scored = analyze_lemma_set({"moudrost", "zákon", "modlitba"})
        self.assertNotIn("hindu", scored["tradition_diagnostic"])


if __name__ == "__main__":
    unittest.main()
