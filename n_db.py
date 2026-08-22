import logging
import sqlite3
from datetime import datetime

from a_paths import DB_PATH, ensure_bible_db


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

# Declared SQLite types for columns that Tab 2 aggregates with mean().
_COLUMN_SQL_TYPE = {
    "has_coordination": "INTEGER",
    "dative_present": "INTEGER",
    "indirect_object_present": "INTEGER",
    "adjective_count": "INTEGER",
    "adverb_count": "INTEGER",
    "pronoun_count": "INTEGER",
    "has_negation": "INTEGER",
    "confidence": "REAL",
    "type_token_ratio": "REAL",
}
_INT_COLUMNS = frozenset(
    name for name, typ in _COLUMN_SQL_TYPE.items() if typ == "INTEGER"
)
_REAL_COLUMNS = frozenset(
    name for name, typ in _COLUMN_SQL_TYPE.items() if typ == "REAL"
)


# ==========================================================
# N2. CONNECTION
# ==========================================================

def get_conn() -> sqlite3.Connection:
    ensure_bible_db()
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


# Tab 2 charts call groupby().mean() on these flags.  Live rows used to be
# stored as the strings "True"/"False"; pandas to_numeric() turns those into NaN.
_BOOL_TEXT = {
    "true": 1.0, "false": 0.0,
    "1": 1.0, "0": 0.0,
    "1.0": 1.0, "0.0": 0.0,
    "yes": 1.0, "no": 0.0,
}


def _col_sql(name: str) -> str:
    return f'"{name}" {_COLUMN_SQL_TYPE.get(name, "TEXT")}'


def _sql_value(column: str, value):
    """Coerce a cell for SQLite.

    ``None`` is stored as SQL NULL (not the string ``"None"``).
    Known flag/count columns are INTEGER; confidence/TTR are REAL.
    All other values stay TEXT-compatible via ``str()``.
    """
    if value is None:
        return None
    if column in _NULLISH_FIELDS and value == "":
        return None
    if column in _INT_COLUMNS:
        if isinstance(value, str) and value.strip().lower() in _BOOL_TEXT:
            return int(_BOOL_TEXT[value.strip().lower()])
        return int(value)
    if column in _REAL_COLUMNS:
        return float(value)
    if isinstance(value, bool):
        return 1 if value else 0
    return str(value)


def coerce_numeric_columns(df, columns):
    """Turn TEXT 0/1 and True/False flags into numbers for aggregation."""
    import pandas as pd

    for col in columns:
        if col not in df.columns:
            continue
        series = df[col]
        if pd.api.types.is_bool_dtype(series):
            df[col] = series.astype(int)
            continue
        numeric = pd.to_numeric(series, errors="coerce")
        mapped = series.astype(str).str.strip().str.lower().map(_BOOL_TEXT)
        df[col] = mapped.fillna(numeric)
    return df


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
        col_defs = ", ".join(_col_sql(c) for c in all_cols)
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
                    conn.execute(
                        f'ALTER TABLE "{table}" ADD COLUMN {_col_sql(c)}'
                    )
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


def count_table_rows(table: str, run_id: str | None = None) -> int | None:
    """Return row count (optionally for one run_id) or None if table is missing."""
    conn = get_conn()
    try:
        if run_id:
            n = conn.execute(
                f'SELECT COUNT(*) FROM "{table}" WHERE run_id = ?', (run_id,)
            ).fetchone()[0]
        else:
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


def compact_bible_db(keep_run_id: str | None = None) -> str:
    """Keep one Bible run, drop the others, and restamp numeric columns.

    Recreates the three pipeline tables with INTEGER/REAL affinity so Tab 2
    ``groupby.mean()`` does not depend on TEXT ``"0"``/``"1"``.
    """
    keep_run_id = keep_run_id or latest_bible_run_id(TABLE_SKINNER)
    if not keep_run_id:
        raise ValueError("No Bible run to keep")

    conn = get_conn()
    try:
        for table in (TABLE_SKINNER, TABLE_RELATIONS, TABLE_REFINED):
            existing = [row[1] for row in conn.execute(f'PRAGMA table_info("{table}")')]
            if not existing:
                continue
            data_cols = [c for c in existing if c != "id"]
            tmp = f"{table}__typed"
            conn.execute(f'DROP TABLE IF EXISTS "{tmp}"')
            col_defs = ", ".join(_col_sql(c) for c in data_cols)
            conn.execute(
                f'CREATE TABLE "{tmp}" '
                f'(id INTEGER PRIMARY KEY AUTOINCREMENT, {col_defs})'
            )
            selects = []
            for c in data_cols:
                typ = _COLUMN_SQL_TYPE.get(c)
                if typ == "INTEGER":
                    selects.append(f'CAST("{c}" AS INTEGER)')
                elif typ == "REAL":
                    selects.append(f'CAST("{c}" AS REAL)')
                else:
                    selects.append(f'"{c}"')
            col_list = ", ".join(f'"{c}"' for c in data_cols)
            sel_list = ", ".join(selects)
            conn.execute(
                f'INSERT INTO "{tmp}" ({col_list}) '
                f'SELECT {sel_list} FROM "{table}" WHERE run_id = ?',
                (keep_run_id,),
            )
            conn.execute(f'DROP TABLE "{table}"')
            conn.execute(f'ALTER TABLE "{tmp}" RENAME TO "{table}"')
            for idx_col in ("file_name", "run_id"):
                if idx_col in data_cols:
                    conn.execute(
                        f'CREATE INDEX IF NOT EXISTS '
                        f'"idx_{table}_{idx_col}" ON "{table}" ("{idx_col}")'
                    )
        conn.commit()
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        conn.execute("VACUUM")
    finally:
        conn.close()
    return keep_run_id


def pack_bible_db() -> None:
    """Gzip the unpacked DB so git tracks ``output/bible_analysis.db.gz``."""
    import gzip
    import shutil

    from a_paths import DB_GZ_PATH

    ensure_bible_db()
    tmp_path = DB_GZ_PATH.with_name(DB_GZ_PATH.name + ".tmp")
    with DB_PATH.open("rb") as src, gzip.open(tmp_path, "wb", compresslevel=9) as dst:
        shutil.copyfileobj(src, dst)
    tmp_path.replace(DB_GZ_PATH)


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
