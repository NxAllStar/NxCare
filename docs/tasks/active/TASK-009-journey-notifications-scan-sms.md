---
title: "TASK-009: Journey + notifications + patient-code scan + SMS"
status: Planned
fr: "FR-06, FR-11, FR-15, FR-17"
owner: journey-dev
deps: "TASK-008"
priority: P1
phase: 2
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-009: Journey + notifications + patient-code scan + SMS

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree. Read the board row back after writing it.

## Goal

Per-patient escort through the care-plan journey: timeline notifications, patient-code scan at each
station, and the SMS channel. Blocked on the Care Plan handoff (TASK-008).

## Inputs and context

- Related FR: [FR-06](../../specs/05-functional-requirements.md#fr-06),
  [FR-11](../../specs/05-functional-requirements.md#fr-11),
  [FR-15](../../specs/05-functional-requirements.md#fr-15),
  [FR-17](../../specs/05-functional-requirements.md#fr-17).
- Related files and modules: `src/vaic/agents/journey/` (exclusive owner).
- Depends on the care-plan state object from TASK-008; start on the agreed handoff stub while
  Care Plan is in flight, integrate when it lands.
- FR-23 after-each-step rebalance half lands in TASK-028.

## To do

- [ ] Journey escort + resequencing (FR-06).
- [ ] Timeline notifications (FR-11) and SMS channel (FR-15); providers mocked.
- [ ] Patient-code scan at station arrival (FR-17).
- [ ] Tests first (pytest); a test making a real network call is a defect.

## Acceptance criteria

- [ ] Tracks FR-06/FR-11/FR-15/FR-17 acceptance criteria.
- [ ] Notifications and SMS are logged and auditable; no personal data in logs.
- [ ] Scan advances the journey only for the matching patient.

## Decisions and blockers

- Blocker: needs the care-plan handoff contract from TASK-008 frozen before integration.

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator | Created task file from template so the Journey lane can claim it | Planned |

## Result

<Filled when the task moves to Done.>
