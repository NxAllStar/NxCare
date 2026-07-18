"""FR-03 diagnosis / service-order capture (TASK-008).

AC-03.1: doctor enters a diagnosis and 3 valid orders -> Diagnosis + 3 ServiceOrders recorded,
FR-04 triggered (proven by feeding the capture straight into generate_care_plan).
AC-03.2 (negative): a non-doctor actor (agent or other role) tries to create a ServiceOrder ->
refused and audited.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from vaic.agents.careplan import (
    build_activate_care_plan_tool,
    build_create_care_plan_tool,
    build_create_diagnosis_tool,
    build_create_service_order_tool,
    build_create_task_tool,
    capture_diagnosis_and_orders,
)
from vaic.agents.careplan.care_plan import generate_care_plan
from vaic.agents.careplan.slots import SlotCandidate, build_allocate_slot_tool
from vaic.agents.core import ActionExecutor
from vaic.models import Diagnosis, Resource, ResourceType, ServiceOrder, ServiceType
from vaic.state import InMemoryRepository
from vaic.tools import Action, AuditLog, ConstraintChecker, ToolRegistry


def _build():
    repo = InMemoryRepository()
    registry = ToolRegistry()
    registry.register(build_create_diagnosis_tool())
    registry.register(build_create_service_order_tool())
    registry.register(build_create_care_plan_tool())
    registry.register(build_create_task_tool())
    registry.register(build_allocate_slot_tool())
    registry.register(build_activate_care_plan_tool())
    audit = AuditLog(repo)
    executor = ActionExecutor(repo, registry, ConstraintChecker(repo), audit)
    return repo, executor, audit


def _service_type(repo, **kw) -> ServiceType:
    base = {"code": "BLOOD_TEST", "display_label": "Blood test"}
    base.update(kw)
    return repo.save(ServiceType(**base))


def test_ac_03_1_diagnosis_and_three_orders_recorded_and_triggers_care_plan():
    repo, executor, audit = _build()
    blood = _service_type(repo, code="BLOOD_TEST")
    ultrasound = _service_type(repo, code="ULTRASOUND")
    xray = _service_type(repo, code="XRAY")
    appointment_id = uuid4()
    doctor_id = uuid4()

    result = capture_diagnosis_and_orders(
        executor,
        actor="role_doctor",
        appointment_id=appointment_id,
        conditions=["synthetic condition A"],
        diagnosed_by=doctor_id,
        actor_role="role_doctor",
        service_type_ids=[blood.id, ultrasound.id, xray.id],
    )

    assert result.ok
    assert len(result.order_results) == 3
    assert repo.get(Diagnosis, result.diagnosis_id) is not None
    orders = repo.list(ServiceOrder, diagnosis_id=result.diagnosis_id)
    assert len(orders) == 3
    assert {o.service_type_id for o in orders} == {blood.id, ultrasound.id, xray.id}

    # AC-03.1's "triggers FR-04": the capture output feeds straight into care-plan generation.
    orders_with_types = [
        (o, repo.get(ServiceType, o.service_type_id))
        for o in sorted(orders, key=lambda o: o.signed_at)
    ]
    owner = repo.save(Resource(type=ResourceType.ROOM, department_id=uuid4(), capacity_per_hour=5))
    diagnosis = repo.get(Diagnosis, result.diagnosis_id)

    plan_result = generate_care_plan(
        repo,
        executor,
        actor="careplan-agent",
        patient_id=uuid4(),
        diagnosis=diagnosis,
        orders_with_types=orders_with_types,
        estimate_duration=lambda st, owner_id: 10,
        owner_resolver=lambda order, st: owner.id,
        candidates_for=lambda task, seq: [SlotCandidate(resource_id=owner.id,
                                                          start=datetime.now(UTC))],
    )
    assert len(plan_result.tasks) == 3


def test_ac_03_2_non_doctor_actor_refused_and_audited():
    repo, executor, audit = _build()
    st = _service_type(repo)
    diagnosis = repo.save(Diagnosis(appointment_id=uuid4(), diagnosed_by=uuid4()))
    before = len(audit.entries())

    result = executor.execute(
        Action(
            tool="create_service_order",
            actor="disruption-agent",
            params={
                "diagnosis_id": diagnosis.id,
                "service_type_id": st.id,
                "ordered_by": uuid4(),
                "actor_role": "role_coordinator",  # not role_doctor
            },
        )
    )

    assert result.allowed is False
    assert "doctor" in result.reason
    assert repo.list(ServiceOrder, diagnosis_id=diagnosis.id) == []
    assert len(audit.entries()) == before + 1
    assert audit.entries()[-1].action == "BLOCKED:create_service_order"


def test_ac_03_2_non_doctor_cannot_create_diagnosis_either():
    repo, executor, audit = _build()
    before = len(audit.entries())

    result = executor.execute(
        Action(
            tool="create_diagnosis",
            actor="agent:careplan",
            params={
                "appointment_id": uuid4(),
                "conditions": ["x"],
                "diagnosed_by": uuid4(),
                "actor_role": "role_technician",
            },
        )
    )

    assert result.allowed is True  # no checker rule for create_diagnosis...
    assert result.ok is False  # ...but the handler itself refuses (BR-05) and it is audited
    assert "doctor" in result.reason
    assert repo.list(Diagnosis) == []
    assert len(audit.entries()) == before + 1
    assert audit.entries()[-1].action == "FAILED:create_diagnosis"


def test_service_order_requires_valid_service_type():
    repo, executor, _ = _build()
    diagnosis = repo.save(Diagnosis(appointment_id=uuid4(), diagnosed_by=uuid4()))
    result = executor.execute(
        Action(
            tool="create_service_order",
            actor="role_doctor",
            params={
                "diagnosis_id": diagnosis.id,
                "service_type_id": uuid4(),  # does not exist
                "ordered_by": uuid4(),
                "actor_role": "role_doctor",
            },
        )
    )
    assert result.allowed is True
    assert result.ok is False
    assert "ServiceType" in result.reason
