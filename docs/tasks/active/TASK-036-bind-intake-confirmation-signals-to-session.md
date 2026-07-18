---
title: "TASK-036: Bind intake staff_confirmed/emergency_suspected to the authenticated session"
status: Planned
fr: "FR-18"
owner: agent-core-dev
deps: "TASK-013, TASK-007, TASK-034"
priority: P2
phase: 2
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-036: Bind intake staff_confirmed/emergency_suspected to the authenticated session

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree. Read the board row back after writing it.

## Goal

`book_appointment`'s `staff_confirmed` and `emergency_suspected` are today caller-supplied booleans,
not bound to an authenticated coordinator or to the triage result. Derive them from the FR-18 session
and the stored triage output instead of trusting `Action.params`, the same authenticated-principal
pattern TASK-034 applies to the care-plan/executor/checker gate.

## Inputs and context

- Origin: security-reviewer finding B2 (Major) on TASK-007.
- Related: [[TASK-034]] applies the equivalent fix to the care-plan gate; do this in the same pattern.
- Related files: `src/vaic/agents/intake/agent.py` (intake-dev's scope - this task edits the auth
  binding surface only, coordinate the call-site change with intake-dev).

## To do

- [ ] Derive `staff_confirmed` from the authenticated session identity, not a caller-supplied flag.
- [ ] Derive `emergency_suspected` from the stored triage result, not a caller-supplied flag.
- [ ] Coordinate the intake-side call-site change with intake-dev.

## Acceptance criteria

- [ ] `book_appointment` no longer trusts `Action.params` for either signal.
- [ ] A test proves a forged `staff_confirmed=true` from an unauthenticated/wrong-role caller is
  rejected.

## Decisions and blockers

- <decision or blocker>

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator | Registered from TASK-007 review finding B2 during TASK-007 close-out | Planned |

## Result

<Filled when the task moves to Done.>
