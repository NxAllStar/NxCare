---
title: "TASK-035: Link Appointment to owner/slot for an accurate capacity guard"
status: Planned
fr: "FR-02, FR-08"
owner: data-modeler
deps: "TASK-003, TASK-007"
priority: P2
phase: 2
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-035: Link Appointment to owner/slot for an accurate capacity guard

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree. Read the board row back after writing it.

## Goal

Give `Appointment` a resolvable owner/slot link so intake's `book_appointment` capacity guard counts
booked appointments themselves, not just the owner's Task queue - closing the gap where a booking can
be made while `hour` and the true per-owner appointment load are never checked together.

## Inputs and context

- Origin: code-reviewer finding B1 (Major) on TASK-007 - `book_appointment` guards capacity via
  `owner_queue` (Tasks), while the write it performs (`Appointment`) never enters that queue, so an
  over-capacity booking is reachable (BR-04, BR-16).
- Related files: `src/vaic/models/entities.py` (Appointment), `src/vaic/agents/intake/slots.py` and
  `agent.py` (guard call site, data-modeler does not touch these - intake-dev's scope).

## To do

- [ ] Add the owner/slot link to `Appointment` in the data model.
- [ ] Update the data dictionary in the same change.
- [ ] Hand back to intake-dev to wire the guard to the new link (out of this task's scope).

## Acceptance criteria

- [ ] `Appointment` carries a resolvable owner and slot reference.
- [ ] Data dictionary updated in the same PR as the schema change.

## Decisions and blockers

- <decision or blocker>

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator | Registered from TASK-007 review finding B1 during TASK-007 close-out | Planned |

## Result

<Filled when the task moves to Done.>
