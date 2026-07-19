"""PII redaction for text that reaches the audit log (TASK-037, NFR-SEC-01).

Agent `reasoning` is free text and could carry structured PII - a phone number, an email, a national
id / MRN. This scrubs those before they are persisted, so a leak never reaches the append-only log
(which has no delete path, BR-23, so redaction must happen at write time, not after).

Scope is deliberately precise over exhaustive: it targets structured identifiers (email, long
contiguous digit runs) and leaves short operational numbers ("blast radius 30", "ETA 20 min")
untouched, so it never mangles legitimate reasoning. Names are not pattern-detectable and remain a
discipline rule (no PII in reasoning); this is the mechanical backstop for the structured cases.
"""

from __future__ import annotations

import re

_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
# A contiguous run of 9+ digits (optionally +-prefixed, with . or - separators): phone, national
# id, MRN. Spaces are NOT allowed inside, so a list of small numbers is never mistaken for one id.
_LONG_NUMBER = re.compile(r"\+?\d[\d.-]{7,}\d")


def redact_pii(text: str) -> str:
    """Return `text` with structured PII (emails, long digit runs) replaced by redaction markers."""
    if not text:
        return text
    text = _EMAIL.sub("[redacted-email]", text)
    return _LONG_NUMBER.sub("[redacted-number]", text)
