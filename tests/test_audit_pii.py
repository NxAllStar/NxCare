"""Audit-log PII guard (TASK-037): free-text reasoning is redacted before it is persisted.

The audit log is append-only and explains agent decisions (FR-13), but a model-authored `reasoning`
string could carry PII (a phone number, an email, a national id). NFR-SEC-01 forbids PII in logs, so
the audit boundary scrubs structured PII before storing, and never writes the raw value.
"""

from __future__ import annotations

from vaic.state import InMemoryRepository
from vaic.tools import AuditLog
from vaic.tools.pii import redact_pii


def test_redacts_email():
    assert redact_pii("contact jane.doe@example.com about it") == (
        "contact [redacted-email] about it"
    )


def test_redacts_phone_and_national_id():
    assert "[redacted-number]" in redact_pii("call 0912345678 now")
    assert "[redacted-number]" in redact_pii("id 079201001234 on file")


def test_keeps_short_operational_numbers():
    text = "blast radius 30, ETA about 20 min, moved to position 3"
    assert redact_pii(text) == text  # nothing here is PII, so nothing is touched


def test_empty_text_is_unchanged():
    assert redact_pii("") == ""


def test_audit_record_scrubs_reasoning_before_persisting():
    repo = InMemoryRepository()
    audit = AuditLog(repo)

    entry = audit.record(
        actor="disruption",
        action="execute_replan",
        reasoning="notified patient at 0912345678 and jane@example.com",
    )

    stored = audit.entries()[-1]
    assert "0912345678" not in stored.reasoning
    assert "jane@example.com" not in stored.reasoning
    assert "[redacted-number]" in stored.reasoning and "[redacted-email]" in stored.reasoning
    assert stored.reasoning == entry.reasoning  # what is returned is what is stored
