"""The five roles in docs/specs/06-access-control.md. Values are English, matching the spec exactly.

Assigned by role_admin (role_admin bootstraps itself); see 06 "Roles" for the held-by mapping.
"""

from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    PATIENT = "role_patient"
    DOCTOR = "role_doctor"
    TECHNICIAN = "role_technician"
    COORDINATOR = "role_coordinator"
    ADMIN = "role_admin"
