---
title: "TASK-037: Guard the Action.reasoning free-text field against PII leakage"
status: Planned
fr: "FR-13"
owner: agent-core-dev
deps: "TASK-004, TASK-007"
priority: P2
phase: 2
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-037: Guard the Action.reasoning free-text field against PII leakage

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree. Read the board row back after writing it.

## Goal

`Action.reasoning` is a free-text field written into the audit log. Nothing today stops a caller or
a model from writing patient-identifying text into it, which would then persist in an auditable,
committed-adjacent trail. Add a boundary check (schema constraint, redaction, or an explicit ban on
transcript-shaped content) so the audit log cannot become a PII channel.

## Inputs and context

- Origin: security-reviewer finding (Minor) on TASK-007 - `Action.reasoning` is a free-text PII
  channel; contrast with the `escalate_emergency` schema, which structurally excludes `transcript`
  via `extra=forbid` (D8 in TASK-007).
- Related files: `src/vaic/tools/` (Action schema, audit write path) - agent-core-dev's scope.

## To do

- [ ] Decide the guard shape: structural (schema constraint), redaction, or length/content ban.
- [ ] Apply it at the `Action.reasoning` write boundary, before the audit write.
- [ ] Add a test proving injected PII-shaped text is rejected or redacted, not persisted verbatim.

## Acceptance criteria

- [ ] `Action.reasoning` cannot carry unredacted patient-identifying free text into the audit log.
- [ ] A test proves the guard, not just a docstring note.

## Decisions and blockers

- <decision or blocker>

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator | Registered from TASK-007 review finding (reasoning-PII Minor) during TASK-007 close-out | Planned |

## Result

<Filled when the task moves to Done.>
