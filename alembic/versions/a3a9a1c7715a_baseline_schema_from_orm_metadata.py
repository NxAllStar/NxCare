"""baseline schema (original 15 entities, pre ADR-003)

Revision ID: a3a9a1c7715a
Revises:
Create Date: 2026-07-18 21:35:02.958239

Frozen baseline of the ORIGINAL 15-entity schema, as it existed before ADR-003. It is
"frozen" on purpose: it builds a fresh MetaData holding only the 15 pre-ADR-003 tables and
strips `Appointment.owner_id`, so it stays a fixed point-in-time snapshot even though the live
ORM models (`src/vaic/state/sql/models.py`) have since grown to 17 entities. ADR-003's
`Department`, `QueueTicket`, and `Appointment.owner_id` land in the follow-on delta revision,
not here.

Adopting Alembic on the existing database (which already holds these 15 tables): stamp this
revision without running it -

    alembic stamp a3a9a1c7715a

then `alembic upgrade head` applies only the ADR-003 delta. On a brand-new empty database,
`alembic upgrade head` runs this baseline and then the delta, reproducing the full 17-entity
schema.
"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a3a9a1c7715a'
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# The 15 tables that existed before ADR-003. Frozen here so this baseline never drifts as the
# live ORM metadata grows - later schema changes are explicit deltas, never a re-snapshot.
_BASELINE_TABLES: tuple[str, ...] = (
    "patients",
    "resources",
    "service_types",
    "disruption_events",
    "intake_sessions",
    "appointments",
    "diagnoses",
    "service_orders",
    "care_plans",
    "tasks",
    "slots",
    "payments",
    "notifications",
    "audit_log_entries",
    "scan_events",
)


def _frozen_metadata():
    """A MetaData holding only the 15 pre-ADR-003 tables, with `appointments.owner_id` stripped."""
    from sqlalchemy import MetaData

    from vaic.state.sql.models import Base

    frozen = MetaData()
    for name in _BASELINE_TABLES:
        table = Base.metadata.tables[name].to_metadata(frozen)
        if name == "appointments" and "owner_id" in table.c:
            # Drop the owner_id FK constraint first: removing the column alone leaves a dangling
            # `FOREIGN KEY(owner_id)` in the emitted DDL. ColumnCollection membership is by name.
            for constraint in list(table.constraints):
                if "owner_id" in getattr(constraint, "columns", ()):
                    table.constraints.discard(constraint)
            table._columns.remove(table.c["owner_id"])  # ADR-003 column belongs to the delta
    return frozen


def upgrade() -> None:
    """Create the original 15 tables (and their enum types)."""
    _frozen_metadata().create_all(bind=op.get_bind())


def downgrade() -> None:
    """Drop the original 15 tables (and their enum types)."""
    _frozen_metadata().drop_all(bind=op.get_bind())
