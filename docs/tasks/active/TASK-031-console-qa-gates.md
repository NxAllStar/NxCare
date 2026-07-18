---
title: "TASK-031: Console QA - Vitest sweep, e2e golden path, review gates"
status: Planned
fr: FR-12
owner: qa-test
deps: TASK-027, TASK-028, TASK-029, TASK-030
priority: P1
phase: 2
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-031: Console QA - Vitest sweep, e2e golden path, review gates

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree. Read the board row back after writing it:
a board write can fail silently while the task file lands.

## Goal

Close the hospital console out with a QA pass across all console screens: fill Vitest coverage gaps,
add a Playwright golden-path e2e (staff login -> role -> flagship approve/reject) covering the key
staff flows, and run the final review gates (code + security review, secret scan) before the console
is proposed for merge.

## Inputs and context

- Related FR: FR-12 and the console screen set (SCR-03..07), FR-18 (session/role).
- Depends on the real screens: TASK-027 (SCR-06), TASK-028 (SCR-03/04), TASK-029 (SCR-05),
  TASK-030 (SCR-07). Do not start until those are Done.
- Test tooling: Vitest (unit/component), Playwright (e2e). Coverage floor 80% for behavior
  (`.claude/rules/testing.md`); the role guard and the approve/reject audit path are critical paths
  and covered before the number is discussed.
- Node toolchain: default `node` is v12 and FAILS Vitest/Playwright; use the v22 binary on PATH
  (memory note "frontend-node-toolchain"). A gate counts as passed only when this task's session log
  records the actual command and result.

## To do

- [ ] Audit the per-screen Vitest suites (TASK-026..030) for gaps against each screen's acceptance
      criteria and the locked role->screen contract; add the missing cases. Every added test names the
      acceptance criterion it proves and mocks all external providers (none should be real).
- [ ] Playwright golden-path e2e: staff login (role selector) -> land on the role's default screen ->
      for coordinator, open the flagship dashboard and approve then reject a proposal (assert the
      audit entry and the queue change); assert a non-permitted role is redirected away from SCR-06.
- [ ] Confirm the patient companion app e2e/golden path still passes (console work must not regress
      the shipped patient app).
- [ ] Run the full frontend suite under node v22 and record the exact commands + results here.
- [ ] Route the console diff through `code-reviewer` + `security-reviewer` (parallel) and
      `/secret-scan`; record each run in this log. This task does not fix findings itself - it routes
      Blocking/Major findings back through the orchestrator to `frontend-ui-dev`.

## Acceptance criteria

- [ ] Vitest: every console screen's acceptance criteria have at least one asserting test; the role
      guard and the approve/reject audit path are covered; suite is green under node v22, recorded.
- [ ] Playwright golden path green: login -> role home -> coordinator approve+reject with audit
      assertion; non-permitted role redirected from SCR-06.
- [ ] The shipped patient app suite still passes (no regression).
- [ ] `code-reviewer`, `security-reviewer`, and `/secret-scan` have each run on the console diff with
      the result recorded here; no Blocker/Major outstanding.

## Decisions and blockers

- Blocked until TASK-027..030 are Done (needs the real screens to test). Registered now so the board
  is complete and the close-out gate is visible.

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator | Registered (Planned). Final console gate; blocked on TASK-027..030. | Planned |

## Result

<Filled at Done.>
