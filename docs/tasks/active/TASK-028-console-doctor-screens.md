---
title: "TASK-028: Console SCR-03 consult and orders + SCR-04 doctor worklist"
status: Active
fr: FR-03
owner: frontend-ui-dev
deps: TASK-026
priority: P1
phase: 2
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-028: Console SCR-03 consult and orders + SCR-04 doctor worklist

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree. Read the board row back after writing it:
a board write can fail silently while the task file lands.

## Goal

Replace the SCR-03 and SCR-04 stubs with the real doctor surfaces: a consult-and-orders screen
(reference triage, diagnosis entry, service orders from the catalog, sign-and-finalise, patient-code
scan) and a doctor worklist (today's slots/tasks + a chat-to-rearrange-my-day panel), on demo mock
data inside the console shell.

## Inputs and context

- Related FR: [FR-03](../../specs/05-functional-requirements.md#fr-03) (diagnosis/order capture, the
  doctor-only clinical boundary BR-05/CO-02), [FR-17](../../specs/05-functional-requirements.md#fr-17)
  (patient-code scan), [FR-08](../../specs/05-functional-requirements.md#fr-08) (worklist/slots),
  [FR-14](../../specs/05-functional-requirements.md#fr-14) (chat reorder, Could)
- Screen specs: [spec 10 SCR-03](../../specs/10-ui-ux-wireframes.md#scr-03-consult-and-orders),
  [spec 10 SCR-04](../../specs/10-ui-ux-wireframes.md#scr-04-doctor-worklist). Both visible to
  `doctor` only (TASK-026 role->screen contract).
- Access control: [spec 06](../../specs/06-access-control.md) - doctor scope is Assigned / Own worklist.
- Enums stay English/UPPER_SNAKE (`.claude/rules/coding-standards.md`): task/order statuses.
- Foundation: `frontend/src/console/` shell + the SCR-03/04 routes and stubs from TASK-026.

## To do

- [ ] Console mock-data for doctor screens (synthetic): a patient summary + reference triage, a
      `ServiceType` catalog, the signed-in doctor's slots/tasks. Under `src/console/`.
- [ ] SCR-03: patient summary + read-only reference triage labelled "AI reference - not a diagnosis"
      (NFR-USE-05); diagnosis entry (required before ordering); add-order select from the ServiceType
      catalog; sign-and-finalise button; patient-code scan control (FR-17). Diagnosis-before-order and
      doctor-only ordering enforced in the UI flow (the real write boundary is backend/CO-02, out of
      scope here - note it).
- [ ] SCR-03 states: empty (blank form + reference triage), loading, error, success (signed;
      care-plan-generating indicator).
- [ ] SCR-04: today's worklist as a sortable table of slots/tasks (Own worklist only); a chat panel
      to request a rearrange whose result is AI-labelled and requires confirm/cancel; on chat failure
      hold the current schedule.
- [ ] SCR-04 states: empty ("no cases today"), loading skeleton, error, success (rearranged and
      confirmed).
- [ ] Vitest coverage: order add is blocked until a diagnosis exists; sign transitions to the
      success state; scan control emits a mock scan event; worklist shows only the own schedule; chat
      reorder result is AI-labelled and confirm/cancel works; chat failure holds the schedule.

## Acceptance criteria

- [ ] A `doctor` reaches SCR-03 and SCR-04; other roles cannot (TASK-026 contract) - unchanged.
- [ ] Reference triage is clearly labelled AI reference and is read-only; a service order cannot be
      added before a diagnosis is entered (FR-03, BR-05); sign moves the screen to the signed/success
      state.
- [ ] The worklist shows only the signed-in doctor's slots/tasks and is sortable; the chat-reorder
      result is AI-labelled and applied only on explicit confirm; a chat failure leaves the schedule
      unchanged.
- [ ] The patient-code scan control produces a (mock) `ScanEvent` (FR-17).
- [ ] Built from shared primitives/tokens (use the ListRow/Timeline/StatusChip primitives and a real
      sortable table primitive - add one if missing, exported and tested; no raw native select/table
      per frontend.md); no emoji; patient app unaffected. Typecheck + Vitest pass under node v22,
      recorded in the log.

## Decisions and blockers

- Mock data only; wiring to the real Care Plan / Intake / Journey agents (TASK-007..009) is later
  integration, not this task. The clinical write boundary (only a doctor path creates a ServiceOrder,
  CO-02) is enforced server-side in the backend tasks; here it is a UI-flow constraint only - state
  that in the code so it is not mistaken for the security boundary.

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator | Registered (Planned). Sequenced after TASK-027 (shares the console shell; serialize - one frontend-ui-dev at a time on src/console). | Planned |
| 2026-07-18 | orchestrator | Flipped to Active. Branch feat/TASK-028-console-doctor-screens stacked off the TASK-027 tip (3c7404e) so the combined console base is a single coherent runnable tip. Read SCR-03/SCR-04 spec 10 sections + acceptance criteria. Dispatching frontend-ui-dev to build test-first from shared primitives (node v22). Velocity mode: security-reviewer deferred to pre-PR batch per owner; test-first + tsc + Vitest + code-review kept. | Active |

## Result

<Filled at Done.>
