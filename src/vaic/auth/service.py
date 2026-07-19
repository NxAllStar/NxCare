"""AuthService: the facade an API layer calls (login, logout, require_session, authorize)."""

from __future__ import annotations

from uuid import UUID

from .accounts import Account, AccountDirectory
from .exceptions import Unauthorized
from .permissions import authorize as _authorize
from .session import Session, SessionService


class AuthService:
    def __init__(self, accounts: AccountDirectory, sessions: SessionService) -> None:
        self._accounts = accounts
        self._sessions = sessions

    def login(self, username: str) -> Session:
        """Demo login: account/role selection, no password (docs/specs/06 "Authentication").

        Raises Unauthorized if `username` is not a registered account.
        """
        account = self._accounts.get_by_username(username)
        if account is None:
            raise Unauthorized(f"unknown account: {username}")
        return self._sessions.create(account)

    def login_by_patient_id(self, patient_id: UUID) -> Session:
        """Patient-facing login: the caller resolves a `patient_code` to a `patient_id` (a real
        `Patient` row lookup, not a client-side table) and this looks up the account linked to it -
        same demo posture as `login` (no password), just keyed by `patient_id` instead of
        `username` so the patient-facing login screen never needs to know internal usernames.
        """
        account = self._accounts.get_by_patient_id(patient_id)
        if account is None:
            raise Unauthorized(f"no account linked to patient {patient_id}")
        return self._sessions.create(account)

    def logout(self, token: str) -> None:
        self._sessions.revoke(token)

    def require_session(self, token: str) -> Account:
        """AC-18.1: no valid session for `token` -> Unauthorized (401)."""
        session = self._sessions.validate(token)
        account = self._accounts.get_by_id(session.account_id)
        if account is None:
            raise Unauthorized("session refers to an unknown account")
        return account

    def authorize(self, account: Account, action: str) -> None:
        """AC-18.3: `account`'s role lacks permission for `action` -> Forbidden (403)."""
        _authorize(account, action)
