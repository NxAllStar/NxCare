"""FR-23 (v2.3): queue-driven route generation - the doctor-facing seam for `generate_care_plan`.

The doctor's input is a plain list of test names (`list[str]`, exactly how the FE form collects
them - see `orders.py` module docstring for why the ID-based `service_type_ids` input further down
the pipeline cannot take that shape directly). This module is the one place that:

1. Resolves each name to a seeded `ServiceType` (`resolve_service_types`) - BR-07 in reverse: a name
   that does not resolve must never be silently dropped, so the caller decides whether to fail the
   whole request rather than record a doctor-ordered test as something it was not.
2. Reads each test's duration from the `ServiceType.default_duration_min` config field
   (`default_duration_estimator`) - the BR-09 seam `durations.DurationEstimator` already defines;
   this is the concrete average-duration source until a forecast-grounded adapter replaces it.
3. Ranks candidate stations by CURRENT load - `owner_queue`/`owner_load_minutes` already encode
   "how many patients are ahead and how long that queue runs" (BR-10: only paid, not-yet-finished
   tasks count) - so a task is routed to whichever qualifying station is least busy right now
   (`queue_aware_candidates_for`, `least_loaded_owner_resolver`).

No function here invents a service, a duration, or a queue length: durations come from the
`ServiceType` config row exactly as stored, and load comes from `owner_queue`/`owner_load_minutes`
exactly as `state/repository.py` already computes it for FR-08's capacity guard.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from ...models import Resource, ServiceType
from ...state import Repository, owner_load_minutes, owner_queue
from .slots import SlotCandidate


@dataclass(frozen=True)
class ServiceTypeResolution:
    """The outcome of resolving the doctor's raw test names against the `ServiceType` catalog."""

    resolved: list[ServiceType]  # in the same order as the input names that matched
    unmatched: list[str]  # raw names with no matching ServiceType - never silently dropped

    @property
    def ok(self) -> bool:
        return not self.unmatched


def _catalog_index(repo: Repository) -> dict[str, ServiceType]:
    """Case-insensitive lookup by `code` or `display_label`, last-write-wins on a collision."""
    index: dict[str, ServiceType] = {}
    for service_type in repo.list(ServiceType):
        index[service_type.code.strip().lower()] = service_type
        index[service_type.display_label.strip().lower()] = service_type
    return index


def resolve_service_types(repo: Repository, names: Iterable[str]) -> ServiceTypeResolution:
    """Resolve the doctor's raw test names to seeded `ServiceType`s (config rows, OI-15).

    A name is matched case-insensitively against either a `ServiceType.code` or its
    `display_label` (whichever the FE happened to send). Order of `resolved` follows the order of
    `names` for the names that matched; unmatched names are reported, never guessed at or dropped.
    """
    index = _catalog_index(repo)
    resolved: list[ServiceType] = []
    unmatched: list[str] = []
    for name in names:
        service_type = index.get(name.strip().lower())
        if service_type is None:
            unmatched.append(name)
        else:
            resolved.append(service_type)
    return ServiceTypeResolution(resolved=resolved, unmatched=unmatched)


def default_duration_estimator(service_type: ServiceType, owner_id: UUID) -> int:
    """BR-09 `DurationEstimator`: the test's configured average duration (`default_duration_min`).

    `owner_id` is accepted only to match the `DurationEstimator` protocol shape (`durations.py`) -
    the config value is per-`ServiceType`, not per-station, until a forecast-grounded adapter (a
    real per-station estimate) replaces this.
    """
    del owner_id
    return service_type.default_duration_min


def _available_candidates(repo: Repository, candidate_owner_ids: Iterable[UUID]) -> list[UUID]:
    """Candidate owners that are open and not yet at/over their hourly capacity (BR-04, BR-16)."""
    qualifying: list[UUID] = []
    for owner_id in candidate_owner_ids:
        resource = repo.get(Resource, owner_id)
        if resource is None or not resource.is_available:
            continue
        if resource.capacity_per_hour is not None:
            if len(owner_queue(repo, owner_id)) >= resource.capacity_per_hour:
                continue
        qualifying.append(owner_id)
    return qualifying


def least_loaded_owner_resolver(
    repo: Repository, candidate_owner_ids: list[UUID]
) -> Callable[[object, ServiceType], UUID]:
    """Build an `owner_resolver` (sequencing.py) that picks the candidate with the least current
    queued minutes (`owner_load_minutes`) - "AI checks the queue and picks the least busy station".

    Falls back to the full candidate list (ignoring availability) only if none currently qualify,
    so `sequence_orders` always gets an owner_id to estimate a duration against; `candidates_for`
    below is what actually decides whether a booking succeeds.
    """

    def resolver(order: object, service_type: ServiceType) -> UUID:
        del order, service_type
        qualifying = _available_candidates(repo, candidate_owner_ids) or list(candidate_owner_ids)
        return min(qualifying, key=lambda owner_id: owner_load_minutes(repo, owner_id))

    return resolver


def queue_aware_candidates_for(
    repo: Repository,
    candidate_owner_ids: list[UUID],
    hours: list[int],
    reference_date: datetime,
) -> Callable[[object, object], list[SlotCandidate]]:
    """Build a `candidates_for` (care_plan.py) that offers qualifying stations least-busy-first.

    Ranked once per call by current `owner_load_minutes` (total queued minutes, BR-10: unpaid tasks
    never count) - the station carrying the least real, currently-paid load is tried first, across
    `hours` from `reference_date`. A station at/over its hourly capacity or closed is never offered
    (BR-04/BR-16 already gate this in `_available_candidates`); `allocate_task_slot` (slots.py)
    still re-checks capacity/clash at write time and falls through on rejection.
    """

    def candidates_for(task: object, seq: object) -> list[SlotCandidate]:
        del task, seq
        qualifying = _available_candidates(repo, candidate_owner_ids)
        ranked = sorted(qualifying, key=lambda owner_id: owner_load_minutes(repo, owner_id))
        return [
            SlotCandidate(resource_id=owner_id, start=reference_date + timedelta(hours=hour))
            for owner_id in ranked
            for hour in hours
        ]

    return candidates_for
