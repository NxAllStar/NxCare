---
title: "TASK-027: FR-23 queue-driven route generation (care-plan half)"
status: Planned
fr: "FR-23"
owner: careplan-dev
deps: "TASK-008, TASK-026, TASK-005"
priority: P1
phase: 2
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-027: FR-23 queue-driven route generation (care-plan half)

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree. Read the board row back after writing it.

## Goal

Generate the care-plan route from current per-station queue waits and mean service time, balancing
load across stations rather than following a fixed schedule (FR-23, generation side).

## Inputs and context

- Related FR: [FR-23](../../specs/05-functional-requirements.md#fr-23) (BR-33..35, AC-23.1..5);
  refines FR-04. Spec authored in TASK-026 - BLOCKED until the owner ratifies the v2.0 contract.
- Related files and modules: `src/vaic/agents/careplan/` (exclusive owner).
- Consumes forecast-dev's `estimate_wait` / `get_queue_state` (TASK-005). `station_wait` is derived
  and transient (`queue_length_paid x avg_service_time`); only PAID tasks count (BR-10).
- Pairs with the rebalance half (TASK-028, journey).

## To do

- [ ] Read per-station queue state via the forecast tool and derive `station_wait`.
- [ ] Generate the initial route by load-balancing across stations (FR-23 generation).
- [ ] Tests first (pytest) naming AC-23.x; forecast tool mocked.

## Acceptance criteria

- [ ] Tracks the generation-side FR-23 acceptance criteria (AC-23.1..5 as applicable).
- [ ] Route is grounded in live queue state, not a fixed order; grounding follows FR-07 (BR-14/15).

## Decisions and blockers

- Blocker: FR-23 v2.0 contract (TASK-026) is `pending` owner approval; do not code against it until ratified.

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator | Created task file: FR-23 generation half, split from the TASK-026 spec | Planned |

## Result

<Filled when the task moves to Done.>
