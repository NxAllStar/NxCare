---
title: "TASK-032: Hospital landing page and entry portal"
status: Done
fr: -
owner: frontend-ui-dev
deps: TASK-025, TASK-026
priority: P2
phase: 2
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-032: Hospital landing page and entry portal

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree.

## Goal

Create a premium, high-fidelity responsive landing page at `/landing-page` and `/landing` that showcases the system features (VAIC Patient Companion App and NxCare Hospital Web Console) and provides launching points for the two distinct environments.

## Inputs and context

- Style guide: `frontend/src/index.css` (clinical trust teal and console blue HSL variables, Inter font).
- Shared primitives: `frontend/src/components/primitives/` (buttons, cards, badges, language toggler).
- Main App: `frontend/src/App.tsx` (route intercepting path routing).

## To do

- [x] Modify `frontend/src/App.tsx` to handle `/landing` and `/landing-page` routes.
- [x] Implement `frontend/src/pages/LandingPage.tsx` with modern responsive layout, interactive features, SVGs, and launches.
- [x] Build and verify correctness.

## Acceptance criteria

- [x] Accessing `/landing-page` or `/landing` renders a full-page responsive landing page.
- [x] The landing page showcases the system features in Vietnamese/English, honoring the calm medical aesthetics.
- [x] The landing page contains clear launch buttons to launch the Patient Companion App (`/?home=1` or `/`) and the Hospital Web Console (`/console`).

## Decisions and blockers

- *None*

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | frontend-ui-dev | Started TASK-032, created task files and plan | Active |
| 2026-07-18 | frontend-ui-dev | Coded LandingPage component and App.tsx routing | Done |
