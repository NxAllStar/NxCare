---
title: "TASK-010: Coordinator + Disruption tiered autonomy"
status: Done
fr: "FR-09, FR-10"
owner: agent-core-dev
deps: "TASK-004, TASK-005"
priority: P1
phase: 2
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-010: Coordinator + Disruption tiered autonomy

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree. Read the board row back after writing it.

## Goal

The Coordinator agent and the Disruption agent with tiered autonomy: auto-handle small re-plans,
require coordinator approval when blast radius exceeds N patients (FR-09 human-in-the-loop gate).

## Inputs and context

- Related FR: [FR-09](../../specs/05-functional-requirements.md#fr-09),
  [FR-10](../../specs/05-functional-requirements.md#fr-10). See `.claude/rules/ai-governance.md`
  (human in the loop): no agent auto-executes a re-plan above the threshold.
- Related files and modules: `src/vaic/agents/core/` (exclusive owner).
- Consumes: agent/tool framework + constraint checker + audit (TASK-004), forecast tool (TASK-005).
- Surfaces the approval gate to the coordinator console (TASK-029) and feeds the A/B eval (TASK-012).

## To do

- [x] Disruption detection + re-plan proposal (FR-09) - `agents/core/disruption.py`, `replan.py`.
- [x] Blast-radius computation and the > N approval gate; above threshold, propose not execute.
- [x] Coordinator orchestration of the specialist agents (FR-10) - `agents/core/coordinator.py`.
- [x] Every re-plan traces to an audit-log entry with the approval decision.
- [x] Tests first (pytest), including the gated-vs-auto branch and a schema-invalid-input case.

## Acceptance criteria

- [x] Tracks FR-09/FR-10 acceptance criteria (AC-09.1/2/3, AC-10.1/2) in
  `tests/test_coordinator_disruption.py`.
- [x] A re-plan above the blast-radius threshold cannot execute without a recorded human approval
  (`ConstraintChecker._check_execute_replan` gate + `DisruptionAgent.approve/reject`).
- [x] Model output is schema-validated before any action; validation failure is a tested path
  (`test_replan_input_is_schema_validated_bad_params_do_not_execute`).

## Decisions and blockers

- Reused, not rebuilt: the `execute_replan` constraint-checker gate, the `ActionExecutor` spine,
  the `Notifier`, and `resequence`-style deterministic logic already existed (TASK-004/008/009).
  This task added the missing agents and the API surface, not new guardrails.
- Entity completion: added `DisruptionEvent.resource_id` and `.created_at`. The event must know
  which resource failed (so an approval can execute the parked re-plan) and needs an ordering key
  for the console queue. Small, backward-compatible (both optional/defaulted) additions to the
  FR-09 entity; noted here since `models/entities.py` is normally data-modeler's file.
- Layering: `agents/core` must not import the sibling `agents/journey` package at load time. The
  `Notifier` is injected into `DisruptionAgent`; `build_coordinator_stack` constructs the default
  via a local import. This keeps the core spine free of a feature-agent dependency.
- Threshold N (spec OI-03) is still undecided: the wired default stays 5
  (`DEFAULT_REPLAN_THRESHOLD`), overridable per `build_coordinator_stack(threshold=...)`.
- `actor_role`/`actor_id` trust for FR-18 (TASK-034/036) is out of scope here and unchanged; the
  coordinator/disruption actors are agent names, not authenticated principals.
- Remaining human step: PR + review + merge. The authoring agent does not merge its own work.

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator | Created task file from template so the Coordinator/Disruption lane can claim it | Planned |
| 2026-07-18 | agent-core-dev | Claimed the task (Active) and implemented FR-09/FR-10 test-first: snapshot, blast-radius, execute_replan tool, Disruption + Coordinator agents, coordinator API | Active |
| 2026-07-18 | agent-core-dev | Ran `.venv/bin/python -m pytest` | 301 passed (17 new: `test_coordinator_disruption.py`, `test_coordinator_api.py`) |
| 2026-07-18 | agent-core-dev | Ran `.venv/bin/ruff check src/vaic tests/` | All checks passed |
| 2026-07-18 | agent-core-dev | Smoke-tested `create_app()` boot with the coordinator router mounted | `/coordinator/snapshot` 200, `/coordinator/disruptions` 200 |

## Result

FR-09 (Disruption, tiered autonomy) and FR-10 (Coordinator loop) are implemented and verified
locally. New modules in `src/vaic/agents/core/`: `snapshot.py` (deterministic perceive),
`replan.py` (blast radius + `execute_replan` tool), `disruption.py` (`DisruptionAgent` with
`handle`/`approve`/`reject`), `coordinator.py` (`CoordinatorAgent` + rule-based brain +
`build_coordinator_stack`). API: `src/vaic/api/coordinator_routes.py` (snapshot/heatmap, approval
queue, trigger, approve, reject) mounted in `app.py`.

Autonomy is enforced by the existing deterministic `execute_replan` gate: blast radius at/below the
threshold auto-executes and notifies affected patients with a reason (AC-09.1); above it, the
re-plan is parked `PENDING_APPROVAL` and is not executed (AC-09.2); a rejection keeps the original
plan and is audited (AC-09.3). The Coordinator perceives a code-built snapshot, delegates, and
audits its reasoning (AC-10.1); an action outside the closed tool set is rejected by the spine
(AC-10.2). 301 pytest pass, ruff clean.

Not done here (tracked elsewhere): binding actor identity to an authenticated session
(TASK-034/036), the coordinator console UI (TASK-029), the A/B eval vs FIFO (TASK-012), and the
final PR + human review + merge.
