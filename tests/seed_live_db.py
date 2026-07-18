"""Load .env, create schemas.sql's tables against the configured PostgreSQL DB, then seed synthetic
data (TASK-033). NOT a pytest test - it touches a real database, so it is deliberately named without
a `test_`/`_test` prefix and pytest's default discovery ignores it.

Run manually:

    .venv/bin/python tests/seed_live_db.py

Connection variables are read from `.env` (loaded into THIS process's environment only - never
printed, never written back anywhere) under either naming convention:

    POSTGRES_HOST / POSTGRES_PORT / POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_NAME (or _DB)
    DB_HOST       / DB_PORT       / DB_USER       / DB_PASSWORD       / DB_NAME

If the named database does not exist yet, it is created via a maintenance connection to the
server's default `postgres` database first.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))


def _load_dotenv(path: Path) -> None:
    """Minimal `.env` loader: KEY=VALUE per line, '#' comments, optional quotes. No dependency."""
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _first_env(*names: str) -> str | None:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return None


def _target_dbname() -> str:
    return _first_env("POSTGRES_NAME", "POSTGRES_DB", "DB_NAME") or "nxcare"


def _build_url(dbname: str) -> str:
    host = _first_env("POSTGRES_HOST", "DB_HOST") or "localhost"
    port = _first_env("POSTGRES_PORT", "DB_PORT") or "5432"
    user = _first_env("POSTGRES_USER", "DB_USER")
    password = _first_env("POSTGRES_PASSWORD", "DB_PASSWORD")
    if not user or password is None:
        raise RuntimeError(
            "missing DB credentials: set POSTGRES_USER/POSTGRES_PASSWORD (or DB_USER/DB_PASSWORD) "
            "in .env"
        )
    return f"postgresql+pg8000://{user}:{password}@{host}:{port}/{dbname}"


def main() -> None:
    _load_dotenv(_REPO_ROOT / ".env")

    from sqlalchemy import create_engine, inspect

    from vaic.state.sql import create_database_if_missing, create_schema, seed_nxcare
    from vaic.state.sql.models import Base

    dbname = _target_dbname()
    maintenance_url = _build_url("postgres")  # postgres's own default maintenance database
    created = create_database_if_missing(maintenance_url, dbname)
    print(f"database {dbname!r}: {'created' if created else 'already existed'}")

    engine = create_engine(_build_url(dbname))
    expected_tables = set(Base.metadata.tables)
    existing_tables = set(inspect(engine).get_table_names())
    if expected_tables - existing_tables:
        print(f"creating {len(expected_tables - existing_tables)} missing table(s)")
        create_schema(engine)
    else:
        print("all expected tables already exist - skipping schema creation")

    counts = seed_nxcare(engine, patient_count=25, room_count=15)
    print("row counts after seeding:")
    for table, count in sorted(counts.items()):
        print(f"  {table:<20} {count}")


if __name__ == "__main__":
    main()
