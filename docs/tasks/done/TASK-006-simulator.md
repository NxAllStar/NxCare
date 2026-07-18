---
title: "TASK-006: SimPy simulator world + synthetic seed + metrics harness"
status: Done
fr: "-"
owner: simulator-dev
deps: TASK-003
priority: P0
phase: 1
created: 2026-07-18
tags: [task]
---

# TASK-006: SimPy simulator world + synthetic seed + metrics harness

## Goal

Build the SimPy "world" the agents run in and are evaluated against: synthetic patient arrivals,
rooms/equipment, disruption events; a deterministic seed; and the eval harness that runs an
agent-orchestrated cohort against a FIFO baseline on the same seeded patients, reporting metrics
(average wait time, congestion/peak load, room-equipment utilisation, ETA MAE).

## Inputs and context

- `docs/specs/12-technical-feasibility.md` (technical approach), `01` success metrics, AS-04 (~50-100
  patients). Builds on TASK-003 (models/state). Owns `src/vaic/simulator/`.

## Acceptance criteria

- [x] Deterministic by seed: the same seed reproduces the same run and metrics (BR-15, NFR-REL-05).
- [x] Generates ~50-100 synthetic patients, rooms/equipment, and injectable disruption events.
- [x] Runs A/B (a simple policy vs FIFO baseline) on the same cohort and computes the four metrics.
- [x] Synthetic data only; no real patient data. Tests + ruff green.

<!-- Coordinate: the agent-orchestrated policy will later plug in the real agents (Phase 2). For now a
     minimal policy hook is enough so the harness and metrics exist and are testable. -->

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | simulator-dev | Built `src/vaic/simulator/` (SimPy world, FIFO/load-aware policies, disruption injection, metrics, A/B harness, CLI); added `tests/test_simulator.py` (12 tests, TDD). Added `simpy>=4.1` (MIT, permissive) to pyproject deps. | `pytest`: 52 passed. `ruff`: clean. |
| 2026-07-18 | orchestrator | Verified gates independently; found the documented CLI failed without the package installed; fixed via `pip install -e .`; confirmed deterministic identical output across two runs (seed 42) | verified -> Done |

## Result

Delivered `src/vaic/simulator/`: a deterministic SimPy world (seeded cohort ~80 patients, rooms +
scarce shared equipment, injectable disruptions), a `SchedulingPolicy` ABC (Phase-2 plug point for
the real agents) with FIFO and load-aware policies, metrics (avg wait, peak load/area, room +
equipment utilisation, ETA MAE), an A/B harness on the same seeded cohort, and a CLI
(`python -m vaic.simulator.run --seed 42 --patients 80`). 12 new tests (52 total), ruff clean.
Orchestrator-verified: gates re-run green; CLI byte-identical across runs; a hand-checkable
1-room/2-patient test pins the metric math.

Findings: (1) the CLI needed the package importable - fixed with `pip install -e .` (recorded as a
known issue + workaround). (2) At 80 patients the load-aware policy only marginally beats FIFO on avg
wait (12.11 vs 12.18) - expected, since the real gains come from the agent-orchestrated policy in
Phase 2; the harness and metrics are what TASK-006 needed and they work. `simpy>=4.1` (MIT) added -
ratified as permissive pending the KI-03 licence policy. File moved to docs/tasks/done/.
