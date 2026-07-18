---
title: "TASK-028: FR-23 after-each-step rebalance (journey half)"
status: Planned
fr: "FR-23"
owner: journey-dev
deps: "TASK-009, TASK-027, TASK-026, TASK-005"
priority: P1
phase: 2
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-028: FR-23 after-each-step rebalance (journey half)

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree. Read the board row back after writing it.

## Goal

Re-evaluate and rebalance the next journey step after each station completes, using current
per-station waits (FR-23, rebalance side).

## Inputs and context

- Related FR: [FR-23](../../specs/05-functional-requirements.md#fr-23); refines FR-06.
  Spec authored in TASK-026 - BLOCKED until the owner ratifies the v2.0 contract.
- Related files and modules: `src/vaic/agents/journey/` (exclusive owner).
- Consumes the generation contract from TASK-027 and the forecast tool (TASK-005).

## To do

- [ ] On station completion, re-query per-station waits and re-pick the next step (FR-23 rebalance).
- [ ] Emit the resequence as a journey notification; audit-log the change.
- [ ] Tests first (pytest) naming AC-23.x; forecast tool mocked.

## Acceptance criteria

- [ ] Tracks the rebalance-side FR-23 acceptance criteria.
- [ ] Next step is chosen from live queue state after each completion; the change is auditable.

## Decisions and blockers

- Blocker: FR-23 v2.0 contract (TASK-026) is `pending` owner approval; and depends on TASK-027 generation contract.

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator | Created task file: FR-23 rebalance half, split from the TASK-026 spec | Planned |

## Result

<Filled when the task moves to Done.>
