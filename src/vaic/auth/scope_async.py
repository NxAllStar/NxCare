"""Async twin of `scope.py`, against `AsyncPostgresRepository` instead of the sync `Repository`.

Line-for-line port of `is_own`/`is_team`/`matches_scope`/`filter_by_scope`: same rules, same
docs/specs/06-access-control.md predicates, only the two I/O calls (`repo.get`) are awaited.
`is_assigned` needs no twin - it never touches the repo, so the sync version in `scope.py` is
reused unchanged. This is the enforcement point for every new API route's scope-filtered read
(`api/crud.py`, `api/deps.py`); the sync path in `scope.py` still backs `auth/session.py` and the
existing `agents/*` code, untouched.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..models import CarePlan, Patient, Resource
from .accounts import Account
from .scope import Scope, is_assigned

if TYPE_CHECKING:
    from ..state.sql.repository import AsyncPostgresRepository


async def is_own_async(repo: AsyncPostgresRepository, account: Account, record: Any) -> bool:
    """Async twin of `scope.is_own` - see that docstring for the resolution order."""
    if isinstance(record, Patient):
        return account.patient_id is not None and record.id == account.patient_id
    patient_id = getattr(record, "patient_id", None)
    if patient_id is not None:
        return account.patient_id is not None and patient_id == account.patient_id
    care_plan_id = getattr(record, "care_plan_id", None)
    if care_plan_id is not None and account.patient_id is not None:
        plan = await repo.get(CarePlan, care_plan_id)
        if plan is not None:
            return plan.patient_id == account.patient_id
    created_by = getattr(record, "created_by", None)
    return created_by is not None and created_by == account.id


async def is_team_async(repo: AsyncPostgresRepository, account: Account, record: Any) -> bool:
    """Async twin of `scope.is_team`."""
    if account.resource_id is None:
        return False
    acting = await repo.get(Resource, account.resource_id)
    if acting is None:
        return False
    department_id = getattr(record, "department_id", None)
    return department_id is not None and department_id == acting.department_id


async def matches_scope_async(
    repo: AsyncPostgresRepository, account: Account, record: Any, scope: Scope
) -> bool:
    if scope is Scope.ALL:
        return True
    if scope is Scope.NONE:
        return False
    if scope is Scope.OWN:
        return await is_own_async(repo, account, record)
    if scope is Scope.ASSIGNED:
        return is_assigned(account, record)
    if scope is Scope.TEAM:
        return await is_team_async(repo, account, record)
    raise ValueError(f"unhandled scope: {scope}")  # exhaustive guard - every Scope is listed above


async def filter_by_scope_async(
    repo: AsyncPostgresRepository, account: Account, records: list[Any], scope: Scope
) -> list[Any]:
    """The async data-layer enforcement point: keep only what `scope` permits `account` to see."""
    return [record for record in records if await matches_scope_async(repo, account, record, scope)]
