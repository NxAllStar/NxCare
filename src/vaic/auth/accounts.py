"""Accounts + demo seed roster (FR-18, docs/specs/06-access-control.md).

Demo auth only: no password field, no custom crypto. An account is looked up by username (or
selected by role for a presentation); production SSO/MFA identity stays out of scope (OI-11).
"""

from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from .roles import Role


class Account(BaseModel):
    """A demo account. `patient_id` anchors the Own scope for `role_patient`; `resource_id`
    anchors the Assigned/Team scopes for staff roles (see docs/specs/06 "Data scope rules").
    """

    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    username: str
    role: Role
    patient_id: UUID | None = None
    resource_id: UUID | None = None


class AccountDirectory:
    """username -> Account lookup, held in memory. Swappable behind this small interface if a
    real identity store replaces it later (OI-11 remains a production decision, not a demo one).
    """

    def __init__(self, accounts: Iterable[Account] = ()) -> None:
        self._by_username: dict[str, Account] = {}
        self._by_id: dict[UUID, Account] = {}
        for account in accounts:
            self.register(account)

    def register(self, account: Account) -> Account:
        """Add or replace an account. Stores (and returns) a defensive copy."""
        stored = account.model_copy(deep=True)
        self._by_username[stored.username] = stored
        self._by_id[stored.id] = stored
        return stored.model_copy(deep=True)

    def get_by_username(self, username: str) -> Account | None:
        found = self._by_username.get(username)
        return found.model_copy(deep=True) if found is not None else None

    def get_by_id(self, account_id: UUID) -> Account | None:
        found = self._by_id.get(account_id)
        return found.model_copy(deep=True) if found is not None else None


def seed_demo_accounts() -> AccountDirectory:
    """One synthetic demo account per role (docs/specs/06 "Roles"). No real names, no passwords.

    `patient_id`/`resource_id` are left unset here (deterministic, no random linkage at seed time);
    wiring an account to a specific simulator-seeded Patient/Resource is a separate, explicit step
    (`AccountDirectory.register` again with the link filled in) so this seed stays reproducible.
    """
    directory = AccountDirectory()
    directory.register(Account(username="demo_patient", role=Role.PATIENT))
    directory.register(Account(username="demo_doctor", role=Role.DOCTOR))
    directory.register(Account(username="demo_technician", role=Role.TECHNICIAN))
    directory.register(Account(username="demo_coordinator", role=Role.COORDINATOR))
    directory.register(Account(username="demo_admin", role=Role.ADMIN))
    return directory
