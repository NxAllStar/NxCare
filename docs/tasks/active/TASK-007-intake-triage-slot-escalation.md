---
title: "TASK-007: Intake triage + slot recommendation + emergency escalation"
status: Active
fr: "FR-01, FR-02, BF-05"
owner: intake-dev
deps: "TASK-004, TASK-005"
priority: P1
phase: 2
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-007: Intake triage + slot recommendation + emergency escalation

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree. Read the board row back after writing it.

## Goal

Conversational intake that triages the patient, recommends the least-crowded consult slot, and
escalates emergencies out of the normal flow.

## Inputs and context

- Related FR: [FR-01](../../specs/05-functional-requirements.md#fr-01),
  [FR-02](../../specs/05-functional-requirements.md#fr-02); flow
  [BF-05](../../specs/04-business-flows.md) (emergency escalation).
- Related files and modules: `src/vaic/agents/intake/` (exclusive owner).
- Consumes: agent/tool framework + constraint checker + audit (TASK-004), forecast tool
  `estimate_wait`/`get_queue_state` (TASK-005). Freeze those signatures at the Day-0 contract session.
- Hands off the intake state object to the Care Plan lane (TASK-008): agree the shape before coding.

## To do

- [ ] Intake conversation + triage routing (FR-01).
- [ ] Least-crowded consult-slot recommendation via the forecast tool (FR-02).
- [ ] Emergency escalation path (BF-05): detect, escalate, bypass normal routing, audit-log it.
- [ ] Tests first (pytest) naming the acceptance criterion each proves; external providers mocked.

## Acceptance criteria

- [ ] Tracks FR-01 and FR-02 acceptance criteria and the BF-05 escalation flow.
- [ ] Every consequential action routes through the constraint checker and lands in the audit log.
- [ ] Slot recommendation is grounded in the forecast tool, not invented.

## Decisions and blockers

- <decision or blocker>

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator | Created task file from template so the Intake lane can claim it | Planned |
| 2026-07-18 | Vuong (intake-dev) | Claimed task; verified deps TASK-004, TASK-005 Done and their code present; branch feat/TASK-007-intake-triage-slot-escalation off cnv-dev | Active |

## Result

<Filled when the task moves to Done.>
