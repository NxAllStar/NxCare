---
title: "ADR-001: Agent framework - PocketFlow, isolated behind the agent-core interface"
status: Accepted # Proposed | Accepted | Deprecated | Superseded by ADR-MMM
date: 2026-07-18
deciders: [Team lead]
tags: [adr, architecture]
---

# ADR-001: Agent framework - PocketFlow, isolated behind the agent-core interface

Resolves spec open issue OI-18. Recorded from TASK-001. **Accepted** - ratified by the Team lead on
2026-07-18. Immutable now (docs-workflow): supersede it with a new ADR rather than editing this one.

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

Use **PocketFlow** for the orchestration graph (Coordinator/Disruption, shared state, human-in-the-loop,
streaming), and **isolate it behind the `src/vaic/agents/core` interface** so that individual agents and
every tool (Intake, Journey, the forecast-LLM, the constraint checker) are plain framework-agnostic
Python. The framework choice must not leak past agent-core.

LangGraph (Option A) was the strong alternative and is now the documented fallback - see the reversal
condition. Its built-in interrupt/resume and streaming were weighed against PocketFlow's transparency,
zero dependencies, and plain-dict Redis mapping - the team chose to own those two primitives in
exchange for a minimal, fully transparent runtime.

## Options considered

| Option | Pros | Cons |
|--------|------|------|
| A LangGraph, isolated behind agent-core | Interrupt/resume for tiered approval and streaming are built in - the two demo-critical primitives that are expensive to hand-roll; graph + shared-state maps 1:1 to the proposal's architecture; checkpointing aligns with the harness "survive compaction" ethos; matches the team's roadmap; multi-backend model support | A framework to learn and debug under time pressure; opinionated state/checkpoint model that must be reconciled with Redis (use a Redis checkpointer or keep domain state in Redis and graph state thin); an added dependency |
| B Hand-rolled FastAPI tool-use loop | Minimal deps; full control; constraint checker trivially placed before every action; transparent latency/cost; leanest for a few agents | Must build interrupts, resume, parallel dispatch, and streaming yourself - exactly the primitives that are hard to get right quickly; more code to write and test in a hackathon |
| C (chosen) PocketFlow (~100-line graph lib, zero deps), isolated behind agent-core | Minimal (~100 lines, zero dependencies, ~56KB) and fully transparent - readable and debuggable under time pressure; shared store is a plain dict that serialises straight to Redis, so it removes Option A's state/checkpoint reconciliation friction; constraint checker slots in as a node or exec() wrapper; no vendor lock-in, trivial to point at both the hosted API and self-hosted Qwen; isolation-behind-agent-core ethos fits its compose-your-own philosophy | Does NOT provide the two demo-critical primitives as core features - interrupt/resume and streaming are cookbook patterns you build and debug yourself (this is why it is nearer Option B than Option A); no built-in checkpointer; you own all the plumbing, which is the cost the framework was meant to save under a hackathon deadline |

## Consequences

- Positive: a minimal, fully transparent runtime that is readable and debuggable under time pressure;
  a plain-dict shared store that serialises straight to Redis with zero state/checkpoint reconciliation
  friction; zero dependencies and no vendor lock-in; trivially points at both the hosted API and
  self-hosted Qwen; isolation behind agent-core is cheap to honour.
- Negative and trade-offs: the two demo-critical primitives are NOT framework primitives and must be
  hand-rolled and tested - interrupt/resume for tiered approval (FR-09) and streaming reasoning (demo
  step 3). There is no built-in checkpointer, so persistence against Redis is hand-rolled. Mitigation:
  build and test these two primitives EARLY - they are on the critical path - and the isolation behind
  agent-core keeps a reversal cheap.
- Reversal condition (named, so it is a decision not a hope): if hand-rolling interrupt/resume or
  streaming blocks the demo build, fall back to LangGraph (Option A), whose interrupt/resume,
  streaming, and checkpointer are built in. Because agents and tools are framework-agnostic by this
  ADR, the fallback is a change to `agent-core` only - not a rewrite. A reversal is a new ADR
  superseding this one.
- Follow-up work:
  - TASK-004 builds the agent-core interface first, framework code strictly behind it.
  - PocketFlow's shared dict maps to Redis directly, so decide the serialisation boundary (what lives
    in Redis vs the in-flight shared dict) in TASK-003/TASK-004.
  - Empirical check: PoC-3 (spec 12) measures agent-loop latency/cost at ~50-100 patients; if it
    fails the NFR-PERF budget (OI-05), revisit batching or the reversal condition - not this ADR's
    framework choice per se.
  - On acceptance: update `.claude/rules/tech-stack.md` to name PocketFlow and drop the "not ratified"
    note, and move TASK-001 to Done.

## References

- spec OI-18, and the technical approach in `docs/specs/12-technical-feasibility.md`
- FR-07, FR-09, FR-10 in `docs/specs/05-functional-requirements.md`
- TASK-001 in `docs/tasks/active/`
- `docs/context/known-issues.md` (agent framework not chosen)
