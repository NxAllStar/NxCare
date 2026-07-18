---
title: "TASK-016: Denormalize a resolvable patient link onto owned entities"
status: Planned
fr: "FR-18"
owner: data-modeler
deps: "TASK-003"
priority: P2
phase: 2
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-016: Denormalize a resolvable patient link onto owned entities

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree. Read the board row back after writing it.

## Goal

Add a resolvable patient link onto Diagnosis, ServiceOrder, Slot, Payment, and AuditLogEntry so the
Own-scope authorization check (from TASK-013) covers them directly. Land this early in Wave 1: it
touches shared entities every agent lane reads.

## Inputs and context

- Related FR: [FR-18](../../specs/05-functional-requirements.md#fr-18) (server-side authz, Own scope).
- Related files and modules: `src/vaic/state/`, `src/vaic/models/` (data-modeler owns the schema).
- Origin: follow-up from TASK-013 (auth) - Own-scope needs a patient reference on these entities.

## To do

- [ ] Add the patient reference field to Diagnosis, ServiceOrder, Slot, Payment, AuditLogEntry.
- [ ] Update the data dictionary (`.claude/rules/data-model.md` / docs data model) in the same change.
- [ ] Confirm the Own-scope check resolves through the new field.

## Acceptance criteria

- [ ] Each listed entity carries a resolvable patient link.
- [ ] Own-scope authz covers all five entities via the link.
- [ ] Data dictionary updated in the same PR as the schema change.

## Decisions and blockers

- <decision or blocker>

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator | Created task file from template so the data lane can claim it | Planned |

## Result

<Filled when the task moves to Done.>
