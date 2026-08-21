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
    DIVINE_ELEMENTS,
    KINSHIP_ELEMENTS,
    RITUAL_SACRIFICE,
    LIFE_DEATH_ELEMENTS,
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
    YHWH_ELEMENTS,
    CHRISTIAN_ELEMENTS,
    CHRISTOLOGICAL_ELEMENTS,
    analyze_lemma_set,
    analyze_sentences,
    detect_tradition_from_lemmas,
    distinctive,
    canonicalize_lemma,
    field_hits,
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
    def test_gated_supporting_only_after_distinctive_hit(self):
        bible = analyze_lemma_set({"duše", "světlo", "vědomí", "hospodin"})
        self.assertEqual(bible["supporting"], {})
        self.assertIn("soul_body", bible["shared_motifs"])

        theo = analyze_lemma_set(
            {"akáša", "teosofie", "duše", "světlo", "vědomí"}
        )
        self.assertEqual(theo["detected_tradition"], "theosophical")
        self.assertIn("theosophical", theo["supporting"])
        self.assertTrue({"duše", "světlo", "vědomí"} <= theo["supporting"]["theosophical"])

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

    def test_bible_like_is_yhwh_not_gnostic(self):
        # hospodin is the YHWH theonym layer, not a foreign philosophy
        detected = detect_tradition_from_lemmas(Counter(BIBLE_CORE))
        self.assertEqual(detected, "yhwh")
        self.assertNotEqual(detected, "gnostic")
        self.assertNotEqual(detected, "theosophical")
        self.assertNotEqual(detected, "buddhist")

    def test_hospodin_stays_in_christian_elements_and_yhwh(self):
        self.assertIn("hospodin", CHRISTIAN_ELEMENTS)
        self.assertIn("hospodin", YHWH_ELEMENTS)
        self.assertNotIn("hospodin", CHRISTOLOGICAL_ELEMENTS)

    def test_kristus_is_christian_not_only_yhwh(self):
        scored = analyze_lemma_set({"kristus", "evangelium", "kříž"})
        self.assertEqual(scored["detected_tradition"], "christian")
        self.assertIn("christian", scored["tradition_diagnostic"])
        self.assertNotIn("yhwh", scored["tradition_diagnostic"])

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


class LogosCompromiseTests(unittest.TestCase):
    def test_slovo_alone_is_word_common_not_stoic(self):
        scored = analyze_lemma_set({"slovo", "přišel", "muž"})
        self.assertIn("word_common", scored["shared_motifs"])
        self.assertNotIn("logos_word", scored["shared_motifs"])
        self.assertNotIn("stoic", scored["philosophical"])
        self.assertNotIn("stoic", scored["tradition_diagnostic"])

    def test_johannine_slovo_is_logos_and_stays_informative(self):
        scored = analyze_lemma_set({"slovo", "počátek", "světlo", "tělo"})
        self.assertIn("logos_word", scored["shared_motifs"])
        self.assertNotIn("word_common", scored["shared_motifs"])
        self.assertIn("stoic", SHARED_MOTIFS["logos_word"]["later_traditions"])
        self.assertNotIn("stoic", scored["philosophical"])

    def test_slovo_hospodinovo_is_dabar_not_logos(self):
        scored = analyze_lemma_set({"slovo", "hospodin", "prorok"})
        self.assertIn("word_of_god", scored["shared_motifs"])
        self.assertNotIn("logos_word", scored["shared_motifs"])
        self.assertNotIn("word_common", scored["shared_motifs"])

    def test_slovo_lemma_is_never_deleted(self):
        self.assertIn("slovo", POLYVALENT_BIBLICAL_LEMMAS)
        self.assertIn("slovo", SHARED_MOTIFS["logos_word"]["lemmas"])
        self.assertIn("slovo", SHARED_MOTIFS["word_of_god"]["lemmas"])
        self.assertIn("slovo", SHARED_MOTIFS["word_common"]["lemmas"])


class ContextGateTests(unittest.TestCase):
    def test_pan_without_god_is_not_divine(self):
        self.assertIn("pán", DIVINE_ELEMENTS)
        self.assertEqual(field_hits({"pán", "král"}, "divine", DIVINE_ELEMENTS), set())
        self.assertIn("pán", field_hits({"pán", "bůh"}, "divine", DIVINE_ELEMENTS))

    def test_krev_requires_sacrifice_cluster(self):
        self.assertIn("krev", RITUAL_SACRIFICE)
        self.assertEqual(
            field_hits({"krev", "zabít"}, "ritual_sacrifice", RITUAL_SACRIFICE),
            set(),
        )
        self.assertIn(
            "krev",
            field_hits({"krev", "oběť", "oltář"}, "ritual_sacrifice", RITUAL_SACRIFICE),
        )

    def test_syn_bozi_is_not_kinship(self):
        self.assertIn("syn", KINSHIP_ELEMENTS)
        self.assertEqual(
            field_hits({"syn", "bůh"}, "kinship", KINSHIP_ELEMENTS),
            set(),
        )
        self.assertIn(
            "syn",
            field_hits({"syn", "dcera", "matka"}, "kinship", KINSHIP_ELEMENTS),
        )

    def test_zivot_without_theological_co_text_is_not_life_death(self):
        self.assertIn("život", LIFE_DEATH_ELEMENTS)
        self.assertEqual(
            field_hits({"život", "otroctví"}, "life_death", LIFE_DEATH_ELEMENTS),
            set(),
        )
        self.assertIn(
            "život",
            field_hits({"život", "věčný"}, "life_death", LIFE_DEATH_ELEMENTS),
        )


class AliasAndEncliticTests(unittest.TestCase):
    def test_bkr_surface_forms_canonicalize(self):
        self.assertEqual(canonicalize_lemma("Krista"), "kristus")
        self.assertEqual(canonicalize_lemma("Hospodina"), "hospodin")
        self.assertEqual(canonicalize_lemma("obět"), "oběť")
        self.assertEqual(canonicalize_lemma("temnostech"), "temnota")
        self.assertEqual(canonicalize_lemma("Jezukrista"), "ježíš")

    def test_aliased_forms_detect_christian_and_yhwh(self):
        scored = analyze_lemma_set({"Krista", "Hospodina", "obět"})
        self.assertIn("christian", scored["tradition_diagnostic"])
        self.assertIn("yhwh", scored["tradition_diagnostic"])
        self.assertIn("oběť", scored["thematic"]["ritual_sacrifice"])

    def test_gates_are_per_sentence_not_document(self):
        scored = analyze_sentences([
            {"slovo", "muž", "přišel"},
            {"počátek", "světlo", "bůh"},
        ])
        self.assertIn("word_common", scored["shared_motifs"])
        self.assertNotIn("logos_word", scored["shared_motifs"])

    def test_attached_t_enclitic_splits_but_keeps_nebot(self):
        from d_preprocessing import normalize_bkr
        self.assertEqual(normalize_bkr("nyníť pravím"), "nyní ť pravím")
        self.assertEqual(normalize_bkr("neboť Bůh miloval"), "neboť Bůh miloval")


if __name__ == "__main__":
    unittest.main()
