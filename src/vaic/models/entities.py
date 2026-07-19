"""Pydantic entities for VAIC, implementing docs/specs/08-data-model.md.

The spec is the source of truth; change the spec in the same PR as any model change
(see .claude/rules/data-model.md). No ORM - these persist behind vaic.state.Repository.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from .enums import (
    AppointmentStatus,
    CarePlanStatus,
    DisruptionEventType,
    DisruptionStatus,
    ExecutionStatus,
    NotificationChannel,
    PaymentStatus,
    PaymentSubjectType,
    PriorityLevel,
    QueueSubjectType,
    QueueTicketStatus,
    ResourceType,
)


def _now() -> datetime:
    return datetime.now(UTC)


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(default_factory=uuid4)


class Patient(_Base):
    full_name: str  # PII - excluded from logs (NFR-SEC-01)
    phone: str | None = None  # PII
    patient_code: str  # scannable identifier shown in the app (FR-17); also the login username
    priority_level: PriorityLevel = PriorityLevel.ROUTINE
    created_at: datetime = Field(default_factory=_now)
    # FR-18 login: bcrypt hash (auth/password_login.py), NEVER the API - every response schema
    # built from this entity MUST exclude it (see api/schemas.py::camel_schema's `exclude`).
    password_hash: str | None = None


class IntakeSession(_Base):
    patient_id: UUID
    transcript: str = ""  # Sensitive PII, untrusted content (NFR-SEC-11) - never logged
    # structured triage: {specialty, priority_level, constraints}
    structured_triage: dict = Field(default_factory=dict)
    emergency_suspected: bool = False  # BF-05: blocks routine booking until staff-confirmed
    created_at: datetime = Field(default_factory=_now)


class Appointment(_Base):
    patient_id: UUID
    specialty: str
    status: AppointmentStatus = AppointmentStatus.PROPOSED
    payment_status: PaymentStatus = PaymentStatus.UNPAID
    # ADR-003: the consult's owning Resource (doctor/room). Nullable while PROPOSED, before a
    # department queue is attached. Its queue position lives on a QueueTicket, not here.
    owner_id: UUID | None = None
    # ADR-003: reinterpreted as a *recommended arrival window*, not a reserved slot - the walk-in
    # ticket, not this timestamp, determines serving order.
    slot_start: datetime | None = None
    created_at: datetime = Field(default_factory=_now)


class Diagnosis(_Base):
    patient_id: UUID  # denormalized from Appointment so Own-scope resolves directly (TASK-016)
    appointment_id: UUID
    conditions: list[str] = Field(default_factory=list)  # Sensitive PII
    diagnosed_by: UUID  # the doctor
    created_at: datetime = Field(default_factory=_now)


class ServiceOrder(_Base):
    patient_id: UUID  # denormalized from Diagnosis so Own-scope resolves directly (TASK-016)
    diagnosis_id: UUID
    service_type_id: UUID
    ordered_by: UUID  # only a doctor may create this (BR-05) - enforced at the write boundary
    signed_at: datetime = Field(default_factory=_now)


class ServiceType(_Base):
    code: str  # e.g. BLOOD_TEST
    display_label: str
    requires_fasting: bool = False
    turnaround_minutes: int = 0
    default_duration_min: int = 10


class CarePlan(_Base):
    patient_id: UUID
    diagnosis_id: UUID
    status: CarePlanStatus = CarePlanStatus.DRAFT
    assigned_staff: list[UUID] = Field(default_factory=list)  # drives Assigned data scope
    created_at: datetime = Field(default_factory=_now)


class Task(_Base):
    care_plan_id: UUID
    service_order_id: UUID
    owner_id: UUID  # a Resource (doctor / technician / room)
    execution_status: ExecutionStatus = ExecutionStatus.LOCKED
    payment_status: PaymentStatus = PaymentStatus.UNPAID
    estimated_duration_min: int = 0  # from the forecast tool
    sequence_index: int = 0
    depends_on: list[UUID] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=_now)

    @property
    def is_locked(self) -> bool:
        """A task is locked while unpaid (BR-10): excluded from every queue and load."""
        return self.payment_status is PaymentStatus.UNPAID

    @property
    def in_queue(self) -> bool:
        """A task counts toward an owner's queue only when paid and not yet finished (BR-10)."""
        return (not self.is_locked) and self.execution_status in (
            ExecutionStatus.PENDING,
            ExecutionStatus.IN_PROGRESS,
        )


