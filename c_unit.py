"""
c_unit.py — AnalysisUnit dataclass
Unified model for both Bible books and uploaded text chapters.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from c_input import SourceType, InteractionType, StimulusType, TextUnitType


@dataclass
class AnalysisUnit:
    """Single unit of analysis — one Bible book or one chapter of an uploaded text."""

    corpus_id: str
    """Stable corpus identifier.  'bible_bkr'  |  'upload_{stem}_{ts}'"""

    unit_id: str
    """Unique identifier within the corpus.  e.g. 'genesis'  |  'chapter_03'"""

    unit_type: TextUnitType
    """Granularity level: 'book' for Bible books, 'chapter' for upload segments."""

    display_name: str
    """Human-readable label used in UI and chart axes."""

    text: str
    """Raw text content."""

    source: SourceType = "written_record"
    interaction: InteractionType = "monologue"
    stimulus: StimulusType = "unknown"


@dataclass
class ProcessedUnit:
    """Container for the three result tables produced by process_unit()."""

    unit: AnalysisUnit
    skinner_rows: list = field(default_factory=list)
    relation_rows: list = field(default_factory=list)
    refined_rows: list = field(default_factory=list)
