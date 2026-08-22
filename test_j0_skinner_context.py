"""Regression tests for the Q-Skinner lexicons, context profile, discursive
context, and RST relation modules.  No Stanza required.
"""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from i_q_skinner_lexicons import (
    EMOTIVE_HOPE_LEMMAS,
    ILLOCUTIONARY_FORCE_MAP,
    INTENTION_VALUES,
    QUESTIONING_MARKER_LEMMAS,
    REWARD_CONDITION_LEMMAS,
    THREAT_CONDITION_LEMMAS,
    WARNING_CONDITION_LEMMAS,
    WARNING_PREVENTIVE_LEMMAS,
    compute_corpus_idf,
)
from j0_context_profile import (
    compute_profile_idf_delta,
    get_builtin_profile,
    load_profile_or_none,
)
from j0_discursive_context import (
    _GENRE_EXPECTED_MODE,
    _MODE_EXPECTED,
    _MODE_INTENTION_BOOSTS,
    _genre_cross_validate,
    resolve_discursive_context,
)
from j0_rst_relations import annotate_rst, classify_rst_relation, rst_profile
from j_r_perlocutionary_effect import (
    _INTENTION_TO_EFFECT,
    PERLOCUTION_DEONTIC_LEMMAS,
    PERLOCUTION_FEAR_LEMMAS,
    PERLOCUTION_HOPE_LEMMAS,
    derive_perlocutionary_effect,
)


def _feat(**kwargs):
    defaults = dict(
        lemmas="",
        root_tense="Pres",
        is_imperative_like=False,
        has_question=False,
        has_conditional=False,
    )
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


class LexiconBugfixTests(unittest.TestCase):
    def test_force_map_covers_every_intention(self):
        self.assertEqual(set(ILLOCUTIONARY_FORCE_MAP), INTENTION_VALUES)

    def test_question_markers_are_not_content_words(self):
        for lemma in ("přivázat", "povolat", "svobodný", "služebník"):
            self.assertNotIn(lemma, QUESTIONING_MARKER_LEMMAS)

    def test_threat_condition_matches_bkr_paklit(self):
        self.assertIn("pakliť", THREAT_CONDITION_LEMMAS)
        self.assertIn("pakliť", WARNING_CONDITION_LEMMAS)

    def test_reward_condition_does_not_use_dead_budete(self):
        self.assertNotIn("budete", REWARD_CONDITION_LEMMAS)
        self.assertIn("li", REWARD_CONDITION_LEMMAS)

    def test_preventive_lexicon_has_no_multiword_phrase(self):
        self.assertNotIn("take care", WARNING_PREVENTIVE_LEMMAS)
        self.assertTrue(all(" " not in lemma for lemma in WARNING_PREVENTIVE_LEMMAS))

    def test_hope_lexicon_uses_czech_upokojit(self):
        self.assertIn("upokojit", EMOTIVE_HOPE_LEMMAS)
        self.assertNotIn("upokojiť", EMOTIVE_HOPE_LEMMAS)

    def test_corpus_idf_tolerates_none_lemmas(self):
        idf = compute_corpus_idf([
            {"lemmas": None},
            {"lemmas": "bůh slovo"},
            {},
        ])
        self.assertIn("bůh", idf)
        self.assertGreater(idf["bůh"], 0.0)


class ContextProfileTests(unittest.TestCase):
    def test_bkr_profile_boosts_formulaic_rare_lemmas(self):
        profile = get_builtin_profile("biblical_czech_bkr")
        feat = _feat(lemmas="haleluja amen zpívat")
        delta = compute_profile_idf_delta(feat, profile)
        self.assertGreater(delta, 0.0)

    def test_esoteric_profile_penalises_prophetic_condemnation(self):
        profile = get_builtin_profile("esoteric_christian_en")
        feat = _feat(lemmas="běda")
        delta = compute_profile_idf_delta(feat, profile)
        self.assertLess(delta, 0.0)

    def test_load_profile_or_none_swallows_corrupt_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "broken.json"
            bad.write_text("{not json", encoding="utf-8")
            self.assertIsNone(load_profile_or_none(str(bad)))
            self.assertIsNone(load_profile_or_none("no_such_profile", Path(tmp)))


