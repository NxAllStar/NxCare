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
