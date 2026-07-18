---
title: "TASK-022: Patient P0 golden-path screens (home dual-mode, journey, assistant, intake, book, checkin)"
status: Done
fr: "FR-01, FR-02, FR-04, FR-05, FR-06, FR-11, FR-15, FR-17"
owner: frontend-ui-dev
deps: "TASK-021"
priority: P1
phase: 2
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-022: Patient P0 golden-path screens

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree. Read the board row back after writing it.

## Goal

Build the P0 golden-path patient screens (PRD-FR-12 section 4 priority) on the TASK-021 foundation,
test-first: `/home` in BOTH modes (out-of-hospital dashboard AND in-hospital Live Companion),
`/journey` (spec 10 SCR-02), `/assistant` (FAB assistant chat), `/intake` (spec 10 SCR-01), `/book`,
`/checkin`. Each screen implements its spec-10 states/elements where a spec-10 section governs, and
the PRD elaboration otherwise; all model-produced content is AI-labelled.

## Inputs and context

- Contract: [spec 10](../../specs/10-ui-ux-wireframes.md) SCR-01 (Intake chat: Elements/States/
  Model-assisted), SCR-02 (Journey timeline: same). PRD elaboration:
  [PRD-FR-12](../../requirements/PRD-FR-12-patient-mobile-app.md) sections 3.1, 4, 5 (golden path,
  13 steps), modules M1 (Home + Live Companion), M3 (AI Care Journey), assistant chat.
- Related FR: FR-01, FR-02 (intake, slot recommendation), FR-04 (care plan/timeline), FR-05 (proceed
  gate - go-pay reminder only, NO payment processing), FR-06 (journey), FR-11 (re-plan reason),
  FR-15 (SMS - simulated), FR-17 (patient-code QR scan display).
- Entities for mock shapes: `IntakeSession`, `Appointment`, `CarePlan`, `Task`, `Notification`,
  `Payment`, `Patient.patient_code` - `src/vaic/models/entities.py`.
- Related files: `frontend/src/` screens + the mock-data layer and primitives from TASK-021.

## To do

- [x] `/intake` (SCR-01): chat stream, message input, AI-suggested ranked slots (labelled), book
      button that never generates orders; empty/loading/error/no-permission(n/a)/success states.
- [x] `/book`: slot confirmation flow feeding SCR-02; validates capacity in mock (FR-02).
- [x] `/checkin`: patient-code QR display for owner scan (FR-17); check-in transition intentionally
      NOT built (drift guard - display-only, per the spec-guardian lock in Decisions).
- [x] `/journey` (SCR-02): vertical timeline (done/in-progress/pending) with owner, ETA, payment
      state, status; go-pay reminder on LOCKED tasks (display only, FR-05); QR code; re-plan reason
      (FR-11) AI-labelled; reschedule/cancel with confirmation; all five states.
