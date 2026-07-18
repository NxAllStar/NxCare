"""SQLAlchemy models mirroring `schemas.sql` (TASK-032).

These models describe the relational schema for querying; they do not create it. Table creation
runs `schemas.sql` verbatim (see `engine.py::create_schema`) so the SQL file stays the single source
of truth for DDL, per the project's request. Requires the optional `sql` dependency group
(`pip install -e ".[sql]"`).
"""

from __future__ import annotations

from sqlalchemy import (
    JSON,
    TIMESTAMP,
    Boolean,
    CheckConstraint,
    Column,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# ---- enums, matching src/vaic/models/enums.py and the CREATE TYPE statements in schemas.sql -----

def _enum(name: str, *values: str) -> Enum:
    return Enum(*values, name=name, create_type=False)


PriorityLevelEnum = _enum("priority_level_enum", "ROUTINE", "URGENT", "EMERGENCY")
AppointmentStatusEnum = _enum(
    "appointment_status_enum",
    "PROPOSED", "BOOKED", "CHECKED_IN", "IN_CONSULT", "DONE", "NO_SHOW", "CANCELLED",
)
PaymentStatusEnum = _enum("payment_status_enum", "UNPAID", "PAID")
CarePlanStatusEnum = _enum("care_plan_status_enum", "DRAFT", "ACTIVE", "COMPLETED")
ExecutionStatusEnum = _enum(
    "execution_status_enum", "LOCKED", "PENDING", "IN_PROGRESS", "DONE", "CANCELLED"
)
ResourceTypeEnum = _enum("resource_type_enum", "DOCTOR", "TECHNICIAN", "ROOM", "EQUIPMENT")
DisruptionEventTypeEnum = _enum(
    "disruption_event_type_enum",
    "EQUIPMENT_FAILURE", "OVERLOAD", "SCHEDULE_CHANGE", "EMERGENCY",
)
DisruptionStatusEnum = _enum(
    "disruption_status_enum",
    "DETECTED", "ASSESSED", "AUTO_RESOLVED", "PENDING_APPROVAL", "APPROVED", "REJECTED",
)
NotificationChannelEnum = _enum("notification_channel_enum", "IN_APP", "SCREEN", "SMS")
PaymentSubjectTypeEnum = _enum("payment_subject_type_enum", "TASK", "APPOINTMENT")


# ---- tables, in the same dependency order as schemas.sql ----------------------------------------

class PatientRow(Base):
    __tablename__ = "patients"

    id = Column(UUID(as_uuid=True), primary_key=True)
    full_name = Column(Text, nullable=False)
    phone = Column(Text)
    patient_code = Column(Text, nullable=False, unique=True)
    priority_level = Column(PriorityLevelEnum, nullable=False, server_default="ROUTINE")
    created_at = Column(TIMESTAMP(timezone=True), nullable=False)


class ResourceRow(Base):
    __tablename__ = "resources"

    id = Column(UUID(as_uuid=True), primary_key=True)
    type = Column(ResourceTypeEnum, nullable=False)
    department_id = Column(UUID(as_uuid=True), nullable=False)
    is_available = Column(Boolean, nullable=False, server_default="true")
    capacity_per_hour = Column(Integer)


class ServiceTypeRow(Base):
    __tablename__ = "service_types"

    id = Column(UUID(as_uuid=True), primary_key=True)
    code = Column(Text, nullable=False, unique=True)
    display_label = Column(Text, nullable=False)
    requires_fasting = Column(Boolean, nullable=False, server_default="false")
    turnaround_minutes = Column(
        Integer, CheckConstraint("turnaround_minutes >= 0"), nullable=False, server_default="0"
    )
    default_duration_min = Column(
        Integer, CheckConstraint("default_duration_min > 0"), nullable=False, server_default="10"
    )


class DisruptionEventRow(Base):
    __tablename__ = "disruption_events"

    id = Column(UUID(as_uuid=True), primary_key=True)
    event_type = Column(DisruptionEventTypeEnum, nullable=False)
    status = Column(DisruptionStatusEnum, nullable=False, server_default="DETECTED")
    blast_radius = Column(Integer, nullable=False, server_default="0")
    decided_by = Column(UUID(as_uuid=True))


class IntakeSessionRow(Base):
    __tablename__ = "intake_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True)
    patient_id = Column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False
    )
    transcript = Column(Text, nullable=False, server_default="")
    structured_triage = Column(JSONB, nullable=False, server_default="{}")
    emergency_suspected = Column(Boolean, nullable=False, server_default="false")
    created_at = Column(TIMESTAMP(timezone=True), nullable=False)


class AppointmentRow(Base):
    __tablename__ = "appointments"

    id = Column(UUID(as_uuid=True), primary_key=True)
    patient_id = Column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False
    )
    specialty = Column(Text, nullable=False)
    status = Column(AppointmentStatusEnum, nullable=False, server_default="PROPOSED")
    payment_status = Column(PaymentStatusEnum, nullable=False, server_default="UNPAID")
    slot_start = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False)


