"""The SimPy "world": rooms and equipment as resources, patients as processes, disruptions injected.

DP-03 (spec 11): the simulator is the ground truth the agents are evaluated against. Determinism
(BR-15, NFR-REL-05) depends on: (1) the cohort being generated from a seeded RNG (cohort.py), and
(2) SimPy's own event ordering, which is deterministic given the same sequence of process creation
and the same event times - no wall-clock or unseeded randomness is used anywhere in this module.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import simpy

from .areas import DEFAULT_AREAS, AreaConfig
from .cohort import PatientArrival
from .disruptions import DisruptionSpec
from .metrics import MetricsRecorder, PatientRecord
from .policies import SchedulingPolicy


@dataclass(frozen=True)
class WorldResult:
    """A completed run: the raw metrics recorder plus the simulated duration it covered."""

    recorder: MetricsRecorder
    total_duration_min: float


def run_world(
    patients: Sequence[PatientArrival],
    policy: SchedulingPolicy,
    area_configs: Sequence[AreaConfig] = DEFAULT_AREAS,
    disruptions: Sequence[DisruptionSpec] = (),
) -> WorldResult:
    """Run `patients` through `policy` over `area_configs`, with `disruptions` injected.

    Returns the raw `MetricsRecorder` plus the simulated duration; see `metrics.compute_metrics`
    for turning that into the headline numbers.
    """
    env = simpy.Environment()
    areas_by_name = {area.name: area for area in area_configs}
    rooms: dict[str, list[simpy.Resource]] = {
        area.name: [simpy.Resource(env, capacity=1) for _ in range(area.num_rooms)]
        for area in area_configs
    }
    equipment: dict[str, simpy.Resource] = {
        area.name: simpy.Resource(env, capacity=area.equipment_capacity)
        for area in area_configs
        if area.equipment_capacity is not None
    }
    recorder = MetricsRecorder(area_names=[area.name for area in area_configs])

    # Disruptions are started before patients so that, when a disruption and a patient's arrival
    # land on the same simulated instant, the disruption claims the resource first - SimPy breaks
    # same-time ties by process-creation order, so this ordering is what makes "the machine is
    # down starting at t=0" actually block a patient arriving at t=0 (see TestDisruptions).
    for spec in disruptions:
        resource = (
            rooms[spec.area][spec.room_index]
            if spec.target == "room"
            else equipment[spec.area]
        )
        env.process(_disruption_process(env, resource, spec))

    for patient in patients:
        env.process(
            _patient_process(env, patient, areas_by_name, rooms, equipment, policy, recorder)
        )

    env.run()
    return WorldResult(recorder=recorder, total_duration_min=env.now)


def _patient_process(
    env: simpy.Environment,
    patient: PatientArrival,
    areas_by_name: dict[str, AreaConfig],
    rooms: dict[str, list[simpy.Resource]],
    equipment: dict[str, simpy.Resource],
    policy: SchedulingPolicy,
    recorder: MetricsRecorder,
):
    if patient.arrival_min > env.now:
        yield env.timeout(patient.arrival_min - env.now)

    area = patient.area
    area_rooms = rooms[area]
    area_equipment = equipment.get(area)

    recorder.patient_arrived(area)
    room_loads = [room.count + len(room.queue) for room in area_rooms]
    predicted_wait = _predict_wait(areas_by_name[area], room_loads)
    room_index = policy.select_room(area, room_loads)
    room = area_rooms[room_index]

    with room.request() as room_request:
        equipment_request = area_equipment.request() if area_equipment is not None else None
        try:
            if equipment_request is not None:
                yield room_request & equipment_request
            else:
                yield room_request
            start_min = env.now
            recorder.patient_started(area)
            yield env.timeout(patient.service_duration_min)
            end_min = env.now
        finally:
            if equipment_request is not None:
                area_equipment.release(equipment_request)

    recorder.record_room_busy(area, start_min, end_min)
    if area_equipment is not None:
        recorder.record_equipment_busy(area, start_min, end_min)
    recorder.add_patient_record(
        PatientRecord(
            patient_id=patient.patient_id,
            area=area,
            arrival_min=patient.arrival_min,
            wait_min=start_min - patient.arrival_min,
            start_min=start_min,
            end_min=end_min,
            predicted_wait_min=predicted_wait,
        )
    )


def _disruption_process(env: simpy.Environment, resource: simpy.Resource, spec: DisruptionSpec):
    if spec.start_min > env.now:
        yield env.timeout(spec.start_min - env.now)
    with resource.request() as request:
        yield request
        yield env.timeout(spec.duration_min)


def _predict_wait(area_config: AreaConfig, room_loads: Sequence[int]) -> float:
    """A deterministic, grounded ETA heuristic - see the module docstring in metrics.py."""
    average_service = (area_config.min_service_min + area_config.max_service_min) / 2
    total_ahead = sum(room_loads)
    return (total_ahead / max(len(room_loads), 1)) * average_service
