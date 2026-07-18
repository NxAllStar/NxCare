"""Deterministic synthetic seed for the `nxcare` PostgreSQL database (TASK-033).

Generates 10-50 rows per table (a fixed RNG seed keeps the run reproducible - data-model.md's seed
discipline), inserted through SQLAlchemy ORM in FK dependency order. No real personal data, ever -
every field is a synthetic placeholder. Requires the optional `sql` dependency group.
"""

from __future__ import annotations

import random
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import Engine
from sqlalchemy.orm import Session

from .models import (
    AppointmentRow,
    AuditLogEntryRow,
    CarePlanRow,
    DiagnosisRow,
    DisruptionEventRow,
    IntakeSessionRow,
    NotificationRow,
    PatientRow,
    PaymentRow,
    ResourceRow,
    ScanEventRow,
    ServiceOrderRow,
    ServiceTypeRow,
    SlotRow,
    TaskRow,
)

_SEED = 20260718  # fixed - the whole point is a reproducible demo dataset
_MIN_ROWS, _MAX_ROWS = 10, 50

_SPECIALTIES = ["cardiology", "neurology", "orthopedics", "pediatrics", "dermatology", "ent"]
_SERVICE_CODES = ["BLOOD_TEST", "X_RAY", "ULTRASOUND", "MRI", "ECG", "URINE_TEST"]
_EXECUTION_STATUSES = ["LOCKED", "PENDING", "IN_PROGRESS", "DONE", "CANCELLED"]
_PAYMENT_STATUSES = ["UNPAID", "PAID"]
_APPOINTMENT_STATUSES = ["PROPOSED", "BOOKED", "CHECKED_IN", "IN_CONSULT", "DONE", "NO_SHOW"]
_CARE_PLAN_STATUSES = ["DRAFT", "ACTIVE", "COMPLETED"]
_PRIORITY_LEVELS = ["ROUTINE", "URGENT", "EMERGENCY"]
_DISRUPTION_TYPES = ["EQUIPMENT_FAILURE", "OVERLOAD", "SCHEDULE_CHANGE", "EMERGENCY"]
_DISRUPTION_STATUSES = ["DETECTED", "ASSESSED", "AUTO_RESOLVED", "PENDING_APPROVAL", "APPROVED"]
_NOTIFICATION_CHANNELS = ["IN_APP", "SCREEN", "SMS"]

_ALL_ROW_CLASSES = (
    PatientRow, ResourceRow, ServiceTypeRow, DisruptionEventRow, IntakeSessionRow,
    AppointmentRow, NotificationRow, DiagnosisRow, CarePlanRow, ServiceOrderRow, TaskRow,
    SlotRow, ScanEventRow, PaymentRow, AuditLogEntryRow,
)


def _table_counts(session: Session) -> dict[str, int]:
    return {row_cls.__tablename__: session.query(row_cls).count() for row_cls in _ALL_ROW_CLASSES}


def _now() -> datetime:
    return datetime.now(UTC)


def _row_count(rng: random.Random) -> int:
    return rng.randint(_MIN_ROWS, _MAX_ROWS)


