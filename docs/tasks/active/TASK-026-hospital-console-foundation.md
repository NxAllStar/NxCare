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

## To do

- [ ] Extend the mock session/role model to cover staff roles alongside `patient` (demo only).
- [ ] Path-based entry switch so `/console/*` mounts the console and the patient app is untouched.
- [ ] Desktop shell: sidebar nav filtered by role, top bar (user + role + language toggle + logout).
- [ ] Staff login (role selector) and a client-side role guard (non-permitted role is redirected).
- [ ] Route stubs for SCR-03..SCR-07, each rendering a proper ScreenState placeholder + role gate.
- [ ] Vitest coverage: entry switch, role gating/redirect, shell renders per role.

## Acceptance criteria

- Navigating to `/console` with no staff session lands on the console login; the patient app at `/`
  is byte-for-byte unaffected (its entry still renders `PatientCompanionApp`).
- After selecting a staff role, the sidebar shows exactly that role's permitted screens (FR-12
  AC-12.2: a non-coordinator cannot reach the coordinator dashboard).
- Every stub screen renders inside the desktop shell using shared tokens/primitives (no hardcoded
  one-off styles where a token exists), no emoji, WCAG AA contrast.
- `npm run typecheck`, `npm run test`, and `ruff`-equivalent lint pass; runs recorded in the log.

## Session log

| When | Who | What |
|------|-----|------|
| 2026-07-18 | Claude (driver) | Registered task; settled the console structure (src/console, path-based entry, shared tokens/primitives); dispatching frontend-ui-dev to build the foundation. |
