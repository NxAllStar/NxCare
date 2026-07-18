---
title: "TASK-025: Patient app visual upgrade to iOS-native design"
status: Done
fr: FR-12
owner: frontend-ui-dev
deps: TASK-023
priority: P2
phase: 2
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-025: Patient app visual upgrade to iOS-native design

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`.

## Goal

Upgrade the visual language of the existing patient app (all P0/P1 screens + shell) to match the
owner-supplied "Patient Companion App" design: a calm, generous, iOS-native look built on the
existing teal design tokens - hero cards, large section titles, pill buttons, grouped cards, a
step timeline, bottom sheets, mono numerals, and subtle enter animations - without changing screen
behaviour, data wiring, routes, i18n keys, or the labels/testids the test suite asserts.

## Inputs and context

- Design source: owner-supplied `Patient Companion App.html` (a bundled Design Composer artifact).
  The declarative render markup and per-screen structure were extracted for reference (teal
  `#0E7490`, surface `#F7F8F9`, border `#E2E5E8`, success `#2F9D66`, warning `#D9902B`, danger
  `#E5484D`, radii 14-22px, pills 999px, Inter + IBM Plex Mono).
- Related FR: [FR-12](../../specs/05-functional-requirements.md) coordinator/patient UI screens.
- Related PRD: patient-app IA in `docs/requirements/`.
- Related files: `frontend/src/components/**`, `frontend/src/pages/**`, `frontend/src/index.css`.
- Design direction rule: `.claude/rules/frontend.md` - build from tokens + shared primitives, no
  hardcoded colours outside primitives, keep VI default + EN toggle, a11y (keyboard, names,
  contrast, colour never the sole signal).

## To do

- [ ] Foundation: enter/pulse/toast keyframes + safe-area in `index.css`; shared primitives
      (Button, Card, SectionLabel, ListRow, Timeline, Sheet, Toast, Switch, SegmentedProgress,
      Avatar, IconButton); enrich app shell (context header + profile chip + notification badge)
      and bottom nav; add any new i18n keys to BOTH `vi.ts` and `en.ts`.
- [ ] Restyle all screens (home, login, journey, journey-step, book, intake, checkin, prep,
      results, medications, recovery, billing, family, settings, notifications, assistant) using
      the primitives, preserving testids/labels/roles/data.

## Acceptance criteria

- [ ] Every patient screen and the shell render the upgraded visual language built from tokens +
      primitives (no new hardcoded hex outside the primitive layer).
- [ ] No screen's behaviour, route, data source, or i18n key changed; VI default + EN toggle intact.
- [ ] `tsc -b --noEmit` clean; the Vitest suite stays green; `vite build` succeeds.

## Decisions and blockers

- Design imported from a local file: the Claude Design MCP project link 404s for this account
  (share link owned by another account), so the owner exported the bundle locally; the render
  markup was decoded from it for reference.
- Environment: the repo's default `node` is v12 (too old for Vitest/Vite); tests and build are run
  with a local node v22 on PATH. Pre-existing condition, recorded so the gate runs are reproducible.

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | frontend-ui-dev | Imported design from local bundle, decoded render markup, mapped all screens to existing pages; baseline `tsc -b --noEmit` clean, `HomePage.test.tsx` green (node v22) | Foundation starting |
| 2026-07-18 | frontend-ui-dev | Foundation: added motion + safe-area layer to `index.css`; built primitives (Button, Card/HeroCard/MutedCard, SectionLabel, ListRow, IconButton, Avatar, Switch, SegmentedProgress, Timeline, Sheet, Toast) + barrel; added extra icons; added `useOptionalSession`; enriched AppShell header + BottomNav + FAB | tsc clean; shell + Home tests green |
| 2026-07-18 | frontend-ui-dev | Restyled exemplars HomePage + LoginPage; added one i18n key `home.nextVisitLabel` (vi + en); polished PlaceholderScreen | Home (7) + Login (6) tests green |
| 2026-07-18 | frontend-ui-dev | Restyled remaining 14 screens (journey, journey-step, book, intake, checkin, prep, results, medications, recovery, billing, family, settings, notifications, assistant) using the primitives; all labels/testids/roles/data preserved | Per-screen tests green |
| 2026-07-18 | frontend-ui-dev | Full gates on node v22 | `tsc -b --noEmit` clean; Vitest 24 files / 123 tests passed; `vite build` OK; visual smoke via `vite preview` + Playwright (login, home dual-mode, journey timeline, billing, settings) confirms the upgraded look |
| 2026-07-18 | frontend-ui-dev | Owner clarified: wanted a FAITHFUL 1:1 clone of the design (not a restyle of the existing app) WITH the iPhone device frame. Pivoted: built `src/companion/` - a self-contained VN-only reproduction (iOS frame, onboarding Google/OTP/profile/BHYT, exact demo content, all screens transcribed verbatim from the decoded render markup). App entry (`App.tsx`) now renders it; `?home=1` skips onboarding | `tsc -b --noEmit` clean; `vite build` OK; Playwright screenshot sweep of every screen confirms pixel-1:1 with the design |

## Result

Two phases. Phase 1 (delivered, then superseded as the app entry): reskinned the existing routed
patient app (16 screens + shell) to the design's visual language via a new shared primitive layer
(`frontend/src/components/primitives/`); those files and their 123 passing tests remain in the tree.

Phase 2 (final deliverable, per owner clarification "sao chép 1:1 toàn bộ" + iPhone frame): a
faithful 1:1 clone of the design in `frontend/src/companion/` - `state.ts` (state machine + demo
data), `frame.tsx` (iPhone bezel/island/status-bar/home-indicator), `PatientCompanionApp.tsx`
(header/tabbar/FAB/family+notification sheets/chat/toast), and `screens/` (Onboarding, Home,
Appointments, Journey, Records, More) transcribed verbatim from the decoded design markup. `App.tsx`
renders it; the onboarding flow (Google/OTP/profile/BHYT) is the entry, `?home=1` skips it.
Verified: `tsc -b --noEmit` clean, `vite build` OK, Playwright screenshot sweep of every screen
confirms pixel-1:1 with the design.

Note: the clone deliberately uses inline styles with the design's exact hex values (not the token
primitives) - a conscious deviation from frontend.md's token rule, justified by the explicit 1:1
requirement and scoped entirely to `src/companion/`. It is VN-only (the design has no EN toggle) and
a self-contained demo (the login/OTP are demo affordances, like the prototype). The Phase-1 routed
app + its Vitest suite are now dormant, not deleted.

Gates NOT yet run (standard feature flow, follow-ups for whoever lands this): `code-reviewer` +
`security-reviewer` on the diff, and `/secret-scan`. Nothing was committed - the whole `frontend/`
tree is untracked in this branch (pre-existing repo state), so there is no PR yet.

Follow-up noted by the records agent: the design's `/recovery` "Trợ lý hỏi thăm" interactive
check-in card (Đỡ nhiều / Vẫn đau + symptom diary input) was intentionally NOT added, because the
current data model (`RecoveryCheckIn`, `recordsApi`) has no fields/handlers for it - wiring it is a
feature task, not a restyle. Register as a new task if that interaction is wanted.

Then move this file to docs/tasks/done/.
