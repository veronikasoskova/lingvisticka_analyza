import logging
import sqlite3
from datetime import datetime

from a_paths import DB_PATH


logger = logging.getLogger(__name__)


# ==========================================================
# N1. CONFIG
# ==========================================================

# Primary pipeline tables → written by k_apply_all_to_bible
TABLE_SKINNER     = "skinner_analysis"
TABLE_RELATIONS   = "verbal_relations"
TABLE_REFINED     = "refined_descriptions"
TABLE_TRAINING    = "training_data"

# Optional fields stored as SQL NULL rather than the string "None".
_NULLISH_FIELDS = frozenset({
    "secondary_intention",
    "secondary_strategy",
})


# ==========================================================
# N2. CONNECTION
# ==========================================================

def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


# ==========================================================
# N3. WRITE
# ==========================================================

def make_run_id() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _sql_value(column: str, value):
    """Coerce a cell for SQLite.

    ``None`` is stored as SQL NULL (not the string ``"None"``).  All other
    values stay TEXT-compatible via ``str()``, matching the auto-schema.
    """
    if value is None:
        return None
    if column in _NULLISH_FIELDS and value == "":
        return None
    return str(value)


def insert_rows(table: str, rows: list, run_id: str) -> int:
    """Append rows to table (created/migrated automatically). Returns row count."""
    if not rows:
        return 0

    cols = list(rows[0].keys())
    all_cols = cols + ["run_id"]
    placeholders = ", ".join("?" * len(all_cols))
    col_list = ", ".join(f'"{c}"' for c in all_cols)

    conn = get_conn()

    # Get existing columns (empty set if table doesn't exist yet)
    existing = {row[1] for row in conn.execute(f'PRAGMA table_info("{table}")')}

    if not existing:
        col_defs = ", ".join(f'"{c}" TEXT' for c in all_cols)
        conn.execute(
            f'CREATE TABLE "{table}" '
            f'(id INTEGER PRIMARY KEY AUTOINCREMENT, {col_defs})'
        )
        for idx_col in ("file_name", "run_id"):
            if idx_col in all_cols:
                conn.execute(
                    f'CREATE INDEX IF NOT EXISTS '
                    f'"idx_{table}_{idx_col}" ON "{table}" ("{idx_col}")'
                )
    else:
        # Add any columns that are in the data but missing from the table.
        # Guard against race conditions: re-check inside a try/except in case
        # another process added the column between the PRAGMA read and here.
        for c in all_cols:
            if c not in existing:
                try:
                    conn.execute(f'ALTER TABLE "{table}" ADD COLUMN "{c}" TEXT')
                except sqlite3.OperationalError as exc:
                    if "duplicate column" not in str(exc).lower():
                        raise

    conn.executemany(
        f'INSERT INTO "{table}" ({col_list}) VALUES ({placeholders})',
        [
            tuple(_sql_value(c, r.get(c)) for c in cols) + (run_id,)
            for r in rows
        ],
    )
    conn.commit()
    conn.close()
    return len(rows)


# ==========================================================
# N4. READ
# ==========================================================

def _normalize_row(row: dict) -> dict:
    """Map legacy ``"None"`` strings on optional fields back to Python None."""
    for key in _NULLISH_FIELDS:
        if key in row and row[key] in (None, "None", ""):
            row[key] = None
    return row


def load_rows(table: str, run_id: str | None = None) -> list:
    """Return rows for the given run_id (or latest non-upload run if None)."""
    if run_id is None:
        run_id = latest_bible_run_id(table)
    conn = get_conn()
    conn.execute("PRAGMA cache_size = -32768")  # 32 MB page cache
    rows = []
    try:
        if run_id:
            cur = conn.execute(
                f'SELECT * FROM "{table}" WHERE run_id = ?', (run_id,)
            )
        else:
            cur = conn.execute(f'SELECT * FROM "{table}"')
        for r in cur:
            row = dict(r)
            row.pop("id", None)
            rows.append(_normalize_row(row))
    except sqlite3.OperationalError as exc:
        msg = str(exc).lower()
        if "no such table" in msg:
            logger.info("Table %s is missing (%s); returning no rows.", table, exc)
        else:
            logger.warning("Failed to load rows from %s: %s", table, exc)
    finally:
        conn.close()
    return rows


def count_table_rows(table: str) -> int | None:
    """Return row count or None if table doesn't exist."""
    conn = get_conn()
    try:
        n = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
    except sqlite3.OperationalError as exc:
        logger.info("count_table_rows(%s): %s", table, exc)
        n = None
    conn.close()
    return n


def list_runs(table: str) -> list:
    """Return distinct run_ids in insertion order."""
    conn = get_conn()
    try:
        runs = [
            r[0] for r in
            conn.execute(f'SELECT DISTINCT run_id FROM "{table}" ORDER BY id')
        ]
    except sqlite3.OperationalError as exc:
        logger.info("list_runs(%s): %s", table, exc)
        runs = []
    conn.close()
    return runs


def latest_run_id(table: str) -> str | None:
    """Return the most recent run_id or None."""
    runs = list_runs(table)
    return runs[-1] if runs else None


def latest_bible_run_id(table: str) -> str | None:
    """Return the most-recent Bible-corpus run_id in *table*, or None.

    Prefers rows where corpus_id = 'bible_bkr' when that column exists.
    Falls back to run_id NOT LIKE 'upload_%' for older databases.
    """
    conn = get_conn()
    try:
        existing = {row[1] for row in conn.execute(f'PRAGMA table_info("{table}")')}
        if "corpus_id" in existing:
            row = conn.execute(
                f'SELECT run_id FROM "{table}" WHERE corpus_id = \'bible_bkr\''
                f' ORDER BY id DESC LIMIT 1'
            ).fetchone()
        else:
            row = conn.execute(
                f'SELECT run_id FROM "{table}" WHERE run_id NOT LIKE \'upload_%\''
                f' ORDER BY id DESC LIMIT 1'
            ).fetchone()
        return row[0] if row else None
    except sqlite3.OperationalError as exc:
        logger.info("latest_bible_run_id(%s): %s", table, exc)
        return None
    finally:
        conn.close()
