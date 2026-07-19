---
title: "TASK-027: FR-23 queue-driven route generation (care-plan half)"
status: Active
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

- [x] Generate the initial route by load-balancing across stations (`agents/careplan/routing.py`:
      `queue_aware_candidates_for`, `least_loaded_owner_resolver`) - ranks by `owner_load_minutes`
      (paid, unfinished tasks only, BR-10/BR-35), never a fixed order.
- [x] Doctor-facing HTTP entry point (`POST /api/careplan/generate`, `api/careplan_routes.py`):
      resolves the doctor's raw test-name list to seeded `ServiceType`s, captures the
      diagnosis/orders, and drives `generate_care_plan` with the queue-aware seam above.
- [x] Tests first (pytest): `tests/test_careplan_routing.py` (unit, 8 tests) and
      `tests/test_careplan_routes.py` (route-level, 4 tests) - AC-23.2/AC-23.5 named explicitly.
- [ ] Read per-station queue state via the forecast tool's `estimate_wait()`/grounding contract
      (BR-33/BR-35's literal `station_wait`) - current ranking uses `owner_load_minutes` (sum of
      `estimated_duration_min` already queued) as a same-spirit proxy, not a call through FR-07's
      grounding contract. Closing AC-23.1 (a single per-station wait view) needs this.
- [ ] `parallel_eligible` marking (BR-34/AC-23.3) - not modeled at all yet; every task is still
      sequenced strictly one-after-another, never marked parallelizable.
- [ ] Full BR-08 dependency enforcement (AC-23.4) beyond the existing fasting/turnaround check -
      blocked on TASK-032 (no `breaks_fasting`/dependency-edge fields exist on `ServiceType`/`Task`
      yet); today's queue preference can only ever be constrained by the fasting-only subset of
      BR-08 that `sequencing.py` already enforces.

## Acceptance criteria

- [x] AC-23.2: among BR-08-eligible next steps, the shorter-load station is offered first.
- [x] AC-23.5: an UNPAID/LOCKED task never influences the route recommendation.
- [ ] AC-23.1: a single view exposing every relevant station's wait - not built (no dedicated
      response field surfaces `station_wait` itself, only the resulting route).
- [ ] AC-23.3: parallel_eligible marking - not built.
- [ ] AC-23.4: queue preference never overrides a BR-08 dependency - only as strong as the
      fasting-only BR-08 enforcement that exists today (TASK-032 gap).
- [x] Route is grounded in live queue state (`owner_load_minutes`), not a fixed order; the FR-07
      grounding contract itself (`estimate_wait`) is not yet in this path - see the `station_wait`
      to-do above.

## Decisions and blockers

- Blocker: FR-23 v2.0 contract (TASK-026) is `pending` owner approval; do not code against it until ratified.
- Resolved: TASK-026 landed and was approved as v2.3 on 2026-07-18; this task was unblocked and
  partially implemented in the same session (see session log). Remaining scope (AC-23.1, AC-23.3,
  full AC-23.4) is left open, not silently dropped - see the To do / Acceptance criteria gaps above.
- New follow-up, not yet a numbered task: ground `station_wait` through `estimate_wait()`/FR-07
  instead of the `owner_load_minutes` proxy, and add `parallel_eligible` marking (BR-34). Both
  need an owner decision on whether they land under TASK-027 (reopened) or a new task.

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator | Created task file: FR-23 generation half, split from the TASK-026 spec | Planned |
| 2026-07-18 | careplan-dev (via Claude Code) | Synced real `ServiceType` config from Postgres into the runtime repo (`api/demo_state.py`); built `agents/careplan/routing.py` (name resolution, config-driven duration, queue-aware station ranking) and `POST /api/careplan/generate`; 12 new tests, full suite green (180 passed), ruff clean | AC-23.2/AC-23.5 covered; AC-23.1/AC-23.3/full AC-23.4 remain open (see To do) |

## Result

Partial: queue-driven station preference (AC-23.2, AC-23.5) is implemented and tested end-to-end
from a doctor-facing HTTP endpoint through to a slotted, ACTIVE `CarePlan`. Not yet done: a
dedicated per-station wait view (AC-23.1), `parallel_eligible` marking (AC-23.3, BR-34), and full
BR-08 dependency enforcement beyond fasting (AC-23.4, blocked on TASK-032). Left `Active`, not
`Done`, until an owner decides whether the remaining scope stays under this task or splits out.