class Slot(_Base):
    patient_id: UUID  # denormalized from Task/CarePlan so Own-scope resolves directly (TASK-016)
    task_id: UUID
    owner_id: UUID
    start: datetime
    end: datetime | None = None


class Payment(_Base):
    """A proceed-gate flag, NOT money processing (AS-02). `amount` is display-only."""

    patient_id: UUID  # denormalized since subject_id is polymorphic (TASK-016)
    subject_type: PaymentSubjectType
    subject_id: UUID
    amount: Decimal | None = None
    status: PaymentStatus = PaymentStatus.UNPAID
    confirmed_by: UUID | None = None  # authorised source (staff / hospital billing)
    confirmed_at: datetime | None = None


class Department(_Base):
    """A queue-owning department (ADR-003). `code` renders the ticket label prefix, e.g. `DepB`."""

    code: str  # short prefix shown on tickets/screens, e.g. `DepB`
    display_label: str


class Resource(_Base):
    type: ResourceType
    department_id: UUID
    is_available: bool = True
    capacity_per_hour: int | None = None
    # FR-18 staff login (doctor only, for now): a plain login handle and a bcrypt hash
    # (auth/password_login.py). Both None for non-login resources (room/equipment, or a
    # doctor/technician not yet issued a login). NEVER the API - see `Patient.password_hash`.
    username: str | None = None
    password_hash: str | None = None


class DisruptionEvent(_Base):
    event_type: DisruptionEventType
    status: DisruptionStatus = DisruptionStatus.DETECTED
    blast_radius: int = 0
    decided_by: UUID | None = None


class Notification(_Base):
    patient_id: UUID
    channel: NotificationChannel = NotificationChannel.IN_APP
    body: str  # never contains another patient's data (FR-11 AC-11.2)
    reason: str | None = None
    created_at: datetime = Field(default_factory=_now)


class AuditLogEntry(_Base):
    """Append-only: no actor edits a recorded decision (BR-23)."""

    actor: str
    action: str
    target_id: UUID | None = None
    # Nullable (TASK-016): not every entry is about a patient (e.g. a blocked unknown-tool call
    # audited before any patient context is resolved). When set, it resolves Own-scope directly.
    patient_id: UUID | None = None
    reasoning: str = ""
    created_at: datetime = Field(default_factory=_now)


class ScanEvent(_Base):
    patient_id: UUID
    task_id: UUID
    scanned_by: UUID  # must be the task owner (BR-26)
    scanned_at: datetime = Field(default_factory=_now)


class QueueTicket(_Base):
    """A numbered ticket in a department-scoped shared queue (ADR-003).

    Polymorphic over its subject, like `Payment`: a `CONSULT` ticket points at an `Appointment`,
    a `SERVICE` ticket at a `Task`. `ticket_label` (e.g. `DepB-00001`) is a human-readable identity
    announced on the desk screen, NOT the serving order - order is `(priority_band, issued_at)`.
    """

    patient_id: UUID  # set at desk registration; denormalized so Own-scope resolves directly
    department_id: UUID  # FK -> Department; the queue scope and number series
    # optional service-capability key: splits the queue when a department's rooms are not
    # interchangeable (skill-based routing). None = one shared queue for the whole department.
    capability: str | None = None
    # copied from Patient.priority_level at issue; drives the serving order and the number series
    priority_band: PriorityLevel = PriorityLevel.ROUTINE
    subject_type: QueueSubjectType
    subject_id: UUID  # FK -> Appointment (CONSULT) or Task (SERVICE)
    ticket_seq: int  # monotonic within (department, priority_band, day)
    ticket_label: str  # rendered token, e.g. `DepB-00001` / `DepB-E-00001`
    status: QueueTicketStatus = QueueTicketStatus.WAITING
    called_by_owner_id: UUID | None = None  # the Resource that called it; None until CALLED
    issued_at: datetime = Field(default_factory=_now)  # FIFO tiebreaker within a band
    called_at: datetime | None = None


# The registry the repository uses to key collections. English names, one per entity.
ENTITIES: tuple[type[_Base], ...] = (
    Patient,
    IntakeSession,
    Appointment,
    Diagnosis,
    ServiceOrder,
    ServiceType,
    CarePlan,
    Task,
    Slot,
    Payment,
    Department,
    Resource,
    DisruptionEvent,
    Notification,
    AuditLogEntry,
    ScanEvent,
    QueueTicket,
)
