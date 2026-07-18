"""Tests for the SimPy hospital simulator (TASK-006).

Covers: seed reproducibility (BR-15, NFR-REL-05), the load-aware policy beating the FIFO baseline
on average wait for a congested cohort (G-01), and a tiny hand-checkable scenario for the metrics
computation itself.
"""

from __future__ import annotations

from uuid import UUID

from vaic.models.enums import PriorityLevel
from vaic.simulator.areas import AreaConfig
from vaic.simulator.cohort import generate_cohort
from vaic.simulator.disruptions import equipment_failure, room_failure
from vaic.simulator.harness import run_ab, run_policy
from vaic.simulator.policies import FIFOPolicy, LoadAwarePolicy
from vaic.simulator.world import run_world

ONE_ROOM_AREA = (
    AreaConfig(
        name="test_area", num_rooms=1, weight=1.0, min_service_min=10.0, max_service_min=10.0
    ),
)


def _patient(patient_id: int, arrival_min: float, area: str, duration: float):
    from vaic.simulator.cohort import PatientArrival

    return PatientArrival(
        patient_id=UUID(int=patient_id),
        arrival_min=arrival_min,
        area=area,
        priority=PriorityLevel.ROUTINE,
        service_duration_min=duration,
    )


class TestCohortGeneration:
    def test_same_seed_produces_identical_cohort(self):
        cohort_a = generate_cohort(seed=42, num_patients=80)
        cohort_b = generate_cohort(seed=42, num_patients=80)
        assert cohort_a == cohort_b

    def test_different_seed_produces_different_cohort(self):
        cohort_a = generate_cohort(seed=42, num_patients=80)
        cohort_b = generate_cohort(seed=43, num_patients=80)
        assert cohort_a != cohort_b

    def test_scale_matches_as_04(self):
        """AS-04: demo scale is ~50-100 patients per run."""
        cohort = generate_cohort(seed=1, num_patients=80)
        assert len(cohort) == 80
        assert 50 <= len(cohort) <= 100

    def test_arrivals_are_sorted_and_within_window(self):
        cohort = generate_cohort(seed=7, num_patients=60, arrival_window_min=240.0)
        arrival_times = [p.arrival_min for p in cohort]
        assert arrival_times == sorted(arrival_times)
        assert all(0.0 <= t <= 240.0 for t in arrival_times)


class TestDeterministicWorldRun:
    def test_same_seed_same_policy_reproduces_metrics_exactly(self):
        metrics_a = run_policy(seed=42, num_patients=80, policy=FIFOPolicy())
        metrics_b = run_policy(seed=42, num_patients=80, policy=FIFOPolicy())
        assert metrics_a == metrics_b

    def test_run_ab_same_seed_reproduces_both_policies_exactly(self):
        results_a = run_ab(seed=42, num_patients=80)
        results_b = run_ab(seed=42, num_patients=80)
        assert results_a == results_b


class TestTinyHandCheckableScenario:
    """One room, two patients, fixed durations - every number below is hand-derived.

    Patient 1 arrives at t=0, room free, serves 0->10 (wait 0).
    Patient 2 arrives at t=5, room busy until t=10, so waits 5, serves 10->20.
    """

    def test_metrics_match_hand_computed_values(self):
        patients = [
            _patient(1, arrival_min=0.0, area="test_area", duration=10.0),
            _patient(2, arrival_min=5.0, area="test_area", duration=10.0),
        ]
        result = run_world(patients, FIFOPolicy(), area_configs=ONE_ROOM_AREA)

        from vaic.simulator.metrics import compute_metrics

        metrics = compute_metrics(
            result.recorder,
            result.total_duration_min,
            room_counts={"test_area": 1},
            equipment_capacity={},
        )

        assert result.total_duration_min == 20.0
        assert metrics.patient_count == 2
        assert metrics.average_wait_min == 2.5
        assert metrics.peak_load_per_area["test_area"] == 1
        assert metrics.room_utilisation_per_area["test_area"] == 1.0
        assert metrics.eta_mae_min == 2.5


class TestLoadAwareBeatsFifo:
    def test_load_aware_reduces_average_wait_on_a_congested_cohort(self):
        congested_area = (
            AreaConfig(
                name="busy",
                num_rooms=2,
                weight=1.0,
                min_service_min=5.0,
                max_service_min=30.0,
            ),
        )
        fifo_metrics = run_policy(
            seed=100, num_patients=40, policy=FIFOPolicy(), area_configs=congested_area
        )
        load_aware_metrics = run_policy(
            seed=100, num_patients=40, policy=LoadAwarePolicy(), area_configs=congested_area
        )

        assert load_aware_metrics.average_wait_min < fifo_metrics.average_wait_min

    def test_run_ab_reports_both_policies_on_the_same_cohort(self):
        results = run_ab(seed=100, num_patients=40)
        assert set(results) == {"fifo", "load_aware"}
        assert results["fifo"].patient_count == results["load_aware"].patient_count == 40


class TestDisruptions:
    def test_equipment_failure_blocks_service_during_the_window(self):
        area = (
            AreaConfig(
                name="imaging",
                num_rooms=1,
                weight=1.0,
                min_service_min=5.0,
                max_service_min=5.0,
                equipment_capacity=1,
            ),
        )
        patients = [_patient(1, arrival_min=0.0, area="imaging", duration=5.0)]
        disruption = equipment_failure(area="imaging", start_min=0.0, duration_min=20.0)

        result = run_world(patients, FIFOPolicy(), area_configs=area, disruptions=[disruption])

        record = result.recorder.records[0]
        # the machine is down 0..20, so the patient cannot start service before t=20
        assert record.start_min >= 20.0

    def test_room_failure_blocks_only_that_room(self):
        area = (
            AreaConfig(
                name="consult", num_rooms=2, weight=1.0, min_service_min=5.0, max_service_min=5.0
            ),
        )
        patients = [_patient(1, arrival_min=0.0, area="consult", duration=5.0)]
        disruption = room_failure(area="consult", room_index=0, start_min=0.0, duration_min=15.0)

        result = run_world(patients, FIFOPolicy(), area_configs=area, disruptions=[disruption])

        # FIFO's round-robin sends the first patient to room 0, which is down: it should
        # nonetheless be served (constrained to room 0 by the FIFO baseline) only after recovery.
        record = result.recorder.records[0]
        assert record.start_min >= 15.0


class TestRunEntryPoint:
    def test_main_prints_metrics_for_both_policies(self, capsys):
        from vaic.simulator.run import main

        main(["--seed", "1", "--patients", "50"])
        captured = capsys.readouterr()
        assert "fifo" in captured.out.lower()
        assert "load_aware" in captured.out.lower()
        assert "average wait" in captured.out.lower()
