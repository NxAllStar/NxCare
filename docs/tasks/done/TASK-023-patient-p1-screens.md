---
title: "TASK-023: Patient P1 screens (notifications, settings, results, meds, recovery, billing, family, prep, journey-step)"
status: Done
fr: "FR-11, FR-15, FR-20, FR-21"
owner: frontend-ui-dev
deps: "TASK-022"
priority: P2
phase: 2
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-023: Patient P1 screens (time-permitting, after P0 is solid)

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree. Read the board row back after writing it.

## Goal

After the P0 golden path (TASK-022) is solid, build the PRD P1 patient screens, test-first:
`/notifications` (spec 10 SCR-09 patient), `/settings` (spec 10 SCR-10 patient), `/journey/step/:id`,
`/results`, `/medications`, `/recovery`, `/billing` (display-only, no money), `/family`, `/prep/:id`.
P2 screens stay placeholder stubs from TASK-021.

## Inputs and context

- Contract for the spec-backed screens: [spec 10](../../specs/10-ui-ux-wireframes.md) SCR-09
  (Notifications: paginated, read/unread, filter by type, Own-only; NOTE spec-10 SCR-09 has no
  Model-assisted table - no AI content here), SCR-10 (Settings: language VI/EN, notification channel
  in-app/SMS, logout; NOTE spec-10 SCR-10 Loading is "-" and has NO no-permission state - do not
  invent them).
- PRD elaboration (NO backing FR - rest on PRD section 7 open items, built under explicit user
  direction): [PRD-FR-12](../../requirements/PRD-FR-12-patient-mobile-app.md) M4 (`/results` records),
  M5 (`/medications`, `/recovery`), M6 (`/billing` - display-only per FR-05/AS-02), M7 (`/family`),
  M2 (`/prep/:id`), M3 (`/journey/step/:id`).
- Related FR (spec-backed only): FR-20 (notifications), FR-21 (language), FR-11/FR-15 (re-plan
  reason, simulated SMS channel).
- Entities: `Notification`, user prefs, plus mock shapes for records/meds/billing display.

## To do

- [x] `/notifications` (SCR-09): list paginated, read/unread, filter by type, Own-only; mark-read;
      empty/loading/error/no-permission/success.
- [x] `/settings` (SCR-10): language select (labels localise, codes stay English), notification
      channel (in-app/SMS simulated), logout; states per spec-10 exactly (no invented Loading/no-perm).
- [x] `/journey/step/:id`: per-step detail (ETA range, "why this order," wayfinding); AI content
      labelled where model-produced.
- [x] `/results`, `/medications`, `/recovery`: display-only records with the PRD safety guardrail
      (label within/outside reference range + "discuss with your doctor"; never infer disease).
- [x] `/billing`: DISPLAY-ONLY cost estimate / coverage / invoice history; NO wallet/card/QR, NO
      payment processing (spec 10 / FR-05 / AS-02 win over PRD M6).
- [x] `/family`: family-switcher UI stub; DO NOT implement cross-patient data access (spec 06 has no
      delegated-viewer scope - flag as open, mock the switcher shell only).
- [x] `/prep/:id`: pre-visit prep reminders (fasting etc.).
- [x] Vitest component test per screen, written first and failing first, naming the criterion proven.

## Acceptance criteria

- [x] SCR-09 renders read/unread + filter + mark-read; Own-scope only; no AI-labelled content.
- [x] SCR-10 renders language (VI<->EN, codes stay English) + channel + logout; matches spec-10
      states exactly (no unrequested Loading spinner or no-permission state).
- [x] `/billing` shows amounts/coverage as display-only; there is no payment form anywhere.
- [x] `/results|/medications|/recovery` never infer diagnosis/prognosis; abnormal results carry the
      "discuss with your doctor" guardrail.
- [x] `/family` does not expose another patient's Own-scope data (switcher shell only, flagged open).
- [x] `npm run build`, `npm run typecheck`, `npm run test` all pass.

## Decisions and blockers

