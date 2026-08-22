"""
k_pipeline_core.py — Shared 4-stage analysis pipeline
Extracted from k_apply_all_to_bible._process_book() so that both
the Bible batch runner and the upload flow call the same code.

Architectural note:
- process_unit() is the production pipeline built around Quentin Skinner
  illocutionary analysis + downstream RST/relation/refinement stages.
- B.F. Skinner verbal-behavior rules (apply_skinner_rules in h_classifiers)
  are intentionally not part of this production path and are used only for
  training-data generation in k_apply_all_to_bible.make_training_data_from_bible().
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Optional

from c_input import create_input_from_text
from c_unit import AnalysisUnit, ProcessedUnit
from d_preprocessing import preprocess_text
from e_extraction import extract_features
from f_semantics import semantic_enrichment
from j0_discursive_context import resolve_discursive_context
from j0_rst_relations import annotate_rst
from j_q_skinner_taxonomy import classify_q_skinner
from m_verbal_relations import classify_relation
from p_refine_descriptions import refine_description


def process_unit(
    unit: AnalysisUnit,
    profile=None,
) -> ProcessedUnit:
    """Run the full 4-stage pipeline on a single AnalysisUnit.

    Stages
    ------
    1. Q. Skinner illocutionary classification
    2. RST relation annotation
    3. Verbal relations classification
    4. Refined description labelling

    Returns a ProcessedUnit with three row-lists ready for insert_rows().
    """

    text_input = create_input_from_text(
        text=unit.text,
        source=unit.source,
        interaction=unit.interaction,
        stimulus=unit.stimulus,
        corpus_id=unit.corpus_id,
        source_id=unit.unit_id,
        unit=unit.unit_type,
    )

    preprocessed = preprocess_text(text_input)
    features = extract_features(preprocessed)
    _use_genre_priors = unit.corpus_id == "bible_bkr" and unit.unit_type == "book"
    # Genre priors (biblical register weights) are enabled only for the Bible
    # corpus (corpus_id='bible_bkr', unit_type='book').  For uploaded texts,
    # use_genre_priors=False so the classifier uses generic, corpus-neutral
    # priors — this is intentional and keeps upload results unbiased.
    disc_context = resolve_discursive_context(features, unit.unit_id, use_genre_priors=_use_genre_priors)
    semantics = semantic_enrichment(features)
    rst_relations = annotate_rst(features)

    result = ProcessedUnit(unit=unit)

    for i, (feat, sem) in enumerate(zip(features, semantics)):
        if feat.root_lemma is None:
            continue

        # ── Stage 1: Q. Skinner ──────────────────────────────────────────────
        sk = classify_q_skinner(
            feat, sem, text_input,
            context=disc_context,
            profile=profile,
        )
        sk_row = _with_unit(asdict(sk), unit)
        sk_row["rst_relation"] = rst_relations[i]
        # Lemmas live on SentenceFeatures / RefinedDescription, not QSkinnerDecision.
        # Copy them onto the skinner row so upload UI / wordcloud / TF-IDF can
        # read a single table without joining refined_descriptions.
        sk_row["lemmas"] = feat.lemmas or ""
        result.skinner_rows.append(sk_row)

        # ── Stage 2: Verbal relations ────────────────────────────────────────
        rel = classify_relation(feat, sem, file_name=unit.unit_id)
        result.relation_rows.append(_with_unit(asdict(rel), unit))

        # ── Stage 3: Refined descriptions ────────────────────────────────────
        ref = refine_description(feat, sem)
        result.refined_rows.append(_with_unit(asdict(ref), unit))

    return result


def _with_unit(row: dict, unit: AnalysisUnit) -> dict:
    """Stamp shared unit identity onto a pipeline row.

    ``file_name`` is a backward-compat alias of ``unit_id`` (Bible books use
    the source filename; uploads use chapter/section/document ids).
    """
    row["unit_id"] = unit.unit_id
    row["corpus_id"] = unit.corpus_id
    row["display_name"] = unit.display_name
    row["file_name"] = unit.unit_id
    return row
