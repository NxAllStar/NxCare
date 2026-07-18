---
title: "TASK-029: Console SCR-05 technician task view"
status: Planned
fr: FR-06
owner: frontend-ui-dev
deps: TASK-026
priority: P2
phase: 2
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-029: Console SCR-05 technician task view

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree. Read the board row back after writing it:
a board write can fail silently while the task file lands.

## Goal

Replace the SCR-05 stub with the real technician task view: a queue of tasks assigned to the
signed-in technician, a patient-code scan that moves a task to IN_PROGRESS, and a complete action
that moves it to DONE - on demo mock data inside the console shell.

## Inputs and context

- Related FR: [FR-06](../../specs/05-functional-requirements.md#fr-06) (task status update),
  [FR-17](../../specs/05-functional-requirements.md#fr-17) (patient-code scan)
- Screen spec: [spec 10 SCR-05](../../specs/10-ui-ux-wireframes.md#scr-05-technician-task-view).
  Visible to `technician` only (TASK-026 role->screen contract).
- Access control: [spec 06](../../specs/06-access-control.md) - Own worklist; `LOCKED` tasks are
  hidden and cannot be scanned. Statuses stay English UPPER_SNAKE: `PENDING`, `IN_PROGRESS`, `DONE`,
  `LOCKED` (`.claude/rules/coding-standards.md`, glossary).
- Foundation: `frontend/src/console/` shell + the SCR-05 route/stub from TASK-026.

## To do

- [ ] Console mock-data for the technician queue (synthetic): tasks with patient ref, service, start
      time, execution status; include at least one `LOCKED` task to prove it is hidden. Under
      `src/console/`.
- [ ] Task queue table: Own-worklist tasks only, each showing patient ref, service, start, status
      (StatusChip primitive); `LOCKED` tasks excluded.
- [ ] Patient-code scan control: scanning moves a task `PENDING -> IN_PROGRESS` and emits a mock
      `ScanEvent` (FR-17); a `LOCKED` task cannot be scanned.
- [ ] Complete control: `IN_PROGRESS -> DONE` (FR-06); a completed task leaves the queue.
- [ ] States: empty ("no pending tasks"), loading skeleton, error, success (task done, leaves queue).
      No-permission handled by the TASK-026 route guard.
- [ ] Vitest coverage: LOCKED tasks are not listed and cannot be scanned; scan moves PENDING->
      IN_PROGRESS and emits a ScanEvent; complete moves IN_PROGRESS->DONE and dequeues; empty state
      renders when the queue is empty.

## Acceptance criteria

- [ ] A `technician` reaches SCR-05; other roles cannot (TASK-026 contract) - unchanged.
- [ ] The queue lists only the signed-in technician's own-worklist tasks; `LOCKED` tasks are hidden
      and are not scannable (spec 06, FR-17).
- [ ] Scanning a task moves it `PENDING -> IN_PROGRESS` and records a mock `ScanEvent`; completing a
      task moves it `IN_PROGRESS -> DONE` and removes it from the queue, following the status machine
      in spec 08.
- [ ] Built from shared primitives/tokens (StatusChip, ListRow, a real table primitive); no emoji;
      patient app unaffected. Typecheck + Vitest pass under node v22, recorded in the log.

## Decisions and blockers

- Mock data only; wiring to the real Journey Agent / scan pipeline (TASK-009) is later integration.

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator | Registered (Planned). Sequenced after TASK-028 (shares the console shell; serialize). | Planned |

## Result

<Filled at Done.>
