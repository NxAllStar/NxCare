"""Append-only reasoning audit log (FR-13).

Every agent decision is recorded with its reasoning so it can be explained ("why was my schedule
changed?"). Append-only: there is no update or delete path (BR-23). Never log secrets or PII.
"""

from __future__ import annotations

from uuid import UUID

from ..models import AuditLogEntry
from ..state import Repository


class AuditLog:
    def __init__(self, repo: Repository) -> None:
        self._repo = repo

    def record(
        self,
        actor: str,
        action: str,
        reasoning: str = "",
        target_id: UUID | None = None,
        patient_id: UUID | None = None,
    ) -> AuditLogEntry:
        """Append one entry and return it. There is deliberately no way to edit a recorded entry."""
        entry = AuditLogEntry(
            actor=actor, action=action, reasoning=reasoning, target_id=target_id,
            patient_id=patient_id,
        )
        return self._repo.save(entry)

    def entries(self) -> list[AuditLogEntry]:
        return sorted(self._repo.list(AuditLogEntry), key=lambda e: e.created_at)
