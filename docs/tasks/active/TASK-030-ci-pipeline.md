---
title: "TASK-030: CI pipeline (GitHub Actions) - tests + lint on every PR"
status: Planned
fr: "-"
owner: devops
deps: "-"
priority: P2
phase: 3
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-030: CI pipeline (GitHub Actions) - tests + lint on every PR

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree. Read the board row back after writing it.

## Goal

A GitHub Actions workflow that runs the suites on every PR so "CI is green before merge" (git-workflow.md)
is actually enforced. Deferred: build it later, once a lane or two is producing mergeable code - it
is not on the critical path and no agent lane blocks on it.

## Inputs and context

- Related files and modules: `.github/workflows/` (currently empty), owned by the `devops` seat.
- Rule it satisfies: `.claude/rules/git-workflow.md` - "CI (GitHub Actions) is green and terminal
  before merge - pending is not green."
- Commands as run (tech-stack.md): `pytest`, `ruff check .`, `npm test` (Vitest), `npm run build`.

## To do

- [ ] `.github/workflows/ci.yml`: on pull_request, run `ruff check .` + `pytest` (backend) and
      `npm test` + `npm run build` (frontend).
- [ ] Report pass/fail as a required status check. It REPORTS; it never merges (humans decide).
- [ ] External providers mocked; no real network calls in CI (testing.md).

## Acceptance criteria

- [ ] A PR with a failing test or lint error shows a red, terminal check.
- [ ] A green run is terminal (not pending) before a human merges.
- [ ] CI performs no merge, deploy, or status write on its own.

## Decisions and blockers

- DECISION: deferred by owner request - build after the first lanes land code, not up front.

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator | Registered CI task, deferred (build later) | Planned |

## Result

<Filled when the task moves to Done.>