class DiscursiveContextTests(unittest.TestCase):
    def test_intention_boosts_are_not_aliased_to_module_map(self):
        feats = [_feat(lemmas="amen sláva zpívat chválit", root_tense="Pres")] * 4
        ctx = resolve_discursive_context(feats)
        self.assertEqual(ctx.dominant_mode, "hymnic")
        original = _MODE_INTENTION_BOOSTS["hymnic"]["praising"]
        ctx.intention_boosts["praising"] = 99.0
        self.assertEqual(_MODE_INTENTION_BOOSTS["hymnic"]["praising"], original)

    def test_hymnic_expected_intentions_are_actual_intentions(self):
        self.assertTrue(_MODE_EXPECTED["hymnic"] <= INTENTION_VALUES)
        self.assertNotIn("repetition", _MODE_EXPECTED["hymnic"])

    def test_law_genre_maps_to_directive(self):
        self.assertEqual(_GENRE_EXPECTED_MODE["law"], "directive")

    def test_genre_lookup_uses_basename(self):
        genre, note = _genre_cross_validate("prophetic", "/tmp/data/bible_BKR_Abd.txt")
        self.assertEqual(genre, "prophetic")
        self.assertIn("genre_mode_agreement", note)

    def test_empty_features_are_undetermined(self):
        ctx = resolve_discursive_context([])
        self.assertEqual(ctx.dominant_mode, "undetermined")
        self.assertEqual(ctx.illocutionary_density, 0.0)


class RstRelationTests(unittest.TestCase):
    def test_consecutive_questions_are_not_answers(self):
        prev = _feat(has_question=True, lemmas="proč bouřit národ")
        cur = _feat(has_question=True, lemmas="kde být prorok")
        self.assertEqual(classify_rst_relation(prev, cur), "question")

    def test_question_then_statement_is_answer(self):
        prev = _feat(has_question=True, lemmas="proč bouřit národ")
        cur = _feat(has_question=False, lemmas="hospodin smát se")
        self.assertEqual(classify_rst_relation(prev, cur), "answer")

    def test_causal_proto_connector(self):
        prev = _feat(lemmas="činit pokání")
        cur = _feat(lemmas="proto přiblížit království")
        self.assertEqual(classify_rst_relation(prev, cur), "cause")

    def test_paklit_condition_connector(self):
        prev = _feat(lemmas="slyšet slovo")
        cur = _feat(lemmas="pakliť nepřijmout zahynout")
        self.assertEqual(classify_rst_relation(prev, cur), "condition")

    def test_annotate_rst_length_and_first_label(self):
        feats = [
            _feat(lemmas="na počátek stvořit"),
            _feat(lemmas="ale země být pustý"),
            _feat(lemmas="neboť bůh říci"),
        ]
        labels = annotate_rst(feats)
        self.assertEqual(len(labels), 3)
        self.assertEqual(labels[0], "continuation")
        self.assertEqual(labels[1], "contrast")
        self.assertEqual(labels[2], "cause")

    def test_rst_profile_density(self):
        profile = rst_profile(["continuation", "contrast", "cause", "continuation"])
        self.assertEqual(profile["total"], 4)
        self.assertEqual(profile["coherence_density"], 0.5)


