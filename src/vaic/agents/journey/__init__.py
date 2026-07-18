"""Journey Agent: per-patient escort, timeline notifications, patient-code scan, SMS.

Covers FR-06 (escort and resequencing), FR-11 (timeline notifications), FR-15 (SMS channel),
FR-17 (patient-code scan). Builds on the agent-core spine (vaic.agents.core) and the shared tool
framework (vaic.tools); it registers one domain tool (`scan_patient`) and otherwise acts through
the Notifier and the deterministic resequencer.
"""

from __future__ import annotations

from .agent import JourneyAgent
from .chat import (
    ChatReasonerError,
    ChatReply,
    JourneyChatLLM,
    RuleBasedJourneyChatLLM,
    interpret_chat,
)
from .events import EtaUpdate, JourneyHandover, PatientChat
from .llm_client import HttpJourneyChatLLM, build_journey_chat_llm
from .notifications import CrossPatientScopeError, Notifier
from .resequence import (
    ResequenceProposal,
    apply_order,
    bring_forward,
    is_order_legal,
    propose_resequence,
)
from .scan import SCAN_TOOL, ScanPatientIn, register_journey_tools
from .sms import SimulatedSmsGateway, SmsGateway, SmsReceipt

__all__ = [
    "JourneyAgent",
    "Notifier",
    "CrossPatientScopeError",
    "SmsGateway",
    "SimulatedSmsGateway",
    "SmsReceipt",
    "ResequenceProposal",
    "propose_resequence",
    "bring_forward",
    "apply_order",
    "is_order_legal",
    "ChatReply",
    "ChatReasonerError",
    "JourneyChatLLM",
    "RuleBasedJourneyChatLLM",
    "HttpJourneyChatLLM",
    "build_journey_chat_llm",
    "interpret_chat",
    "JourneyHandover",
    "EtaUpdate",
    "PatientChat",
    "SCAN_TOOL",
    "ScanPatientIn",
    "register_journey_tools",
]
