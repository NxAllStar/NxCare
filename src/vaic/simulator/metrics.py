"""Metrics recorded during a world run, and the pure function that turns them into headline numbers.

Covers the four metrics named in docs/specs/01-overview.md "Success metrics": average wait time,
peak/congestion load per area, room and equipment utilisation, and ETA forecast error (MAE).

The ETA prediction used for MAE is a deterministic, grounded heuristic (queue-ahead count times the
area's average service time) - a stand-in for the real forecast-LLM tool (FR-07, owned by
forecast-dev). It lets this task's MAE metric exist and be tested now without depending on that
later integration, and it keeps the number traceable to observed config rather than fabricated.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean
from uuid import UUID


@dataclass(frozen=True)
class PatientRecord:
    """One patient's outcome for one visit: when they waited, were served, and were predicted."""

    patient_id: UUID
    area: str
    arrival_min: float
    wait_min: float
    start_min: float
    end_min: float
    predicted_wait_min: float


@dataclass
class MetricsRecorder:
    """Accumulates the raw events a world run needs to compute metrics from, per area."""

    area_names: list[str]
    records: list[PatientRecord] = field(default_factory=list)
    peak_waiting: dict[str, int] = field(default_factory=dict)
    room_busy_intervals: dict[str, list[tuple[float, float]]] = field(default_factory=dict)
    equipment_busy_intervals: dict[str, list[tuple[float, float]]] = field(default_factory=dict)
    _waiting_count: dict[str, int] = field(default_factory=dict, repr=False)

    def __post_init__(self) -> None:
        for name in self.area_names:
            self._waiting_count.setdefault(name, 0)
            self.peak_waiting.setdefault(name, 0)
            self.room_busy_intervals.setdefault(name, [])
            self.equipment_busy_intervals.setdefault(name, [])

    def patient_arrived(self, area: str) -> None:
        """A patient has arrived and is waiting for a room (and possibly equipment)."""
        self._waiting_count[area] += 1
        self.peak_waiting[area] = max(self.peak_waiting[area], self._waiting_count[area])

    def patient_started(self, area: str) -> None:
        """A waiting patient has been granted a room and started service."""
        self._waiting_count[area] -= 1

    def record_room_busy(self, area: str, start_min: float, end_min: float) -> None:
        self.room_busy_intervals[area].append((start_min, end_min))

    def record_equipment_busy(self, area: str, start_min: float, end_min: float) -> None:
        self.equipment_busy_intervals[area].append((start_min, end_min))

    def add_patient_record(self, record: PatientRecord) -> None:
        self.records.append(record)


@dataclass(frozen=True)
class Metrics:
    """The headline numbers for one policy's run over one seeded cohort."""

    patient_count: int
    average_wait_min: float
    peak_load_per_area: dict[str, int]
    room_utilisation_per_area: dict[str, float]
    equipment_utilisation_per_area: dict[str, float]
    eta_mae_min: float


def compute_metrics(
    recorder: MetricsRecorder,
    total_duration_min: float,
    room_counts: dict[str, int],
    equipment_capacity: dict[str, int],
) -> Metrics:
    """Turn a completed run's raw records into the four headline metrics.

    `room_counts` and `equipment_capacity` describe world capacity per area, so utilisation can be
    expressed as a fraction of the time that capacity was actually busy.
    """
    records = recorder.records
    average_wait = mean(record.wait_min for record in records) if records else 0.0
    eta_mae = (
        mean(abs(record.predicted_wait_min - record.wait_min) for record in records)
        if records
        else 0.0
    )

    room_utilisation: dict[str, float] = {}
    for area, count in room_counts.items():
        busy_minutes = sum(end - start for start, end in recorder.room_busy_intervals.get(area, []))
        capacity_minutes = count * total_duration_min
        room_utilisation[area] = busy_minutes / capacity_minutes if capacity_minutes > 0 else 0.0

    equipment_utilisation: dict[str, float] = {}
    for area, capacity in equipment_capacity.items():
        busy_minutes = sum(
            end - start for start, end in recorder.equipment_busy_intervals.get(area, [])
        )
        capacity_minutes = capacity * total_duration_min
        equipment_utilisation[area] = (
            busy_minutes / capacity_minutes if capacity_minutes > 0 else 0.0
        )

    return Metrics(
        patient_count=len(records),
        average_wait_min=average_wait,
        peak_load_per_area=dict(recorder.peak_waiting),
        room_utilisation_per_area=room_utilisation,
        equipment_utilisation_per_area=equipment_utilisation,
        eta_mae_min=eta_mae,
    )
