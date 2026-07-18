"""Backend auth for VAIC (FR-18, TASK-013): accounts, sessions, and server-side role/scope
authorization.

The login SCREEN and app shell are a separate frontend task (TASK-015); this module is the backend
the shell calls. Demo auth only - seeded accounts, no password, no custom crypto (docs/specs/06);
production SSO/MFA stays out of scope (OI-11).
"""

from __future__ import annotations

from .accounts import Account, AccountDirectory, seed_demo_accounts
from .exceptions import AuthError, Forbidden, Unauthorized
from .permissions import (
    ACTION_ROLES,
    PERMISSION_MATRIX,
    CrudOp,
    authorize,
    list_scoped,
    resolve_scope,
)
from .roles import Role
from .scope import Scope, filter_by_scope, is_assigned, is_own, is_team, matches_scope
from .service import AuthService
from .session import Session, SessionService

__all__ = [
    "Account",
    "AccountDirectory",
    "seed_demo_accounts",
    "AuthError",
    "Forbidden",
    "Unauthorized",
    "ACTION_ROLES",
    "PERMISSION_MATRIX",
    "CrudOp",
    "authorize",
    "list_scoped",
    "resolve_scope",
    "Role",
    "Scope",
    "filter_by_scope",
    "is_assigned",
    "is_own",
    "is_team",
    "matches_scope",
    "AuthService",
    "Session",
    "SessionService",
]
