---
title: "TASK-034: Bind action authz to the authenticated principal"
status: Active
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

- [x] `POST /care-plans/{id}/tasks/{id}/proceed` (`api/careplan_routes.py::confirm_proceed`, the FR-18
      authenticated layer): derive `actor_role`/`confirmed_by` from `account`, never the request body.
      Routed through `ActionExecutor` instead of `tool.run` directly, so the PAID flip is audited.
- [x] `POST /coordinator/disruptions/{id}/approve|reject` (`api/coordinator_routes.py`, was fully
      unauthenticated): added `get_current_account` + `authorize(account, "approve_replan"/"reject_replan")`,
      bound `decided_by` to `account.resource_id or account.id`. Not in this task's original file list
      but the same class of defect (FR-09 human-in-the-loop gate defeatable by a spoofed identity).
- [ ] `POST /api/careplan/generate` and the rest of `build_careplan_router`/`build_intake_router`/
      `build_staff_router`/`build_coordinator_router` (the sync/demo layer mounted unauthenticated in
      `api/app.py:92-96`) still trust caller-supplied `actor_role`/`diagnosed_by`. NOT fixed here: the
      staff console's login (`frontend/src/console/auth/StaffAuthContext.tsx`) is a client-only role
      selector with no backend call and issues no JWT, and `generateCarePlan`
      (`frontend/src/lib/api/careplan.ts:125`) sends no `Authorization` header - hard-authenticating
      this route now would 401 the doctor console with no way for it to obtain a token. Needs
      frontend-ui-dev to wire the staff console through `POST /auth/login` first; tracked as
      remaining scope here rather than closed silently.
- [ ] `constraint_checker.py` (`_check_create_service_order` and friends) still reads `actor_role`
      from `Action.params` for the tools reachable via the demo layer above - same blocker.
- [ ] Add a test where an agent actor supplies a spoofed privileged `actor_role` and the action is
      refused+audited (covered for `confirm_payment` in `tests/test_careplan_proceed_route.py`; not
      yet for `create_service_order`/`create_diagnosis`, blocked on the item above).

## Acceptance criteria

- [x] `confirm_payment`: an action whose actor_role would disagree with the authenticated principal
      cannot be submitted at all (the route has no field for it) - refused+audited when the
      authenticated account itself is not authorised (BR-11).
- [ ] No agent actor can create a ServiceOrder/Diagnosis (BR-05) by self-asserting a role - open,
      see the unresolved items above.

## Decisions and blockers

- Raised 2026-07-18 by the TASK-008 review gate; owner agent-core-dev (owns FR-18 auth + the checker).
- Blocked on frontend-ui-dev wiring the staff/coordinator console through real `POST /auth/login` +
  `Authorization` headers before the demo/sync layer's mutating routes can be hard-authenticated
  without breaking the live console. Raised 2026-07-19 during the judge-driven backend security pass.

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator | Registered from TASK-008 review findings cM7/sM2 | Planned |
| 2026-07-19 | cnvntq (judge-driven review) | Fixed `confirm_proceed` (actor binding + audited via `ActionExecutor`) and `coordinator_routes` approve/reject (added auth). Added regression tests (`test_careplan_proceed_route.py`, `test_coordinator_api.py`). 338/338 tests pass, ruff clean. Left the demo/sync layer's `actor_role` trust open pending frontend auth wiring. | Active, partially complete |

## Result

<Filled when the task moves to Done.>
