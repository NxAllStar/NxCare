"""The events the Journey Agent is woken by (BR-12: event-driven, no polling loop).

The care-plan handover is the frozen integration point with the Care Plan Agent (TASK-008). The
Journey Agent holds no care-plan state of its own; it is handed a `care_plan_id` and reads the
`CarePlan` and its `Task` list from the shared repository (the entity contract in
`vaic.models.entities`). When TASK-008 lands, the Care Plan Agent emits `JourneyHandover`; until
then the same event is constructed directly in tests and the run harness.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class JourneyHandover(BaseModel):
    """Care Plan Agent -> Journey Agent handover (FR-06 trigger).

    Carries only identifiers; the Journey Agent reads the care plan and its tasks from state so the
    two agents never share mutable objects across a boundary.
    """

    model_config = ConfigDict(extra="forbid")

    care_plan_id: UUID


class EtaUpdate(BaseModel):
    """A change in one or more per-task ETAs (minutes), from the forecast tool (FR-07).

    `etas` maps a `Task.id` to its current estimated wait in minutes. The Journey Agent reacts by
    proposing a dependency-legal reorder when a next step's ETA spikes (FR-06 AC-06.1).
    """

    model_config = ConfigDict(extra="forbid")

    care_plan_id: UUID
    etas: dict[UUID, int]


class PatientChat(BaseModel):
    """An inbound patient chat message. The `message` is untrusted DATA, never an instruction.

    See `.claude/rules/agent-guardrails.md` (Untrusted data is data) and FR-06 AC-06.3.
    """

    model_config = ConfigDict(extra="forbid")

    care_plan_id: UUID
    patient_id: UUID
    message: str
