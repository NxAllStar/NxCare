"""Deterministic emergency detection (BF-05, FR-01 AC-01.2).

`RED_FLAG_SIGNALS` is a small, clearly-marked PLACEHOLDER set. The clinical red-flag list is not
this lane's authority: the content is owned by the clinician (OI-09, owner SH-02). This set exists
only so the escalation MECHANISM has something deterministic to check against in the demo/tests;
replacing it with the real clinical list is a content change, not a mechanism change, and does not
require touching `detect_emergency`.
"""

from __future__ import annotations

from ...models import PriorityLevel

# OI-09-pending: placeholder red-flag phrases only, NOT a clinical authority. Synthetic, ASCII
# (no diacritics) Vietnamese phrasing to match this task's synthetic transcript fixtures. A
# clinician-owned list replaces this frozenset wholesale when OI-09 is resolved.
RED_FLAG_SIGNALS: frozenset[str] = frozenset(
    {
        "dau nguc du doi",  # severe chest pain
        "kho tho nang",  # severe difficulty breathing
        "ngat xiu",  # fainting / loss of consciousness
        "chay mau khong cam duoc",  # uncontrolled bleeding
        "co giat",  # seizure
    }
)


def detect_emergency(transcript: str, priority: PriorityLevel) -> bool:
    """Deterministic check (code, not the model) - FR-01 "model flags, code checks".

    True when the model-assigned priority is already EMERGENCY, or when the transcript contains
    one of the placeholder red-flag signals. The transcript is treated as plain DATA: matching is a
    case-insensitive substring search, never an instruction the transcript can issue.
    """
    if priority is PriorityLevel.EMERGENCY:
        return True
    lowered = transcript.lower()
    return any(signal in lowered for signal in RED_FLAG_SIGNALS)
