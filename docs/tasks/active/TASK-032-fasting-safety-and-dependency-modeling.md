---
title: "TASK-032: Model fasting-safety and inter-service dependencies"
status: Planned
fr: "FR-04"
owner: data-modeler
deps: "TASK-003, TASK-008"
priority: P2
phase: 2
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-032: Model fasting-safety and inter-service dependencies

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree. Read the board row back after writing it.

## Goal

Give the data model the fields the care-plan sequencer needs to honor BR-08 fully: a fasting-safety
attribute and inter-service dependency edges, so sequencing never breaks a fast or violates a
clinically required order.

## Inputs and context

- Related FR: [FR-04](../../specs/05-functional-requirements.md#fr-04) (BR-08 dependency + fasting).
- Origin: TASK-008 review findings code-M8 / code-M9. The careplan sequencer currently enforces only
  the fasting/turnaround constraint and assumes every non-fasting step is fast-safe (no
  `breaks_fasting` attribute exists), and it cannot honor inter-service dependencies because
  `ServiceOrder` has no dependency field and `Task.depends_on` is populated nowhere. The BR-08
  "Enforced in" note in `docs/context/business-rules.md` currently overclaims (fasting-only is real).
- Related files and modules: `src/vaic/models/entities.py`, `src/vaic/agents/careplan/sequencing.py`
  (consumer; coordinate with careplan-dev), `docs/specs/08-data-model.md`, `docs/context/business-rules.md`.

## To do

- [ ] Add a fasting-safety attribute (e.g. `breaks_fasting` on `ServiceType`) and dependency edges.
- [ ] Update `docs/specs/08-data-model.md` and `docs/context/business-rules.md` (BR-08 enforced-in) in the same PR.
- [ ] Coordinate with careplan-dev to make the sequencer consume the new fields.

## Acceptance criteria

- [ ] Sequencing never interleaves a fast-breaking step between two fasting orders.
- [ ] Sequencing respects a declared inter-service dependency order.
- [ ] The BR-08 "Enforced in" note reflects reality (no overclaim).

## Decisions and blockers

- Raised 2026-07-18 by the TASK-008 review gate; needs a data-model change so it is not careplan-local.

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator | Registered from TASK-008 review findings cM8/cM9 | Planned |

## Result

<Filled when the task moves to Done.>