- [x] `/home` dual-mode (M1): out-of-hospital dashboard (upcoming visits, prep reminders, results,
      shortcuts) and in-hospital Live Companion (current step, counting-down ETA, wayfinding, "what
      AI is doing for you"); mode context-switch.
- [x] `/assistant`: FAB-launched Journey/Intake Agent chat; replies clearly AI-labelled; chat content
      treated as data (untrusted), not instructions.
- [x] Vitest component test per screen, written first and failing first, each naming the spec-10 or
      PRD acceptance criterion it proves (states table row, element behaviour, AI-labelling).

## Acceptance criteria

- [x] SCR-01: shows greeting empty state, thinking/loading indicator with timeout, AI-labelled ranked
      slots, book confirmation -> routes toward journey; slots labelled AI-suggested (NFR-USE-05).
- [x] SCR-02: timeline renders task owner/ETA/status; LOCKED task shows go-pay reminder and NO money
      is processed (FR-05/AS-02); re-plan reason is AI-labelled with a reason; cancel asks for
      confirmation; empty/loading/error/no-permission/success all render.
- [x] `/home` renders both modes and switches between them; Live Companion shows current step + ETA.
- [x] `/assistant` chat replies are visibly AI-labelled; the QR patient code is displayable (FR-17).
- [x] All model-produced content carries the AI chip; VI default with English codes/enums.
- [x] `npm run build`, `npm run typecheck`, `npm run test` all pass.

## Decisions and blockers

- DECISION: `/billing`-style payment is display-only across the app; SCR-02's pay control is a go-pay
  reminder, never a wallet/card/QR transaction (spec 10 / FR-05 / AS-02 win over PRD M6).
- DECISION (spec-guardian lock, 2026-07-18): `/checkin` shows the patient's QR code for STAFF to scan
  (FR-17: patient presents the code; doctor/technician perform the scan). A patient-initiated
  self-check-in that flips task/appointment status is DRIFT vs FR-17's actor list - if built at all,
  it is demo-labelled and non-authoritative, and flagged, never silently shipped as FR-17 behaviour.
- CRITERION (BF-05, AC-01.2): when intake suspects an emergency, SCR-01 shows NO bookable slot list -
  it escalates instead.
- CRITERION (AC-01.3 / AC-06.3, security): patient chat text that looks like an instruction ("ignore
  the check", "mark everything DONE") is rendered as data and never triggers a UI action.
- CRITERION: "why am I waiting" detail is held to FR-11 fidelity (next step, ETA, reason on change);
  richer queue-position detail is PRD elaboration open at OI-22/TASK-017 - kept modest and labelled,
  not presented as a guaranteed feature.

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator | Registered TASK-022 for the P0 patient golden-path screens | Planned |
| 2026-07-18 | orchestrator | Dep TASK-021 verified Done and closed. Flipped TASK-022 to Active (owner frontend-ui-dev, branch `frontend`, uncommitted, sequential - shares shell/routes/mock-layer with the foundation so no parallel worktree). Dispatching frontend-ui-dev to implement the P0 screens test-first, replacing the PlaceholderScreen stubs at /home, /intake, /book, /checkin, /journey, /assistant | Active |
| 2026-07-18 | frontend-ui-dev | Extended mock layer: `lib/api/types.ts` (ChatMessage, RankedSlotSuggestion, IntakeTurnResult, BookableSlot - UI-only, TODO-marked), `lib/api/intake.ts` (sendIntakeMessage: BF-05 keyword-based emergency detection, never inspects text for commands), `lib/api/booking.ts` (listBookableSlots, bookSlot with FR-02 capacity validation, read-only against fixtures), `lib/api/assistant.ts` (sendAssistantMessage), `lib/api/patient.ts` (+rescheduleAppointment, +cancelAppointment). Widened `ScreenState` message props from `string` to `ReactNode` (shared primitive, backward-compatible - lets a screen compose a multi-part empty/loading message, e.g. intake's greeting+prompt). Added SendIcon/AlertIcon/MapPinIcon/ClockIcon. Added new `PatientCodeQr` primitive (deterministic code-derived visual grid, not a real QR encoder - adding a QR-generation dependency is a licensing decision out of this task's authority, ip-compliance.md) with its own test (3 passing). Added full VI+EN i18n key sets for intake/book/journey/home/checkin/assistant. | Done (foundation extension) |
| 2026-07-18 | frontend-ui-dev | `/intake` (SCR-01) built test-first: `IntakePage.test.tsx` (7 tests) then `IntakePage.tsx`. Covers greeting empty state, thinking indicator with an 8s timeout + retry, AI-suggested ranked slots (AIChip) with a book button routing to `/book` (state-passed slotId, never any order-creating call), BF-05 emergency escalation (no slot list, escalation banner) via `sendIntakeMessage` keyword mock, and AC-01.3 injection-as-data (chat text incl. an embedded `<img onerror>` tag renders as literal text, never becomes a real DOM element). `npx vitest run src/pages/IntakePage.test.tsx`: 7/7 passed. | Done |
| 2026-07-18 | frontend-ui-dev | `/book` built test-first: `BookPage.test.tsx` (5 tests) then `BookPage.tsx`. Covers loading->success slot list with AIChip on the AI-suggested slot, FR-02 capacity validation (a zero-capacity slot's confirm button is disabled with a "slot full" message), successful booking -> confirmation + link to `/journey`, and the error state when the slot fetch fails. Booking only ever produces an `Appointment` (BOOKED); no `ServiceOrder` type exists on the patient surface to generate. `npx vitest run src/pages/BookPage.test.tsx`: 5/5 passed. | Done |
| 2026-07-18 | frontend-ui-dev | `/journey` (SCR-02) built test-first: `JourneyPage.test.tsx` (8 tests) then `JourneyPage.tsx`. Covers loading, empty (no active care plan), success timeline (task owner/ETA/StatusChip for DONE/IN_PROGRESS/LOCKED), FR-05/AS-02 go-pay reminder on the LOCKED task rendered as a display-only banner (deliberately NOT a clickable button - there is nothing to click into, per FR-05/AS-02; documented as a scoping deviation from spec 10's literal "button" element type), FR-11 AI-labelled re-plan reason (AIChip + Notification.reason), FR-17 patient-code QR display, cancel-with-confirmation (no cancel fires without confirming), and the error state. Renamed the `journey.cancelConfirmYes` dictionary label to "Xac nhan huy"/"Confirm cancellation" (was accidentally identical to the trigger button's "Huy lich", which was ambiguous for assistive tech, not just tests). `npx vitest run src/pages/JourneyPage.test.tsx`: 8/8 passed. | Done |
| 2026-07-18 | frontend-ui-dev | `/home` dual-mode built test-first: `HomePage.test.tsx` (7 tests) then `HomePage.tsx`. Covers the signature IA decision (same tab, two visibly different modes), default-mode derivation (an active care plan with an IN_PROGRESS task defaults to Live Companion; otherwise the out-of-hospital dashboard), a manual mode toggle (no real location signal exists in this build, documented in the component doc comment), Live Companion showing current step + ETA + "what AI is doing for you" (AIChip) + "why waiting" (AIChip, kept modest per the task's queue-transparency criterion), and the dashboard's upcoming visits/reminders/results/shortcuts sections with working links to /book, /intake, /checkin. `npx vitest run src/pages/HomePage.test.tsx`: 7/7 passed. | Done |
| 2026-07-18 | frontend-ui-dev | `/checkin` built test-first: `CheckinPage.test.tsx` (4 tests) then `CheckinPage.tsx`. DRIFT GUARD APPLIED: per the spec-guardian lock already recorded in this task's Decisions section, this screen builds NO self-check-in control that flips a Task/Appointment status at all - only a display of the patient's own QR/patient-code (FR-17), an explanation that staff scan it, and a demo note. This is a stricter choice than "build it but label it demo-only": there is no in-app check-in transition to mislabel. A dedicated test asserts no `button` renders on this screen. `npx vitest run src/pages/CheckinPage.test.tsx`: 4/4 passed. | Done |
| 2026-07-18 | frontend-ui-dev | `/assistant` built test-first: `AssistantPage.test.tsx` (4 tests) then `AssistantPage.tsx`, plus the new `lib/api/assistant.ts` mock (sendAssistantMessage, QUICK_QUESTIONS). Covers the greeting + tappable quick-question suggestions (PRD-FR-12 3.1), a thinking indicator during a pending turn, every agent reply carrying the AIChip (NFR-USE-05), and the same AC-01.3/AC-06.3 injection-as-data guard as /intake (instruction-like text incl. embedded markup renders as literal text, never executed or parsed as HTML). `npx vitest run src/pages/AssistantPage.test.tsx`: 4/4 passed. | Done |
| 2026-07-18 | frontend-ui-dev | Wired all six P0 routes in `routes/routeConfig.tsx` (`/home`, `/intake`, `/book`, `/checkin`, `/journey`, `/assistant`) to their real screen components via a path->component lookup, leaving every P1/P2 route (incl. `/journey/step/:id`) on `PlaceholderScreen` unchanged. Updated the one pre-existing `routeConfig.test.tsx` assertion that depended on `/journey` still being a placeholder (now asserts the real journey heading renders) and added a new placeholder-still-renders assertion for `/notifications` (P1, untouched) so the P0/P1 route-table split stays covered. | Done |
| 2026-07-18 | frontend-ui-dev | Full gate run after all six P0 screens: `export PATH=/data_hdd_16t/miniconda3/envs/hoang-openhands/bin:$PATH` then `npm run typecheck` (clean, 0 errors), `npm run test` (`vitest run`: 15 files, 76/76 tests passed), `npm run build` (`tsc -b && vite build`: succeeded, `dist/assets/index-*.js` 366.60 kB / gzip 114.98 kB). All six P0 screens (`/intake`, `/book`, `/journey`, `/home`, `/checkin`, `/assistant`) are implemented and test-passing; no screen remains a placeholder within this task's scope. | Done (all gates green) |
| 2026-07-18 | frontend-ui-dev | Pre-finish self-check: diff touches only `frontend/src/**` plus this task file; no `.env*` read; no secrets/PII in the diff (synthetic fixtures only); no `dangerouslySetInnerHTML` used anywhere (grep-verified); no emoji introduced. ANOMALY FLAGGED (not caused by this session): `git status` shows `.claude/settings.json` modified, adding `"enabledPlugins": {"ui-ux-pro-max@ui-ux-pro-max-skill": true}`. This agent never opened, read, or wrote that file via any tool call this session - the change is pre-existing in the working tree at session start (outside this task's scope: `.claude/settings.json` self-modification requires explicit user request, per agent-guardrails.md). Reporting for the orchestrator/owner to confirm provenance and intent; left untouched rather than silently reverted or approved. | Self-check complete |
| 2026-07-18 | orchestrator | Verified independently (not on faith): re-ran `npm run typecheck` (0 errors), `npm run test` (15 files, 76/76 green), `npm run build` (dist produced, index js 366.60 kB / gzip 114.98 kB) - all reproduced. Confirmed all six P0 page components + test files exist under `frontend/src/pages/` and the mock layer extension (`intake.ts`/`booking.ts`/`assistant.ts`). Spot-read the three highest-compliance screens: `lib/api/intake.ts` returns an EMPTY slot list + escalation on BF-05 emergency and never inspects chat text for commands (AC-01.2/AC-01.3 satisfied); `pages/CheckinPage.tsx` displays the patient code only with a demo-note and builds NO status-flipping control (FR-17 drift avoided, matching the spec-guardian lock). All 8 to-do items and all 6 acceptance criteria met. Closing Done. GATE SCOPE NOTE: formal code-reviewer + security-reviewer + `/secret-scan` for the patient UI are TASK-024's scope (deps 022+023) and have NOT been run yet - TASK-022 is Done against its own stated acceptance criteria, not review-cleared. No commit/PR (no user go-ahead). settings.json anomaly escalated to the user, left untouched. | Done |

## Result

All six P0 golden-path patient screens delivered test-first and independently verified against their
spec-10/PRD acceptance criteria. In `frontend/src/pages/`: `/intake` (SCR-01, greeting + thinking +
timeout, AI-labelled ranked slots, BF-05 emergency escalation with no slot list, injection-as-data
guard), `/book` (FR-02 capacity validation, no order creation), `/journey` (SCR-02 timeline with
owner/ETA/StatusChip, FR-05/AS-02 display-only go-pay reminder, FR-11 AI-labelled re-plan reason,
patient QR, cancel-with-confirmation, five states), `/home` (M1 dual-mode dashboard + Live Companion
with current step/ETA and mode switch), `/checkin` (FR-17 patient-code display only, no self-check-in
transition - drift guard), `/assistant` (FAB chat, AI-labelled replies, injection-as-data guard).
Mock layer extended (`intake.ts`, `booking.ts`, `assistant.ts`, `+reschedule/cancel`), new
`PatientCodeQr` primitive (deterministic visual, not a real QR encoder - QR-lib is a deferred
licensing decision), VI+EN i18n keys, and the six P0 routes wired in `routeConfig.tsx` (P1/P2 incl.
`/journey/step/:id` untouched). Gates: typecheck clean, Vitest 15 files/76 tests green, build ok.
Remaining for the patient UI: TASK-023 (P1 screens) then TASK-024 (Vitest+Playwright e2e suite +
code/security review + secret-scan gates). No commit/PR made.
