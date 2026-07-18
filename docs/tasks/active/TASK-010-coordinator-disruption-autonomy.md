---
title: "TASK-010: Coordinator + Disruption tiered autonomy"
status: Planned
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

- [ ] Disruption detection + re-plan proposal (FR-09).
- [ ] Blast-radius computation and the > N approval gate; above threshold, propose not execute.
- [ ] Coordinator orchestration of the specialist agents (FR-10).
- [ ] Every re-plan traces to an audit-log entry with the approval decision.
- [ ] Tests first (pytest), including the gated-vs-auto branch and an injection-in-input case.

## Acceptance criteria

- [ ] Tracks FR-09/FR-10 acceptance criteria.
- [ ] A re-plan above the blast-radius threshold cannot execute without a recorded human approval.
- [ ] Model output is schema-validated before any action; validation failure is a tested path.

## Decisions and blockers

- <decision or blocker>

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator | Created task file from template so the Coordinator/Disruption lane can claim it | Planned |

## Result

<Filled when the task moves to Done.>
