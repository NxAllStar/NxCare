---
title: "TASK-031: Enforce the denormalized patient_id invariant at write boundaries"
status: Planned
fr: "FR-18"
owner: agent-core-dev
deps: "TASK-016"
priority: P2
phase: 2
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-031: Enforce the denormalized patient_id invariant at write boundaries

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree. Read the board row back after writing it.

## Goal

Make the denormalized `patient_id` on Diagnosis/ServiceOrder/Slot/Payment/AuditLogEntry (added in
TASK-016) a controlled invariant, not just prose, so Own-scope authorization cannot be silently
subverted by a copy-at-write bug once production write paths for these entities land.

## Inputs and context

- Related FR: [FR-18](../../specs/05-functional-requirements.md#fr-18) (server-side authz, Own scope).
- Origin: security-reviewer and code-reviewer findings on TASK-016. Both flagged that authorization
  correctness on five entities now depends on the denormalized `patient_id` staying equal to the
  parent's patient, and nothing in code enforces or tests that equality - it lives only as a spec
  invariant in `docs/specs/08-data-model.md` ("phải khớp" / "must match" notes).
- Related files and modules: `src/vaic/tools/constraint_checker.py` (write-boundary checks),
  `src/vaic/tools/audit.py` (`AuditLog.record` currently stores `patient_id` unchecked),
  `src/vaic/agents/core/executor.py` (audit call sites carry no patient context to supply one),
  `src/vaic/auth/scope.py` (the consumer of the invariant).

## To do

- [ ] Add a write-boundary validator (or a repository-save assertion) that a denormalized
  `patient_id` equals its parent's: `Diagnosis.patient_id == Appointment.patient_id`,
  `ServiceOrder.patient_id == Diagnosis.patient_id`, `Slot.patient_id` == the patient of `task_id`
  via `Task.care_plan_id -> CarePlan.patient_id`, `Payment.patient_id` == the subject's patient.
- [ ] Thread patient context into `AuditLog.record` at the call sites that have it, so audit entries
  about a patient carry `patient_id` (today every entry created via `ActionExecutor` resolves
  `patient_id=None` and so is invisible to Own-scope - the FR-18 benefit for `AuditLogEntry` is
  presently unrealized).
- [ ] Confirm the Confidential `reasoning` field is projected out before an `AuditLogEntry` reaches a
  patient under Own-scope read (field-level minimization) - or record it as separately owned.

## Acceptance criteria

- [ ] A constructor/write path that sets `patient_id` mismatched from the resolved parent is rejected
  with a tested failure path (not silently stored).
- [ ] Audit entries created about a patient carry the correct `patient_id` and resolve under
  Own-scope; a test proves it.
- [ ] No cross-patient read is possible via a mismatched denormalized link.

## Decisions and blockers

- Deferred, not urgent: as of TASK-016 close-out there is no production write path that constructs
  Diagnosis/ServiceOrder/Slot/Payment, so the risk is latent. This task must land with (or before)
  the first such builder. Raised 2026-07-18 by the TASK-016 review gates.

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator | Registered from TASK-016 security/code review findings (unenforced authz invariant) | Planned |

## Result

<Filled when the task moves to Done.>
