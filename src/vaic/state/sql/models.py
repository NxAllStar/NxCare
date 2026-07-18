"""SQLAlchemy ORM models for the durable PostgreSQL store (OI-15).

One table per entity in `vaic.models.entities.ENTITIES`, column-for-column, including the
denormalized `patient_id` columns added by TASK-016 (`Diagnosis`, `ServiceOrder`, `Slot`, `Payment`,
`AuditLogEntry`) so Own-scope resolves directly at the row level too. `Base.metadata.create_all` is
the only schema-creation path - there is no separate DDL file to keep in sync.
"""

from __future__ import annotations

from sqlalchemy import (
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


# ---- enums, matching src/vaic/models/enums.py exactly -------------------------------------------


def _enum(name: str, *values: str) -> Enum:
    return Enum(*values, name=name, native_enum=True)


PriorityLevelEnum = _enum("priority_level_enum", "ROUTINE", "URGENT", "EMERGENCY")
AppointmentStatusEnum = _enum(
    "appointment_status_enum",
    "PROPOSED",
    "BOOKED",
    "CHECKED_IN",
    "IN_CONSULT",
    "DONE",
    "NO_SHOW",
    "CANCELLED",
)
PaymentStatusEnum = _enum("payment_status_enum", "UNPAID", "PAID")
CarePlanStatusEnum = _enum("care_plan_status_enum", "DRAFT", "ACTIVE", "COMPLETED")
ExecutionStatusEnum = _enum(
    "execution_status_enum", "LOCKED", "PENDING", "IN_PROGRESS", "DONE", "CANCELLED"
)
ResourceTypeEnum = _enum("resource_type_enum", "DOCTOR", "TECHNICIAN", "ROOM", "EQUIPMENT")
DisruptionEventTypeEnum = _enum(
    "disruption_event_type_enum",
    "EQUIPMENT_FAILURE",
    "OVERLOAD",
    "SCHEDULE_CHANGE",
    "EMERGENCY",
)
DisruptionStatusEnum = _enum(
    "disruption_status_enum",
    "DETECTED",
    "ASSESSED",
    "AUTO_RESOLVED",
    "PENDING_APPROVAL",
    "APPROVED",
    "REJECTED",
)
NotificationChannelEnum = _enum("notification_channel_enum", "IN_APP", "SCREEN", "SMS")
PaymentSubjectTypeEnum = _enum("payment_subject_type_enum", "TASK", "APPOINTMENT")


def _uuid_pk() -> Column:
    return Column(UUID(as_uuid=True), primary_key=True)


def _uuid_fk(table: str, column: str = "id", *, ondelete: str = "RESTRICT") -> Column:
    return Column(UUID(as_uuid=True), ForeignKey(f"{table}.{column}", ondelete=ondelete))


# ---- tables, in dependency order ------------------------------------------------------------


class PatientRow(Base):
    __tablename__ = "patients"

    id = _uuid_pk()
    full_name = Column(Text, nullable=False)
    phone = Column(Text)
    patient_code = Column(Text, nullable=False, unique=True)
    priority_level = Column(PriorityLevelEnum, nullable=False, server_default="ROUTINE")
    created_at = Column(TIMESTAMP(timezone=True), nullable=False)


class ResourceRow(Base):
    __tablename__ = "resources"

    id = _uuid_pk()
    type = Column(ResourceTypeEnum, nullable=False)
    department_id = Column(UUID(as_uuid=True), nullable=False)
    is_available = Column(Boolean, nullable=False, server_default="true")
    capacity_per_hour = Column(Integer)


class ServiceTypeRow(Base):
    __tablename__ = "service_types"

    id = _uuid_pk()
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

    id = _uuid_pk()
    event_type = Column(DisruptionEventTypeEnum, nullable=False)
    status = Column(DisruptionStatusEnum, nullable=False, server_default="DETECTED")
    blast_radius = Column(Integer, nullable=False, server_default="0")
    decided_by = Column(UUID(as_uuid=True))


class IntakeSessionRow(Base):
    __tablename__ = "intake_sessions"

    id = _uuid_pk()
    patient_id = _uuid_fk("patients", ondelete="RESTRICT")
    transcript = Column(Text, nullable=False, server_default="")
    structured_triage = Column(JSONB, nullable=False, server_default="{}")
    emergency_suspected = Column(Boolean, nullable=False, server_default="false")
    created_at = Column(TIMESTAMP(timezone=True), nullable=False)

    __table_args__ = (CheckConstraint("patient_id IS NOT NULL"),)


class AppointmentRow(Base):
    __tablename__ = "appointments"

    id = _uuid_pk()
    patient_id = _uuid_fk("patients", ondelete="RESTRICT")
    specialty = Column(Text, nullable=False)
    status = Column(AppointmentStatusEnum, nullable=False, server_default="PROPOSED")
    payment_status = Column(PaymentStatusEnum, nullable=False, server_default="UNPAID")
    slot_start = Column(TIMESTAMP(timezone=True))
    created_at = Column(TIMESTAMP(timezone=True), nullable=False)


class DiagnosisRow(Base):
    __tablename__ = "diagnoses"

    id = _uuid_pk()
    patient_id = _uuid_fk("patients", ondelete="RESTRICT")  # denormalized, TASK-016
    appointment_id = _uuid_fk("appointments", ondelete="RESTRICT")
    conditions = Column(JSONB, nullable=False, server_default="[]")
    diagnosed_by = Column(UUID(as_uuid=True), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False)


class ServiceOrderRow(Base):
    __tablename__ = "service_orders"

    id = _uuid_pk()
    patient_id = _uuid_fk("patients", ondelete="RESTRICT")  # denormalized, TASK-016
    diagnosis_id = _uuid_fk("diagnoses", ondelete="RESTRICT")
    service_type_id = _uuid_fk("service_types", ondelete="RESTRICT")
    ordered_by = Column(UUID(as_uuid=True), nullable=False)
    signed_at = Column(TIMESTAMP(timezone=True), nullable=False)


class CarePlanRow(Base):
    __tablename__ = "care_plans"

    id = _uuid_pk()
    patient_id = _uuid_fk("patients", ondelete="RESTRICT")
    diagnosis_id = _uuid_fk("diagnoses", ondelete="RESTRICT")
    status = Column(CarePlanStatusEnum, nullable=False, server_default="DRAFT")
    assigned_staff = Column(JSONB, nullable=False, server_default="[]")
    created_at = Column(TIMESTAMP(timezone=True), nullable=False)


class TaskRow(Base):
    __tablename__ = "tasks"

    id = _uuid_pk()
    care_plan_id = _uuid_fk("care_plans", ondelete="RESTRICT")
    service_order_id = _uuid_fk("service_orders", ondelete="RESTRICT")
    owner_id = _uuid_fk("resources", ondelete="RESTRICT")
    execution_status = Column(ExecutionStatusEnum, nullable=False, server_default="LOCKED")
    payment_status = Column(PaymentStatusEnum, nullable=False, server_default="UNPAID")
    estimated_duration_min = Column(Integer, nullable=False, server_default="0")
    sequence_index = Column(Integer, nullable=False, server_default="0")
    depends_on = Column(JSONB, nullable=False, server_default="[]")
    created_at = Column(TIMESTAMP(timezone=True), nullable=False)


class SlotRow(Base):
    __tablename__ = "slots"

    id = _uuid_pk()
    patient_id = _uuid_fk("patients", ondelete="RESTRICT")  # denormalized, TASK-016
    task_id = _uuid_fk("tasks", ondelete="RESTRICT")
    owner_id = _uuid_fk("resources", ondelete="RESTRICT")
    start = Column(TIMESTAMP(timezone=True), nullable=False)
    end = Column("end", TIMESTAMP(timezone=True))


class PaymentRow(Base):
    __tablename__ = "payments"

    id = _uuid_pk()
    patient_id = _uuid_fk("patients", ondelete="RESTRICT")  # denormalized, TASK-016
    subject_type = Column(PaymentSubjectTypeEnum, nullable=False)
    subject_id = Column(UUID(as_uuid=True), nullable=False)
    amount = Column(Numeric)
    status = Column(PaymentStatusEnum, nullable=False, server_default="UNPAID")
    confirmed_by = Column(UUID(as_uuid=True))
    confirmed_at = Column(TIMESTAMP(timezone=True))


class NotificationRow(Base):
    __tablename__ = "notifications"

    id = _uuid_pk()
    patient_id = _uuid_fk("patients", ondelete="RESTRICT")
    channel = Column(NotificationChannelEnum, nullable=False, server_default="IN_APP")
    body = Column(Text, nullable=False)
    reason = Column(Text)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False)


class AuditLogEntryRow(Base):
    __tablename__ = "audit_log_entries"

    id = _uuid_pk()
    actor = Column(Text, nullable=False)
    action = Column(Text, nullable=False)
    target_id = Column(UUID(as_uuid=True))
    patient_id = _uuid_fk("patients", ondelete="SET NULL")  # nullable, denormalized (TASK-016)
    reasoning = Column(Text, nullable=False, server_default="")
    created_at = Column(TIMESTAMP(timezone=True), nullable=False)


class ScanEventRow(Base):
    __tablename__ = "scan_events"

    id = _uuid_pk()
    patient_id = _uuid_fk("patients", ondelete="RESTRICT")
    task_id = _uuid_fk("tasks", ondelete="RESTRICT")
    scanned_by = _uuid_fk("resources", ondelete="RESTRICT")
    scanned_at = Column(TIMESTAMP(timezone=True), nullable=False)
