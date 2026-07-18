"""ADR-003 ticketed queue: Department, QueueTicket, Appointment.owner_id

Revision ID: 6578d1fee0c9
Revises: a3a9a1c7715a
Create Date: 2026-07-18 23:05:18.484801

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '6578d1fee0c9'
down_revision: str | Sequence[str] | None = 'a3a9a1c7715a'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add ADR-003: Department, QueueTicket, and Appointment.owner_id."""
    # priority_level_enum already exists (created by the baseline / present in the live DB), so it
    # is referenced with create_type=False. The two queue_* enums are new and created here.
    priority_band = postgresql.ENUM(
        "ROUTINE", "URGENT", "EMERGENCY", name="priority_level_enum", create_type=False
    )
    queue_status = postgresql.ENUM(
        "WAITING", "CALLED", "IN_SERVICE", "DONE", "SKIPPED", name="queue_ticket_status_enum"
    )
    queue_subject = postgresql.ENUM("CONSULT", "SERVICE", name="queue_subject_type_enum")

    op.create_table(
        "departments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.Text(), nullable=False, unique=True),
        sa.Column("display_label", sa.Text(), nullable=False),
    )
    op.create_table(
        "queue_tickets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("patients.id", ondelete="RESTRICT"),
        ),
        sa.Column(
            "department_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("departments.id", ondelete="RESTRICT"),
        ),
        sa.Column("capability", sa.Text()),
        sa.Column("priority_band", priority_band, nullable=False, server_default="ROUTINE"),
        sa.Column("subject_type", queue_subject, nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ticket_seq", sa.Integer(), nullable=False),
        sa.Column("ticket_label", sa.Text(), nullable=False),
        sa.Column("status", queue_status, nullable=False, server_default="WAITING"),
        sa.Column(
            "called_by_owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("resources.id", ondelete="RESTRICT"),
        ),
        sa.Column("issued_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("called_at", sa.TIMESTAMP(timezone=True)),
    )
    op.add_column(
        "appointments",
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("resources.id", ondelete="RESTRICT"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Reverse ADR-003."""
    op.drop_column("appointments", "owner_id")
    op.drop_table("queue_tickets")
    op.drop_table("departments")
    # priority_level_enum is owned by the baseline - do not drop it here.
    postgresql.ENUM(name="queue_ticket_status_enum").drop(op.get_bind(), checkfirst=False)
    postgresql.ENUM(name="queue_subject_type_enum").drop(op.get_bind(), checkfirst=False)
