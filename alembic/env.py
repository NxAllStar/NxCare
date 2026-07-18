"""Alembic migration environment for the VAIC durable PostgreSQL store (OI-15).

Wired to the project's own configuration and ORM metadata rather than a hardcoded URL:

- the connection URL comes from `vaic.config.get_settings().postgres_url` (the same
  `postgresql+asyncpg://` URL the app engine uses), so credentials live only in the
  environment / `.env` and are never written into `alembic.ini` (security-privacy.md);
- `target_metadata` is `vaic.state.sql.models.Base.metadata`, the single source of truth
  for every table, so `alembic revision --autogenerate` diffs against the real ORM models.
"""

from __future__ import annotations

import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# The package lives under ./src (see [tool.pytest.ini_options] pythonpath in pyproject.toml);
# put it on the path so `import vaic...` works when alembic runs from the repo root.
_SRC = Path(__file__).resolve().parent.parent / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from vaic.config import get_settings  # noqa: E402
from vaic.state.sql.models import Base  # noqa: E402

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Feed the real connection URL in from settings, overriding the alembic.ini placeholder.
config.set_main_option("sqlalchemy.url", get_settings().postgres_url)

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Model metadata for 'autogenerate' support - the one Base every entity table hangs off.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (emit SQL without a live DBAPI connection)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and associate a connection with the migration context."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