- DECISION: P1 is built only after P0 (TASK-022) is solid; if time runs short, P1 screens degrade to
  documented placeholders rather than half-built flows.
- BLOCKER (design, not build-stopping): `/family` cross-patient access and the M4/M5/M6/M7 modules
  have NO backing FR and rest on PRD section 7 open items (owner: Team lead). Built as UI shells under
  explicit user direction; not to be treated as accepted contract.

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator | Registered TASK-023 for the P1 patient screens (time-permitting) | Planned |
| 2026-07-18 | orchestrator | Flipped to Active (owner frontend-ui-dev); dispatching P1 screen build test-first, continuation after TASK-021/022 Done | Active |
| 2026-07-18 | frontend-ui-dev | Added TASK-023 P1 mock types/fixtures (`NotificationType`, `ReferenceRangeStatus`, `RecoverySeverity`, `StepDetail`, `LabResult`, `Medication`, `RecoveryCheckIn`, `BillingEstimate`, `Invoice`, `FamilyProfile`, `PrepReminder`) in `frontend/src/lib/api/types.ts` + `fixtures.ts`, and new isolated mock api modules `notifications.ts`, `settings.ts`, `records.ts`, `billing.ts`, `family.ts`, `prep.ts`, `journeyStep.ts` (all barrel-exported from `index.ts`) | Done |
| 2026-07-18 | frontend-ui-dev | Built `/notifications` (SCR-09) test-first: `NotificationsPage.test.tsx` written first (8 cases: loading/empty/success/read-unread/own-scope/no-AI-chip/filter-by-type/mark-read/pagination/error), then `NotificationsPage.tsx` to green. Confirms own-scope only, paginated (3/page), filter by type, mark-read, and deliberately NO AIChip anywhere (spec-10 SCR-09 has no Model-assisted row) | 8/8 passed |
| 2026-07-18 | frontend-ui-dev | Built `/settings` (SCR-10) test-first: `SettingsPage.test.tsx` (5 cases), then `SettingsPage.tsx`. Does NOT use the shared `ScreenState` wrapper - spec-10 SCR-10's own states table governs exactly ("Loading: -", no no-permission row); asserted their absence directly. Covers FR-21 (VI/EN toggle, codes stay English), channel select (in-app/SMS via `lib/api/settings.ts`, synchronous - no fetch delay per "Loading: -"), invalid-choice error path, and FR-18 logout | 5/5 passed |
| 2026-07-18 | frontend-ui-dev | Built `/journey/step/:id` test-first: `JourneyStepPage.test.tsx` (5 cases), then `JourneyStepPage.tsx`. ETA range, "why this order" (AIChip, NFR-USE-05), wayfinding, queue position; `getJourneyStep(patientId, taskId)` in `journeyStep.ts` verifies the task's care-plan ownership before returning it (own-scope mirror, NFR-SEC-05); a foreign/unknown task id renders not-found | 5/5 passed |
| 2026-07-18 | frontend-ui-dev | Built `/results`, `/medications`, `/recovery` (PMA-M4/M5, no backing FR - PRD-FR-12 section 7 open item) test-first, one test file per screen (5+5+5 cases). Safety guardrail asserted directly: `/results` labels only within/outside reference range with "discuss with your doctor" on the abnormal one only, never a diagnosis; `/medications` AIChips only the entry with a real `interactionWarning`; `/recovery` shows the escalation banner + "contact your doctor" only for `RecoverySeverity.WARNING`, never a treatment recommendation | 15/15 passed |
| 2026-07-18 | frontend-ui-dev | Built `/billing` (PMA-M6) test-first: `BillingPage.test.tsx` (5 cases) then `BillingPage.tsx`. DECISION enforced: FR-05/AS-02 win over PRD-FR-12 M6's "online payment" line - screen renders cost estimate, BHYT coverage, co-pay, and invoice history (via `StatusChip` for PAID/UNPAID) with a display-only notice; test explicitly asserts absence of any `<form>`, and of any button/link named like pay/checkout/wallet/thẻ/QR | 5/5 passed |
| 2026-07-18 | frontend-ui-dev | Built `/family` (PMA-M7) switcher-shell test-first: `FamilyPage.test.tsx` (5 cases) then `FamilyPage.tsx`. DECISION enforced: spec 06 has no delegated-viewer scope, so selecting a non-self profile only flips local UI state to a "not implemented" notice and the test asserts `patientApi.getPatient` is never called for that path - no cross-patient Own-scope fetch happens at all | 5/5 passed |
| 2026-07-18 | frontend-ui-dev | Built `/prep/:id` (PMA-M2) test-first: `PrepPage.test.tsx` (4 cases) then `PrepPage.tsx` - loading/success/not-found/error, reminders read from `lib/api/prep.ts` | 4/4 passed |
| 2026-07-18 | frontend-ui-dev | Wired all 9 screens into `frontend/src/routes/routeConfig.tsx` (renamed `P0_SCREEN_COMPONENTS` -> `SCREEN_COMPONENTS`, now covering both TASK-022 and TASK-023 real routes); updated the one existing `routeConfig.test.tsx` case that expected the `/notifications` PlaceholderScreen to instead assert the real screen renders. P2 routes (`/welcome`, `/telehealth`, `/emergency`, `/wellness`, `/journey/updates`) left untouched as PlaceholderScreen, out of scope | Done |
| 2026-07-18 | frontend-ui-dev | Final gates from `frontend/`: `npm run typecheck` (tsc -b --noEmit) clean, no errors; `npm run test -- --run` (Vitest) 24 test files / 123 tests passed, 0 failed; `npm run build` (tsc -b && vite build) succeeded, `dist/` emitted (index-CvicnPHd.js 395.98 kB / gzip 121.13 kB) | typecheck clean / 123 passed / build OK |
| 2026-07-18 | orchestrator | Independently re-ran all gates (did not trust self-report): `npm run typecheck` clean; `npm run test -- --run` 24 files / 123 tests passed; `npm run build` OK (dist emitted); `npx playwright test --list` shows only the intended single smoke spec (1 test in 1 file, no stray e2e). Verified diff in-scope (only frontend/src + this task file; settings.json unchanged by this batch); spot-checked load-bearing assertions in code (billing no-payment-form, notifications no-AIChip, settings no invented Loading/no-perm, results doctor-guardrail on abnormal only) | Gates green, AC verified |
| 2026-07-18 | orchestrator | MISSION COMPLETE - all AC met and verified; review/secret-scan/e2e gates deferred to TASK-024 by design; no commit/PR this run | Done |

