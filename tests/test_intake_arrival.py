"""Tests for the arrival-time grounding + agent reasoning (extends FR-02).

Covers the two halves: `summarize_reservations` (the deterministic DB search that buckets
reservations against hospital working hours) and `recommend_arrival_times` (the PocketFlow
reason -> validate flow). No test drives a live provider - the reasoner is a fake/deterministic
client (a real network call in a test is a defect, testing.md).
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import uuid4

from vaic.agents.intake.arrival import (
    CLOSE_HOUR,
    OPEN_HOUR,
    DayLoad,
    HourLoad,
    confirm_arrival_slot,
    summarize_reservations,
)
from vaic.agents.intake.arrival_chat import (
    ArrivalChatError,
    ArrivalRecommendation,
    RuleBasedArrivalChatLLM,
    recommend_arrival_times,
)
from vaic.models import Appointment, AppointmentStatus
from vaic.state import InMemoryRepository

ANCHOR = datetime(2026, 7, 20, 0, 0, tzinfo=UTC)


def _reserve(repo, start, status=AppointmentStatus.PROPOSED):
    repo.save(
        Appointment(
            patient_id=uuid4(), specialty="NOI_TONG_QUAT", slot_start=start, status=status
        )
    )


def _hour(day: DayLoad, hour: int) -> int:
    return next(h.reservations for h in day.hours if h.hour == hour)


# ---- summarize_reservations (the grounding search) ----------------------------------------------


def test_summary_buckets_reservations_by_hour():
    repo = InMemoryRepository()
    _reserve(repo, ANCHOR + timedelta(hours=8))
    _reserve(repo, ANCHOR + timedelta(hours=8))
    _reserve(repo, ANCHOR + timedelta(hours=9))
    _reserve(repo, ANCHOR + timedelta(days=1, hours=7))

    summary = summarize_reservations(repo, ANCHOR, 2)

    assert len(summary) == 2
    assert _hour(summary[0], 8) == 2
    assert _hour(summary[0], 9) == 1
    assert _hour(summary[0], 10) == 0
    assert _hour(summary[1], 7) == 1


def test_summary_covers_only_working_hours():
    repo = InMemoryRepository()

    summary = summarize_reservations(repo, ANCHOR, 1)

    hours = [h.hour for h in summary[0].hours]
    assert hours == list(range(OPEN_HOUR, CLOSE_HOUR))  # 06:00 .. 19:00


def test_summary_ignores_cancelled_and_unscheduled():
    repo = InMemoryRepository()
    _reserve(repo, ANCHOR + timedelta(hours=8), status=AppointmentStatus.CANCELLED)
    _reserve(repo, ANCHOR + timedelta(hours=8), status=AppointmentStatus.NO_SHOW)
    repo.save(Appointment(patient_id=uuid4(), specialty="X", slot_start=None))  # no time set

    summary = summarize_reservations(repo, ANCHOR, 1)

    assert _hour(summary[0], 8) == 0


# ---- recommend_arrival_times (the reasoning flow) -----------------------------------------------


def _summary_fixture() -> list[DayLoad]:
    return [
        DayLoad(
            day=date(2026, 7, 20),
            weekday="Monday",
            hours=(HourLoad(6, 0), HourLoad(7, 3), HourLoad(8, 5), HourLoad(9, 1)),
        )
    ]


class _FakeArrivalLLM:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def reply(self, message: str, context: dict[str, Any]) -> dict[str, Any]:
        return self._payload


class _FailingArrivalLLM:
    def reply(self, message: str, context: dict[str, Any]) -> dict[str, Any]:
        raise ArrivalChatError("provider down")


def test_rule_based_reasoner_picks_least_crowded_first():
    result = recommend_arrival_times(
        "when should I come?", _summary_fixture(), RuleBasedArrivalChatLLM()
    )

    assert isinstance(result, ArrivalRecommendation)
    counts = [b.reservation_count for b in result.recommendations]
    assert counts == sorted(counts)
    assert result.recommendations[0].reservation_count == 0
    assert result.recommendations[0].start_hour == 6


def test_valid_llm_output_is_used():
    payload = {
        "message": "Come between 06:00 and 07:00 on Monday.",
        "recommendations": [
            {"date": "2026-07-20", "start_hour": 6, "end_hour": 7, "reservation_count": 0,
             "reason": "empty"}
        ],
    }
    result = recommend_arrival_times("hi", _summary_fixture(), _FakeArrivalLLM(payload))

    assert result.message == "Come between 06:00 and 07:00 on Monday."
    assert result.recommendations[0].start_hour == 6


def test_failing_provider_degrades_to_deterministic():
    result = recommend_arrival_times("hi", _summary_fixture(), _FailingArrivalLLM())

    assert isinstance(result, ArrivalRecommendation)
    assert result.recommendations[0].reservation_count == 0  # deterministic fallback still answers


def test_offschema_output_degrades_to_deterministic():
    result = recommend_arrival_times("hi", _summary_fixture(), _FakeArrivalLLM({"unexpected": 1}))

    assert isinstance(result, ArrivalRecommendation)
    assert result.recommendations[0].start_hour == 6


def test_llm_block_outside_working_hours_is_rejected():
    # start_hour 25 violates the schema bound -> validation fails -> deterministic fallback.
    payload = {"message": "x", "recommendations": [
        {"date": "2026-07-20", "start_hour": 25, "end_hour": 26, "reservation_count": 0}
    ]}
    result = recommend_arrival_times("hi", _summary_fixture(), _FakeArrivalLLM(payload))

    assert result.recommendations[0].start_hour == 6  # fell back, did not trust the bad block


# ---- confirm_arrival_slot (log which time) ------------------------------------------------------


def test_confirm_persists_proposed_appointment_without_owner():
    repo = InMemoryRepository()
    patient = uuid4()
    start = ANCHOR + timedelta(hours=6)

    appointment = confirm_arrival_slot(repo, patient, "NOI_TONG_QUAT", start)

    assert appointment.status == AppointmentStatus.PROPOSED
    assert appointment.owner_id is None  # time-block arrival: doctor assigned at the desk
    assert appointment.slot_start == start
    stored = repo.get(Appointment, appointment.id)
    assert stored is not None and stored.patient_id == patient
