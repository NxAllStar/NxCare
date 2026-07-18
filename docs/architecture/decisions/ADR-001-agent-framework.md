---
title: "ADR-001: Agent framework - LangGraph, isolated behind the agent-core interface"
status: Proposed # Proposed | Accepted | Deprecated | Superseded by ADR-MMM
date: 2026-07-18
deciders: []
tags: [adr, architecture]
---

# ADR-001: Agent framework - LangGraph, isolated behind the agent-core interface

Resolves spec open issue OI-18. Recorded from TASK-001. **Proposed** - awaiting Team-lead acceptance;
once accepted it becomes immutable (docs-workflow), so land any change before the flip.

## Context

VAIC is a multi-agent system (Coordinator, Disruption, Intake, Care Plan, per-patient Journey, plus a
forecast-LLM tool). The build is a hackathon demo on a SimPy simulator. The choice of agent runtime
binds `agent-core-dev`, `intake-dev`, `careplan-dev`, `journey-dev`, and `forecast-dev`, so it must be
made before the runtime is built (TASK-004 depends on it).

Binding constraints, from the specs:

- **Shared state = a hospital snapshot**; agents perceive it and act on it (proposal muc 2, FR-10).
- **Tiered human-in-the-loop**: a re-plan with blast radius > N pauses for coordinator approval
  (FR-09, FR-12). This is an interrupt-and-resume pattern, not a request/response.
- **Streaming reasoning** is a demo-critical moment (the disruption "golden moment", demo step 3).
- **Event-driven** Journey agents; batched Coordinator (FR-06 BR-12, FR-10 BR-20).
- **Closed action space**: a deterministic constraint checker runs before every action (NFR-SEC-13),
  and the forecast tool enforces the retrieve-reason-validate grounding contract (FR-07).
- **Mixed model backends**: hosted API for reasoning seats, self-hosted Qwen for Intake/Journey/forecast.
- **Hackathon**: speed to demo, reproducibility (fixed seed), and reversibility all matter.
- The team's LLM-engineering roadmap already includes LangGraph (proposal muc 6).

## Decision

Use **LangGraph** for the orchestration graph (Coordinator/Disruption, shared state, human-in-the-loop
interrupts, streaming), and **isolate it behind the `src/vaic/agents/core` interface** so that
individual agents and every tool (Intake, Journey, the forecast-LLM, the constraint checker) are plain
framework-agnostic Python. The framework choice must not leak past agent-core.

## Options considered

| Option | Pros | Cons |
|--------|------|------|
| A (chosen) LangGraph, isolated behind agent-core | Interrupt/resume for tiered approval and streaming are built in - the two demo-critical primitives that are expensive to hand-roll; graph + shared-state maps 1:1 to the proposal's architecture; checkpointing aligns with the harness "survive compaction" ethos; matches the team's roadmap; multi-backend model support | A framework to learn and debug under time pressure; opinionated state/checkpoint model that must be reconciled with Redis (use a Redis checkpointer or keep domain state in Redis and graph state thin); an added dependency |
| B Hand-rolled FastAPI tool-use loop | Minimal deps; full control; constraint checker trivially placed before every action; transparent latency/cost; leanest for a few agents | Must build interrupts, resume, parallel dispatch, and streaming yourself - exactly the primitives that are hard to get right quickly; more code to write and test in a hackathon |

## Consequences

- Positive: tiered approval (FR-09) and streamed reasoning (demo step 3) come from framework
  primitives, not hand-rolled code; the graph/state model matches the spec; the team builds on its
  existing roadmap.
- Negative and trade-offs: a learning/debugging cost, and LangGraph's own state/checkpoint must be
  reconciled with Redis rather than duplicated. Isolation behind agent-core is the mitigation and is
  mandatory, not optional.
- Reversal condition (named, so it is a decision not a hope): if LangGraph debugging blocks the demo
  build, fall back to Option B. Because agents and tools are framework-agnostic by this ADR, the
  fallback is a change to `agent-core` only - not a rewrite. A reversal is a new ADR superseding this one.
- Follow-up work:
  - TASK-004 builds the agent-core interface first, framework code strictly behind it.
  - Reconcile LangGraph state with Redis (`src/vaic/state`) - decide checkpointer vs thin graph state
    in TASK-003/TASK-004.
  - Empirical check: PoC-3 (spec 12) measures agent-loop latency/cost at ~50-100 patients; if it
    fails the NFR-PERF budget (OI-05), revisit batching or the reversal condition - not this ADR's
    framework choice per se.
  - On acceptance: update `.claude/rules/tech-stack.md` to name LangGraph and drop the "not ratified"
    note, and move TASK-001 to Done.

## References

- spec OI-18, and the technical approach in `docs/specs/12-technical-feasibility.md`
- FR-07, FR-09, FR-10 in `docs/specs/05-functional-requirements.md`
- TASK-001 in `docs/tasks/active/`
- `docs/context/known-issues.md` (agent framework not chosen)
