"""Tests for vaic.auth (TASK-013, FR-18): sessions, and server-side role/scope authorization.

Covers AC-18.1 (no session -> 401/Unauthorized), AC-18.2 (patient Own-scope), AC-18.3 (role lacking
permission -> 403/Forbidden), session create/validate/revoke, and that scope filtering runs in the
data layer (never by hiding UI). All state is in-memory; no wall-clock or network dependency.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from vaic.auth import (
    Account,
    AccountDirectory,
    AuthService,
    CrudOp,
    Forbidden,
    Role,
    Scope,
    Session,
    SessionService,
    Unauthorized,
    authorize,
    filter_by_scope,
    is_own,
    list_scoped,
    resolve_scope,
    seed_demo_accounts,
)
from vaic.models import (
    Appointment,
    AuditLogEntry,
    CarePlan,
    Diagnosis,
    Payment,
    PaymentSubjectType,
    ServiceOrder,
    Slot,
    Task,
)
from vaic.state import InMemoryRepository

_FIXED_NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _fixed_clock() -> datetime:
    return _FIXED_NOW


def _build_service() -> tuple[InMemoryRepository, AccountDirectory, AuthService]:
    repo = InMemoryRepository()
    accounts = AccountDirectory()
    sessions = SessionService(repo, clock=_fixed_clock)
    return repo, accounts, AuthService(accounts, sessions)


# ---- AC-18.1: no valid session -> Unauthorized (401) --------------------------------------------

def test_require_session_with_no_token_is_unauthorized():
    _, _, auth = _build_service()
    with pytest.raises(Unauthorized):
        auth.require_session("not-a-real-token")


def test_require_session_with_malformed_token_is_unauthorized():
    _, _, auth = _build_service()
    with pytest.raises(Unauthorized):
        auth.require_session("")


def test_require_session_after_revoke_is_unauthorized():
    _, accounts, auth = _build_service()
    account = accounts.register(Account(username="demo_patient", role=Role.PATIENT))
    session = auth.login("demo_patient")
    assert isinstance(session, Session)
    auth.logout(str(session.id))
    with pytest.raises(Unauthorized):
        auth.require_session(str(session.id))
    assert account.username == "demo_patient"  # unused-var guard: account really was registered


def test_login_unknown_username_is_unauthorized():
    _, _, auth = _build_service()
    with pytest.raises(Unauthorized):
        auth.login("nobody_registered")


# ---- session create/validate/revoke lifecycle ----------------------------------------------------

def test_login_creates_a_deterministic_session_and_require_session_resolves_the_account():
    _, accounts, auth = _build_service()
    accounts.register(Account(username="demo_doctor", role=Role.DOCTOR))
    session = auth.login("demo_doctor")
    assert session.created_at == _FIXED_NOW  # no wall-clock nondeterminism
    resolved = auth.require_session(str(session.id))
    assert resolved.username == "demo_doctor"
    assert resolved.role is Role.DOCTOR


def test_revoke_is_idempotent_second_call_does_not_raise():
    _, accounts, auth = _build_service()
    accounts.register(Account(username="demo_admin", role=Role.ADMIN))
    session = auth.login("demo_admin")
    auth.logout(str(session.id))
    auth.logout(str(session.id))  # second logout: no error


def test_revoke_unknown_token_is_unauthorized():
    _, _, auth = _build_service()
    with pytest.raises(Unauthorized):
        auth.logout(str(uuid4()))


# ---- AC-18.3: role_patient calling a coordinator-only operation -> Forbidden (403) ---------------

def test_patient_calling_coordinator_only_action_is_forbidden():
    patient = Account(username="p1", role=Role.PATIENT, patient_id=uuid4())
    with pytest.raises(Forbidden):
        authorize(patient, "approve_replan")


def test_coordinator_calling_approve_replan_is_allowed():
    coordinator = Account(username="c1", role=Role.COORDINATOR)
    authorize(coordinator, "approve_replan")  # must not raise


def test_unregistered_action_is_forbidden_by_default():
    admin = Account(username="a1", role=Role.ADMIN)
    with pytest.raises(Forbidden):
        authorize(admin, "some_action_nobody_registered")


# ---- AC-18.2 / scope predicates enforced in the data layer ---------------------------------------

def test_patient_resolves_only_their_own_appointments_via_own_scope():
    repo = InMemoryRepository()
    mine, other = uuid4(), uuid4()
    mine_appt = repo.save(Appointment(patient_id=mine, specialty="cardiology"))
    repo.save(Appointment(patient_id=other, specialty="neurology"))
    account = Account(username="p1", role=Role.PATIENT, patient_id=mine)

    visible = list_scoped(repo, account, Appointment)

    assert [a.id for a in visible] == [mine_appt.id]


def test_patient_resolves_only_their_own_task_via_one_hop_care_plan_join():
    repo = InMemoryRepository()
    mine, other = uuid4(), uuid4()
    my_plan = repo.save(CarePlan(patient_id=mine, diagnosis_id=uuid4()))
    other_plan = repo.save(CarePlan(patient_id=other, diagnosis_id=uuid4()))
    my_task = repo.save(
        Task(care_plan_id=my_plan.id, service_order_id=uuid4(), owner_id=uuid4())
    )
    repo.save(Task(care_plan_id=other_plan.id, service_order_id=uuid4(), owner_id=uuid4()))
    account = Account(username="p1", role=Role.PATIENT, patient_id=mine)

    visible = list_scoped(repo, account, Task)

    assert [t.id for t in visible] == [my_task.id]


# ---- TASK-016: denormalized patient_id resolves Own-scope on the previously fail-closed entities -

def test_own_scope_resolves_via_denormalized_patient_id_on_diagnosis_service_order_slot_payment():
    repo = InMemoryRepository()
    mine, other = uuid4(), uuid4()
    account = Account(username="p1", role=Role.PATIENT, patient_id=mine)

    my_diagnosis = Diagnosis(patient_id=mine, appointment_id=uuid4(), diagnosed_by=uuid4())
    other_diagnosis = Diagnosis(patient_id=other, appointment_id=uuid4(), diagnosed_by=uuid4())
    my_order = ServiceOrder(
        patient_id=mine, diagnosis_id=uuid4(), service_type_id=uuid4(), ordered_by=uuid4()
    )
    other_order = ServiceOrder(
        patient_id=other, diagnosis_id=uuid4(), service_type_id=uuid4(), ordered_by=uuid4()
    )
    my_slot = Slot(patient_id=mine, task_id=uuid4(), owner_id=uuid4(), start=_FIXED_NOW)
    other_slot = Slot(patient_id=other, task_id=uuid4(), owner_id=uuid4(), start=_FIXED_NOW)
    my_payment = Payment(
        patient_id=mine, subject_type=PaymentSubjectType.TASK, subject_id=uuid4()
    )
    other_payment = Payment(
        patient_id=other, subject_type=PaymentSubjectType.TASK, subject_id=uuid4()
    )

    for mine_record, other_record in (
        (my_diagnosis, other_diagnosis),
        (my_order, other_order),
        (my_slot, other_slot),
        (my_payment, other_payment),
    ):
        assert is_own(repo, account, mine_record)
        assert not is_own(repo, account, other_record)


def test_own_scope_resolves_via_patient_id_on_audit_log_entry_when_set():
    repo = InMemoryRepository()
    mine, other = uuid4(), uuid4()
    account = Account(username="p1", role=Role.PATIENT, patient_id=mine)

    mine_entry = AuditLogEntry(actor="Journey Agent", action="notify", patient_id=mine)
    other_entry = AuditLogEntry(actor="Journey Agent", action="notify", patient_id=other)

    assert is_own(repo, account, mine_entry)
    assert not is_own(repo, account, other_entry)


def test_audit_log_entry_with_no_patient_id_fails_closed_for_own_scope():
    repo = InMemoryRepository()
    account = Account(username="p1", role=Role.PATIENT, patient_id=uuid4())
    entry = AuditLogEntry(actor="agent-core", action="BLOCKED:drop_database")

    assert not is_own(repo, account, entry)


def test_scope_filtering_is_applied_by_the_data_layer_not_the_caller():
    """filter_by_scope is the enforcement point itself - a caller cannot bypass it by re-listing."""
    repo = InMemoryRepository()
    mine, other = uuid4(), uuid4()
    mine_appt = repo.save(Appointment(patient_id=mine, specialty="ent"))
    other_appt = repo.save(Appointment(patient_id=other, specialty="ent"))
    account = Account(username="p1", role=Role.PATIENT, patient_id=mine)

    filtered = filter_by_scope(repo, account, [mine_appt, other_appt], Scope.OWN)

    assert filtered == [mine_appt]
    assert not is_own(repo, account, other_appt)
    assert is_own(repo, account, mine_appt)


def test_doctor_read_scope_on_patient_is_assigned_not_all():
    account = Account(username="doc1", role=Role.DOCTOR, resource_id=uuid4())
    scope = resolve_scope(account, Appointment, CrudOp.READ)
    assert scope is Scope.ASSIGNED


def test_role_with_no_matrix_entry_for_op_is_forbidden():
    # role_patient has no CREATE right on CarePlan (R only, per docs/specs/06)
    account = Account(username="p1", role=Role.PATIENT, patient_id=uuid4())
    with pytest.raises(Forbidden):
        resolve_scope(account, CarePlan, CrudOp.CREATE)


def test_role_with_no_policy_row_at_all_is_forbidden():
    # role_technician has no access to Payment at all (see docs/specs/06 permission matrix)
    account = Account(username="t1", role=Role.TECHNICIAN, resource_id=uuid4())
    with pytest.raises(Forbidden):
        list_scoped(InMemoryRepository(), account, Payment)


# ---- accounts / seeded demo roster ---------------------------------------------------------------

def test_seed_demo_accounts_has_one_account_per_role_and_no_password_field():
    directory = seed_demo_accounts()
    roles_seen = set()
    for role in Role:
        found = None
        for name in ("demo_patient", "demo_doctor", "demo_technician",
                     "demo_coordinator", "demo_admin"):
            candidate = directory.get_by_username(name)
            if candidate is not None and candidate.role is role:
                found = candidate
                break
        assert found is not None, f"no seeded account for {role}"
        roles_seen.add(found.role)
        assert not hasattr(found, "password")
    assert roles_seen == set(Role)


def test_account_directory_lookup_by_id_returns_a_copy():
    directory = AccountDirectory()
    registered = directory.register(Account(username="x", role=Role.ADMIN))
    fetched = directory.get_by_id(registered.id)
    assert fetched == registered
    assert fetched is not registered  # defensive copy, mutation-proof
