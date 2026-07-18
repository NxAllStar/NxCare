"""Least-crowded consult-slot recommendation (FR-02).

`recommend_slots` is a pure query: it never mutates state and never touches the audit log - "no
slots available today" is a valid empty result (AC-02.2), not a denial (D10). Every ETA comes only
from the forecast tool's `estimate_wait` (BR-03): this module never computes or invents a number.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from ...forecast import ForecastLLM, estimate_wait
from ...models import Resource
from ...state import Repository, owner_queue


class SlotProposal(BaseModel):
    model_config = ConfigDict(extra="forbid")

    owner_id: UUID
    hour: int
    eta_minutes: float
    source: str
    confidence: float


def _has_room(repo: Repository, resource: Resource) -> bool:
    """BR-04: an owner with a configured hourly capacity already met/exceeded by its queue has no
    room left; an owner with no configured capacity is treated as uncapped.

    Limitation (B1, tracked as a cross-lane follow-up, not fixed here): this counts the owner's
    Task queue (`owner_queue`), not booked Appointments - `Appointment` has no owner_id/slot link in
    the current entity shape (data-model gap, spec 08-data-model.md), so a confirmed booking never
    enters this count. This reflects Task-driven capacity only, not full per-owner-per-hour
    appointment capacity; see the matching comment in `agent.py`'s `_book_appointment` guard.
    """
    if resource.capacity_per_hour is None:
        return True
    return len(owner_queue(repo, resource.id)) < resource.capacity_per_hour


def recommend_slots(
    repo: Repository,
    specialty: str,
    candidate_owner_ids: list[UUID],
    hours: list[int],
    llm: ForecastLLM,
) -> list[SlotProposal]:
    """Rank candidate owners (Resources) by grounded ETA, least-crowded first (AC-02.1).

    `specialty` is carried through for traceability only: the caller (Care Plan lane, per D4) has
    already mapped specialty -> `candidate_owner_ids`; this function does not re-derive specialty
    from a `Resource` because `Resource` carries no specialty field.

    Drops any candidate whose `Resource` is unavailable or at/over capacity (BR-04); returns `[]`
    when no candidate qualifies (AC-02.2), which is a normal empty result, not an error.
    """
    del specialty  # reserved for the caller-side specialty -> owner mapping (D4); unused here
    proposals: list[SlotProposal] = []
    for owner_id in candidate_owner_ids:
        resource = repo.get(Resource, owner_id)
        if resource is None or not resource.is_available:
            continue
        if not _has_room(repo, resource):
            continue
        for hour in hours:
            forecast = estimate_wait(repo, owner_id, hour, llm)  # BR-03: only source of a number
            proposals.append(
                SlotProposal(
                    owner_id=owner_id,
                    hour=hour,
                    eta_minutes=forecast.value,
                    source=forecast.source,
                    confidence=forecast.confidence,
                )
            )

    return sorted(proposals, key=lambda proposal: proposal.eta_minutes)
