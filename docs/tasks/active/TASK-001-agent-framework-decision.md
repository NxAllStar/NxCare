---
title: "TASK-001: Decide agent framework (LangGraph vs FastAPI tool-loop)"
status: Active
fr: "-"
owner: tech-researcher
deps: "-"
priority: P0
phase: 1
created: 2026-07-18
tags: [task]
---

# TASK-001: Decide agent framework (LangGraph vs FastAPI tool-loop)

A status change is written in BOTH places at once: the `status:` field above, and this task's row in
`docs/tasks/master-plan.md`. They must never disagree.

## Goal

Choose the agent runtime framework for VAIC - LangGraph or a hand-rolled FastAPI tool-use loop - and
record it as an ADR, so every dev agent builds against a settled runtime (resolves spec OI-18).

## Inputs and context

- Related FR: implicit foundation for [FR-09](../../specs/05-functional-requirements.md#fr-09), [FR-10](../../specs/05-functional-requirements.md#fr-10)
- Related PRD: -
- Related files and modules: `src/vaic/agents/core/`, `src/vaic/tools/`
- Open issue: spec OI-18 (framework); see also `docs/context/known-issues.md`

## To do

- [x] Analyse LangGraph vs FastAPI tool-loop against the constraints (multi-agent orchestration,
      Qwen self-hosting, event-driven Journey, tiered human-in-the-loop, streaming, cost/latency).
- [x] Score a trade-off matrix (fit, speed to demo, reversibility, cost).
- [x] Record the decision and its rationale in an ADR (ADR-001, status Proposed).
- [ ] Team lead accepts ADR-001 (flip status to Accepted).
- [ ] Update `tech-stack.md` to name LangGraph and drop the "not ratified" note (on acceptance).

## Acceptance criteria

- [x] An ADR names the framework and the reasoning - ADR-001 (Proposed; needs Team-lead acceptance).
- [ ] `tech-stack.md` reflects the decision; `agent-core-dev` scope is unblocked.

## Decisions and blockers

- DECISION (proposed): LangGraph for orchestration, isolated behind the `src/vaic/agents/core`
  interface; agents and tools stay framework-agnostic. Named reversal condition to Option B (FastAPI
  loop) if LangGraph blocks the demo. Full rationale: [ADR-001](../../architecture/decisions/ADR-001-agent-framework.md).
- BLOCKER: awaiting Team-lead acceptance of ADR-001. Unblocker: Team lead (SH-01). Raised 2026-07-18.
  Until accepted, `tech-stack.md` keeps its "not ratified" note and TASK-003/TASK-004 build only the
  framework-agnostic agent-core interface (safe under either option).

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator (bootstrap) | Registered TASK-001 on the board and opened this file to smoke-test the task loop | Active |
| 2026-07-18 | tech-researcher | Analysed LangGraph vs FastAPI tool-loop against spec constraints; scored trade-off matrix; drafted ADR-001 recommending LangGraph isolated behind agent-core, with a named fallback | ADR-001 Proposed |

## Result

<Filled when the task moves to Done.>
