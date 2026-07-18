---
title: "TASK-013: Auth + role-based access (session, server-side authz)"
status: Done
fr: "FR-18"
owner: agent-core-dev
deps: TASK-003, TASK-004
priority: P1
phase: 2
created: 2026-07-18
tags: [task]
---

# TASK-013: Auth + role-based access (session, server-side authz)

## Goal

Build the backend auth layer for the one responsive role-gated web app (FR-18): accounts + roles,
a session service, and server-side authorization that enforces the role/scope model in
`docs/specs/06-access-control.md`. The login SCREEN (SCR-08) and app shell are a separate frontend
task (TASK-015); this task is the backend the shell calls.

## Inputs and context

- FR-18 in `docs/specs/05-functional-requirements.md`; the permission matrix and scope predicates in
  `docs/specs/06-access-control.md`; NFR-SEC-05/06.
- Builds on TASK-003 (models/state), TASK-004 (agent-core). Scope for this task extends to a new
  module `src/vaic/auth/` (approved ownership: agent-core-dev, recorded in the routing table).

## Acceptance criteria

- [x] AC-18.1: a request with no valid session to any protected operation returns 401.
- [x] AC-18.2: a `role_patient` session resolves only that patient's own records (Own scope).
- [x] AC-18.3: a `role_patient` calling a coordinator-only operation returns 403 - enforced
      server-side, not by hiding UI (NFR-SEC-05).
- [x] Scope predicates (Own / Assigned / Team / All) from 06 are enforced in the data layer.
- [x] Demo auth is simple (seeded accounts / role selection) - no custom crypto; production SSO/MFA
      stays OI-11. Tests + ruff green.

## Decisions and blockers

- DECISION: demo auth uses a seeded account list mapping username -> role (+ linked patient/resource);
  no password KDF rolled by hand. Production identity/SSO/MFA remain OI-11.
- Scope note: `src/vaic/auth/` is a new module owned by agent-core-dev (routing table updated).

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | agent-core-dev | Built `src/vaic/auth/` (roles, accounts + demo seed, session service, permission matrix + scope predicates, `AuthService` facade) test-first per TDD; wrote `tests/test_auth.py` covering AC-18.1 (Unauthorized on no/invalid/revoked session), AC-18.2 (Own-scope filtering for a patient via `list_scoped`, incl. one-hop `Task -> CarePlan` join), AC-18.3 (Forbidden for role_patient calling `approve_replan`), session create/validate/revoke lifecycle with an injected deterministic clock, and that scope filtering runs in the data layer (`filter_by_scope`). Imported `vaic.models`/`vaic.state` only, no edits outside `src/vaic/auth/` and `tests/`. | `python3 -m pytest -q` = 70 passed (18 new in `tests/test_auth.py`); `python3 -m ruff check src tests` = all checks passed. Cross-boundary note logged for the data-modeler: `Diagnosis`, `ServiceOrder`, `Slot`, `Payment`, `AuditLogEntry` have no direct or one-hop field back to `patient_id`, so `is_own` (in `src/vaic/auth/scope.py`) fails closed (denies) for those entities under Own scope pending a denormalized link - not a blocker for this task's ACs, but flagged for FR-18 UI wiring in TASK-015 and for any future PRD/data-model update. |

## Result

Delivered `src/vaic/auth/`: `Role` enum, `Account` + demo account seed (no password/crypto),
`SessionService` (create/validate/revoke, injected clock) behind the state `Repository`, the full
`PERMISSION_MATRIX` + scope predicates (Own/Assigned/Team/All) transcribed from spec 06, and an
`AuthService` facade (`login`/`logout`/`require_session`/`authorize`). Exceptions: `Unauthorized`->401,
`Forbidden`->403 (framework-agnostic). `tests/test_auth.py` = 18 tests.

Orchestrator-verified: `pytest` 70 passed, `ruff` clean; read `scope.py` to confirm authz genuinely
enforces (real resolution, fail-closed, data-layer `filter_by_scope`) - not a dead control. Diff
confined to `src/vaic/auth/` + `tests/`; models/state imported, not edited.

Finding accepted (fail-closed, so safe, not a hole): `Diagnosis`, `ServiceOrder`, `Slot`, `Payment`,
`AuditLogEntry` have no direct/one-hop link to a patient, so Own-scope DENIES them for now. Registered
as TASK-016 (data-modeler: add a resolvable patient link) + a known issue. Demo auth done; production
SSO/MFA remain OI-11. No git yet -> formal code/security review before the first PR. File moved to done/.
