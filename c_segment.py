"""
c_segment.py — Structural segmentation for uploaded texts.

Approved segmentation rule
--------------------------
1. Real chapter markers            -> chapter units
2. Real section/subchapter markers -> section units
3. No reliable structure           -> single whole-text unit

Synthetic size-based segmentation is intentionally not used.
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import List

from c_unit import AnalysisUnit


_CHAPTER_PATTERNS = [
    r"(?:^|\n)\s*KAPITOLA\s+\d+[^\n]*",
    r"(?:^|\n)\s*Kapitola\s+\d+[^\n]*",
    r"(?:^|\n)\s*Chapter\s+\d+[^\n]*",
    r"(?:^|\n)\s*Kap\.\s*\d+[^\n]*",
    r"(?:^|\n)\s*[IVX]{1,8}\.\s{2,}[^\n]+",
    r"(?:^|\n)\s*\d+\.\s{2,}[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ][^\n]*",
]

_SECTION_PATTERNS = [
    r"(?:^|\n)\s*(?:Oddíl|Oddil|Sekce|Sekcia|Section|Part|Část|Cast)\s+[A-Z0-9IVX]+[^\n]*",
    r"(?:^|\n)\s*§\s*\d+[^\n]*",
    r"(?:^|\n)\s*\d+\.\d+(?:\.\d+)*\s+[^\n]+",
]

_CHAPTER_RE = re.compile("|".join(_CHAPTER_PATTERNS), re.MULTILINE)
_SECTION_RE = re.compile("|".join(_SECTION_PATTERNS), re.MULTILINE)


def _clean_heading(text: str) -> str:
    heading = text.strip().splitlines()[0].strip() if text.strip() else ""
    heading = re.sub(r"\s+", " ", heading)
    return heading[:120]


def _make_display(prefix: str, index: int, total: int) -> str:
    width = max(2, len(str(total)))
    return f"{prefix} {index:0{width}d}"


def _make_unit_id(kind: str, index: int, total: int) -> str:
    width = max(2, len(str(total)))
    return f"{kind}_{index:0{width}d}"


def _split_by_matches(text: str, regex: re.Pattern[str]) -> list[tuple[str, str]] | None:
    matches = list(regex.finditer(text))
    if len(matches) < 2:
        return None

    chunks: list[tuple[str, str]] = []
    leading = text[:matches[0].start()].strip()
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        chunk = text[start:end].strip()
        if not chunk:
            continue
        if i == 0 and leading:
            chunk = f"{leading}\n\n{chunk}".strip()
        heading = _clean_heading(match.group(0))
        chunks.append((heading, chunk))

    return chunks or None


def _segment_with_structure(text: str, corpus_id: str, kind: str, title_prefix: str,
                            matches: list[tuple[str, str]] | None) -> list[AnalysisUnit] | None:
    if not matches:
        return None

    total = len(matches)
    units: list[AnalysisUnit] = []
    for i, (heading, chunk) in enumerate(matches, start=1):
        units.append(
            AnalysisUnit(
                corpus_id=corpus_id,
                unit_id=_make_unit_id(kind, i, total),
                unit_type=kind,
                display_name=heading or _make_display(title_prefix, i, total),
                text=chunk,
            )
        )
    return units


def segment_book(
    text: str,
    corpus_id: str,
    source_name: str = "uploaded_text",
    sentence_window: int = 150,
) -> List[AnalysisUnit]:
    """
    Segment *text* into a list of AnalysisUnit objects using only real structure.

    Parameters kept for backward compatibility; sentence_window is intentionally
    ignored because synthetic window segmentation is not approved behaviour.
    """
    del source_name, sentence_window

    text = text.strip()
    if not text:
        return []

    chapter_matches = _split_by_matches(text, _CHAPTER_RE)
    chapter_units = _segment_with_structure(
        text,
        corpus_id,
        "chapter",
        "Kapitola",
        chapter_matches,
    )
    if chapter_units:
        return chapter_units

    section_matches = _split_by_matches(text, _SECTION_RE)
    section_units = _segment_with_structure(
        text,
        corpus_id,
        "section",
        "Sekce",
        section_matches,
    )
    if section_units:
        return section_units

    return [
        AnalysisUnit(
            corpus_id=corpus_id,
            unit_id="whole",
            unit_type="document",
            display_name="Celý text",
            text=text,
        )
    ]


def make_corpus_id(source_name: str) -> str:
    """Generate a stable corpus_id from a filename and current timestamp."""
    stem = Path(source_name).stem[:40]
    stem = re.sub(r"[^\w]", "_", stem).strip("_")
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    return f"upload_{stem}_{ts}"
