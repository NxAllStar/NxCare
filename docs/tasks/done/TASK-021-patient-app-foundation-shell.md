---
title: "TASK-021: Patient app foundation, shell, nav, auth-login, i18n, mock-data layer"
status: Done
fr: "FR-12, FR-18, FR-21"
owner: frontend-ui-dev
deps: "TASK-019"
priority: P1
phase: 2
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-021: Patient app foundation, shell, nav, auth-login, i18n, mock-data layer

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree. Read the board row back after writing it.

## Goal

Build the patient mobile-app foundation the screen batches sit on: a mobile-first responsive shell
with the 5-tab bottom nav and FAB, role-gated routing (patient path), the patient slice of the login
(SCR-08), VI-default i18n (VI/EN) with English codes/enums, an isolated mock-data layer conforming to
`src/vaic/models/entities.py`, and the shared UI primitives (AI-content chip, status chips, the
five-state wrappers empty/loading/error/no-permission/success). Test tooling (Vitest + Playwright +
Testing Library + router) is installed here.

## Inputs and context

- Contract: [spec 10](../../specs/10-ui-ux-wireframes.md) - SCR-08 (patient slice), Visual design
  direction, Cross-cutting UI rules. Patient IA/sitemap and 5-tab nav:
  [PRD-FR-12 section 3.1/3.2](../../requirements/PRD-FR-12-patient-mobile-app.md#31-screen-sitemap).
- Related FR: [FR-18](../../specs/05-functional-requirements.md#fr-18) (auth/session, patient path),
  [FR-21](../../specs/05-functional-requirements.md#fr-21) (VI/EN language).
- Design system: `/design-system` command; tokens in `frontend/design-tokens.json`,
  `frontend/src/index.css`, `frontend/tailwind.config.ts` (already wired - do NOT re-scaffold).
- Entities for mock shapes: `src/vaic/models/entities.py`, `src/vaic/models/enums.py`,
  [spec 08](../../specs/08-data-model.md).
- Related files: `frontend/src/` (App shell, routing, `lib/api/` + `mocks/`, `components/`, `i18n/`).
- No backend API exists. Mock data only, clearly isolated, with `// TODO: replace with real API call`
  markers. No pretend integration.

## To do

- [x] Install and wire test tooling: Vitest, @testing-library/react, @testing-library/jest-dom,
      jsdom, Playwright; add `test`, `test:e2e`, `typecheck` scripts. External providers mocked.
- [x] Add routing (react-router or equivalent) with a patient-only route table; P2 routes
      (`/welcome`, `/telehealth`, `/emergency`, `/wellness`, `/journey/updates`) are placeholder stubs.
- [x] Mobile-first app shell: 5-tab bottom nav + FAB assistant entry (PRD IA), safe thumb reach.
- [x] Patient slice of SCR-08 Login (role entry, demo account/role selector, VI/EN toggle, no account
      enumeration on error) + a mock session/auth context that routes to the patient home.
- [x] i18n scaffold: VI default, EN toggle; display labels localised, codes/enums stay English.
- [x] Isolated mock-data layer under `frontend/src/lib/api/` (or `mocks/`) typed to the entities;
      obvious TODO markers; no network calls.
- [x] Shared primitives: AI-content chip ("Đề xuất bởi AI" / AI-suggested, NFR-USE-05), semantic
      status chips (done/waiting/blocked/in-progress), and the five-state wrapper
      (empty/loading/error/no-permission/success).
- [x] Vitest tests written test-first for the shell, login patient path, i18n toggle, and each
      primitive, each naming the acceptance criterion it proves.

## Acceptance criteria

- [x] `npm run build` and `npm run typecheck` pass; `npm run test` runs Vitest green.
- [x] Login (patient) authenticates a demo patient and routes to the patient home; error state does
      not reveal whether an account exists (spec 10 SCR-08 States).
- [x] The shell renders the 5-tab nav + FAB and is single-column mobile-first (Cross-cutting rules).
- [x] Language toggle switches VI<->EN labels while codes/enums stay English (FR-21, NFR-USE-03).
- [x] The mock-data layer is isolated, typed to the entities, and marked TODO; no real network call.
- [x] AI-content chip, status chips, and the five-state wrapper exist and are covered by tests.

## Decisions and blockers

- DECISION (orchestrator, 2026-07-18): Patient-only mission scope. Staff screens
  SCR-03/04/05/06/07/11 are NOT built. See orchestration notes below.
- DECISION: All UI work runs under the single owner `frontend-ui-dev` on the `frontend` branch,
  uncommitted, sequentially (batches share the shell/route-registry/mock-layer files, so no parallel
  worktrees - avoids same-file collisions). No commit/PR without explicit user go-ahead.

## Orchestration notes

- Mission narrowed mid-flight (user, 2026-07-18) from all-11-screens to PATIENT-ONLY, expanded into
  the fuller patient app per PRD-FR-12 priority order. This foundation task replaces the shell/nav/
  i18n portion of the parked TASK-015 and the auth-UI portion tied to TASK-013 (done, backend only).
- Stale scaffold-era placeholders TASK-011/014/015 are parked Pending (superseded); their in-scope
  parts (patient chat/timeline, notifications, settings) are folded into TASK-021/022/023.
- spec 10 wins on any conflict with the PRD (e.g. no money moves through the app - FR-05/AS-02).

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator | Registered TASK-021 for the patient-app foundation under the narrowed patient-only scope | Planned |
| 2026-07-18 | spec-guardian | Scope-lock returned: SCR-08/09/10 patient path + cross-cutting rules (VI-default labels, English enums BR-31, WCAG AA, AI-labelling, no-account-enumeration on login) locked as acceptance criteria | Locked |
| 2026-07-18 | orchestrator | Flipped to Active; dispatching frontend-ui-dev to build the foundation | Active |
| 2026-07-18 | frontend-ui-dev | Close-out gap: wired Playwright. Added `frontend/playwright.config.ts` (testDir: './e2e', single chromium project, webServer runs `npm run dev -- --port 4319 --strictPort` against `http://127.0.0.1:4319`, reuseExistingServer outside CI) and `frontend/e2e/smoke.spec.ts` (unauthenticated `/` redirects to `/login` and renders the VAIC app name, proving RouteGuard per `src/auth/RouteGuard.tsx` and `src/routes/routeConfig.tsx`). Ran `npx playwright install chromium` (succeeded, no sandbox block). `npx playwright test --list` shows exactly 1 test in `e2e/smoke.spec.ts` (no node_modules/node_modules.orig-rootowned scanned). `npm run test:e2e` executed the spec against a real booted dev server: 1 passed. `npm run typecheck` and `npm run test` (Vitest, 37 tests / 8 files) re-verified green after the change. No commit made (no user go-ahead). | Playwright wired and green; only remaining foundation to-do item closed |
| 2026-07-18 | orchestrator | Verified independently: read `frontend/playwright.config.ts` (testDir './e2e' confirmed) and `frontend/e2e/smoke.spec.ts` (real RouteGuard redirect assertion); re-ran `npx playwright test --list` (exactly 1 test, e2e-scoped, node_modules not walked) and `npm run typecheck` (exit 0). Earlier this session also confirmed `npm run typecheck`, `npm run test` (37 tests/8 files green), `npm run build` (dist produced), and mock-layer type fidelity: `src/lib/api/types.ts` mirrors `src/vaic/models/entities.py`/`enums.py` field-for-field (documented snake->camel boundary; UI-only additions Task.label, Notification.read/aiGenerated each annotated). All 8 to-do items and all 6 acceptance criteria met. Closing Done. | Done |

## Result

Patient-app foundation delivered and verified against all acceptance criteria. In `frontend/src/`:
mobile-first app shell with 5-tab BottomNav + assistant FAB (`components/shell/`), patient-only
route table with RouteGuard gating everything except `/login` (`routes/`, `auth/`), SCR-08 patient
login with no account-enumeration on error and a demo quick-select (`pages/LoginPage.tsx`), VI-default
i18n with EN toggle (`i18n/`, labels localised, codes/enums English), an isolated TODO-marked
mock-data layer typed to the backend entities (`lib/api/`), and the shared primitives AIChip /
StatusChip / ScreenState (five-state wrapper), each with its own Vitest file. Test tooling wired:
Vitest (37 tests/8 files green) and Playwright (config scoped to `e2e/`, smoke spec green against a
real dev server). typecheck and build both clean. No commit/PR (awaiting user go-ahead). Foundation
is ready for the TASK-022 P0 screens to build on.

<Filled when the task moves to Done.>
