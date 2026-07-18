"""State-machine invariants (TASK-003), per docs/specs/08-data-model.md."""

from __future__ import annotations

import pytest

from vaic.models import (
    APPOINTMENT_TRANSITIONS,
    CAREPLAN_TRANSITIONS,
    DISRUPTION_TRANSITIONS,
    TASK_TRANSITIONS,
    AppointmentStatus,
    CarePlanStatus,
    DisruptionStatus,
    ExecutionStatus,
    InvalidTransition,
    assert_transition,
    can_transition,
)


def test_task_payment_unlocks_to_pending():
    assert can_transition(TASK_TRANSITIONS, ExecutionStatus.LOCKED, ExecutionStatus.PENDING)


def test_task_cannot_skip_in_progress():
    assert not can_transition(TASK_TRANSITIONS, ExecutionStatus.PENDING, ExecutionStatus.DONE)
    with pytest.raises(InvalidTransition):
        assert_transition(TASK_TRANSITIONS, ExecutionStatus.PENDING, ExecutionStatus.DONE)


def test_task_scan_then_complete():
    assert_transition(TASK_TRANSITIONS, ExecutionStatus.PENDING, ExecutionStatus.IN_PROGRESS)
    assert_transition(TASK_TRANSITIONS, ExecutionStatus.IN_PROGRESS, ExecutionStatus.DONE)


def test_appointment_must_check_in_before_consult():
    assert can_transition(APPOINTMENT_TRANSITIONS, AppointmentStatus.PROPOSED,
                          AppointmentStatus.BOOKED)
    assert not can_transition(APPOINTMENT_TRANSITIONS, AppointmentStatus.BOOKED,
                              AppointmentStatus.IN_CONSULT)


def test_careplan_draft_cannot_jump_to_completed():
    assert can_transition(CAREPLAN_TRANSITIONS, CarePlanStatus.DRAFT, CarePlanStatus.ACTIVE)
    assert not can_transition(CAREPLAN_TRANSITIONS, CarePlanStatus.DRAFT, CarePlanStatus.COMPLETED)


def test_disruption_large_impact_needs_approval_path():
    assert can_transition(DISRUPTION_TRANSITIONS, DisruptionStatus.ASSESSED,
                          DisruptionStatus.PENDING_APPROVAL)
    assert not can_transition(DISRUPTION_TRANSITIONS, DisruptionStatus.DETECTED,
                              DisruptionStatus.APPROVED)
