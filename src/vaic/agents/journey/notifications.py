"""Patient timeline notifications (FR-11) and the SMS fan-out (FR-15).

A notification is built for exactly one patient. The scope guard (FR-11 AC-11.2) refuses to persist
anything that references another patient's task, so a mis-addressed or cross-wired notification is
blocked before it reaches the timeline rather than leaking data across patients. Bodies are
patient-facing operational text (next step, ETA, reason); no other patient's data and no secrets
ever enter a body, and bodies are never written to logs.
"""

from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

from ...models import CarePlan, Notification, NotificationChannel, Patient, Task
from ...state import Repository
from .sms import SimulatedSmsGateway, SmsGateway


class CrossPatientScopeError(Exception):
    """Raised when a notification would reference a task that is not the target patient's.

    The notification is not persisted and no SMS is sent - the disclosure never happens (FR-11
    AC-11.2). The error message names no patient identifier.
    """


class Notifier:
    """Builds, scope-checks, and persists patient notifications, with an optional SMS fan-out.

    The SMS gateway defaults to the simulated one (FR-15 BR-25). A real but unconfigured gateway
    degrades to simulation rather than failing (FR-15 AC-15.2).
    """

    def __init__(self, repo: Repository, sms_gateway: SmsGateway | None = None) -> None:
        self._repo = repo
        self._sms = sms_gateway or SimulatedSmsGateway()
        self._fallback = SimulatedSmsGateway()

    def notify(
        self,
        patient_id: UUID,
        body: str,
        *,
        reason: str | None = None,
        about_task_ids: Iterable[UUID] = (),
        sms: bool = False,
    ) -> list[Notification]:
        """Persist an in-app timeline notification, plus an SMS copy when `sms` is set.

        `about_task_ids` are the tasks this message is about; every one must belong to
        `patient_id` or the whole call is refused (AC-11.2). Returns the persisted notifications
        (the IN_APP timeline entry, and the SMS entry when requested), which carry the same body
        (FR-15 AC-15.1).
        """
        self._assert_scope(patient_id, about_task_ids)

        timeline = self._repo.save(
            Notification(
                patient_id=patient_id,
                channel=NotificationChannel.IN_APP,
                body=body,
                reason=reason,
            )
        )
        out = [timeline]

        if sms:
            sms_notification = self._send_sms(patient_id, body, reason)
            if sms_notification is not None:
                out.append(sms_notification)
        return out

    # ---- internals -----------------------------------------------------------

    def assert_scope(self, patient_id: UUID, about_task_ids: Iterable[UUID]) -> None:
        """Public scope guard (FR-11 AC-11.2): raise `CrossPatientScopeError` if any of
        `about_task_ids` does not belong to `patient_id`.

        Exposed so a caller that mutates state on the strength of a reorder (the Journey Agent's
        resequence path) can verify the scope BEFORE persisting anything, not only when it later
        calls `notify` - a partial state change must never survive a rejected scope check.
        """
        self._assert_scope(patient_id, about_task_ids)

    def _assert_scope(self, patient_id: UUID, about_task_ids: Iterable[UUID]) -> None:
        for task_id in about_task_ids:
            task = self._repo.get(Task, task_id)
            if task is None:
                raise CrossPatientScopeError("notification references an unknown task")
            care_plan = self._repo.get(CarePlan, task.care_plan_id)
            if care_plan is None or care_plan.patient_id != patient_id:
                # Do not name the other patient - this text may be logged (security-privacy.md).
                raise CrossPatientScopeError(
                    "notification references a task belonging to another patient"
                )

    def _send_sms(self, patient_id: UUID, body: str, reason: str | None) -> Notification | None:
        # A missing patient is a no-op: never send to a phone number we cannot look up, and never
        # persist an SMS entry for a send that did not happen.
        patient = self._repo.get(Patient, patient_id)
        if patient is None:
            return None
        # A real but unconfigured provider degrades to simulation (AC-15.2), never an error.
        gateway = self._sms if self._sms.configured else self._fallback
        gateway.send(patient_id, patient.phone, body)
        return self._repo.save(
            Notification(
                patient_id=patient_id,
                channel=NotificationChannel.SMS,
                body=body,  # same content as the timeline entry (AC-15.1)
                reason=reason,
            )
        )
