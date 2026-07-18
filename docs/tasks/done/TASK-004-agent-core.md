---
title: "TASK-004: Agent/tool framework + constraint checker + audit log"
status: Done
fr: "FR-13"
owner: agent-core-dev
deps: TASK-001, TASK-003
priority: P0
phase: 1
created: 2026-07-18
tags: [task]
---

# TASK-004: Agent/tool framework + constraint checker + audit log

## Goal

Build the framework-agnostic agent-core spine: a closed-action-space tool registry, the deterministic
constraint checker that runs before every action (NFR-SEC-13), the append-only reasoning audit log
(FR-13), and an Agent base with a perceive-reason-act shape. No agent-framework import (safe under
either ADR-001 option; LangGraph, if accepted, sits behind this interface).

## Inputs and context

- FR-09 (tiered autonomy), FR-10 (Coordinator loop), FR-13 (audit log); guardrails CO-02..CO-05.
- Depends on TASK-003 models/state.
- Related files: `src/vaic/tools/`, `src/vaic/agents/core/`, `tests/`.

## To do

- [x] Tool base + registry (closed action space: unknown tool rejected).
- [x] Constraint checker (deterministic) with the guardrail rules.
- [x] Append-only audit log writing AuditLogEntry.
- [x] ActionExecutor spine (check -> run -> audit) + Agent ABC.
- [x] Tests for each guardrail + audit append-only + denied action does not execute.

## Acceptance criteria

- [x] Every action passes the constraint checker before execution (NFR-SEC-13).
- [x] A LOCKED/unpaid task cannot be started or scanned (BR-10, BR-27); scan only by owner (BR-26).
- [x] Slot allocation to an unavailable resource is blocked (BR-16).
- [x] A ServiceOrder cannot be created by a non-doctor (BR-05).
- [x] A re-plan above the blast-radius threshold N needs approval (FR-09); tool output is
      schema-validated (NFR-SEC-12); unknown tools are rejected (BR-19); audit is append-only (BR-23).

## Decisions and blockers

- DECISION: framework-agnostic spine; LangGraph (ADR-001, if accepted) wraps this, does not replace it.
- BLOCKER (soft): blast-radius threshold N is undecided (spec OI-03). Implemented as a configurable
  `replan_threshold` (interim default 5) - not a policy, just a wired default pending OI-03.

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | agent-core-dev | Built tools/registry, constraint checker, audit log, executor, Agent base + tests | see Result |
| 2026-07-18 | agent-core-dev | Ran gates: `ruff check src tests` clean; `pytest` 27 passed (10 new) | green -> Done |

## Result

Delivered the framework-agnostic agent-core spine (no LangGraph import; ADR-001, if accepted, wraps it):
- `src/vaic/tools/base.py` - `Tool` (schema-validates input, NFR-SEC-12) and `ToolRegistry` (closed
  action space; unknown tool rejected, BR-19).
- `src/vaic/tools/constraint_checker.py` - deterministic checker run before every action (NFR-SEC-13):
  blocks starting/scanning a LOCKED task (BR-10/BR-27), scan by non-owner (BR-26), allocation to an
  unavailable resource (BR-16), service-order creation by a non-doctor (BR-05/CO-02), and a re-plan
  over the blast-radius threshold without approval (FR-09). `replan_threshold` default 5 pending OI-03.
- `src/vaic/tools/audit.py` - append-only `AuditLog` writing `AuditLogEntry` (FR-13, BR-23); no
  update/delete path.
- `src/vaic/agents/core/executor.py` - the spine: action-space check -> constraint check -> tool ->
  audit; a blocked action never executes and is still audited.
- `src/vaic/agents/core/agent.py` - `Agent` ABC (perceive/reason/act via the executor).
- Tests: `tests/test_agent_core.py` - 10 tests covering every guardrail, schema validation, unknown-
  tool rejection, blocked-action-does-not-execute, and audit append-only. Suite 27 passing, ruff clean.

No git yet, so no PR. Follow-up: concrete domain tools (start_task, scan, allocate_slot, etc.) are
stubbed in tests only - the real ones belong to careplan/journey/intake tasks (Phase 2). File moved
to docs/tasks/done/.