class DiagnosisRow(Base):
    __tablename__ = "diagnoses"

    id = Column(UUID(as_uuid=True), primary_key=True)
    appointment_id = Column(
        UUID(as_uuid=True), ForeignKey("appointments.id", ondelete="RESTRICT"), nullable=False
    )
    conditions = Column(JSONB, nullable=False, server_default="[]")
    diagnosed_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False)


class CarePlanRow(Base):
    __tablename__ = "care_plans"

    id = Column(UUID(as_uuid=True), primary_key=True)
    patient_id = Column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False
    )
    diagnosis_id = Column(
        UUID(as_uuid=True), ForeignKey("diagnoses.id", ondelete="RESTRICT"), nullable=False
    )
    status = Column(CarePlanStatusEnum, nullable=False, server_default="DRAFT")
    assigned_staff = Column(JSONB, nullable=False, server_default="[]")
    created_at = Column(TIMESTAMP(timezone=True), nullable=False)


class NotificationRow(Base):
    __tablename__ = "notifications"

    id = Column(UUID(as_uuid=True), primary_key=True)
    patient_id = Column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False
    )
    channel = Column(NotificationChannelEnum, nullable=False, server_default="IN_APP")
    body = Column(Text, nullable=False)
    reason = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False)


class ServiceOrderRow(Base):
    __tablename__ = "service_orders"

    id = Column(UUID(as_uuid=True), primary_key=True)
    diagnosis_id = Column(
        UUID(as_uuid=True), ForeignKey("diagnoses.id", ondelete="RESTRICT"), nullable=False
    )
    service_type_id = Column(
        UUID(as_uuid=True), ForeignKey("service_types.id", ondelete="RESTRICT"), nullable=False
    )
    ordered_by = Column(UUID(as_uuid=True), nullable=False)
    signed_at = Column(TIMESTAMP(timezone=True), nullable=False)


class TaskRow(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True)
    care_plan_id = Column(
        UUID(as_uuid=True), ForeignKey("care_plans.id", ondelete="RESTRICT"), nullable=False
    )
    service_order_id = Column(
        UUID(as_uuid=True), ForeignKey("service_orders.id", ondelete="RESTRICT"), nullable=False
    )
    owner_id = Column(
        UUID(as_uuid=True), ForeignKey("resources.id", ondelete="RESTRICT"), nullable=False
    )
    execution_status = Column(ExecutionStatusEnum, nullable=False, server_default="LOCKED")
    payment_status = Column(PaymentStatusEnum, nullable=False, server_default="UNPAID")
    estimated_duration_min = Column(Integer, nullable=False, server_default="0")
    sequence_index = Column(Integer, nullable=False, server_default="0")
    depends_on = Column(JSONB, nullable=False, server_default="[]")
    created_at = Column(TIMESTAMP(timezone=True), nullable=False)


class SlotRow(Base):
    __tablename__ = "slots"

    id = Column(UUID(as_uuid=True), primary_key=True)
    task_id = Column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="RESTRICT"), nullable=False
    )
    owner_id = Column(
        UUID(as_uuid=True), ForeignKey("resources.id", ondelete="RESTRICT"), nullable=False
    )
    start = Column(TIMESTAMP(timezone=True), nullable=False)
    end = Column("end", TIMESTAMP(timezone=True))


class ScanEventRow(Base):
    __tablename__ = "scan_events"

    id = Column(UUID(as_uuid=True), primary_key=True)
    patient_id = Column(
        UUID(as_uuid=True), ForeignKey("patients.id", ondelete="RESTRICT"), nullable=False
    )
    task_id = Column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="RESTRICT"), nullable=False
    )
    scanned_by = Column(
        UUID(as_uuid=True), ForeignKey("resources.id", ondelete="RESTRICT"), nullable=False
    )
    scanned_at = Column(TIMESTAMP(timezone=True), nullable=False)


class PaymentRow(Base):
    __tablename__ = "payments"

    id = Column(UUID(as_uuid=True), primary_key=True)
    subject_type = Column(PaymentSubjectTypeEnum, nullable=False)
    subject_id = Column(UUID(as_uuid=True), nullable=False)
    amount = Column(Numeric)
    status = Column(PaymentStatusEnum, nullable=False, server_default="UNPAID")
    confirmed_by = Column(UUID(as_uuid=True))
    confirmed_at = Column(TIMESTAMP(timezone=True))


class AuditLogEntryRow(Base):
    __tablename__ = "audit_log_entries"

    id = Column(UUID(as_uuid=True), primary_key=True)
    actor = Column(Text, nullable=False)
    action = Column(Text, nullable=False)
    target_id = Column(UUID(as_uuid=True))
    reasoning = Column(Text, nullable=False, server_default="")
    created_at = Column(TIMESTAMP(timezone=True), nullable=False)


assert JSON  # imported for type clarity only; JSONB is what is actually used (Postgres-specific)
