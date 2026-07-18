"""BR-09 seam: a task's duration MUST come from the Forecast tool, never a guessed constant.

`DurationEstimator` is a plain, structurally-typed callable so this package never imports
`vaic.forecast` directly - FR-07 is forecast-dev's module (see AGENTS.md routing table), and this
agent only owns FR-03/04/05/08. The seam keeps BR-09 honest: every duration used by
`sequence_orders` / `generate_care_plan` is injected, so a test can prove "the sequencer never
invents a number" by asserting it only ever sees what the injected estimator returned.

Real wiring (left for forecast-dev or a later integration task) is an adapter shaped like:

    def forecast_duration_estimator(repo, hour, llm):
        def estimate(service_type: ServiceType, owner_id: UUID) -> int:
            result = estimate_wait(repo, owner_id, hour, llm)  # vaic.forecast.tool.estimate_wait
            return round(result.value)
        return estimate

`estimate_wait` already returns a grounded, range-validated figure (FR-07); this module only
defines the shape a caller must satisfy to plug one in.
"""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from ...models import ServiceType


class DurationEstimator(Protocol):
    """Callable: `(service_type, owner_id) -> estimated duration in whole minutes`.

    Tests inject a deterministic fake (a plain function or lambda) - never a real model or network
    call (testing.md "mock every external provider").
    """

    def __call__(self, service_type: ServiceType, owner_id: UUID) -> int: ...


# BR-14 / NFR-SEC-20: a "grounded" forecast is still an external number. A cheap local sanity bound
# at every point of use (sequencing.py, slots.py) stops a bad estimator return from ever producing
# an inverted or day-spanning Slot window - review sec-m1, TASK-008 fix round.
MIN_DURATION_MIN = 1
MAX_DURATION_MIN = 24 * 60  # one day: generous, but a single service step past this is bad data


def validate_duration_minutes(value: int) -> int:
    """Range-guard a duration in minutes; returns it unchanged, or raises `ValueError`.

    Callers convert the `ValueError` to whatever failure shape fits their layer (a `ToolError` in
    slots.py's handler, a bare raise pre-persistence in sequencing.py) - this function only
    encodes the bound itself, once, so the two call sites cannot silently drift apart.
    """
    if value < MIN_DURATION_MIN or value > MAX_DURATION_MIN:
        raise ValueError(
            f"estimated duration {value} minutes is out of range "
            f"({MIN_DURATION_MIN}..{MAX_DURATION_MIN}) - BR-14 / NFR-SEC-20"
        )
    return value