class PerlocutionaryEffectTests(unittest.TestCase):
    def test_map_covers_every_intention(self):
        self.assertTrue(INTENTION_VALUES <= set(_INTENTION_TO_EFFECT))
        self.assertEqual(_INTENTION_TO_EFFECT["unclassified"], "effect_indeterminate")

    def test_warning_without_emotive_stays_inferred(self):
        self.assertEqual(
            derive_perlocutionary_effect(_feat(lemmas="jestliže varovat"), "warning"),
            "evoke_fear_urgency",
        )

    def test_warning_plus_fear_is_lexical_confirmation(self):
        self.assertEqual(
            derive_perlocutionary_effect(_feat(lemmas="strach zahynout"), "warning"),
            "evoke_fear_urgency[lexically_confirmed]",
        )

    def test_warning_plus_threat_outcome_confirms_fear(self):
        self.assertEqual(
            derive_perlocutionary_effect(_feat(lemmas="jestliže zahynout"), "warning"),
            "evoke_fear_urgency[lexically_confirmed]",
        )

    def test_warning_plus_divine_wrath_confirms_fear(self):
        self.assertEqual(
            derive_perlocutionary_effect(_feat(lemmas="hněv soud"), "warning"),
            "evoke_fear_urgency[lexically_confirmed]",
        )

    def test_bozi_alone_is_not_fear_evidence(self):
        self.assertNotIn("boží", PERLOCUTION_FEAR_LEMMAS)
        self.assertEqual(
            derive_perlocutionary_effect(_feat(lemmas="boží slovo"), "declaring"),
            "evoke_belief_understanding",
        )

    def test_promising_plus_beatitude_confirms_hope(self):
        self.assertEqual(
            derive_perlocutionary_effect(_feat(lemmas="blahoslavený dát"), "promising"),
            "evoke_hope_trust[lexically_confirmed]",
        )

    def test_promising_plus_eschatological_reward_confirms_hope(self):
        self.assertEqual(
            derive_perlocutionary_effect(_feat(lemmas="království věčný"), "promising"),
            "evoke_hope_trust[lexically_confirmed]",
        )

    def test_slava_alone_is_not_hope_evidence(self):
        self.assertNotIn("sláva", PERLOCUTION_HOPE_LEMMAS)
        self.assertEqual(
            derive_perlocutionary_effect(_feat(lemmas="sláva amen"), "praising"),
            "evoke_awe_reverence",
        )

    def test_commanding_plus_deontic_confirms_compliance(self):
        self.assertEqual(
            derive_perlocutionary_effect(_feat(lemmas="muset činit"), "commanding"),
            "evoke_compliance_obedience[lexically_confirmed]",
        )

    def test_mit_alone_is_not_deontic_evidence(self):
        self.assertNotIn("mít", PERLOCUTION_DEONTIC_LEMMAS)
        self.assertEqual(
            derive_perlocutionary_effect(_feat(lemmas="mít dům"), "commanding"),
            "evoke_compliance_obedience",
        )

    def test_condemning_plus_guilt_is_lexical_confirmation(self):
        self.assertEqual(
            derive_perlocutionary_effect(_feat(lemmas="vina hřích"), "condemning"),
            "evoke_shame_guilt[lexically_confirmed]",
        )

    def test_warning_plus_fear_is_lexical_confirmation(self):
        self.assertEqual(
            derive_perlocutionary_effect(_feat(lemmas="strach zahynout"), "warning"),
            "evoke_fear_urgency[lexically_confirmed]",
        )

    def test_condemning_plus_fear_does_not_rewrite_to_fear(self):
        # Fear does not confirm shame/guilt; keep the inferred effect and attach fear.
        self.assertEqual(
            derive_perlocutionary_effect(_feat(lemmas="strach hřích"), "condemning"),
            "evoke_shame_guilt+fear_evoked",
        )

    def test_justifying_plus_hope_does_not_rewrite_to_hope_trust(self):
        self.assertEqual(
            derive_perlocutionary_effect(_feat(lemmas="naděje neboť"), "justifying"),
            "evoke_trust_assurance+hope_evoked",
        )

    def test_promising_plus_hope_is_lexical_confirmation(self):
        self.assertEqual(
            derive_perlocutionary_effect(_feat(lemmas="naděje dát"), "promising"),
            "evoke_hope_trust[lexically_confirmed]",
        )

    def test_condemning_plus_hope_is_tension(self):
        self.assertEqual(
            derive_perlocutionary_effect(_feat(lemmas="naděje běda"), "condemning"),
            "evoke_fear_urgency+hope_despite_judgment",
        )

    def test_reader_address_is_suffixed(self):
        self.assertEqual(
            derive_perlocutionary_effect(_feat(lemmas="vy slovo"), "declaring"),
            "evoke_belief_understanding; reader_directly_addressed",
        )

    def test_unknown_intention_is_indeterminate(self):
        self.assertEqual(
            derive_perlocutionary_effect(_feat(lemmas=""), "not_a_real_intention"),
            "effect_indeterminate",
        )


if __name__ == "__main__":
    unittest.main()
