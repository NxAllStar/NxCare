---
title: "TASK-029: Minimal coordinator console (re-plan approval + A/B metrics)"
status: Planned
fr: "FR-09, FR-10, FR-12"
owner: frontend-ui-dev
deps: "TASK-010, TASK-012"
priority: P2
phase: 3
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-029: Minimal coordinator console (re-plan approval + A/B metrics)

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree. Read the board row back after writing it.

## Goal

One coordinator screen that shows a disruption alert, its blast radius, an approve/reject control for
the re-plan (FR-09 human-in-the-loop gate), and the A/B eval metrics panel. Deliberately scoped down
from the superseded full staff suite (TASK-011/014/015) to the demo-critical surface only.

## Inputs and context

- Related FR: [FR-09](../../specs/05-functional-requirements.md#fr-09),
  [FR-10](../../specs/05-functional-requirements.md#fr-10),
  [FR-12](../../specs/05-functional-requirements.md#fr-12).
- Related files and modules: `frontend/src/` (frontend-ui-dev owner). Reuses the design system /
  primitives from TASK-021/025.
- Consumes the Coordinator/Disruption approval gate (TASK-010) and the A/B metrics (TASK-012).

## To do

- [ ] Disruption alert + blast-radius display.
- [ ] Approve/reject re-plan control wired to the FR-09 gate; the decision is audit-logged server-side.
- [ ] A/B metrics panel (wait time, utilisation, ETA MAE) from TASK-012.
- [ ] Vitest + a Playwright smoke for the approve path; providers/data mocked.

## Acceptance criteria

- [ ] A re-plan above the blast-radius threshold surfaces here and cannot execute without an explicit approval.
- [ ] Metrics panel renders the A/B result.
- [ ] Scope holds: no staff worklist/search beyond the approval + metrics surface.

## Decisions and blockers

- DECISION (pending owner confirm): keep a minimal coordinator console in demo scope for the FR-09
  approval story and the A/B metrics, despite the patient-only re-scope of the rest of the frontend.

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator | Created task file: minimal coordinator console for the demo | Planned |

## Result

<Filled when the task moves to Done.>
