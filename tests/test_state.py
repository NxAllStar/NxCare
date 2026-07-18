"""State repository + domain queries (TASK-003)."""

from __future__ import annotations

from uuid import uuid4

from vaic.models import ExecutionStatus, Patient, PaymentStatus, PriorityLevel, Task
from vaic.state import InMemoryRepository, owner_load_minutes, owner_queue


def test_save_get_round_trip_and_isolation():
    repo = InMemoryRepository()
    p = Patient(full_name="Nguyen Van A", patient_code="VAIC-1")
    repo.save(p)
    got = repo.get(Patient, p.id)
    assert got is not None and got.full_name == "Nguyen Van A"
    # mutating the returned copy must not change the stored value
    got.priority_level = PriorityLevel.EMERGENCY
    assert repo.get(Patient, p.id).priority_level is PriorityLevel.ROUTINE


def test_list_filter_and_delete():
    repo = InMemoryRepository()
    a = repo.save(Patient(full_name="A", patient_code="C1", priority_level=PriorityLevel.URGENT))
    repo.save(Patient(full_name="B", patient_code="C2"))
    urgent = repo.list(Patient, priority_level=PriorityLevel.URGENT)
    assert [x.id for x in urgent] == [a.id]
    assert repo.delete(Patient, a.id) is True
    assert repo.get(Patient, a.id) is None


def _task(owner, **kw) -> Task:
    base = dict(care_plan_id=uuid4(), service_order_id=uuid4(), owner_id=owner,
                estimated_duration_min=10)
    base.update(kw)
    return Task(**base)


def test_owner_queue_excludes_unpaid_and_sums_only_paid_load():
    repo = InMemoryRepository()
    owner = uuid4()
    # paid + pending -> in queue
    repo.save(_task(owner, payment_status=PaymentStatus.PAID,
                    execution_status=ExecutionStatus.PENDING, sequence_index=1,
                    estimated_duration_min=10))
    # paid + in_progress -> in queue
    repo.save(_task(owner, payment_status=PaymentStatus.PAID,
                    execution_status=ExecutionStatus.IN_PROGRESS, sequence_index=0,
                    estimated_duration_min=15))
    # unpaid (locked) -> excluded (BR-10)
    repo.save(_task(owner, payment_status=PaymentStatus.UNPAID,
                    execution_status=ExecutionStatus.LOCKED, sequence_index=2,
                    estimated_duration_min=99))
    # paid but done -> excluded
    repo.save(_task(owner, payment_status=PaymentStatus.PAID,
                    execution_status=ExecutionStatus.DONE, estimated_duration_min=99))

    q = owner_queue(repo, owner)
    assert [t.sequence_index for t in q] == [0, 1]  # ordered, only the two active paid tasks
    assert owner_load_minutes(repo, owner) == 25  # 15 + 10, unpaid/done contribute nothing


def test_load_is_zero_for_unknown_owner():
    assert owner_load_minutes(InMemoryRepository(), uuid4()) == 0
