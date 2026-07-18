---
title: "TASK-030: Console SCR-07 admin and audit console"
status: Planned
fr: FR-13
owner: frontend-ui-dev
deps: TASK-026
priority: P2
phase: 2
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-030: Console SCR-07 admin and audit console

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree. Read the board row back after writing it:
a board write can fail silently while the task file lands.

## Goal

Replace the SCR-07 stub with the real admin and audit console: an append-only audit-log search (by
patient, actor, action) and a simulator seed/config surface (ServiceType, Resource) - with the
sub-element role split enforced (audit search readable by `admin` and `coordinator` read-only;
simulator seed/config `admin` only) - on demo mock data inside the console shell.

## Inputs and context

- Related FR: [FR-13](../../specs/05-functional-requirements.md#fr-13) (audit log)
- Screen spec: [spec 10 SCR-07](../../specs/10-ui-ux-wireframes.md#scr-07-admin-and-audit-console).
  Route visible to `admin` (full) and `coordinator` (audit read-only) per the TASK-026 role->screen
  contract - this task implements the SUB-ELEMENT split TASK-026 deferred.
- Access control: [spec 06](../../specs/06-access-control.md) - audit readable by `role_admin` and
  `role_coordinator` (coordinator read-only, cannot edit); seed/config `role_admin` only. Re-seed is a
  destructive action and needs a confirmation (spec 10 cross-cutting rules).
- Foundation: `frontend/src/console/` shell + the SCR-07 route/stub from TASK-026 (which already
  admits both coordinator and admin at the route level).

## To do

- [ ] Console mock-data for audit + config (synthetic): a set of append-only `AuditLogEntry` records
      (agent decisions, approvals, signs, blocked actions) searchable by patient/actor/action; a
      `ServiceType` + `Resource` config set. Under `src/console/`. No real personal data.
- [ ] Audit search pane: query by patient, actor, action; results table is read-only (append-only
      log). Visible to `admin` and `coordinator`.
- [ ] Simulator seed/config pane: view/edit ServiceType + Resource config; a re-seed action guarded
      by a confirmation. Visible and editable to `admin` ONLY - `coordinator` does not see or reach
      this pane (sub-element gating within the shared SCR-07 route).
- [ ] States: empty ("no audit entries"), loading skeleton, error, success (results shown / config
      saved).
- [ ] Vitest coverage: a `coordinator` sees the audit search but NOT the simulator seed/config pane
      and cannot invoke re-seed; an `admin` sees both; audit search filters by patient/actor/action;
      the audit result table exposes no mutation control; re-seed asks for confirmation.

## Acceptance criteria

- [ ] `admin` sees both audit search and simulator seed/config; `coordinator` sees audit search
      read-only and does NOT see or reach the seed/config pane (spec 06 sub-element split); no other
      role reaches SCR-07 (TASK-026 route guard).
- [ ] Audit search filters the append-only log by patient, actor, and action and offers no way to
      edit or delete an entry (FR-13).
- [ ] Re-seeding the simulator requires an explicit confirmation before it runs (cross-cutting
      destructive-action rule); available to `admin` only.
- [ ] Built from shared primitives/tokens (a real filterable table primitive; no raw native
      select/table); no emoji; patient app unaffected. Typecheck + Vitest pass under node v22,
      recorded in the log.

## Decisions and blockers

- Mock data only; wiring to the real audit log (TASK-004) and the SimPy simulator (TASK-006) is later
  integration. The client-side sub-element gating is UX, not the security boundary - the real
  server-side authz is agent-core-dev's (`src/vaic/auth/`); state that in the code.

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator | Registered (Planned). Sequenced after TASK-029 (shares the console shell; serialize). Implements the SCR-07 sub-element role split deferred by TASK-026. | Planned |

## Result

<Filled at Done.>
