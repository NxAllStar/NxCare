---
title: "TASK-038: Wire the patient app to the real Care Plan backend"
status: Planned
fr: FR-04
owner: frontend-ui-dev
deps: TASK-027, TASK-013
priority: P1
phase: 2
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-038: Wire the patient app to the real Care Plan backend

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree. Read the board row back after writing it:
a board write can fail silently while the task file lands.

## Goal

Make `JourneyPage` read a patient's care plan from the real `/api/careplan/*` backend instead of
the static `DEMO_CARE_PLANS`/`DEMO_TASKS` fixtures, so a doctor-entered order is visible on the
patient screen without a manual fixture edit.

## Inputs and context

- Related FR: [FR-04](../../specs/05-functional-requirements.md#fr-04), [FR-03](../../specs/05-functional-requirements.md#fr-03)
- Related PRD: [PRD-FR-12](../../requirements/PRD-FR-12-patient-mobile-app.md)
- Related files and modules: `frontend/src/lib/api/patient.ts`, `frontend/src/lib/api/fixtures.ts`,
  `frontend/src/pages/LoginPage.tsx`, `frontend/src/auth/AuthContext.tsx`,
  `src/vaic/api/careplan_routes.py` (`GET /patient/{patient_id}/active`, added this session)

## Decisions and blockers

- Blocker (found this session, 2026-07-18): demo patient login issues session patient ids as
  fixed demo strings (`"patient-0001"`, `"patient-0002"`, `fixtures.ts`), but every backend model
  and route (`careplan_routes.py`, `models/entities.py`) types `patient_id` as a real `UUID`.
  Calling `GET /api/careplan/patient/patient-0001/active` 422s outright - FastAPI cannot parse the
  path param. `getActiveCarePlan`/`listTasksForCarePlan` cannot simply be repointed at the real
  endpoint until patient identity is reconciled: either the demo login mints/looks up a real
  `Patient` UUID (needs a matching backend `Patient` read/seed path, which does not exist yet
  either - only `Appointment`/`ServiceType`/`Resource` are seeded), or the FE keeps a
  demo-string-to-UUID lookup table. Needs an owner decision before FE code changes, not a
  unilateral pick - this crosses `frontend-ui-dev` and `agent-core-dev` (FR-18 auth) territory.
- A runnable, backend-only demo of the doctor-order -> route-proposal flow already exists
  (`scripts/demo_careplan_flow.py`, added this session) and does not depend on this task landing.

## To do

- [ ] Decide the patient-identity reconciliation approach (see blocker above) with the auth/backend
      owner before touching `patient.ts`.
- [ ] Repoint `getActiveCarePlan`/`listTasksForCarePlan` at `GET /api/careplan/patient/{id}/active`
      (same pattern as `frontend/src/lib/api/intake.ts`'s real backend call).
- [ ] Add a `POST /api/careplan/generate`-calling doctor order-entry surface - scope decision needed
      first: PRD-FR-12 3 "Out of scope" and `routeConfig.tsx`'s docstring currently lock this
      frontend to patient-only screens (TASK-011 was superseded for exactly that reason), so a
      doctor screen inside this app is a product-scope change, not a routine addition. Confirm
      placement (a `role_doctor`-gated route in this same app, vs. a separate staff surface, vs.
      demo-only via `scripts/demo_careplan_flow.py` / curl) with the product owner before building.
- [ ] Update `JourneyPage.test.tsx` and any other test mocking `patientApi` if the return shape
      changes.

## Acceptance criteria

- [ ] Given a `CarePlan` created via `POST /api/careplan/generate` for a real patient UUID, when
      that patient's `JourneyPage` loads, then the timeline shows the same tasks the backend
      returned - no fixture data involved.
- [ ] Given no active care plan exists for the patient, when `JourneyPage` loads, then it shows the
      existing empty state (same UX as today, backed by a real 404 instead of a fixture miss).

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | claude (session) | Added `GET /api/careplan/patient/{patient_id}/active` (careplan_routes.py) + tests; added standalone `scripts/demo_careplan_flow.py` proving the doctor-order -> route-proposal flow end to end; discovered the patient-id UUID/demo-string mismatch blocking FE wiring and filed this task instead of forcing a unilateral fix | Backend read endpoint done (182/182 tests pass); FE wiring intentionally left for a scoped decision |

## Result

<Filled when the task moves to Done: what was delivered, the PR or commit, and any
follow-up items with where they now live. Then move this file to docs/tasks/done/.>
