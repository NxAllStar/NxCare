---
title: "TASK-026: Hospital web console foundation, shell, staff login, role routing"
status: Active
fr: FR-12
owner: frontend-ui-dev
deps: TASK-021, TASK-013
priority: P1
phase: 2
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-026: Hospital web console foundation, shell, staff login, role routing

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree. Read the board row back after writing it:
a board write can fail silently while the task file lands.

## Goal

Stand up the hospital-facing web console as a second app surface inside the existing `frontend/`
Vite project - a desktop-first shell, staff login (role selector), and role-gated routing to stub
screens for SCR-03..SCR-07 - reusing the existing design tokens and shared primitives, without
touching the shipped patient companion app.

## Inputs and context

- Related FR: [FR-12](../../specs/05-functional-requirements.md#fr-12) (coordinator dashboard + staff screens), [FR-18](../../specs/05-functional-requirements.md#fr-18) (session/role)
- Related screens: SCR-03 Consult and orders (doctor), SCR-04 Doctor worklist (doctor), SCR-05
  Technician task view (technician), SCR-06 Coordinator dashboard (coordinator, flagship), SCR-07
  Admin and audit console (admin) - [spec 10](../../specs/10-ui-ux-wireframes.md)
- Access control per role: [spec 06](../../specs/06-access-control.md)
- Design system: `frontend/design-tokens.json`, `frontend/src/components/primitives/`, spec 10
  "Visual design direction". Staff/coordinator views are desktop-first (multi-pane).
- Reuses the patient-app patterns: `src/auth/AuthContext.tsx`, `src/i18n/`, `src/lib/api/`.

## Architectural decisions (settled before build)

- Same `frontend/` app; hospital surface lives under `src/console/`, mirroring `src/companion/`.
- Shared design tokens + `src/components/primitives/` are the source of truth. Console adds its own
  desktop chrome (sidebar shell) under `src/console/`, not an iPhone frame or bottom tab bar.
- Entry switch is path-based: `/console/*` renders the console app (own router, `basename`),
  everything else keeps rendering the patient companion app unchanged.
- Session model extends to staff roles (doctor, technician, coordinator, admin) without breaking the
  existing `role: 'patient'` path. Demo login is a role selector; no real credentials.

## Role -> permitted-screens contract (locked by spec-guardian 2026-07-18, from specs 06 + 10)

The sidebar and the client-side route guard MUST enforce exactly this. A permitted screen appears in
the sidebar for that role and is reachable; every other console route redirects that role away.

| Role | SCR-03 Consult/orders | SCR-04 Doctor worklist | SCR-05 Technician task | SCR-06 Coordinator dashboard | SCR-07 Admin/audit console |
|------|-----------------------|------------------------|------------------------|------------------------------|----------------------------|
| `doctor` | Yes | Yes | No | No | No |
| `technician` | No | No | Yes | No | No |
| `coordinator` | No | No | No | Yes | Yes (audit read-only; no simulator config) |
| `admin` | No | No | No | Yes | Yes (full: audit + simulator config) |
| `patient` | No | No | No | No | No (stays on the companion app) |

- SCR-06 boundary is "coordinator OR admin", NOT "non-coordinator blocked" - `admin` must reach the
  flagship dashboard (FR-12 validation row; SCR-06 visible to role_coordinator + role_admin).
- SCR-07 route admits BOTH `coordinator` (read-only audit) and `admin` (full). Sub-element gating
  (simulator config admin-only, audit read-only for coordinator) is for the real SCR-07 task; the
  TASK-026 stub only enforces route-level access for both roles and may note the future split.
- Role-hierarchy inheritance (spec 06) is capability-only: `admin` does NOT gain SCR-03/04/05.

## Out of scope (explicitly deferred - do not mark these Done via this task)

- Server-side authorization / per-endpoint 403 (FR-18 AC-18.3, BR-28) is NOT delivered here. This
  task ships a client-side guard only (UX, not a security boundary). Real server-side authz is owned
  by `agent-core-dev` (`src/vaic/auth/`) in a separate task; FR-18 is not "Done" on this task.
- The real SCR-03..07 screen implementations (worklists, live heatmap, approval queue, reasoning
  stream, audit search, simulator seed/config) are follow-on tasks; TASK-026 ships on-brand stubs.

## To do

- [ ] Extend the mock session/role model to a discriminated union covering staff roles
      (`doctor | technician | coordinator | admin`) alongside `patient` WITHOUT changing the shipped
      patient login/typecheck path (patient `Session.role: 'patient'` must still compile and behave).
- [ ] Path-based entry switch so `/console/*` mounts the console and the patient app is untouched
      (App.tsx still renders `PatientCompanionApp` for non-`/console` paths; `?home=1` still works).
- [ ] Desktop-first sidebar shell: sidebar nav filtered by role per the contract above, top bar
      (user + role + language toggle + logout). No iPhone frame, no bottom tab bar.
- [ ] Staff login (role selector, synthetic/demo only - no real credentials) and a client-side role
      guard that redirects a role away from any screen not permitted to it per the contract above.
- [ ] Route stubs for SCR-03..SCR-07, each rendering a proper `ScreenState` placeholder + role gate,
      built from shared tokens/primitives.
- [ ] Vitest coverage: entry switch, role gating/redirect for every row of the contract, shell
      renders the correct sidebar per role.

## Acceptance criteria

- Navigating to `/console` with no staff session lands on the console login; the patient app at `/`
  is byte-for-byte unaffected (its entry still renders `PatientCompanionApp`; `?home=1` still works).
- After selecting a staff role, the sidebar shows exactly that role's permitted screens per the
  contract table, and a role visiting a screen not permitted to it is redirected (e.g. a `doctor`
  cannot reach SCR-06; both `coordinator` and `admin` can; `admin` reaches SCR-06 too).
- Every stub screen renders inside the desktop shell using shared tokens/primitives (no hardcoded
  one-off styles where a token exists), no emoji, WCAG AA contrast.
- Typecheck, Vitest, and lint pass under node v22; the actual commands and results are recorded in
  the session log (a gate counts as passed only when the log records the run).

## Session log

| When | Who | What |
|------|-----|------|
| 2026-07-18 | Claude (driver) | Registered task; settled the console structure (src/console, path-based entry, shared tokens/primitives); dispatching frontend-ui-dev to build the foundation. |
| 2026-07-18 | orchestrator | Branch feat/TASK-026-hospital-console-foundation cut off frontend. spec-guardian ran (read-only scope lock): no spec contradiction in the architecture; three corrections applied to this file - SCR-06 guard is coordinator OR admin (admin reaches it), SCR-07 route admits coordinator (read-only) + admin, and server-side authz (FR-18 AC-18.3/BR-28) is explicitly out of scope (owned by agent-core-dev). Locked role->screen contract added above. |
| 2026-07-18 | frontend-ui-dev | Built the foundation test-first, commit 0ba37b2. New src/console/: access.ts (role->screen contract as data), auth/StaffAuthContext (separate demo staff session, NOT the patient AuthContext - patient path untouched by construction), auth/ConsoleRouteGuard, components/ConsoleShell (desktop sidebar + top bar), screens/ (login + 5 ScreenState stubs SCR-03..07), ConsoleApp (own BrowserRouter basename=/console + I18nProvider + StaffAuthProvider). App.tsx: path-based switch (/console -> ConsoleApp, else PatientCompanionApp with ?home=1 intact). Additive-only edits to icons/index.tsx (5 icons) and i18n vi.ts/en.ts (~18 console.* keys). |
| 2026-07-18 | orchestrator | QA gate (orchestrator ran the suites independently under node v22.21.1, verifying the dev's claim against git): `tsc -b --noEmit` clean exit 0; `vitest run` 29 files / 193 tests passed, 0 failed (includes the shipped patient suite -> patient path confirmed unaffected). Lint: no ESLint config or lint script exists repo-wide (pre-existing); tsc is the static gate. GATE PASSED. |
| 2026-07-18 | code-reviewer | Read-only code-quality gate on `git diff da776d2...HEAD -- frontend/`. No Blockers or Major findings: the locked role->screen contract is implemented exactly in access.ts and covered row-by-row by access.test.ts + ConsoleApp.test.tsx + ConsoleShell.test.tsx; patient path untouched (App.test.tsx). 3 Minor + 3 Info raised (path-prefix match `startsWith('/console')` also matches `/console-*` -> blank page; unvalidated sessionStorage cast can crash on a tampered role; captured `state.from` never honored after login). Findings returned to orchestrator; no code modified. |
| 2026-07-18 | security-reviewer | Read-only security/privacy gate on the same diff. No Blockers, no Major. Login is a pure role selector (no password param); no secret/credential/token/key anywhere; demo staff names are synthetic `(demo)`-suffixed personas; no dependency changes; no dangerouslySetInnerHTML/eval/innerHTML. Client-side guard is honestly framed as UX with server-side authz (FR-18 AC-18.3/BR-28) explicitly deferred (Info, correct). 1 Minor (same unvalidated sessionStorage role cast; ASVS v5.0.0 ch.1/5 boundary validation - robustness only, no privilege path since real authz is server-side). sessionStorage holds only a role marker, no token (Info, upgrades to Major only when a real token is stored there). GATE PASSED. |
| 2026-07-18 | orchestrator | Accepted the two convergent Minor findings (exact-path match; validate stored role at the storage boundary) for immediate fix while the dev context is warm - they harden the base every follow-on screen builds on. Dead `state.from` cleanup folded in. Info items and the deferred server-side-authz note accepted as-is. Sent fixes back to frontend-ui-dev. Noted: code-reviewer appended its own log row (out of its read-only lane); content accurate, kept. |
