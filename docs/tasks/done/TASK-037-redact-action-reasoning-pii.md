---
title: "TASK-037: Guard the Action.reasoning free-text field against PII leakage"
status: Done
fr: "FR-13"
owner: agent-core-dev
deps: "TASK-004, TASK-007"
priority: P2
phase: 2
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-037: Guard the Action.reasoning free-text field against PII leakage

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree. Read the board row back after writing it.

## Goal

`Action.reasoning` is a free-text field written into the audit log. Nothing today stops a caller or
a model from writing patient-identifying text into it, which would then persist in an auditable,
committed-adjacent trail. Add a boundary check (schema constraint, redaction, or an explicit ban on
transcript-shaped content) so the audit log cannot become a PII channel.

## Inputs and context

- Origin: security-reviewer finding (Minor) on TASK-007 - `Action.reasoning` is a free-text PII
  channel; contrast with the `escalate_emergency` schema, which structurally excludes `transcript`
  via `extra=forbid` (D8 in TASK-007).
- Related files: `src/vaic/tools/` (Action schema, audit write path) - agent-core-dev's scope.

## To do

- [x] Decide the guard shape: structural (schema constraint), redaction, or length/content ban.
- [x] Apply it at the `Action.reasoning` write boundary, before the audit write.
- [x] Add a test proving injected PII-shaped text is rejected or redacted, not persisted verbatim.

## Acceptance criteria

- [x] `Action.reasoning` cannot carry unredacted patient-identifying free text into the audit log.
- [x] A test proves the guard, not just a docstring note.

## Decisions and blockers

- Redaction (not a hard ban) was the chosen guard shape: `src/vaic/tools/pii.py::redact_pii` scrubs
  emails and long contiguous digit runs (9+, phone/national-id/MRN-shaped) before `AuditLog.record`
  persists `reasoning` (`src/vaic/tools/audit.py`). Scope is deliberately precise, not exhaustive -
  it leaves short operational numbers ("blast radius 30") untouched so legitimate reasoning is never
  mangled; names remain a discipline rule, not a mechanical guard, since they are not
  pattern-detectable.

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator | Registered from TASK-007 review finding (reasoning-PII Minor) during TASK-007 close-out | Planned |
| 2026-07-19 | claude (merge review) | Verified `redact_pii` scrubs at the `AuditLog.record` write boundary and `tests/test_audit_pii.py` proves it against injected email/phone-shaped text; `pytest` green. Moved to Done and reconciled with `master-plan.md` (`feat/coordinator-disruption` branch had already shipped this, master-plan flip was previously unmatched by the task file/folder) | Done |

## Result

Implemented as `src/vaic/tools/pii.py::redact_pii`, called from `src/vaic/tools/audit.py::AuditLog.record`
before every audit write. `tests/test_audit_pii.py` covers email and long-digit-run redaction plus a
negative case (short operational numbers pass through unredacted).
