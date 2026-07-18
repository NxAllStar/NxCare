"""Retrieve phase of the FR-07 grounding contract.

Deterministic code pulls the observed features from state BEFORE any LLM sees them. These are
data, never model output (see "Grounding contract" step 1 in
docs/specs/05-functional-requirements.md#fr-07).
"""

from __future__ import annotations

from statistics import median
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from ..models import ExecutionStatus, Resource, Task
from ..state import Repository, owner_load_minutes, owner_queue

# Used only when an owner has no completed-task history yet, so a first-ever forecast for a new
# room/owner is still a valid (if wide) band rather than a division-by-zero or an empty range.
DEFAULT_MEDIAN_SERVICE_MINUTES = 15.0


class RetrievedFeatures(BaseModel):
    """The exact observed feature set retrieved for one forecast call (FR-07 step 1)."""

    model_config = ConfigDict(extra="forbid")

    owner_id: UUID
    hour: int = Field(ge=0, le=23)
    queue_length: int = Field(ge=0)
    queue_load_minutes: int = Field(ge=0)
    historical_service_times: list[float]
    median_service_time: float = Field(gt=0)
    resource_available: bool

    def as_prompt_dict(self) -> dict[str, Any]:
        """The feature keys the LLM is given and may cite.

        `cited_features` returned by the LLM must be a subset of these keys - enforced by the
        provenance check in `validate.py`.
        """
        return {
            "queue_length": self.queue_length,
            "queue_load_minutes": self.queue_load_minutes,
            "historical_service_times": self.historical_service_times,
            "median_service_time": self.median_service_time,
            "hour": self.hour,
            "resource_available": self.resource_available,
        }


def retrieve_features(repo: Repository, owner_id: UUID, hour: int) -> RetrievedFeatures:
    """Pull the observed features for `owner_id` at `hour`.

    Queue length and load minutes come from `vaic.state.owner_queue` /
    `owner_load_minutes` (already excludes unpaid/LOCKED tasks per BR-10). Historical
    service-time samples are the durations of that owner's completed tasks. Resource
    availability defaults to True when no matching `Resource` exists, so an unknown owner does
    not silently block a forecast. Deterministic; no model call happens here.
    """
    queue_length = len(owner_queue(repo, owner_id))
    queue_load_minutes = owner_load_minutes(repo, owner_id)

    done = repo.list(Task, owner_id=owner_id, execution_status=ExecutionStatus.DONE)
    historical = [float(t.estimated_duration_min) for t in done if t.estimated_duration_min > 0]
    median_service_time = median(historical) if historical else DEFAULT_MEDIAN_SERVICE_MINUTES

    resource = repo.get(Resource, owner_id)
    resource_available = resource.is_available if resource is not None else True

    return RetrievedFeatures(
        owner_id=owner_id,
        hour=hour,
        queue_length=queue_length,
        queue_load_minutes=queue_load_minutes,
        historical_service_times=historical,
        median_service_time=median_service_time,
        resource_available=resource_available,
    )
