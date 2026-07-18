"""Server-side authorization: the permission matrix and named-action role guards from
docs/specs/06-access-control.md ("Permission matrix" and "Action permissions" tables).

Nothing here trusts the caller's role claim from outside; it is always the `Account` resolved by
`SessionService.validate` via `AuthService.require_session` (NFR-SEC-05/06).
"""

from __future__ import annotations

from enum import StrEnum

from ..models import (
    Appointment,
    AuditLogEntry,
    CarePlan,
    Diagnosis,
    DisruptionEvent,
    IntakeSession,
    Notification,
    Patient,
    Payment,
    Resource,
    ScanEvent,
    ServiceOrder,
    ServiceType,
    Slot,
    Task,
)
from ..state import Repository
from .accounts import Account
from .exceptions import Forbidden
from .roles import Role
from .scope import Scope, filter_by_scope


class CrudOp(StrEnum):
    CREATE = "C"
    READ = "R"
    UPDATE = "U"
    DELETE = "D"


def _ops(*ops: CrudOp) -> frozenset[CrudOp]:
    return frozenset(ops)


def _roles(*roles: Role) -> frozenset[Role]:
    return frozenset(roles)


_ALL_CRUD = _ops(CrudOp.CREATE, CrudOp.READ, CrudOp.UPDATE, CrudOp.DELETE)

# The permission matrix from docs/specs/06-access-control.md, one row per entity. A role absent
# from an entity's dict has no access at all (Scope.NONE, no ops) - fail closed by default.
PERMISSION_MATRIX: dict[type, dict[Role, tuple[frozenset[CrudOp], Scope]]] = {
    Patient: {
        Role.PATIENT: (_ops(CrudOp.READ, CrudOp.UPDATE), Scope.OWN),
        Role.DOCTOR: (_ops(CrudOp.READ), Scope.ASSIGNED),
        Role.TECHNICIAN: (_ops(CrudOp.READ), Scope.ASSIGNED),
        Role.COORDINATOR: (_ops(CrudOp.READ), Scope.ALL),
        Role.ADMIN: (_ALL_CRUD, Scope.ALL),
    },
    IntakeSession: {
        Role.PATIENT: (_ops(CrudOp.CREATE, CrudOp.READ), Scope.OWN),
        Role.DOCTOR: (_ops(CrudOp.READ), Scope.ASSIGNED),
        Role.COORDINATOR: (_ops(CrudOp.READ), Scope.ALL),
        Role.ADMIN: (_ALL_CRUD, Scope.ALL),
    },
    Appointment: {
        Role.PATIENT: (_ops(CrudOp.CREATE, CrudOp.READ, CrudOp.UPDATE), Scope.OWN),
        Role.DOCTOR: (_ops(CrudOp.READ, CrudOp.UPDATE), Scope.ASSIGNED),
        Role.TECHNICIAN: (_ops(CrudOp.READ), Scope.ASSIGNED),
        Role.COORDINATOR: (_ALL_CRUD, Scope.ALL),
        Role.ADMIN: (_ALL_CRUD, Scope.ALL),
    },
    Diagnosis: {
        Role.PATIENT: (_ops(CrudOp.READ), Scope.OWN),
        Role.DOCTOR: (_ops(CrudOp.CREATE, CrudOp.READ, CrudOp.UPDATE), Scope.ASSIGNED),
        Role.TECHNICIAN: (_ops(CrudOp.READ), Scope.ASSIGNED),
        Role.COORDINATOR: (_ops(CrudOp.READ), Scope.ALL),
        Role.ADMIN: (_ops(CrudOp.READ), Scope.ALL),
    },
    ServiceOrder: {
        Role.PATIENT: (_ops(CrudOp.READ), Scope.OWN),
        Role.DOCTOR: (_ops(CrudOp.CREATE, CrudOp.READ, CrudOp.UPDATE), Scope.ASSIGNED),
        Role.TECHNICIAN: (_ops(CrudOp.READ), Scope.ASSIGNED),
        Role.COORDINATOR: (_ops(CrudOp.READ), Scope.ALL),
        Role.ADMIN: (_ops(CrudOp.READ), Scope.ALL),
    },
    CarePlan: {
        Role.PATIENT: (_ops(CrudOp.READ), Scope.OWN),
        Role.DOCTOR: (_ops(CrudOp.READ), Scope.ASSIGNED),
        Role.TECHNICIAN: (_ops(CrudOp.READ), Scope.ASSIGNED),
        Role.COORDINATOR: (_ops(CrudOp.READ, CrudOp.UPDATE), Scope.ALL),
        Role.ADMIN: (_ALL_CRUD, Scope.ALL),
    },
    Task: {
        Role.PATIENT: (_ops(CrudOp.READ), Scope.OWN),
        Role.DOCTOR: (_ops(CrudOp.READ, CrudOp.UPDATE), Scope.ASSIGNED),
        Role.TECHNICIAN: (_ops(CrudOp.READ, CrudOp.UPDATE), Scope.ASSIGNED),
        Role.COORDINATOR: (_ops(CrudOp.READ, CrudOp.UPDATE), Scope.ALL),
        Role.ADMIN: (_ALL_CRUD, Scope.ALL),
    },
    Slot: {
        Role.PATIENT: (_ops(CrudOp.READ), Scope.OWN),
        Role.DOCTOR: (_ops(CrudOp.READ), Scope.ASSIGNED),
        Role.TECHNICIAN: (_ops(CrudOp.READ), Scope.ASSIGNED),
        Role.COORDINATOR: (_ops(CrudOp.READ, CrudOp.UPDATE), Scope.ALL),
        Role.ADMIN: (_ALL_CRUD, Scope.ALL),
    },
    Payment: {
        Role.PATIENT: (_ops(CrudOp.CREATE, CrudOp.READ), Scope.OWN),
        Role.COORDINATOR: (_ops(CrudOp.READ), Scope.ALL),
        Role.ADMIN: (_ops(CrudOp.READ), Scope.ALL),
    },
    Resource: {
        Role.DOCTOR: (_ops(CrudOp.READ), Scope.TEAM),
        Role.TECHNICIAN: (_ops(CrudOp.READ), Scope.TEAM),
        Role.COORDINATOR: (_ops(CrudOp.READ, CrudOp.UPDATE), Scope.ALL),
        Role.ADMIN: (_ALL_CRUD, Scope.ALL),
    },
    DisruptionEvent: {
        Role.DOCTOR: (_ops(CrudOp.READ), Scope.ASSIGNED),
        Role.TECHNICIAN: (_ops(CrudOp.READ), Scope.ASSIGNED),
        Role.COORDINATOR: (_ops(CrudOp.READ, CrudOp.UPDATE), Scope.ALL),
        Role.ADMIN: (_ALL_CRUD, Scope.ALL),
    },
    Notification: {
        Role.PATIENT: (_ops(CrudOp.READ), Scope.OWN),
        Role.DOCTOR: (_ops(CrudOp.READ), Scope.OWN),
        Role.TECHNICIAN: (_ops(CrudOp.READ), Scope.OWN),
        Role.COORDINATOR: (_ops(CrudOp.READ), Scope.ALL),
        Role.ADMIN: (_ops(CrudOp.READ), Scope.ALL),
    },
    ScanEvent: {
        Role.PATIENT: (_ops(CrudOp.READ), Scope.OWN),
        Role.DOCTOR: (_ops(CrudOp.CREATE, CrudOp.READ), Scope.ASSIGNED),
        Role.TECHNICIAN: (_ops(CrudOp.CREATE, CrudOp.READ), Scope.ASSIGNED),
        Role.COORDINATOR: (_ops(CrudOp.READ), Scope.ALL),
        Role.ADMIN: (_ALL_CRUD, Scope.ALL),
    },
    AuditLogEntry: {
        Role.PATIENT: (_ops(CrudOp.READ), Scope.OWN),
        Role.DOCTOR: (_ops(CrudOp.READ), Scope.OWN),
        Role.COORDINATOR: (_ops(CrudOp.READ), Scope.ALL),
        Role.ADMIN: (_ops(CrudOp.READ), Scope.ALL),
    },
    ServiceType: {
        Role.PATIENT: (_ops(CrudOp.READ), Scope.ALL),
        Role.DOCTOR: (_ops(CrudOp.READ), Scope.ALL),
        Role.TECHNICIAN: (_ops(CrudOp.READ), Scope.ALL),
        Role.COORDINATOR: (_ops(CrudOp.READ), Scope.ALL),
        Role.ADMIN: (_ALL_CRUD, Scope.ALL),
    },
}


