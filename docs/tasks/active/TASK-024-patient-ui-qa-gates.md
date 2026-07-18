---
title: "TASK-024: Patient UI - QA suite, Playwright golden-path e2e, review gates"
status: Planned
fr: "-"
owner: qa-test
deps: "TASK-022, TASK-023"
priority: P1
phase: 2
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-024: Patient UI - QA suite, Playwright golden-path e2e, review gates

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree. Read the board row back after writing it.

## Goal

Run and green the full patient-UI Vitest suite, add Playwright end-to-end coverage for the patient
golden-path click-through (login -> intake -> journey timeline), then run the review gates
(`code-reviewer` + `security-reviewer` in parallel) and `/secret-scan`. No commit/PR without explicit
user go-ahead.

## Inputs and context

- Built surface: TASK-021 (foundation/shell/login/i18n/mock-layer/primitives), TASK-022 (P0 golden
  path), TASK-023 (P1 screens).
- Acceptance criteria to verify against: the spec-10 states/elements tables per screen + the
  spec-guardian lock (SCR-01/02/08/09/10 patient path; PRD golden-path screens as elaboration).
- External providers always mocked; a test making a real network call is a defect.

## To do

- [ ] Run the full Vitest suite; every screen has a component test naming the criterion it proves.
- [ ] Add a Playwright e2e smoke for the golden path: login (patient) -> intake chat -> book ->
      journey timeline renders.
- [ ] Dispatch `code-reviewer` and `security-reviewer` in parallel on the full working-tree diff.
- [ ] Run `/secret-scan`.
- [ ] Record every gate run in this session log (a gate counts as passed only when logged).

## Acceptance criteria

- [ ] `npm run test` (Vitest) is green; coverage target 80% acknowledged (report actual).
- [ ] Playwright golden-path smoke passes headless, no real network calls.
- [ ] `code-reviewer` and `security-reviewer` findings recorded and triaged; blockers fixed.
- [ ] `/secret-scan` clean (no secret/PII in the diff).

## Decisions and blockers

- DECISION: gates run once across the full patient-UI diff (single owner, single uncommitted tree),
  not per-batch.

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator | Registered TASK-024 for QA + Playwright golden path + review gates | Planned |

## Result

<Filled when the task moves to Done.>
