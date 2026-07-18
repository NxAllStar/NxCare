"""baseline schema from ORM metadata

Revision ID: a3a9a1c7715a
Revises:
Create Date: 2026-07-18 21:35:02.958239

Baseline snapshot of the current 17-entity schema (see src/vaic/state/sql/models.py,
which mirrors docs/specs/08-data-model.md column-for-column). It replaces the previous
`Base.metadata.create_all` bootstrap as the schema-creation path for a fresh database.

This first revision creates the schema straight from the ORM metadata - the single source
of truth - so the baseline can never drift from the models. It includes ADR-003's `Department`
and `QueueTicket` entities and `Appointment.owner_id`: those landed while this baseline had not
yet been applied to any database, so they belong in the initial snapshot rather than a delta.

From the first `alembic upgrade` against a real database onward, every *subsequent* schema
change must be an explicit, reviewable migration, generated with
`alembic revision --autogenerate` and hand-checked, not another metadata snapshot.
"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a3a9a1c7715a'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create every table (and its enum types) defined on the ORM metadata."""
    # Imported inside the function, not at module top level: `alembic history`/`heads`/`show`
    # load this file without running env.py (which puts ./src on sys.path), so a top-level
    # `import vaic...` would break those commands.
    from vaic.state.sql.models import Base

    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    """Drop every table (and its enum types) defined on the ORM metadata."""
    from vaic.state.sql.models import Base

    Base.metadata.drop_all(bind=op.get_bind())
