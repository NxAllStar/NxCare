"""FR-04 task sequencing (BR-07, BR-08, BR-09).

`sequence_orders` turns the doctor's signed `ServiceOrder` list into an ordered list of
`SequencedOrder` - one per input order, always (BR-07: never adds, drops, or re-targets a
service). The Care Plan Agent only optimises HOW that fixed set of steps happens (CO-02).

Sequencing rule (BR-08 - dependency and fasting constraints):

1. Fasting-required orders go first, in the doctor's original relative order (a patient cannot
   safely be routed through a fasting-required step after a step that might break the fast).
2. A fasting order with a turnaround (result wait) opens a "gap" of that many minutes right after
   it. The gap is filled with not-yet-placed, non-fasting orders that individually fit in the
   remaining capacity, tried shortest-duration-first (a greedy bin-fill that maximises how much of
   the unavoidable wait is put to use - this is the "minimise waiting and backtracking" directive
   in FR-04, made concrete). Orders that do not fit fall through to the next gap or the tail.
3. Whatever is left after every gap is filled is appended, in original relative order.

Every duration comes from the injected `DurationEstimator` (BR-09) - this module never guesses one.

Owner resolution (cM4, TASK-008 fix round): `owner_resolver` is called EXACTLY ONCE per order, here,
and the resolved owner is carried on `SequencedOrder.owner_id`. `generate_care_plan` (care_plan.py)
reuses that same value for `Task.owner_id` instead of calling the resolver a second time - with a
stateful or load-balancing resolver, two independent calls can disagree, which would estimate a
duration for one owner and then assign the task to a different one.

Fasting/dependency scope (cM8, cM9 - tracked by TASK-032, not this task): the gap-fill in step 2
below ASSUMES every non-fasting order is safe to interleave during a fasting order's turnaround
wait - there is no `breaks_fasting` attribute on `ServiceType` yet to say otherwise, so this module
cannot currently tell a fast-safe step from one that would break the fast. Likewise, only the
fasting/turnaround constraint is enforced; BR-08's general inter-service dependency ordering (a
step that must follow another for a non-fasting clinical reason) is not modelled here at all. Both
gaps are registered as TASK-032, not fixed in this pass.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from uuid import UUID

from ...models import ServiceOrder, ServiceType
from .durations import DurationEstimator, validate_duration_minutes


@dataclass(frozen=True)
class SequencedOrder:
    """One doctor-signed order, placed and duration-estimated. 1:1 with the input order (BR-07)."""

    order: ServiceOrder
    service_type: ServiceType
    owner_id: UUID  # resolved once here (cM4) - generate_care_plan reuses it, never re-resolves
    duration_min: int
    sequence_index: int


@dataclass(frozen=True)
class _Item:
    original_index: int
    order: ServiceOrder
    service_type: ServiceType
    owner_id: UUID
    duration_min: int


def sequence_orders(
    orders_with_types: list[tuple[ServiceOrder, ServiceType]],
    estimate_duration: DurationEstimator,
    owner_resolver: Callable[[ServiceOrder, ServiceType], UUID],
) -> list[SequencedOrder]:
    """Sequence `orders_with_types` per BR-08. Output length always equals input length (BR-07)."""
    items: list[_Item] = []
    for idx, (order, service_type) in enumerate(orders_with_types):
        owner_id = owner_resolver(order, service_type)  # resolved once (cM4) - see module docstring
        duration_min = validate_duration_minutes(estimate_duration(service_type, owner_id))
        items.append(
            _Item(
                original_index=idx,
                order=order,
                service_type=service_type,
                owner_id=owner_id,
                duration_min=duration_min,
            )
        )

    fasting = [item for item in items if item.service_type.requires_fasting]
    remaining = [item for item in items if not item.service_type.requires_fasting]

    placed: list[_Item] = []
    for gate in fasting:
        placed.append(gate)
        gap = gate.service_type.turnaround_minutes
        if gap <= 0 or not remaining:
            continue
        candidates = sorted(remaining, key=lambda item: (item.duration_min, item.original_index))
        filled: list[_Item] = []
        capacity = gap
        for candidate in candidates:
            if candidate.duration_min <= capacity:
                filled.append(candidate)
                capacity -= candidate.duration_min
        filled_in_original_order = sorted(filled, key=lambda item: item.original_index)
        placed.extend(filled_in_original_order)
        for item in filled_in_original_order:
            remaining.remove(item)

    placed.extend(remaining)  # anything left over, doctor's original relative order

    return [
        SequencedOrder(
            order=item.order,
            service_type=item.service_type,
            owner_id=item.owner_id,
            duration_min=item.duration_min,
            sequence_index=idx,
        )
        for idx, item in enumerate(placed)
    ]
