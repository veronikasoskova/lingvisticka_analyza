"""
c_segment.py — Chapter segmentation for uploaded texts.

Segmentation strategy — hierarchical fallback
---------------------------------------------
1. Marker-based  : scan for KAPITOLA / Chapter / Kap. / Roman numeral headings
2. Paragraph-block: split on triple-newlines, group into ~2000-word chunks
3. Sentence-window: split every N sentences (default 150)

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

# Minimum sentences required to keep a chapter as its own unit;
# shorter chapters are merged into the adjacent one.
_MIN_SENTENCES = 5

# Maximum sentences per chapter (Stanza memory guard).
_MAX_SENTENCES = 3000

# Default sentences per window for fixed-sentence fallback.
_DEFAULT_WINDOW = 150

# Words per chunk for paragraph-block grouping.
_WORDS_PER_CHUNK = 2000

# Chapter-marker patterns (Czech + English, case-insensitive).
_CHAPTER_PATTERNS = [
    r"(?:^|\n)\s*KAPITOLA\s+\d+",
    r"(?:^|\n)\s*Kapitola\s+\d+",
    r"(?:^|\n)\s*Chapter\s+\d+",
    r"(?:^|\n)\s*Kap\.\s*\d+",
    r"(?:^|\n)\s*[IVX]{1,6}\.\s{2,}",   # Roman numeral headings  (I.   II.  ...)
    r"(?:^|\n)\s*\d+\.\s{2,}[A-ZÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ]",  # "1.   Heading"
]

_CHAPTER_RE = re.compile(
    "|".join(_CHAPTER_PATTERNS),
    re.MULTILINE,
)

# Simple sentence-end heuristic (period / ! / ? not inside abbreviations).
_SENTENCE_END_RE = re.compile(r"(?<=[.!?])\s+")


# ──────────────────────────────────────────────────────────────────────────────
# C2. HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def _count_sentences(text: str) -> int:
    return max(1, len(_SENTENCE_END_RE.split(text.strip())))


def _count_words(text: str) -> int:
    return len(text.split())


def _make_display(index: int, total: int) -> str:
    """Return a zero-padded chapter label, e.g. 'Kapitola 03'."""
    width = len(str(total))
    return f"Kapitola {index:0{width}d}"


def _make_unit_id(index: int, total: int) -> str:
    width = len(str(total))
    return f"chapter_{index:0{width}d}"


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
            # Flush carry into this chunk if it existed
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
        sub: List[str] = []
        for i in range(0, len(sentences), _MAX_SENTENCES):
            sub.append(" ".join(sentences[i: i + _MAX_SENTENCES]))
        result.extend(sub)
    return result


# ──────────────────────────────────────────────────────────────────────────────
# C3. SEGMENTATION STRATEGIES
# ──────────────────────────────────────────────────────────────────────────────

def _segment_by_markers(text: str) -> Optional[List[str]]:
    """Strategy 1: split on explicit chapter headings."""
    positions = [m.start() for m in _CHAPTER_RE.finditer(text)]
    if len(positions) < 3:
        return None
    chunks: List[str] = []
    for i, pos in enumerate(positions):
        end = positions[i + 1] if i + 1 < len(positions) else len(text)
        chunks.append(text[pos:end].strip())
    return chunks or None


def _segment_by_paragraphs(text: str) -> Optional[List[str]]:
    """Strategy 2: group triple-newline paragraph blocks into ~2000-word chunks."""
    paragraphs = re.split(r"\n{3,}", text)
    if len(paragraphs) < 3:
        return None
    chunks: List[str] = []
    current_words = 0
    current_parts: List[str] = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        wc = _count_words(para)
        if current_words + wc > _WORDS_PER_CHUNK and current_parts:
            chunks.append("\n\n".join(current_parts))
            current_parts = [para]
            current_words = wc
        else:
            current_parts.append(para)
            current_words += wc
    if current_parts:
        chunks.append("\n\n".join(current_parts))
    return chunks if len(chunks) >= 2 else None


def _segment_by_sentences(text: str, window: int = _DEFAULT_WINDOW) -> List[str]:
    """Strategy 3: fixed-sentence sliding window (always produces output)."""
    sentences = _SENTENCE_END_RE.split(text.strip())
    if len(sentences) <= window:
        return [text.strip()]
    chunks: List[str] = []
    for i in range(0, len(sentences), window):
        chunks.append(" ".join(sentences[i: i + window]))
    return chunks


# ──────────────────────────────────────────────────────────────────────────────
# C4. PUBLIC API
# ──────────────────────────────────────────────────────────────────────────────

def segment_book(
    text: str,
    corpus_id: str,
    source_name: str = "uploaded_text",
    sentence_window: int = _DEFAULT_WINDOW,
) -> List[AnalysisUnit]:
    """
    Segment *text* into a list of AnalysisUnit objects.

    Parameters
    ----------
    text           : full text of the uploaded document
    corpus_id      : stable corpus identifier, e.g. 'upload_book_20240101T120000'
    source_name    : original filename / display label for the whole document
    sentence_window: sentences per chunk for the fallback strategy

    Returns
    -------
    List[AnalysisUnit] — at least one unit, possibly many chapters.
    """
    text = text.strip()

    # Try each strategy in order of preference.
    chunks = (
        _segment_by_markers(text)
        or _segment_by_paragraphs(text)
        or _segment_by_sentences(text, sentence_window)
    )

    # Post-processing: merge short, split long
    chunks = _merge_short(chunks)
    chunks = _split_long(chunks)

    total = len(chunks)
    units: List[AnalysisUnit] = []
    for i, chunk in enumerate(chunks, start=1):
        units.append(
            AnalysisUnit(
                corpus_id=corpus_id,
                unit_id=_make_unit_id(i, total),
                unit_type="chapter",
                display_name=_make_display(i, total),
                text=chunk,
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