## Result

All nine P1 patient screens implemented test-first and wired into `frontend/src/routes/routeConfig.tsx`,
each replacing its PlaceholderScreen; P2 routes remain stubs (out of scope):

- `/notifications` (SCR-09) - paginated, read/unread, filter-by-type, mark-read, own-scope only, no AIChip.
- `/settings` (SCR-10) - VI/EN toggle (codes stay English), in-app/SMS channel, logout; spec-10 state set exactly.
- `/journey/step/:id` - ETA range, AI-chipped "why this order", wayfinding, own-scope ownership check.
- `/results`, `/medications`, `/recovery` - display-only records; abnormal values carry the "discuss with
  your doctor" guardrail; no diagnosis/prognosis inferred.
- `/billing` - display-only estimate/coverage/invoice history; verified NO payment form/button/QR anywhere
  (FR-05/AS-02 win over PRD M6).
- `/family` - switcher shell only; no cross-patient data path (spec 06 has no delegated-viewer scope; flagged open).
- `/prep/:id` - pre-visit prep reminders.

Gates (independently re-run by the orchestrator): typecheck clean, Vitest 123/123 passed (24 files),
build OK, Playwright discovers only the intended smoke spec. Mock-data-only, no backend calls, no commit/PR.
Open PRD items (M4-M7, family cross-patient) built as flagged UI shells under explicit user direction, not
accepted contract. Review + security-review + secret-scan + e2e gates are TASK-024's scope.
