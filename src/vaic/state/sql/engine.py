"""Engine construction and schema creation for the SQL durable store (TASK-032).

Connection parameters come from the process environment (`DB_HOST`, `DB_PORT`, `DB_USER`,
`DB_PASSWORD`, `DB_NAME`) - never read `.env` directly here; whatever starts the process is
responsible for loading it into the environment first (agent-guardrails.md: agents never read
`.env`). Requires the optional `sql` dependency group (`pip install -e ".[sql]"`).
"""

from __future__ import annotations

import os
from importlib import resources
from pathlib import Path

from sqlalchemy import Engine, create_engine, text

_SCHEMA_FILE = "schemas.sql"


def _env(name: str, default: str | None = None) -> str:
    value = os.environ.get(name, default)
    if value is None:
        raise RuntimeError(f"missing required environment variable: {name}")
    return value


def build_url(
    *,
    host: str | None = None,
    port: str | None = None,
    user: str | None = None,
    password: str | None = None,
    dbname: str | None = None,
) -> str:
    """Build a `postgresql+pg8000://` URL from explicit args, falling back to `DB_*` env vars."""
    host = host or _env("DB_HOST")
    port = port or _env("DB_PORT", "5432")
    user = user or _env("DB_USER")
    password = password if password is not None else _env("DB_PASSWORD")
    dbname = dbname or _env("DB_NAME")
    return f"postgresql+pg8000://{user}:{password}@{host}:{port}/{dbname}"


def get_engine(url: str | None = None, **kwargs) -> Engine:
    """Build the SQLAlchemy engine. Pass `url` to override the `DB_*`-derived default (tests)."""
    return create_engine(url or build_url(), **kwargs)


def _schema_sql() -> str:
    return resources.files(__package__).joinpath(_SCHEMA_FILE).read_text(encoding="utf-8")


def create_schema(engine: Engine, schema_path: Path | None = None) -> None:
    """Create every table in `schemas.sql` (or `schema_path`, for tests) against `engine`.

    `schemas.sql` is the source of truth: this executes it verbatim, statement by statement, inside
    one transaction - it does not derive DDL from the SQLAlchemy models in `models.py`.
    """
    sql = schema_path.read_text(encoding="utf-8") if schema_path is not None else _schema_sql()
    # Strip both full-line and trailing "--" comments before splitting on ";" - this file has no
    # string literal containing "--", so a plain substring cut is safe. A naive split on ";" alone
    # would fold comment text into a statement chunk and confuse or corrupt it.
    code_lines = [line.split("--", 1)[0] for line in sql.splitlines()]
    statements = [s.strip() for s in "\n".join(code_lines).split(";") if s.strip()]
    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))


def create_database_if_missing(maintenance_url: str, dbname: str) -> bool:
    """`CREATE DATABASE dbname` against the server `maintenance_url` connects to, if it does not
    already exist. Returns True if it was created, False if it already existed.

    `CREATE DATABASE` cannot run inside a transaction block, so this connects with autocommit.
    `maintenance_url` should point at an existing database on the target server (e.g. the server's
    default `postgres` database), never at `dbname` itself.
    """
    engine = create_engine(maintenance_url, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": dbname}
            ).first()
            if exists:
                return False
            # Identifier, not a value - cannot be a bound parameter; dbname is operator-supplied
            # (task-file-recorded, never end-user input), and quote_ident-style validation below
            # keeps this from being a SQL-injection vector.
            if not dbname.replace("_", "").isalnum():
                raise ValueError(f"unsafe database name: {dbname!r}")
            conn.execute(text(f'CREATE DATABASE "{dbname}"'))
            return True
    finally:
        engine.dispose()
