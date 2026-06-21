from pathlib import Path
from typing import List
import os

from c_input import create_input_from_file
from c_unit import AnalysisUnit
from h_classifiers import apply_skinner_rules, SkinnerDecision
from j0_context_profile import get_builtin_profile
from k_pipeline_core import process_unit

_BKR_PROFILE = get_builtin_profile("biblical_czech_bkr")
from a_paths import BIBLE_FOLDER
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
    text = file_path.read_text(encoding="utf-8")
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

    files = sorted(BIBLE_FOLDER.glob("*.txt"))[:FILES_LIMIT]

    if not files:
        raise FileNotFoundError(f"No txt files found: {BIBLE_FOLDER}")

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

    files = sorted(BIBLE_FOLDER.glob("*.txt"))[:FILES_LIMIT]

    if not files:
        raise FileNotFoundError(
            f"No txt files found: {BIBLE_FOLDER}"
        )

    print(f"Files: {len(files)}  (limit={FILES_LIMIT})")

    run_id = make_run_id()
    all_skinner   = []
    all_relations = []
    all_refined   = []

    for file_path in files:
        print(f"  Processing: {file_path.name}")

        sk_rows, rel_rows, ref_rows = _process_book(file_path)

        all_skinner.extend(sk_rows)
        all_relations.extend(rel_rows)
        all_refined.extend(ref_rows)

    if not all_skinner:
        raise ValueError("No results produced.")

    _write_db(all_skinner,   TABLE_SKINNER,   run_id)
    _write_db(all_relations, TABLE_RELATIONS, run_id)
    _write_db(all_refined,   TABLE_REFINED,   run_id)

    print(f"\nDONE  run={run_id}  db={DB_PATH}")
    print(f"  {TABLE_SKINNER:<40} {len(all_skinner):>6} rows")
    print(f"  {TABLE_RELATIONS:<40} {len(all_relations):>6} rows")
    print(f"  {TABLE_REFINED:<40} {len(all_refined):>6} rows")


if __name__ == "__main__":
    main()
