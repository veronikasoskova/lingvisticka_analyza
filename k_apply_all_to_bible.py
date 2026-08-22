from pathlib import Path
from typing import List
import os

from c_input import create_input_from_file, load_text_from_file
from c_unit import AnalysisUnit
# B.F. Skinner verbal-behavior rules are used here only for training-data
# generation (make_training_data_from_bible), not in the production process_unit().
from h_classifiers import apply_skinner_rules, SkinnerDecision
from j0_context_profile import get_builtin_profile
from k_pipeline_core import process_unit

_BKR_PROFILE = get_builtin_profile("biblical_czech_bkr")
from a_paths import BIBLE_FOLDER, BIBLE_GLOB, list_bible_files
from n_db import (
    insert_rows, make_run_id, DB_PATH,
    TABLE_SKINNER, TABLE_RELATIONS, TABLE_REFINED, TABLE_TRAINING,
)


# ==========================================================
# K1. PATHS / CONFIG
# ==========================================================

FILES_LIMIT = int(os.environ.get("PIPELINE_FILES_LIMIT", 10))


# ==========================================================
# K2. INPUT CREATION (kept for _classify_file / training data)
# ==========================================================

def _make_input(file_path):

    return create_input_from_file(
        file_path=str(file_path),
        source="written_record",
        interaction="monologue",
        stimulus="unknown",
        speaker="unknown",
        addressee="unknown",
        notes=f"Bible file: {file_path.name}",
    )


# ==========================================================
# K3–K5. PER-BOOK PIPELINE  (thin wrapper around process_unit)
# ==========================================================

def _process_book(file_path):
    """
    Run the shared 4-stage pipeline on one Bible book.
    Returns (skinner_rows, relation_rows, refined_rows).
    """
    # BKR sources are Python dicts of verses; join verse text, not the dict syntax.
    text = load_text_from_file(str(file_path))
    unit = AnalysisUnit(
        corpus_id="bible_bkr",
        unit_id=file_path.name,
        unit_type="book",
        display_name=(
            file_path.stem
            .replace("bible_BKR_", "")
            .replace("bible_bkr_", "")
        ),
        text=text,
        source="written_record",
        interaction="monologue",
        stimulus="unknown",
    )
    result = process_unit(unit, profile=_BKR_PROFILE)
    # NOTE: _BKR_PROFILE contains Bible-specific genre priors (biblical_czech_bkr).
    #       It MUST NOT be applied to upload runs — process_unit() called from
    #       run_upload_pipeline() passes profile=None intentionally.
    return result.skinner_rows, result.relation_rows, result.refined_rows


def _write_db(rows, table, run_id):
    if not rows:
        raise ValueError(f"No rows to write: {table}")
    insert_rows(table, rows, run_id)


# ==========================================================
# K7. TRAINING DATA  (absorbed from g_make_training_from_bible)
# ==========================================================

def _classify_file(file_path: Path) -> List[SkinnerDecision]:
    return apply_skinner_rules(_make_input(file_path))


def _build_training_row(
    decision: SkinnerDecision,
    file_name: str,
    previous_was_trigger: bool = False,
) -> dict:
    return {
        "sentence":             decision.sentence,
        "source":               decision.source,
        "stimulus":             decision.stimulus,
        "label":                decision.skinner_label,
        "skinner_class":        decision.skinner_class,
        "proxy_subtype":        decision.proxy_subtype,
        "confidence":           decision.confidence,
        "local_pattern":        decision.local_pattern,
        "semantic_cluster":     decision.semantic_cluster,
        "control_role":         decision.control_role,
        "root_lemma":           decision.root_lemma,
        "is_imperative_like":   decision.is_imperative_like,
        "has_negation":         decision.has_negation,
        "has_modal":            decision.has_modal,
        "has_question":         decision.has_question,
        "subject_present":      decision.subject_present,
        "has_verbum_dicendi":   decision.has_verbum_dicendi,
        "previous_was_trigger": previous_was_trigger,
        "file_name":            file_name,
        "reason":               decision.reason,
    }


def _build_training_rows(
    decisions: List[SkinnerDecision],
    file_name: str,
    min_confidence: float = 0.5,
) -> List[dict]:
    rows = []
    prev_trigger = False
    for d in decisions:
        if d.confidence >= min_confidence:
            rows.append(_build_training_row(d, file_name, prev_trigger))
        prev_trigger = (d.proxy_subtype == "intraverbal_trigger")
    return rows


def make_training_data_from_bible() -> None:
    """Generate B.F. Skinner-style training rows (training-only pathway)."""

    files = list_bible_files(limit=FILES_LIMIT)

    if not files:
        raise FileNotFoundError(f"No {BIBLE_GLOB} files found: {BIBLE_FOLDER}")

    run_id = make_run_id()
    all_rows = []
    for file_path in files:
        print(f"  Training: {file_path.name}")
        decisions = _classify_file(file_path)
        all_rows.extend(_build_training_rows(decisions, file_path.name))

    _write_db(all_rows, TABLE_TRAINING, run_id)
    print(f"\nTraining data → {TABLE_TRAINING}  ({len(all_rows)} rows)  run={run_id}")


# ==========================================================
# K6. MAIN
# ==========================================================

def main():

    files = list_bible_files(limit=FILES_LIMIT)

    if not files:
        raise FileNotFoundError(
            f"No {BIBLE_GLOB} files found: {BIBLE_FOLDER}"
        )

    print(f"Files: {len(files)}  (limit={FILES_LIMIT})", flush=True)

    run_id = make_run_id()
    n_skinner = n_relations = n_refined = 0
    failed = []

    for i, file_path in enumerate(files, start=1):
        print(f"  [{i}/{len(files)}] Processing: {file_path.name}", flush=True)
        try:
            sk_rows, rel_rows, ref_rows = _process_book(file_path)
        except Exception as exc:
            failed.append((file_path.name, str(exc)))
            print(f"    ERROR {file_path.name}: {exc}", flush=True)
            continue
        if not sk_rows:
            print(f"    WARN: no classified sentences in {file_path.name}", flush=True)
            continue
        _write_db(sk_rows, TABLE_SKINNER, run_id)
        _write_db(rel_rows, TABLE_RELATIONS, run_id)
        _write_db(ref_rows, TABLE_REFINED, run_id)
        n_skinner += len(sk_rows)
        n_relations += len(rel_rows)
        n_refined += len(ref_rows)
        print(
            f"    {len(sk_rows)} sentences  (total {n_skinner})",
            flush=True,
        )

    if not n_skinner:
        raise ValueError("No results produced.")

    print(f"\nDONE  run={run_id}  db={DB_PATH}", flush=True)
    print(f"  {TABLE_SKINNER:<40} {n_skinner:>6} rows", flush=True)
    print(f"  {TABLE_RELATIONS:<40} {n_relations:>6} rows", flush=True)
    print(f"  {TABLE_REFINED:<40} {n_refined:>6} rows", flush=True)
    if failed:
        print(f"  Failed books ({len(failed)}):", flush=True)
        for name, err in failed:
            print(f"    {name}: {err}", flush=True)


if __name__ == "__main__":
    main()
