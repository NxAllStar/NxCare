---
title: "TASK-008: Care Plan + proceed gate + slot allocation"
status: Planned
fr: "FR-03, FR-04, FR-05, FR-08"
owner: careplan-dev
deps: "TASK-004, TASK-006"
priority: P1
phase: 2
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-008: Care Plan + proceed gate + slot allocation

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree. Read the board row back after writing it.

## Goal

Generate and sequence the care-plan task list, gate progress behind the proceed/paid flag, and
allocate station slots. This is the critical-path lane: Journey (TASK-009) and the demo depend on it.

## Inputs and context

- Related FR: [FR-03](../../specs/05-functional-requirements.md#fr-03) (backend capture),
  [FR-04](../../specs/05-functional-requirements.md#fr-04),
  [FR-05](../../specs/05-functional-requirements.md#fr-05),
  [FR-08](../../specs/05-functional-requirements.md#fr-08).
- Related files and modules: `src/vaic/agents/careplan/` (exclusive owner).
- Consumes: agent/tool framework + constraint checker + audit (TASK-004), simulator world (TASK-006).
- FR-23 generation half lands in TASK-027; keep the care-plan interface ready for it.

## To do

- [ ] Diagnosis/order capture backend (FR-03) and care-plan task-list generation + sequencing (FR-04).
- [ ] Proceed gate on the paid flag (FR-05); only PAID tasks advance (BR-10).
- [ ] Slot allocation across stations (FR-08).
- [ ] Tests first (pytest); external providers mocked.

## Acceptance criteria

- [ ] Tracks FR-03/FR-04/FR-05/FR-08 acceptance criteria.
- [ ] Proceed gate blocks unpaid tasks; the gate is audit-logged.
- [ ] Care-plan and slot writes route through the constraint checker.

## Decisions and blockers

- <decision or blocker>

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator | Created task file from template so the Care Plan lane can claim it | Planned |

## Result

<Filled when the task moves to Done.>
