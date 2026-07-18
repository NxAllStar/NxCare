---
title: "Execution plan - 5-6 person parallel build"
---

# Execution plan - 5-6 person parallel build

<!-- Written 100% in English (see .claude/rules/task-tracking.md). -->

Coordination companion to `master-plan.md`. The board and the individual task files remain the
source of truth for state; this file only assigns lanes and orders the waves so multiple people can
work Claude Code against this repo without colliding. When this file and the board disagree, the
board wins.

## The model: one person owns one module

The repo avoids merge conflicts by giving each module a single owner (the routing table in
`AGENTS.md`). We map each person to one module lane; branches then never touch the same source files.
`master-plan.md` is the one shared file everyone edits (one row each) - resolve its conflicts by
keeping BOTH rows, never one side.

## Lanes

| Lane | Owner module (exclusive) | Tasks |
|------|--------------------------|-------|
| 1 Intake | `src/vaic/agents/intake/` | TASK-007 |
| 2 Care Plan (critical path) | `src/vaic/agents/careplan/` | TASK-008, then TASK-027 (FR-23 generation) |
| 3 Journey | `src/vaic/agents/journey/` | TASK-009, then TASK-028 (FR-23 rebalance) |
| 4 Coordinator/Disruption | `src/vaic/agents/core/` | TASK-010 |
| 5 Simulator/Eval | `src/vaic/simulator/` | TASK-012 (harness prep now, wire agents as they land) |
| 6 Frontend + QA/integration | `frontend/src/`, `tests/`, `e2e/` | TASK-024, TASK-029, live-API wiring |
| Lead (part-time) | approvals + merges (`docs/`, board) | TASK-002 governance, TASK-026 approval, TASK-016, serialise merges |

Data-model changes (TASK-016) are data-modeler's schema seat - land it in Wave 1 because every lane
reads those entities. The lead or lane 5 can carry it if no separate data person exists.

## Critical path

Care Plan (TASK-008) -> Journey (TASK-009) -> Eval/demo (TASK-012). Care Plan is the bottleneck:
Journey and the demo both wait on it, and it carries the FR-23 generation half. Give it the strongest
person and unblock it first.

## Day-0 contract freeze (before any agent code)

Integration pain in a multi-agent system is the handoffs. In one short session with all lanes present,
freeze these and write down the signatures:

1. Patient/journey state object (`src/vaic/state/`, `src/vaic/models/`) - the shape intake -> care
   plan -> journey pass along. Mostly exists from TASK-003; confirm and freeze.
2. Forecast tool signatures `estimate_wait` / `get_queue_state` (TASK-005) - every lane consumes them.
3. Constraint checker + audit interface (TASK-004) - every consequential write routes through it.
4. FR-23 `station_wait` derivation (`queue_length_paid x avg_service_time`, PAID-only, BR-10) -
   requires the lead to ratify the TASK-026 v2.0 spec first. No FR-23 code before that sign-off.

## Waves

Wave 1 (fully parallel, no cross-deps): TASK-007, TASK-008, TASK-010, TASK-012 (harness scaffold
against mock agents), TASK-024. Lead: TASK-002, TASK-026 approval, TASK-016.

Wave 2: TASK-009 (integrates on the landed Care Plan), TASK-027 + TASK-028 (FR-23), and frontend
wires the patient app to live agent APIs (replacing the mock-data layer).

Wave 3: end-to-end run in the simulator, TASK-012 A/B eval vs FIFO, demo script, TASK-029 coordinator
console, final `code-reviewer` + `security-reviewer` + `/secret-scan` on the full diff.

## Coordination discipline (from `.claude/rules/`)

- Claim before start: set owner + `Active` on the board row AND the task file together, then re-read
  the row. Never start a task someone else holds `Active`.
- Branch per task; Conventional Commits; never commit to `main`.
- One PR merged at a time, recomputed against the current `main` tip; the author never merges their
  own change; inspect with `git diff main...<branch>` (three dots).
- Session-log every gate run in the task file - a gate is "passed" only when logged.
- The standard feature flow per lane: `spec-guardian` locks scope -> implement test-first ->
  `qa-test` -> `code-reviewer` + `security-reviewer` in parallel -> `/secret-scan` -> PR. Run it with
  `/implement-fr FR-NN`.
- Daily (or twice-daily) standup around the board given the hackathon timeline.
