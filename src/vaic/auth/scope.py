"""Data-scope predicates (Own / Assigned / Team / All) from docs/specs/06-access-control.md.

These are applied in the DATA layer (`filter_by_scope`, `list_scoped` in `permissions.py`) - never
by hiding a control in the UI (NFR-SEC-05). "Own worklist" from spec 06 collapses into ASSIGNED
here: both resolve from `task.owner_id = user.id`, which `is_assigned` already checks.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from ..models import CarePlan, Patient, Resource
from ..state import Repository
from .accounts import Account


class Scope(StrEnum):
    OWN = "OWN"
    ASSIGNED = "ASSIGNED"
    TEAM = "TEAM"
    ALL = "ALL"
    NONE = "NONE"


def is_own(repo: Repository, account: Account, record: Any) -> bool:
    """Own: `record.patient_id = user.patient_id`, or a record the account created.

    Resolution order: the Patient record itself, a direct `patient_id` field, one hop via
    `care_plan_id` -> `CarePlan.patient_id` (covers `Task`), then `created_by`.

    `Diagnosis`, `ServiceOrder`, `Slot`, and `Payment` all carry a denormalized `patient_id`
    (TASK-016), so they resolve on the direct-field branch. `AuditLogEntry.patient_id` is nullable:
    an entry with no patient context (e.g. a blocked unknown-tool call) falls through to
    `created_by` and, finding none, fails CLOSED rather than guess.
    """
    if isinstance(record, Patient):
        return account.patient_id is not None and record.id == account.patient_id
    patient_id = getattr(record, "patient_id", None)
    if patient_id is not None:
        return account.patient_id is not None and patient_id == account.patient_id
    care_plan_id = getattr(record, "care_plan_id", None)
    if care_plan_id is not None and account.patient_id is not None:
        plan = repo.get(CarePlan, care_plan_id)
        if plan is not None:
            return plan.patient_id == account.patient_id
    created_by = getattr(record, "created_by", None)
    return created_by is not None and created_by == account.id


def is_assigned(account: Account, record: Any) -> bool:
    """Assigned / Own worklist: `care_plan.assigned_staff` contains the user, or they own the task
    (`task.owner_id = user.id`, `user.id` here being the account's linked `resource_id`).
    """
    if account.resource_id is None:
        return False
    assigned_staff = getattr(record, "assigned_staff", None)
    if assigned_staff is not None:
        return account.resource_id in assigned_staff
    owner_id = getattr(record, "owner_id", None)
    return owner_id is not None and owner_id == account.resource_id


def is_team(repo: Repository, account: Account, record: Any) -> bool:
    """Team: `resource.department_id = user.department_id`, department resolved via the account's
    own linked Resource (accounts do not carry a department field directly)."""
    if account.resource_id is None:
        return False
    acting = repo.get(Resource, account.resource_id)
    if acting is None:
        return False
    department_id = getattr(record, "department_id", None)
    return department_id is not None and department_id == acting.department_id


def matches_scope(repo: Repository, account: Account, record: Any, scope: Scope) -> bool:
    if scope is Scope.ALL:
        return True
    if scope is Scope.NONE:
        return False
    if scope is Scope.OWN:
        return is_own(repo, account, record)
    if scope is Scope.ASSIGNED:
        return is_assigned(account, record)
    if scope is Scope.TEAM:
        return is_team(repo, account, record)
    raise ValueError(f"unhandled scope: {scope}")  # exhaustive guard - every Scope is listed above


def filter_by_scope(
    repo: Repository, account: Account, records: list[Any], scope: Scope
) -> list[Any]:
    """The data-layer enforcement point: keep only the records `scope` permits `account` to see."""
    return [record for record in records if matches_scope(repo, account, record, scope)]
