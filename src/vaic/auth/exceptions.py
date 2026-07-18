"""Auth exceptions. Framework-agnostic on purpose: an API layer maps these to HTTP status codes
(Unauthorized -> 401, Forbidden -> 403). No web framework is imported here (safe under either
ADR-001 option).
"""

from __future__ import annotations


class AuthError(Exception):
    """Base class for every auth failure raised by vaic.auth."""


class Unauthorized(AuthError):
    """No valid session for the request. An API layer maps this to HTTP 401 (AC-18.1)."""


class Forbidden(AuthError):
    """A valid session exists but the account's role/scope does not permit the action.

    Enforced server-side regardless of what the UI shows or hides (NFR-SEC-05). An API layer maps
    this to HTTP 403 (AC-18.3).
    """
