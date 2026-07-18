# agent-core-dev - Implement TASK-013 (see docs/tasks/active/TASK-013-auth.md). Read that task file, FR-18 in docs/specs/05-functional-requirements.md, and docs/specs/06-access-control.md (roles, permission matrix, scope predicates Own/Assigned/Team/All) before writing.

- agent_type: agent-core-dev
- agent_id: acb947198d85fb0e4
- finished: 2026-07-18 08:21:55
- transcript: /home/vuongchu/.claude/projects/-data-hdd-16t-vuongchu-civil-vaic/8c736312-191c-47fe-b8c0-590617ff2b13/subagents/agent-acb947198d85fb0e4.jsonl

## Prompt

```
Implement TASK-013 (see docs/tasks/active/TASK-013-auth.md). Read that task file, FR-18 in docs/specs/05-functional-requirements.md, and docs/specs/06-access-control.md (roles, permission matrix, scope predicates Own/Assigned/Team/All) before writing.

SCOPE FOR THIS TASK (approved extension, recorded in the routing table): you own a NEW module `src/vaic/auth/` plus its tests under `tests/`. The existing modules `src/vaic/models/`, `src/vaic/state/`, `src/vaic/tools/`, `src/vaic/agents/`, `src/vaic/forecast/`, `src/vaic/simulator/` already exist — IMPORT them, do NOT modify them. If you genuinely need a change in one of them (e.g. a new field), STOP and report it rather than editing across the boundary.

This is the BACKEND auth layer only — no UI (the login screen SCR-08 and app shell are TASK-015, a separate frontend task). Build in `src/vaic/auth/`:

1. Accounts + roles: a lightweight `Account` model (id, username, role using `vaic.models.enums` role concept, optional linked patient_id/resource_id). Roles are the five in docs/specs/06 (role_patient, role_doctor, role_technician, role_coordinator, role_admin). Demo accounts are seeded (a username->account map or a seed function) — do NOT roll custom password crypto; simple demo auth (account lookup / role selection) is correct here, and production SSO/MFA stays OI-11. If you do store a secret, never a plaintext password and never a weak hash — but for the demo prefer no password at all (account/role selection).

2. Session service: create/validate/revoke a session (token -> Account). Back it with the existing `vaic.state.Repository` (in-memory in tests) or a small session store behind an interface, so it stays swappable (Redis later). No wall-clock nondeterminism in tests.

3. Server-side authorization (this is the point — NFR-SEC-05/06):
   - `require_session(token)` -> Account or raise Unauthorized (maps to 401).
   - `authorize(account, action)` / role guards -> raise Forbidden (maps to 403) when the role lacks the permission per docs/specs/06.
   - Scope predicates Own / Assigned / Team / All as functions that filter records for an account (e.g. a patient resolves only their own records). These must be applied in the data layer, not by hiding UI.
   Use plain exceptions (e.g. `Unauthorized`, `Forbidden`) that an API layer can map to 401/403 — do not pull in a web framework; keep it framework-agnostic (safe under either ADR-001 option).

4. A `login(username)` (demo) returning a session, and `logout(token)`.

Follow .claude/rules: coding-standards.md, testing.md (TDD, tests first), security-privacy.md (no secrets in code/tests, no PII in logs), tech-stack.md. Write tests under tests/ (e.g. tests/test_auth.py) covering AC-18.1 (no session -> Unauthorized/401), AC-18.2 (patient resolves only own records via the Own predicate), AC-18.3 (patient calling a coordinator-only action -> Forbidden/403), session create/validate/revoke, and that scope filtering is applied in the data layer.

Run `python3 -m pytest -q` and `python3 -m ruff check src tests` and make both pass (line-length 100). Append a session-log row to the task file (that file is yours to append to for this task). Report back: files created, test count, the exception types you defined (so the future API layer knows what to map to 401/403), and any cross-boundary needs. Do NOT edit the master-plan board or any file outside `src/vaic/auth/` and `tests/`.
```

## Response

```
TASK-013 implementation is complete. Summary:

**Files created**
- `/data_hdd_16t/vuongchu/civil/vaic/src/vaic/auth/__init__.py` - public exports
- `/data_hdd_16t/vuongchu/civil/vaic/src/vaic/auth/roles.py` - `Role` StrEnum (the five roles from spec 06)
- `/data_hdd_16t/vuongchu/civil/vaic/src/vaic/auth/accounts.py` - `Account` model, `AccountDirectory`, `seed_demo_accounts()` (no password field)
- `/data_hdd_16t/vuongchu/civil/vaic/src/vaic/auth/session.py` - `Session` model, `SessionService` (create/validate/revoke), clock is injected for deterministic tests
- `/data_hdd_16t/vuongchu/civil/vaic/src/vaic/auth/scope.py` - `Scope` enum + `is_own`/`is_assigned`/`is_team`/`matches_scope`/`filter_by_scope` predicates
- `/data_hdd_16t/vuongchu/civil/vaic/src/vaic/auth/permissions.py` - `CrudOp`, the full `PERMISSION_MATRIX` (entity x role x scope, transcribed from spec 06), `resolve_scope`, `list_scoped` (the data-layer enforcement point), `ACTION_ROLES` and `authorize()` for named-action guards (approve_replan, sign_service_order, etc.)
- `/data_hdd_16t/vuongchu/civil/vaic/src/vaic/auth/service.py` - `AuthService` facade: `login`, `logout`, `require_session`, `authorize`
- `/data_hdd_16t/vuongchu/civil/vaic/src/vaic/auth/exceptions.py` - `AuthError`, `Unauthorized`, `Forbidden`
- `/data_hdd_16t/vuongchu/civil/vaic/tests/test_auth.py` - 18 tests (written first, confirmed RED before implementation)

**Exception types for the future API layer**: `vaic.auth.Unauthorized` -> map to HTTP 401; `vaic.auth.Forbidden` -> map to HTTP 403. Both subclass `vaic.auth.AuthError`. No web framework imported (framework-agnostic, per instructions).

**Test/lint results**: `python3 -m pytest -q` -> 70 passed (18 new, 52 pre-existing untouched). `python3 -m ruff check src tests` -> all checks passed (line-length 100). Session log row appended to `/data_hdd_16t/vuongchu/civil/vaic/docs/tasks/active/TASK-013-auth.md`.

**Cross-boundary need to report (not a blocker for this task)**: the data model has no direct or one-hop link back to `patient_id` for `Diagnosis`, `ServiceOrder`, `Slot`, `Payment`, and `AuditLogEntry` (e.g. `Diagnosis.appointment_id`, `Payment.subject_id` require a 2+ hop join to reach a patient). `is_own` in `src/vaic/auth/scope.py` therefore fails closed (denies) for those entities under Own scope rather than guessing via a deep, unreviewed join chain. This is flagged for the data-modeler / TASK-015 frontend wiring: a future schema change (denormalizing a resolvable patient link onto those rows) would let Own-scope cover them without multi-hop joins. I did not edit `src/vaic/models/` to add this - reporting per the stated boundary instead.

Design notes for reviewers: `Session` and `Account` are plain Pydantic models stored via the existing `vaic.state.Repository` interface (works with both `InMemoryRepository` used in tests and `RedisRepository` unchanged - no edits to `src/vaic/state/` or `src/vaic/models/`). Demo auth has no password/crypto per the task's decision (account/role selection only); production SSO/MFA remains OI-11. "Own worklist" from spec 06 is intentionally folded into the `ASSIGNED` scope value (same `owner_id == user.id` predicate) rather than adding a fifth near-duplicate scope.
```
