"""
c_segment.py — Chapter segmentation for uploaded texts.

Segmentation strategy — hierarchical, structure-only
-----------------------------------------------------
1. Chapter tier  : scan for KAPITOLA / Chapter / Kap. / Roman-numeral headings
                   → unit_type='chapter', 3+ markers required
2. Section tier  : scan for section / subchapter headings (numbered subsections,
                   Sekce, Oddíl, Section, §, Podkapitola, etc.)
                   → unit_type='section', 3+ markers required
3. No-structure  : no reliable structural markers found
                   → single whole-text unit, unit_type='document'

No synthetic paragraph-block or fixed-sentence segmentation is used.

Returns a list of AnalysisUnit objects ready for process_unit().
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from c_unit import AnalysisUnit

# ──────────────────────────────────────────────────────────────────────────────
# C1. CONSTANTS
# ──────────────────────────────────────────────────────────────────────────────

# Minimum sentences required to keep a unit as its own entry;
# shorter units are merged into the adjacent one.
_MIN_SENTENCES = 5

# Maximum sentences per unit (Stanza memory guard).
_MAX_SENTENCES = 3000

# ──────────────────────────────────────────────────────────────────────────────
# C2. PATTERNS
# ──────────────────────────────────────────────────────────────────────────────

# Chapter-marker patterns (Czech + English, case-insensitive).
_CHAPTER_PATTERNS = [
    r"(?:^|\n)\s*KAPITOLA\s+\d+",
    r"(?:^|\n)\s*Kapitola\s+\d+",
    r"(?:^|\n)\s*Chapter\s+\d+",
    r"(?:^|\n)\s*Kap\.\s*\d+",
    r"(?:^|\n)\s*[IVX]{1,6}\.\s{2,}",          # Roman numeral headings (I.   II. …)
    r"(?:^|\n)\s*\d+\.\s{2,}[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ]",  # "1.   Heading"
]

_CHAPTER_RE = re.compile(
    "|".join(_CHAPTER_PATTERNS),
    re.MULTILINE,
)

# Section / subchapter marker patterns (Czech + English).
_SECTION_PATTERNS = [
    r"(?:^|\n)\s*Sekce\s+[\d.]+",               # Sekce 1 / Sekce 1.2
    r"(?:^|\n)\s*SEKCE\s+[\d.]+",
    r"(?:^|\n)\s*Oddíl\s+[\d.]+",
    r"(?:^|\n)\s*ODDÍL\s+[\d.]+",
    r"(?:^|\n)\s*Podkapitola\s+[\d.]+",
    r"(?:^|\n)\s*Section\s+[\d.]+",
    r"(?:^|\n)\s*SECTION\s+[\d.]+",
    r"(?:^|\n)\s*§\s*\d+",                      # § 1, §1
    r"(?:^|\n)\s*\d+\.\d+\.\s{1,}[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ\w]",  # 1.1. Heading
    r"(?:^|\n)\s*\d+\.\d+\s{2,}[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ\w]",    # 1.1  Heading
]

_SECTION_RE = re.compile(
    "|".join(_SECTION_PATTERNS),
    re.MULTILINE,
)

# Simple sentence-end heuristic (period / ! / ? not inside abbreviations).
_SENTENCE_END_RE = re.compile(r"(?<=[.!?])\s+")


# ──────────────────────────────────────────────────────────────────────────────
# C3. HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def _count_sentences(text: str) -> int:
    return max(1, len(_SENTENCE_END_RE.split(text.strip())))


_UNIT_META = {
    "chapter": ("Kapitola", "chapter"),
    "section": ("Sekce", "section"),
}


def _make_display(index: int, total: int, unit_type: str) -> str:
    """Return a zero-padded unit label, e.g. 'Kapitola 03' or 'Sekce 03'."""
    width = len(str(total))
    label, _ = _UNIT_META.get(unit_type, ("Dokument", "document"))
    return f"{label} {index:0{width}d}"


def _make_unit_id(index: int, total: int, unit_type: str) -> str:
    width = len(str(total))
    _, prefix = _UNIT_META.get(unit_type, ("Dokument", "document"))
    return f"{prefix}_{index:0{width}d}"


def _merge_short(chunks: List[str]) -> List[str]:
    """Merge chunks that are shorter than _MIN_SENTENCES into adjacent chunks."""
    if not chunks:
        return chunks
    merged: List[str] = []
    carry = ""
    for chunk in chunks:
        combined = (carry + "\n\n" + chunk).strip() if carry else chunk
        if _count_sentences(combined) < _MIN_SENTENCES:
            carry = combined
        else:
            merged.append(combined)
            carry = ""
    if carry:
        if merged:
            merged[-1] = (merged[-1] + "\n\n" + carry).strip()
        else:
            merged.append(carry)
    return merged


def _split_long(chunks: List[str]) -> List[str]:
    """Sub-split chunks that exceed _MAX_SENTENCES."""
    result: List[str] = []
    for chunk in chunks:
        sentences = _SENTENCE_END_RE.split(chunk.strip())
        if len(sentences) <= _MAX_SENTENCES:
            result.append(chunk)
            continue
        for i in range(0, len(sentences), _MAX_SENTENCES):
            result.append(" ".join(sentences[i: i + _MAX_SENTENCES]))
    return result


# ──────────────────────────────────────────────────────────────────────────────
# C4. SEGMENTATION TIERS
# ──────────────────────────────────────────────────────────────────────────────

def _segment_by_markers(text: str, pattern: re.Pattern) -> Optional[List[str]]:
    """Split on heading matches. Requires ≥3 markers so a lone 'Chapter 1'
    mention in running text is not treated as document structure."""
    positions = [m.start() for m in pattern.finditer(text)]
    if len(positions) < 3:
        return None
    chunks: List[str] = []
    for i, pos in enumerate(positions):
        end = positions[i + 1] if i + 1 < len(positions) else len(text)
        chunks.append(text[pos:end].strip())
    return chunks or None


# ──────────────────────────────────────────────────────────────────────────────
# C5. PUBLIC API
# ──────────────────────────────────────────────────────────────────────────────

def segment_book(
    text: str,
    corpus_id: str,
    source_name: str = "uploaded_text",
) -> List[AnalysisUnit]:
    """
    Segment *text* into a list of AnalysisUnit objects.

    Segmentation follows the approved three-tier architecture:
      1. Real chapter markers  → unit_type='chapter'
      2. Real section markers  → unit_type='section'
      3. No reliable structure → single unit, unit_type='document'

    Parameters
    ----------
    text           : full text of the uploaded document
    corpus_id      : stable corpus identifier, e.g. 'upload_book_20240101T120000'
    source_name    : original filename / display label for the whole document

    Returns
    -------
    List[AnalysisUnit] — one or more units reflecting real document structure.
    """
    text = text.strip()

    chunks = _segment_by_markers(text, _CHAPTER_RE)
    if chunks:
        unit_type = "chapter"
        seg_method: str = "chapter_markers"
    else:
        chunks = _segment_by_markers(text, _SECTION_RE)
        if chunks:
            unit_type = "section"
            seg_method = "section_markers"
        else:
            chunks = [text]
            unit_type = "document"
            seg_method = "single_unit"

    # Post-processing: merge short, split long (only meaningful for multi-unit tiers)
    if len(chunks) > 1:
        chunks = _merge_short(chunks)
        chunks = _split_long(chunks)

    total = len(chunks)
    units: List[AnalysisUnit] = []
    for i, chunk in enumerate(chunks, start=1):
        units.append(
            AnalysisUnit(
                corpus_id=corpus_id,
                unit_id=_make_unit_id(i, total, unit_type),
                unit_type=unit_type,
                display_name=_make_display(i, total, unit_type),
                text=chunk,
                segmentation_method=seg_method,
            )
        )
    return units


def make_corpus_id(source_name: str) -> str:
    """Generate a stable corpus_id from a filename and current timestamp."""
    stem = Path(source_name).stem[:40]
    # Replace characters that could cause issues in filenames or SQL
    stem = re.sub(r"[^\w]", "_", stem).strip("_")
    ts = datetime.now().strftime("%Y%m%dT%H%M%S")
    return f"upload_{stem}_{ts}"

