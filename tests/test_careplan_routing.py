"""FR-23 v2.3 routing seam: name resolution, config-driven duration, queue-aware station ranking.

Covers `agents/careplan/routing.py` in isolation from the HTTP layer and from `generate_care_plan`
(already covered by `test_careplan_generation.py`) - these are the three functions that turn a
doctor's raw test-name list plus current station load into inputs `generate_care_plan` already
knows how to consume.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from vaic.agents.careplan.routing import (
    default_duration_estimator,
    least_loaded_owner_resolver,
    queue_aware_candidates_for,
    resolve_service_types,
)
from vaic.models import (
    ExecutionStatus,
    PaymentStatus,
    Resource,
    ResourceType,
    ServiceType,
    Task,
)
from vaic.state import InMemoryRepository


def _service_type(repo, code: str, **kw) -> ServiceType:
    return repo.save(ServiceType(code=code, display_label=f"Label {code}", **kw))


def test_resolve_service_types_matches_by_code_or_label_case_insensitively():
    repo = InMemoryRepository()
    blood = repo.save(ServiceType(code="BLOOD_TEST", display_label="Xet nghiem mau",
                                   default_duration_min=10))
    xray = repo.save(ServiceType(code="XRAY", display_label="Chup X-quang",
                                  default_duration_min=15))

    resolution = resolve_service_types(repo, ["  blood_test", "CHUP X-QUANG"])

    assert resolution.ok
    assert resolution.unmatched == []
    assert [st.id for st in resolution.resolved] == [blood.id, xray.id]


def test_resolve_service_types_reports_unmatched_names_never_drops_silently():
    repo = InMemoryRepository()
    repo.save(ServiceType(code="BLOOD_TEST", display_label="Xet nghiem mau"))

    resolution = resolve_service_types(repo, ["blood_test", "Nonexistent Test"])

    assert resolution.ok is False
    assert resolution.unmatched == ["Nonexistent Test"]
    assert len(resolution.resolved) == 1  # the one that DID match is still reported


def test_default_duration_estimator_reads_the_service_type_config_value():
    repo = InMemoryRepository()
    st = _service_type(repo, "MRI", default_duration_min=45)

    assert default_duration_estimator(st, uuid4()) == 45


def test_least_loaded_owner_resolver_picks_the_station_with_the_least_queued_minutes():
    repo = InMemoryRepository()
    busy = repo.save(Resource(type=ResourceType.TECHNICIAN, department_id=uuid4(),
                               is_available=True, capacity_per_hour=10))
    light = repo.save(Resource(type=ResourceType.TECHNICIAN, department_id=uuid4(),
                                is_available=True, capacity_per_hour=10))
    # A paid, in-progress task on `busy` counts toward its load (BR-10: paid, unfinished tasks only)
    repo.save(Task(care_plan_id=uuid4(), service_order_id=uuid4(), owner_id=busy.id,
                    payment_status=PaymentStatus.PAID, execution_status=ExecutionStatus.PENDING,
                    estimated_duration_min=40))

    resolver = least_loaded_owner_resolver(repo, [busy.id, light.id])

    assert resolver(order=None, service_type=None) == light.id


def test_least_loaded_owner_resolver_skips_unpaid_locked_tasks_per_br10():
    repo = InMemoryRepository()
    a = repo.save(Resource(type=ResourceType.TECHNICIAN, department_id=uuid4(),
                            is_available=True, capacity_per_hour=10))
    b = repo.save(Resource(type=ResourceType.TECHNICIAN, department_id=uuid4(),
                            is_available=True, capacity_per_hour=10))
    # Unpaid (LOCKED) task on `a` - must NOT count against it (BR-10).
    repo.save(Task(care_plan_id=uuid4(), service_order_id=uuid4(), owner_id=a.id,
                    payment_status=PaymentStatus.UNPAID, execution_status=ExecutionStatus.LOCKED,
                    estimated_duration_min=999))

    resolver = least_loaded_owner_resolver(repo, [a.id, b.id])

    # Both are equally (zero) loaded once the unpaid task is excluded - `min` returns the first.
    assert resolver(order=None, service_type=None) == a.id


def test_queue_aware_candidates_for_offers_least_busy_station_first():
    repo = InMemoryRepository()
    busy = repo.save(Resource(type=ResourceType.TECHNICIAN, department_id=uuid4(),
                               is_available=True, capacity_per_hour=10))
    light = repo.save(Resource(type=ResourceType.TECHNICIAN, department_id=uuid4(),
                                is_available=True, capacity_per_hour=10))
    repo.save(Task(care_plan_id=uuid4(), service_order_id=uuid4(), owner_id=busy.id,
                    payment_status=PaymentStatus.PAID, execution_status=ExecutionStatus.IN_PROGRESS,
                    estimated_duration_min=30))

    candidates_for = queue_aware_candidates_for(
        repo, [busy.id, light.id], hours=[9, 10], reference_date=datetime(2026, 1, 1, tzinfo=UTC)
    )
    candidates = candidates_for(task=None, seq=None)

    # `light` (0 queued minutes) is offered before `busy` (30 queued minutes), both hours each.
    assert [c.resource_id for c in candidates] == [light.id, light.id, busy.id, busy.id]


def test_queue_aware_candidates_for_excludes_a_station_at_or_over_capacity():
    repo = InMemoryRepository()
    full = repo.save(Resource(type=ResourceType.TECHNICIAN, department_id=uuid4(),
                               is_available=True, capacity_per_hour=1))
    open_station = repo.save(Resource(type=ResourceType.TECHNICIAN, department_id=uuid4(),
                                       is_available=True, capacity_per_hour=10))
    repo.save(Task(care_plan_id=uuid4(), service_order_id=uuid4(), owner_id=full.id,
                    payment_status=PaymentStatus.PAID, execution_status=ExecutionStatus.PENDING,
                    estimated_duration_min=10))  # 1 queued task == capacity_per_hour (BR-04)

    candidates_for = queue_aware_candidates_for(
        repo, [full.id, open_station.id], hours=[9], reference_date=datetime(2026, 1, 1, tzinfo=UTC)
    )
    candidates = candidates_for(task=None, seq=None)

    assert [c.resource_id for c in candidates] == [open_station.id]


def test_queue_aware_candidates_for_excludes_an_unavailable_station():
    repo = InMemoryRepository()
    closed = repo.save(Resource(type=ResourceType.TECHNICIAN, department_id=uuid4(),
                                 is_available=False, capacity_per_hour=10))

    candidates_for = queue_aware_candidates_for(
        repo, [closed.id], hours=[9], reference_date=datetime(2026, 1, 1, tzinfo=UTC)
    )

    assert candidates_for(task=None, seq=None) == []
