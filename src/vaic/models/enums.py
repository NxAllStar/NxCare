"""Canonical enums for VAIC. Values are English UPPER_SNAKE_CASE (see docs/specs/03-glossary.md).

Display labels may be localised in the UI; the stored value never is.
"""

from __future__ import annotations

from enum import StrEnum


class ExecutionStatus(StrEnum):
    """Task.execution_status - see docs/specs/08-data-model.md state machine."""

    LOCKED = "LOCKED"  # unpaid: excluded from every queue and load (BR-10)
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    DONE = "DONE"
    CANCELLED = "CANCELLED"


class PaymentStatus(StrEnum):
    UNPAID = "UNPAID"
    PAID = "PAID"


class AppointmentStatus(StrEnum):
    PROPOSED = "PROPOSED"
    BOOKED = "BOOKED"
    CHECKED_IN = "CHECKED_IN"
    IN_CONSULT = "IN_CONSULT"
    DONE = "DONE"
    NO_SHOW = "NO_SHOW"
    CANCELLED = "CANCELLED"


class CarePlanStatus(StrEnum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"


class DisruptionStatus(StrEnum):
    DETECTED = "DETECTED"
    ASSESSED = "ASSESSED"
    AUTO_RESOLVED = "AUTO_RESOLVED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class PriorityLevel(StrEnum):
    ROUTINE = "ROUTINE"
    URGENT = "URGENT"
    EMERGENCY = "EMERGENCY"


class ResourceType(StrEnum):
    DOCTOR = "DOCTOR"
    TECHNICIAN = "TECHNICIAN"
    ROOM = "ROOM"
    EQUIPMENT = "EQUIPMENT"


class DisruptionEventType(StrEnum):
    EQUIPMENT_FAILURE = "EQUIPMENT_FAILURE"
    OVERLOAD = "OVERLOAD"
    SCHEDULE_CHANGE = "SCHEDULE_CHANGE"
    EMERGENCY = "EMERGENCY"


class NotificationChannel(StrEnum):
    IN_APP = "IN_APP"
    SCREEN = "SCREEN"
    SMS = "SMS"


class PaymentSubjectType(StrEnum):
    TASK = "TASK"
    APPOINTMENT = "APPOINTMENT"
