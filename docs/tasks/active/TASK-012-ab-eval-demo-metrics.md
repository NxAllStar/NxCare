---
title: "TASK-012: A/B eval vs FIFO baseline + demo script + metrics"
status: Planned
fr: "-"
owner: simulator-dev
deps: "TASK-010"
priority: P2
phase: 3
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-012: A/B eval vs FIFO baseline + demo script + metrics

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree. Read the board row back after writing it.

## Goal

Run the agent-driven pipeline against a FIFO baseline in the SimPy world, report the metrics (wait
time, utilisation, ETA MAE), and produce the demo script.

## Inputs and context

- Related files and modules: `src/vaic/simulator/` (exclusive owner). Builds on the world + metrics
  harness (TASK-006).
- Depends on the agents being online: Coordinator/Disruption (TASK-010), and the intake/care-plan/
  journey lanes. Scaffold the A/B harness + metrics against mock agents in Wave 1; wire real agents
  as they land. Note: original frontend dep (TASK-011) is superseded by the patient app + TASK-029.
- Feeds the coordinator console metrics panel (TASK-029) and the `judge` evaluation.

## To do

- [ ] A/B harness: agent pipeline vs FIFO baseline on the same seeded world.
- [ ] Metrics: mean wait time, station utilisation, ETA MAE; recorded per run.
- [ ] Frozen, versioned eval case set including the known-hard cases and a safety slice
      (injection, refusal, past-wrong-answer inputs) per `.claude/rules/ai-governance.md`.
- [ ] Demo script: the click-through that shows the win.

## Acceptance criteria

- [ ] A/B run reproducible from a committed seed; results recorded in this task file.
- [ ] Agent pipeline beats FIFO on the headline metric, or the gap is explained.
- [ ] A regression on the safety slice blocks the result, whatever the average did.

## Decisions and blockers

- <decision or blocker>

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator | Created task file from template so the Simulator/Eval lane can claim it | Planned |

## Result

<Filled when the task moves to Done.>
