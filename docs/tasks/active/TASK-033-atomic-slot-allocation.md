---
title: "TASK-033: Atomic slot allocation in the state layer"
status: Planned
fr: "FR-08"
owner: data-modeler
deps: "TASK-008"
priority: P2
phase: 3
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-033: Atomic slot allocation in the state layer

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree. Read the board row back after writing it.

## Goal

Make the slot capacity check-and-insert atomic so two concurrent `allocate_slot` calls cannot both
pass the capacity check and both persist, exceeding capacity.

## Inputs and context

- Related FR: [FR-08](../../specs/05-functional-requirements.md#fr-08) (slot allocation, BR-16).
- Origin: TASK-008 review finding code-M2 (TOCTOU). `allocate_slot` reads the clashing/booked slots,
  checks capacity, then saves - not atomic. The in-memory demo store hides it; a durable/Redis store
  (spec OI-15) makes it a real race under concurrent allocation.
- Related files and modules: `src/vaic/state/` (Repository / durable store), `src/vaic/agents/careplan/slots.py`
  (consumer; coordinate with careplan-dev). Tied to the OI-15 durable-store decision.

## To do

- [ ] Provide an atomic check-and-insert primitive in the state layer (e.g. Redis transaction / Lua), or serialize per resource.
- [ ] Have `allocate_slot` use it so capacity cannot be exceeded under concurrency.

## Acceptance criteria

- [ ] Two concurrent allocations for the same resource/hour at capacity cannot both succeed.

## Decisions and blockers

- Raised 2026-07-18 by the TASK-008 review gate; demo-safe today (in-memory store), so P2/phase 3.
  Best resolved together with the OI-15 durable-store choice.

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator | Registered from TASK-008 review finding cM2 | Planned |

## Result

<Filled when the task moves to Done.>