def resolve_scope(account: Account, model_cls: type, op: CrudOp) -> Scope:
    """Return the Scope `account`'s role may apply `op` under, or raise Forbidden (403)."""
    role_map = PERMISSION_MATRIX.get(model_cls, {})
    ops, scope = role_map.get(account.role, (frozenset(), Scope.NONE))
    if op not in ops or scope is Scope.NONE:
        raise Forbidden(f"role {account.role.value} may not {op.value} {model_cls.__name__}")
    return scope


def list_scoped(
    repo: Repository, account: Account, model_cls: type, op: CrudOp = CrudOp.READ
) -> list:
    """The data-layer query an API handler calls: resolve the account's scope, then filter.

    This IS the enforcement point for AC-18.2/AC-18.3 - it raises Forbidden before any record is
    returned, and it never depends on the caller (or the UI) to hide what should not be visible.
    """
    scope = resolve_scope(account, model_cls, op)
    return filter_by_scope(repo, account, repo.list(model_cls), scope)


# ---- named-action role guards (docs/specs/06 "Action permissions" table) ------------------------

ACTION_ROLES: dict[str, frozenset[Role]] = {
    "sign_service_order": _roles(Role.DOCTOR),
    "make_payment": _roles(Role.PATIENT),
    "approve_replan": _roles(Role.COORDINATOR, Role.ADMIN),
    "reject_replan": _roles(Role.COORDINATOR, Role.ADMIN),
    "update_task_status": _roles(Role.TECHNICIAN, Role.DOCTOR),
    "scan_task": _roles(Role.DOCTOR, Role.TECHNICIAN),
    "reorder_worklist": _roles(Role.DOCTOR),
    "seed_simulator": _roles(Role.ADMIN),
    "read_audit_log": _roles(Role.ADMIN, Role.COORDINATOR),
}


def authorize(account: Account, action: str) -> None:
    """Role guard for a named action. Raises Forbidden (403) when the role is not permitted.

    An action with no registered policy is denied by default (closed action space philosophy,
    mirroring BR-19 for tools): an unrecognised action is never silently allowed.
    """
    allowed = ACTION_ROLES.get(action)
    if not allowed or account.role not in allowed:
        raise Forbidden(f"role {account.role.value} may not perform '{action}'")
