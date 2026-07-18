"""Intake Agent: conversational triage (FR-01), least-crowded slot recommendation (FR-02), and
emergency escalation (BF-05). See docs/tasks/active/TASK-007-intake-triage-slot-escalation.md (D11)
for the frozen public API this package implements.
"""

from __future__ import annotations

from .agent import (
    BookAppointmentInput,
    EscalateEmergencyInput,
    IntakeAgent,
    build_intake_registry,
)
from .emergency import RED_FLAG_SIGNALS, detect_emergency
from .slots import SlotProposal, recommend_slots
from .triage import TriageLLM, TriageResult, extract_triage

__all__ = [
    "IntakeAgent",
    "build_intake_registry",
    "BookAppointmentInput",
    "EscalateEmergencyInput",
    "RED_FLAG_SIGNALS",
    "detect_emergency",
    "SlotProposal",
    "recommend_slots",
    "TriageLLM",
    "TriageResult",
    "extract_triage",
]
