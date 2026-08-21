"""Canonical project paths and Bible-corpus file discovery.

Every writer/reader of output artifacts, the SQLite DB, and BKR source files
should import from this module instead of constructing Path("output/...") or
globbing "*.txt" (which also matches requirements.txt).
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent

BIBLE_FOLDER = PROJECT_ROOT
OUTPUT_DIR = PROJECT_ROOT / "output"
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
DB_PATH = OUTPUT_DIR / "bible_analysis.db"

BIBLE_GLOB = "bible_BKR_*.txt"


def list_bible_files(limit: Optional[int] = None) -> list[Path]:
    """Return sorted BKR bible text files.

    Uses ``bible_BKR_*.txt`` rather than ``*.txt`` so auxiliary files such as
    ``requirements.txt`` are never ingested by the pipeline.
    """
    files = sorted(BIBLE_FOLDER.glob(BIBLE_GLOB))
    if limit is not None:
        files = files[:limit]
    return files


# Create writable dirs on import; warn if BIBLE_FOLDER is missing.
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

if not list_bible_files():
    import warnings
    warnings.warn(
        f"No {BIBLE_GLOB} files found in: {BIBLE_FOLDER}",
        RuntimeWarning,
        stacklevel=2,
    )
