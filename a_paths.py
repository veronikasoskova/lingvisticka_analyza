from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

BIBLE_FOLDER = PROJECT_ROOT
OUTPUT_DIR   = PROJECT_ROOT / "output"
DATA_DIR     = PROJECT_ROOT / "data"
MODELS_DIR   = PROJECT_ROOT / "models"
DB_PATH      = OUTPUT_DIR / "bible_analysis.db"

# Create writable dirs on import; warn if BIBLE_FOLDER is missing.
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)

if not list(BIBLE_FOLDER.glob("bible_BKR_*.txt")):
    import warnings
    warnings.warn(
        f"No bible_BKR_*.txt files found in: {BIBLE_FOLDER}",
        RuntimeWarning,
        stacklevel=2,
    )
