"""Dependency-respecting resequencing (FR-06).

Reordering never crosses a doctor-imposed dependency (BR-13): a task always stays after every task
in its `depends_on`. This is deterministic code, not a model call - the constraint is hard, so an
LLM never decides whether a swap is legal (coding-standards.md). The Journey Agent applies a
proposal only within a single patient's own plan; a reorder that would affect other patients is a
re-plan and routes through the Coordinator/FR-09, not through here.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from ...models import ExecutionStatus, Task


class ResequenceProposal(BaseModel):
    """A proposed new order for a patient's tasks, with a human-readable reason (BR-21)."""

    model_config = ConfigDict(extra="forbid")

    order: list[UUID]  # task ids, in the proposed execution order
    reason: str


def _movable(tasks: list[Task]) -> list[Task]:
    """Tasks that may still be reordered: not yet started, not cancelled.

    DONE/IN_PROGRESS are fixed.
    """
    fixed = (ExecutionStatus.IN_PROGRESS, ExecutionStatus.DONE, ExecutionStatus.CANCELLED)
    return [t for t in tasks if t.execution_status not in fixed]


def is_order_legal(tasks: list[Task], order: list[UUID]) -> bool:
    """True if `order` places every task after all of its `depends_on` (BR-13).

    `order` must be a permutation of the ids of the movable tasks. Dependencies on tasks outside
    `order` (already done/in progress) are treated as already satisfied.
    """
    ids = {t.id for t in tasks}
    order_ids = set(order)
    if order_ids - ids:  # references a task that is not in this plan
        return False
    by_id = {t.id: t for t in tasks if t.id in order_ids}
    if set(by_id) != order_ids or len(order) != len(order_ids):  # not a permutation of movables
        return False
    position = {task_id: i for i, task_id in enumerate(order)}
    for task_id in order:
        for dep in by_id[task_id].depends_on:
            if dep in position and position[dep] > position[task_id]:
                return False  # a dependency scheduled after its dependant - illegal
    return True


def bring_forward(tasks: list[Task], target_id: UUID) -> ResequenceProposal | None:
    """Move `target_id` as early as its dependencies allow, keeping the rest in order (AC-06.2).

    Returns None if the target is unknown, not movable, or already as early as it can legally be.
    """
    movable = _movable(tasks)
    ids = [t.id for t in movable]
    if target_id not in ids:
        return None

    by_id = {t.id: t for t in movable}
    current = sorted(movable, key=lambda t: t.sequence_index)
    current_ids = [t.id for t in current]

    deps = set(by_id[target_id].depends_on) & set(ids)
    # Earliest legal slot: right after the last of its in-plan dependencies.
    earliest = 0
    for i, task_id in enumerate(current_ids):
        if task_id in deps:
            earliest = i + 1

    without = [tid for tid in current_ids if tid != target_id]
    new_order = without[:earliest] + [target_id] + without[earliest:]
    if new_order == current_ids or not is_order_legal(tasks, new_order):
        return None
    return ResequenceProposal(
        order=new_order,
        reason=f"brought a required earlier step forward to position {earliest + 1}",
    )


def propose_resequence(tasks: list[Task], etas: dict[UUID, int]) -> ResequenceProposal | None:
    """Propose swapping the next step ahead when its ETA has spiked (AC-06.1).

    If the first movable task's ETA is higher than a later movable task whose dependencies are
    already met, and moving that later task ahead is legal, propose the swap. Returns None when no
    beneficial, dependency-legal swap exists (on failure the agent holds the current order).
    """
    movable = sorted(_movable(tasks), key=lambda t: t.sequence_index)
    if len(movable) < 2:
        return None
    order_ids = [t.id for t in movable]
    head = movable[0]
    head_eta = etas.get(head.id, head.estimated_duration_min)

    for candidate in movable[1:]:
        cand_eta = etas.get(candidate.id, candidate.estimated_duration_min)
        if cand_eta >= head_eta:
            continue  # only move a genuinely faster next step ahead
        deps_in_plan = set(candidate.depends_on) & set(order_ids)
        if deps_in_plan:
            continue  # cannot jump ahead of unmet, in-plan dependencies
        new_order = [candidate.id] + [tid for tid in order_ids if tid != candidate.id]
        if is_order_legal(tasks, new_order):
            return ResequenceProposal(
                order=new_order,
                reason=(
                    f"next step's wait rose to about {head_eta} min; a ready step with about "
                    f"{cand_eta} min was moved ahead to reduce your total wait"
                ),
            )
    return None


def apply_order(tasks: list[Task], order: list[UUID]) -> list[Task]:
    """Return the tasks with `sequence_index` renumbered to match `order`.

    0-based, order-preserving.

    Tasks not in `order` (fixed: in-progress/done/cancelled) keep their relative position ahead of
    the reordered movable tasks. Callers persist the returned tasks; this function mutates copies'
    fields but returns them for an explicit save (state.memory stores deep copies).
    """
    rank = {task_id: i for i, task_id in enumerate(order)}
    out: list[Task] = []
    for task in tasks:
        if task.id in rank:
            task.sequence_index = rank[task.id]
        out.append(task)
    return out
