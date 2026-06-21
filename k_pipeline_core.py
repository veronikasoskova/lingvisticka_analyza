"""
k_pipeline_core.py — Shared 4-stage analysis pipeline
Extracted from k_apply_all_to_bible._process_book() so that both
the Bible batch runner and the upload flow call the same code.
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

    if unit.unit_type == "book":
        input_unit = "book"
    elif unit.unit_type in {"chapter", "section"}:
        input_unit = unit.unit_type
    else:
        input_unit = "document"

    text_input = create_input_from_text(
        text=unit.text,
        source=unit.source,
        interaction=unit.interaction,
        stimulus=unit.stimulus,
        corpus_id=unit.corpus_id,
        source_id=unit.unit_id,
        unit=input_unit,
    )

    preprocessed = preprocess_text(text_input)
    features = extract_features(preprocessed)
    disc_context = resolve_discursive_context(
        features,
        unit.unit_id,
        allow_genre_priors=(unit.corpus_id == "bible_bkr" and unit.unit_type == "book"),
    )
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
        sk_row = asdict(sk)
        sk_row["unit_id"] = unit.unit_id
        sk_row["corpus_id"] = unit.corpus_id
        sk_row["display_name"] = unit.display_name
        sk_row["file_name"] = unit.unit_id          # backward-compat alias
        sk_row["rst_relation"] = rst_relations[i]
        result.skinner_rows.append(sk_row)

        # ── Stage 2: Verbal relations ────────────────────────────────────────
        rel = classify_relation(feat, sem, file_name=unit.unit_id)
        rel_row = asdict(rel)
        rel_row["unit_id"] = unit.unit_id
        rel_row["corpus_id"] = unit.corpus_id
        rel_row["display_name"] = unit.display_name
        rel_row["file_name"] = unit.unit_id         # backward-compat alias
        result.relation_rows.append(rel_row)

        # ── Stage 3: Refined descriptions ────────────────────────────────────
        ref = refine_description(feat, sem)
        ref_row = asdict(ref)
        ref_row["unit_id"] = unit.unit_id
        ref_row["corpus_id"] = unit.corpus_id
        ref_row["display_name"] = unit.display_name
        ref_row["file_name"] = unit.unit_id         # backward-compat alias
        result.refined_rows.append(ref_row)

    return result
