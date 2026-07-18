"""SMS channel (FR-15). In the demo, SMS is simulated - no real provider is called (BR-25).

A real provider is a production integration behind the `SmsGateway` protocol; every test injects a
fake, so no package here ever makes a network call (.claude/rules/testing.md). The `configured`
flag lets the notifier fall back to simulation when a real provider is not wired (FR-15 AC-15.2),
instead of raising.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class SmsReceipt(BaseModel):
    """The result of a (simulated or real) send. `simulated` marks the demo path (FR-15 AC-15.1)."""

    model_config = ConfigDict(extra="forbid")

    patient_id: UUID
    delivered: bool
    simulated: bool


class SmsGateway(Protocol):
    """A send-SMS client.

    Production wires a real provider; tests and the demo use the simulation.
    """

    @property
    def configured(self) -> bool:
        """True when the gateway can actually deliver. A real, unwired provider returns False."""
        ...

    def send(self, patient_id: UUID, phone: str | None, body: str) -> SmsReceipt:
        """Deliver `body` to the patient. Never log `phone` or `body` - both are PII."""
        ...


class SimulatedSmsGateway:
    """The demo gateway (BR-25). It records that a send happened; it does not log the body/phone.

    Always `configured` - simulation is always available, which is exactly why it is the fallback
    when a real provider is absent (FR-15 AC-15.2). `sent` counts sends for assertions in tests
    and for a demo counter; it deliberately stores no message content and no phone number.
    """

    def __init__(self) -> None:
        self.sent: int = 0

    @property
    def configured(self) -> bool:
        return True

    def send(self, patient_id: UUID, phone: str | None, body: str) -> SmsReceipt:
        # No PII in state or logs: we do not retain `phone` or `body` here (security-privacy.md).
        self.sent += 1
        return SmsReceipt(patient_id=patient_id, delivered=True, simulated=True)
