---
title: "TASK-016: Denormalize a resolvable patient link onto owned entities"
status: Done
fr: "FR-18"
owner: tuan.nguyen15
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

- [x] Add the patient reference field to Diagnosis, ServiceOrder, Slot, Payment, AuditLogEntry.
- [x] Update the data dictionary (`.claude/rules/data-model.md` / docs data model) in the same change.
- [x] Confirm the Own-scope check resolves through the new field.

## Acceptance criteria

- [x] Each listed entity carries a resolvable patient link.
- [x] Own-scope authz covers all five entities via the link.
- [x] Data dictionary updated in the same PR as the schema change.

## Decisions and blockers

- <decision or blocker>

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator | Created task file from template so the data lane can claim it | Planned |
| 2026-07-18 | tuan.nguyen15 | Claimed task, created branch feat/TASK-016-denormalize-patient-link off cnv-dev | Active |
| 2026-07-18 | tuan.nguyen15 | Implemented: patient_id on Diagnosis/ServiceOrder/Slot/Payment (required) + AuditLogEntry (nullable); is_own docstring; AuditLog.record optional patient_id param; fixed call sites; new is_own tests; updated 08-data-model.md + 13-revision-history.md | Uncommitted on branch |
| 2026-07-18 | orchestrator | Verified working tree: 8 in-scope files changed. Re-ran gates myself: pytest 73 passed (baseline 70, +3), ruff clean. Read full diff - source, tests, docs all in scope and correct | Verified |
| 2026-07-18 | spec-guardian | Requirement-drift check vs FR-18 + 3 acceptance criteria: all PASS, no drift; BR-05 write boundary untouched; AuditLogEntry nullable fail-closed confirmed | Passed - no drift |
| 2026-07-18 | code-reviewer | Code-quality review of uncommitted diff; independently ran pytest 73 passed, ruff clean; is_own resolves all 5 entities, null AuditLogEntry fails closed; no missed call sites | Reviewed - no blockers; 2 Minor, 3 Info |
| 2026-07-18 | security-reviewer | Access-control review: cross-patient denied, account.patient_id None denied, AuditLogEntry-unset fails closed; no secrets/PII (synthetic UUIDs only) | Reviewed - no blockers; 1 Minor, 2 Info |
| 2026-07-18 | orchestrator | /secret-scan on diff: no credentials, no forbidden files, no JWT-shaped strings (only synthetic uuid4()/placeholder examples; "sk-" grep hits were the "SK-0" in "TASK-01x", false positive) | Clean |
| 2026-07-18 | orchestrator | Registered TASK-031 for the reviewers' shared follow-up (enforce denormalized patient_id invariant at write boundaries + thread patient context into audit). Committed on branch; moved TASK-016 to Done | Done |
| 2026-07-18 | tuan.nguyen15 | Committed the previously-excluded `.gitignore` `*.pyc` hygiene edit as `75aeeee` (conventional `fix:` message); branch HEAD is now `75aeeee` | Committed |
| 2026-07-18 | orchestrator | Fresh-session re-verification for push: working tree clean (no stray untracked/uncommitted files); correct diff base is `cnv-dev` (main and cnv-dev are unrelated histories, no merge-base, so `main...` is empty); diff touches the 8 code/spec files + docs/tasks (TASK-016 move, TASK-031, board) + `.gitignore`; re-ran pytest 73 passed and ruff clean; all four gates confirmed logged above; no CI configured (no `.github/workflows/`). Ready to push | Verified - ready |
| 2026-07-18 | orchestrator | Pushed branch to origin (`git push -u origin feat/TASK-016-denormalize-patient-link`). PR/merge left for the human owner - author does not merge own change (git-workflow.md) | Pushed |

## Result

Delivered: a required `patient_id` on `Diagnosis`, `ServiceOrder`, `Slot`, `Payment` and a nullable
`patient_id` on `AuditLogEntry`, so `src/vaic/auth/scope.py::is_own` resolves all five on its existing
direct-field branch (no `is_own` logic change needed). `AuditLog.record` gained an optional
`patient_id` param (backward compatible). Data dictionary (`docs/specs/08-data-model.md`, incl. a new
`Slot` section) and revision history (2.2) updated in the same change. Tests: `tests/test_auth.py`
gained own-vs-other coverage for all four required entities plus AuditLogEntry set/unset fail-closed;
`tests/test_models.py` and `tests/test_agent_core.py` call sites fixed for the new required fields.
pytest 73 passed, ruff clean. All three gates passed with no blockers.

Follow-up: the denormalized `patient_id` is an authz-critical invariant not yet enforced in code
(both reviewers) - tracked as TASK-031. No production write path constructs these four entities yet,
so the risk is latent.

Commit: on branch `feat/TASK-016-denormalize-patient-link` (see board), HEAD `75aeeee`. NOT yet
merged - the author does not merge their own reviewed change; merge/PR awaits the owner's decision.
The `.gitignore` `*.pyc` hygiene edit that Wave-1 close-out had left in the working tree was
subsequently committed by the owner as `75aeeee` with a conventional `fix:` message (it is now part
of the branch's committed diff, not an uncommitted change).