def seed_nxcare(
    engine: Engine,
    rng: random.Random | None = None,
    *,
    patient_count: int | None = None,
    room_count: int = 12,
) -> dict[str, int]:
    """Insert synthetic rows per table into `engine`'s database; return counts by table.

    `patient_count` defaults to a random 20-50 (a demo needs a visible patient population).
    `room_count` clinic ROOM resources are guaranteed on top of the random DOCTOR/TECHNICIAN/
    EQUIPMENT mix, so there are always "many rooms" to allocate slots against.
    """
    rng = rng or random.Random(_SEED)
    counts: dict[str, int] = {}

    with Session(engine) as session:
        # Idempotent (data-model.md): a database already carrying seeded patients is left alone
        # rather than growing without bound on every re-run.
        if session.query(PatientRow).count() > 0:
            return _table_counts(session)

        n_patients = patient_count if patient_count is not None else rng.randint(20, 50)
        patients = [
            PatientRow(
                id=uuid.uuid4(),
                full_name=f"Synthetic Patient {i:03d}",
                phone=f"0900{i:06d}",
                patient_code=f"NXC-{i:05d}",
                priority_level=rng.choice(_PRIORITY_LEVELS),
                created_at=_now() - timedelta(days=rng.randint(0, 30)),
            )
            for i in range(n_patients)
        ]
        session.add_all(patients)

        rooms = [
            ResourceRow(
                id=uuid.uuid4(),
                type="ROOM",
                department_id=uuid.uuid4(),
                is_available=rng.random() > 0.1,
                capacity_per_hour=rng.randint(1, 10),
            )
            for _ in range(room_count)
        ]
        other_resources = [
            ResourceRow(
                id=uuid.uuid4(),
                type=rng.choice(["DOCTOR", "TECHNICIAN", "EQUIPMENT"]),
                department_id=uuid.uuid4(),
                is_available=rng.random() > 0.1,
                capacity_per_hour=rng.randint(1, 10),
            )
            for _ in range(_row_count(rng))
        ]
        resources = rooms + other_resources
        session.add_all(resources)

        service_types = [
            ServiceTypeRow(
                id=uuid.uuid4(),
                code=f"{rng.choice(_SERVICE_CODES)}_{i:03d}",
                display_label=f"Synthetic service {i:03d}",
                requires_fasting=rng.random() > 0.7,
                turnaround_minutes=rng.randint(10, 120),
                default_duration_min=rng.randint(5, 60),
            )
            for i in range(_row_count(rng))
        ]
        session.add_all(service_types)

        disruption_events = [
            DisruptionEventRow(
                id=uuid.uuid4(),
                event_type=rng.choice(_DISRUPTION_TYPES),
                status=rng.choice(_DISRUPTION_STATUSES),
                blast_radius=rng.randint(0, 50),
                decided_by=uuid.uuid4() if rng.random() > 0.5 else None,
            )
            for _ in range(_row_count(rng))
        ]
        session.add_all(disruption_events)
        session.flush()  # tables above have no FK dependency; below need their generated ids

        intake_sessions = [
            IntakeSessionRow(
                id=uuid.uuid4(),
                patient_id=rng.choice(patients).id,
                transcript="",
                structured_triage={
                    "specialty": rng.choice(_SPECIALTIES), "priority_level": "ROUTINE"
                },
                emergency_suspected=rng.random() > 0.9,
                created_at=_now(),
            )
            for _ in range(_row_count(rng))
        ]
        session.add_all(intake_sessions)

        appointments = [
            AppointmentRow(
                id=uuid.uuid4(),
                patient_id=rng.choice(patients).id,
                specialty=rng.choice(_SPECIALTIES),
                status=rng.choice(_APPOINTMENT_STATUSES),
                payment_status=rng.choice(_PAYMENT_STATUSES),
                slot_start=_now() + timedelta(hours=rng.randint(1, 72)),
                created_at=_now(),
            )
            for _ in range(_row_count(rng))
        ]
        session.add_all(appointments)

        notifications = [
            NotificationRow(
                id=uuid.uuid4(),
                patient_id=rng.choice(patients).id,
                channel=rng.choice(_NOTIFICATION_CHANNELS),
                body=f"Synthetic notification {i:03d}",
                reason=None,
                created_at=_now(),
            )
            for i in range(_row_count(rng))
        ]
        session.add_all(notifications)
        session.flush()

        diagnoses = [
            DiagnosisRow(
                id=uuid.uuid4(),
                appointment_id=rng.choice(appointments).id,
                conditions=[f"synthetic-condition-{rng.randint(1, 20)}"],
                diagnosed_by=uuid.uuid4(),
                created_at=_now(),
            )
            for _ in range(_row_count(rng))
        ]
        session.add_all(diagnoses)
        session.flush()

        care_plans = [
            CarePlanRow(
                id=uuid.uuid4(),
                patient_id=rng.choice(patients).id,
                diagnosis_id=rng.choice(diagnoses).id,
                status=rng.choice(_CARE_PLAN_STATUSES),
                assigned_staff=[str(rng.choice(resources).id)],
                created_at=_now(),
            )
            for _ in range(_row_count(rng))
        ]
        session.add_all(care_plans)

        service_orders = [
            ServiceOrderRow(
                id=uuid.uuid4(),
                diagnosis_id=rng.choice(diagnoses).id,
                service_type_id=rng.choice(service_types).id,
                ordered_by=uuid.uuid4(),
                signed_at=_now(),
            )
            for _ in range(_row_count(rng))
        ]
        session.add_all(service_orders)
        session.flush()

        tasks = [
            TaskRow(
                id=uuid.uuid4(),
                care_plan_id=rng.choice(care_plans).id,
                service_order_id=rng.choice(service_orders).id,
                owner_id=rng.choice(resources).id,
                execution_status=rng.choice(_EXECUTION_STATUSES),
                payment_status=rng.choice(_PAYMENT_STATUSES),
                estimated_duration_min=rng.randint(5, 60),
                sequence_index=rng.randint(0, 10),
                depends_on=[],
                created_at=_now(),
            )
            for _ in range(_row_count(rng))
        ]
        session.add_all(tasks)
        session.flush()

        slots = [
            SlotRow(
                id=uuid.uuid4(),
                task_id=rng.choice(tasks).id,
                owner_id=rng.choice(resources).id,
                start=_now() + timedelta(hours=rng.randint(1, 48)),
                end=_now() + timedelta(hours=rng.randint(49, 96)),
            )
            for _ in range(_row_count(rng))
        ]
        session.add_all(slots)

        scan_events = [
            ScanEventRow(
                id=uuid.uuid4(),
                patient_id=rng.choice(patients).id,
                task_id=rng.choice(tasks).id,
                scanned_by=rng.choice(resources).id,
                scanned_at=_now(),
            )
            for _ in range(_row_count(rng))
        ]
        session.add_all(scan_events)

        payments = []
        for _ in range(_row_count(rng)):
            if rng.random() > 0.5:
                subject_type, subject_id = "TASK", rng.choice(tasks).id
            else:
                subject_type, subject_id = "APPOINTMENT", rng.choice(appointments).id
            payments.append(
                PaymentRow(
                    id=uuid.uuid4(),
                    subject_type=subject_type,
                    subject_id=subject_id,
                    amount=Decimal(rng.randint(50_000, 2_000_000)),
                    status=rng.choice(_PAYMENT_STATUSES),
                    confirmed_by=uuid.uuid4() if rng.random() > 0.5 else None,
                    confirmed_at=_now() if rng.random() > 0.5 else None,
                )
            )
        session.add_all(payments)

        audit_log_entries = [
            AuditLogEntryRow(
                id=uuid.uuid4(),
                actor=rng.choice(["Coordinator Agent", "Disruption Agent", "Journey Agent"]),
                action=rng.choice(["resequence_patient", "allocate_slot", "notify"]),
                target_id=rng.choice(tasks).id if rng.random() > 0.3 else None,
                reasoning=f"synthetic reasoning {i:03d}",
                created_at=_now(),
            )
            for i in range(_row_count(rng))
        ]
        session.add_all(audit_log_entries)

        session.commit()
        counts = _table_counts(session)

    return counts
