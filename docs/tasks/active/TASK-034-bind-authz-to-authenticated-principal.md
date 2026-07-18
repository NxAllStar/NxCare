---
title: "TASK-034: Bind action authz to the authenticated principal"
status: Planned
fr: "FR-18"
owner: agent-core-dev
deps: "TASK-013, TASK-004, TASK-008"
priority: P1
phase: 2
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-034: Bind action authz to the authenticated principal

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree. Read the board row back after writing it.

## Goal

Make every authorization decision in the action pipeline derive the actor's role from the
authenticated FR-18 session, not from a caller-supplied `Action.params.actor_role` string.

## Inputs and context

- Related FR: [FR-18](../../specs/05-functional-requirements.md#fr-18) (auth: session, server-side authz).
- Origin: TASK-008 review findings code-M7 / security-M2. The constraint checker
  (`_check_create_service_order`) and the careplan tools (`gate.py` confirm_payment, `orders.py`
  create_diagnosis/create_service_order) all read `actor_role` from untrusted `Action.params`. An
  agent can submit `actor="agent:x"` with `actor_role="role_staff"` and pass the BR-11 gate, or claim
  `role_doctor` to create a `ServiceOrder`/`Diagnosis` (BR-05).
- Related files and modules: `src/vaic/agents/core/executor.py`, `src/vaic/tools/constraint_checker.py`,
  `src/vaic/auth/` (FR-18), and the careplan tools that consume `actor_role` (read-only for this task -
  coordinate with careplan-dev if their signature must change).

## To do

- [ ] Establish a trusted principal on `Action` (or in the executor) sourced from the FR-18 session.
- [ ] Have the executor/checker verify/populate `actor_role` from that principal, not from client params.
- [ ] Add a test where an agent actor supplies a spoofed privileged `actor_role` and the action is refused+audited.

## Acceptance criteria

- [ ] An action whose declared `actor_role` disagrees with the authenticated principal is refused and audited.
- [ ] No agent actor can flip PAID (BR-11) or create a ServiceOrder/Diagnosis (BR-05) by self-asserting a role.

## Decisions and blockers

- Raised 2026-07-18 by the TASK-008 review gate; owner agent-core-dev (owns FR-18 auth + the checker).

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator | Registered from TASK-008 review findings cM7/sM2 | Planned |

## Result

<Filled when the task moves to Done.>
