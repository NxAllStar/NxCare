"""The Journey Agent (FR-06): a per-patient escort over one care plan.

Event-driven (BR-12): it wakes on a handover, a scan, an ETA change, or a patient chat message, and
holds no polling loop. Every state-changing scan goes through the guarded executor spine (closed
action space -> constraint checker -> tool -> audit), so authorisation and auditability are not this
agent's to re-implement. Its own outputs - timeline notifications (FR-11/FR-15) and single-patient,
dependency-legal reorders (FR-06) - it performs directly; a reorder that would touch other patients
is a re-plan and belongs to the Coordinator (FR-09), not here.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID

from ...models import CarePlan, ExecutionStatus, ServiceOrder, ServiceType, Task
from ...tools import Action, ActionResult
from ..core import ActionExecutor, Agent
from .chat import ChatReply, JourneyChatLLM, RuleBasedJourneyChatLLM, interpret_chat
from .events import EtaUpdate, JourneyHandover, PatientChat
from .notifications import Notifier
from .resequence import ResequenceProposal, apply_order, bring_forward, propose_resequence
from .scan import SCAN_TOOL


class JourneyAgent(Agent):
    def __init__(
        self,
        executor: ActionExecutor,
        repo,
        notifier: Notifier,
        chat_llm: JourneyChatLLM | None = None,
        name: str = "journey",
    ) -> None:
        super().__init__(name, executor)
        self._repo = repo
        self._notifier = notifier
        self._chat = chat_llm or RuleBasedJourneyChatLLM()

    # ---- Agent base: the scan is the one action routed through the guarded spine --------------

    def perceive(self, event: Any) -> Any:
        return event

    def reason(self, perception: Any) -> list[Action]:
        # The rich, event-typed behaviour lives in the on_* handlers below; the base contract is
        # satisfied here for the scan path so `run()` still works for a bare scan action.
        return []

    # ---- event handlers (BR-12) ---------------------------------------------------------------

    def on_handover(self, event: JourneyHandover):
        """Start the escort: greet the patient with their first step and its ETA (FR-06 trigger)."""
        tasks = self._plan_tasks(event.care_plan_id)
        care_plan = self._repo.get(CarePlan, event.care_plan_id)
        if care_plan is None or not tasks:
            return []
        # Never greet on a DONE/IN_PROGRESS/CANCELLED task: only a still-movable step is a
        # legitimate "next step" to announce (mirrors resequence.py's movable notion).
        candidates = [
            t
            for t in tasks
            if t.execution_status
            not in (ExecutionStatus.DONE, ExecutionStatus.IN_PROGRESS, ExecutionStatus.CANCELLED)
        ]
        if not candidates:
            return []
        first = min(candidates, key=lambda t: t.sequence_index)
        return self._notifier.notify(
            care_plan.patient_id,
            body=f"Your care plan is ready. Next step is queued with an estimated wait of about "
            f"{first.estimated_duration_min} minutes.",
            reason="care plan handover",
            about_task_ids=[first.id],
        )

    def on_scan(self, task_id: UUID, scanned_by: UUID, patient_code: str) -> ActionResult:
        """Advance a task on a station scan and notify the patient (FR-17).

        On success: task -> IN_PROGRESS and an "in progress" notice. On a LOCKED (unpaid) block:
        no state change and a reminder to complete payment (AC-17.2). On any other block (e.g.
        wrong owner, AC-17.3): no state change and no misleading notice.
        """
        action = Action(
            tool=SCAN_TOOL,
            actor=self.name,
            params={"task_id": task_id, "scanned_by": scanned_by, "patient_code": patient_code},
            reasoning="station scan confirms patient presence (FR-17)",
        )
        result = self.act(action)

        patient_id = self._patient_of_task(task_id)
        if patient_id is None:
            return result

        if result.allowed and result.ok:
            self._notifier.notify(
                patient_id,
                body="You have been checked in at the room; your step is now in progress.",
                reason="patient-code scan",
                about_task_ids=[task_id],
            )
        elif not result.allowed:
            # Do not couple to the constraint checker's reason wording: ask the entity model
            # itself whether this task is LOCKED (unpaid) before sending the payment notice.
            task = self._repo.get(Task, task_id)
            if task is not None and task.is_locked:
                self._notifier.notify(
                    patient_id,
                    body="This step is not paid yet, so it cannot start. Please complete payment "
                    "at the counter to unlock it.",
                    reason="scan blocked: unpaid step",
                    about_task_ids=[task_id],
                )
            # Any other block reason (e.g. wrong owner, AC-17.3): no state change, no notice.
        return result

    def on_eta_update(self, event: EtaUpdate) -> ResequenceProposal | None:
        """React to an ETA spike with a dependency-legal reorder and a reason (AC-06.1, FR-11)."""
        tasks = self._plan_tasks(event.care_plan_id)
        care_plan = self._repo.get(CarePlan, event.care_plan_id)
        if care_plan is None or not tasks:
            return None
        proposal = propose_resequence(tasks, event.etas)
        if proposal is None:
            return None  # no beneficial legal swap: hold the current order (failure mode)
        self._apply_and_notify(care_plan.patient_id, tasks, proposal)
        return proposal

    def on_chat(self, event: PatientChat) -> ChatReply:
        """Answer a patient chat message (FR-06). The message is DATA; no command in it is executed.

        For a fasting question, refuse eating and bring the fasting test as early as dependencies
        allow (AC-06.2). No chat path ever changes a task's execution_status (AC-06.3).

        `event.care_plan_id` and `event.patient_id` are bound here against the store, the same way
        `on_handover`/`on_eta_update` bind them: if the care plan does not exist, or exists but
        belongs to a different patient than `event.patient_id` claims, no task is read further, no
        state changes, and no notification is sent (a mismatched request never reorders another
        patient's plan).
        """
        care_plan = self._repo.get(CarePlan, event.care_plan_id)
        if care_plan is None or care_plan.patient_id != event.patient_id:
            return ChatReply(
                answer="I could not find that care plan for you; your plan is unchanged."
            )

        tasks = self._plan_tasks(event.care_plan_id)
        reply = interpret_chat(event.message, self._chat_context(tasks), self._chat)

        if reply.intent == "ASK_FASTING":
            self._bring_fasting_forward(care_plan.patient_id, tasks)
        elif reply.intent == "ASK_REORDER":
            self._bring_fasting_forward(care_plan.patient_id, tasks)  # same safe, legal reorder
        # INFO and REFUSE change nothing.
        return reply

    # ---- internals ---------------------------------------------------------------------------

    def _plan_tasks(self, care_plan_id: UUID) -> list[Task]:
        return self._repo.list(Task, care_plan_id=care_plan_id)

    def _patient_of_task(self, task_id: UUID) -> UUID | None:
        task = self._repo.get(Task, task_id)
        if task is None:
            return None
        care_plan = self._repo.get(CarePlan, task.care_plan_id)
        return care_plan.patient_id if care_plan is not None else None

    def _chat_context(self, tasks: list[Task]) -> dict[str, Any]:
        # Only non-identifying operational context reaches the reasoner (no names, no codes).
        return {
            "pending_steps": sum(
                1 for t in tasks if t.execution_status == ExecutionStatus.PENDING
            ),
            "has_fasting_step": bool(self._fasting_task_ids(tasks)),
        }

    def _fasting_task_ids(self, tasks: list[Task]) -> list[UUID]:
        out: list[UUID] = []
        for task in tasks:
            order = self._repo.get(ServiceOrder, task.service_order_id)
            if order is None:
                continue
            service = self._repo.get(ServiceType, order.service_type_id)
            if service is not None and service.requires_fasting:
                out.append(task.id)
        return out

    def _bring_fasting_forward(self, patient_id: UUID, tasks: list[Task]) -> None:
        for task_id in self._fasting_task_ids(tasks):
            proposal = bring_forward(tasks, task_id)
            if proposal is not None:
                self._apply_and_notify(patient_id, tasks, proposal)
                return

    def _apply_and_notify(
        self, patient_id: UUID, tasks: list[Task], proposal: ResequenceProposal
    ) -> None:
        # Scope-check BEFORE persisting: a reorder is applied only if every task in it belongs to
        # `patient_id`. This raises (and saves nothing) on a mismatch instead of reordering a
        # victim's plan and only failing when `notify` runs its own guard afterwards.
        self._notifier.assert_scope(patient_id, proposal.order)
        for task in apply_order(tasks, proposal.order):
            self._repo.save(task)
        self._notifier.notify(
            patient_id,
            body=f"Your remaining steps were reordered. {proposal.reason}.",
            reason=proposal.reason,
            about_task_ids=proposal.order,
        )
