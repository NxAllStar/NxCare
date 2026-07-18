---
title: "TASK-018: Spec FR-23 dynamic queue-driven load-balanced routing"
status: Active
fr: FR-23
owner: ba-analyst
deps: -
priority: P1
phase: 2
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-018: Spec FR-23 dynamic queue-driven load-balanced routing

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree.

## Goal

Capture, in the spec, that the patient's care-plan route is generated and continuously re-balanced
from real per-station queue waits (dynamic, demand-driven), not a fixed schedule.

## Inputs and context

- Related FR: [FR-23](../../specs/05-functional-requirements.md#fr-23) (new); refines
  [FR-04](../../specs/05-functional-requirements.md#fr-04),
  [FR-06](../../specs/05-functional-requirements.md#fr-06),
  [FR-07](../../specs/05-functional-requirements.md#fr-07).
- Related flow: [BF-03](../../specs/04-business-flows.md).
- Owner request (this session): each station has a ticket queue (assume N patients waiting) ->
  per-station waiting time; route generation uses current per-station waits + mean service time to
  balance load; re-evaluate the next step after each station completes. Consult routing (FR-02)
  explicitly out of scope for this task.

## To do

- [x] Add FR-23 (description, I/O, model-vs-human, BR-33..35, AC-23.1..5, dependencies).
- [x] Summary-table row, US-22, UC-03 serves, traceability row.
- [x] Related links from FR-04, FR-06, FR-07.
- [x] Sharpen BF-03 (mermaid B and M nodes; steps 2 and 5).
- [x] Revision history: v2.0 row, changes-by-section, lifecycle row.
- [ ] Owner review/approval of the v2.0 contract change (Approved-by is `pending`).
- [ ] Downstream: when FR-23 is implemented, owning dev seats are careplan-dev (generation) and
      journey-dev (after-each-step rebalance), consuming forecast-dev's `estimate_wait`/`get_queue_state`.

## Acceptance criteria

- [ ] Tracks FR-23 AC-23.1..AC-23.5 once implemented (spec-only task delivers the contract; code lands
      under the care-plan/journey/forecast tasks).
- [x] Spec set is internally consistent: FR-23 cross-referenced from the summary table, UC-03, US-22,
      traceability matrix, BF-03, and the revision history.

## Decisions and blockers

- Decision: one new dedicated FR (FR-23) rather than amending FR-04/06/07 in place - owner chose the
  single-home form for demo/judging visibility; existing FRs carry Related links.
- Decision: scope limited to the care-plan station journey; consult-slot routing (FR-02) deferred.
- Decision: no data-model change - `station_wait` is a derived, transient quantity
  (`queue_length_paid × avg_service_time`), consistent with FR-07 being transient. Grounded via
  FR-07's contract (BR-14/15); only PAID tasks count (BR-10).
- Blocker: v2.0 is a contract move; Approved-by is `pending` in 13-revision-history.md until the
  owner signs off.

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | ba-analyst (via Claude Code) | Added FR-23 + BR-33..35 + US-22 + traceability; Related links on FR-04/06/07; sharpened BF-03; revision history v2.0 | Spec drafted; internally consistent; awaiting owner approval |

## Result

<Filled when the task moves to Done: owner approval of v2.0 and the merge/PR reference.>
