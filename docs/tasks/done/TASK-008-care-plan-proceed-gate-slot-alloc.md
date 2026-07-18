---
title: "TASK-008: Care Plan + proceed gate + slot allocation"
status: Done
fr: "FR-03, FR-04, FR-05, FR-08"
owner: careplan-dev
branch: feat/TASK-008-care-plan-proceed-gate-slot-alloc
deps: "TASK-004, TASK-006"
priority: P1
phase: 2
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-008: Care Plan + proceed gate + slot allocation

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree. Read the board row back after writing it.

## Goal

Generate and sequence the care-plan task list, gate progress behind the proceed/paid flag, and
allocate station slots. This is the critical-path lane: Journey (TASK-009) and the demo depend on it.

## Inputs and context

- Related FR: [FR-03](../../specs/05-functional-requirements.md#fr-03) (backend capture),
  [FR-04](../../specs/05-functional-requirements.md#fr-04),
  [FR-05](../../specs/05-functional-requirements.md#fr-05),
  [FR-08](../../specs/05-functional-requirements.md#fr-08).
- Related files and modules: `src/vaic/agents/careplan/` (exclusive owner).
- Consumes: agent/tool framework + constraint checker + audit (TASK-004), simulator world (TASK-006).
- FR-23 generation half lands in TASK-027; keep the care-plan interface ready for it.

## To do

- [ ] Diagnosis/order capture backend (FR-03) and care-plan task-list generation + sequencing (FR-04).
- [ ] Proceed gate on the paid flag (FR-05); only PAID tasks advance (BR-10).
- [ ] Slot allocation across stations (FR-08).
- [ ] Tests first (pytest); external providers mocked.

## Acceptance criteria

- [x] Tracks FR-03/FR-04/FR-05/FR-08 acceptance criteria. (AC-03.1/03.2, 04.1/04.2, 05.1-05.4,
  08.1/08.2 each proven by a named test; qa-test verified strong assertions, 97% module coverage.)
- [x] Proceed gate blocks unpaid tasks; the gate is audit-logged. (confirm_payment via executor spine;
  start_task on UNPAID blocked+audited AC-05.3; BR-11 authorised-source predicate, swappable for OI-19.)
- [x] Care-plan and slot writes route through the constraint checker. (create_care_plan/create_task/
  activate_care_plan + allocate_slot all routed through ActionExecutor -> checker -> audit after the
  fix round; verified by orchestrator reading care_plan.py/slots.py.)

## Decisions and blockers

- Decision (2026-07-18, orchestrator): careplan-dev does NOT edit `src/vaic/tools/constraint_checker.py`
  (agent-core-dev scope). Capacity + no-owner-clash enforcement for `allocate_slot`, and
  authorised-source enforcement for the PAID flip (BR-11), live INSIDE careplan's own tool handlers.
  The existing checker rules (closed-room BR-16, doctor-only BR-05, unpaid-start BR-10) are inherited
  via the ActionExecutor spine. If the deterministic pre-check layer should also carry capacity logic,
  that is a follow-up routed to agent-core-dev, not an in-scope cross-boundary edit here.
- Decision (2026-07-18, orchestrator): TASK-008 implements TASK-level proceed gating only - the level
  every FR-05 AC names. `Payment.subject_type == APPOINTMENT` exists in the model but no AC exercises
  appointment-level gating; it is OUT of scope here and surfaced to ba-analyst as a spec/data-model
  coverage gap.
- Decision (2026-07-18, orchestrator): OI-19 (which staff role may perform the payment-confirmation
  scan) is open in the spec. The BR-36 role check is implemented as a NAMED, swappable predicate, not
  hardcoded, so the OI-19 ruling later needs no rewrite.
- Doc debt (spec-guardian finding): `docs/context/business-rules.md` is an unfilled template stub;
  BR-05..BR-11, BR-16, BR-36 live only in `docs/specs/05-functional-requirements.md`. Per docs-workflow
  this PR should populate the BRs this code enforces with an "Enforced in" pointer - routed to
  ba-analyst in parallel (disjoint `docs/` path).

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator | Created task file from template so the Care Plan lane can claim it | Planned |
| 2026-07-18 | Khang | Claimed task: branch feat/TASK-008-care-plan-proceed-gate-slot-alloc, deps TASK-004/006 verified Done | Active |
| 2026-07-18 | orchestrator | Resumed. Verified state: on branch, board+frontmatter Active/Khang, careplan/ absent, framework spine (executor+checker+audit) present with allocate_slot/create_service_order/start_task checker rules. Running standard feature flow | Active |
| 2026-07-18 | orchestrator | Dispatched spec-guardian to lock scope for FR-03/04/05/08 before code | Active |
| 2026-07-18 | spec-guardian | Scope locked: ACs 03.1/03.2, 04.1/04.2, 05.1-05.4, 08.1/08.2; BR-05/06/07/08/09/10/11/16/36 at write boundary; out-of-scope list confirmed. Findings: business-rules.md is a template stub; checker allocate_slot lacks capacity/clash guard; no payment write-path exists yet; OI-19 role open | Active |
| 2026-07-18 | orchestrator | Recorded scope decisions; dispatching careplan-dev (impl, test-first) and ba-analyst (populate enforced BRs in docs/context) in parallel on disjoint paths | Active |
| 2026-07-18 | ba-analyst | Populated docs/context/business-rules.md with BR-05/06/07/08/09/10/11/16/36 (was a template stub); BR-06/09/36 marked aspirational (code not yet written); no specs/revision-history change | Done |
| 2026-07-18 | careplan-dev | Implemented src/vaic/agents/careplan/ test-first: orders.py (FR-03), sequencing.py+care_plan.py (FR-04), gate.py (FR-05, swappable OI-19 predicate), slots.py (FR-08 capacity/clash in-handler), durations.py (BR-09 mocked seam). 5 test files. Reports 22 careplan / 91 total pass, ruff clean. No cross-boundary edits | Active |
| 2026-07-18 | orchestrator | VERIFIED against git: diff scoped to new careplan src + 5 test files only; zero edits to tools/models/state/core (SOURCES.txt/.pyc are editable-install noise). Re-ran pytest independently: `pytest -k careplan` = 22 passed; full suite = 91 passed, 0 regressions; `ruff check` careplan = All checks passed | Active |
| 2026-07-18 | qa-test | GATE PASSED. careplan tests green; coverage 97% on module (care_plan/durations/__init__ 100%, gate 97%, orders 96%, sequencing 98%, slots 93%; misses are defensive edge branches, not critical paths). Full suite 91 passed. Per-AC verdict: all ACs (03.1/03.2, 04.1/04.2, 05.1-05.4, 08.1/08.2) strongly asserted on real state/audit, none weak, no critical-path gap | Active |
| 2026-07-18 | orchestrator | Dispatched code-reviewer + security-reviewer in parallel on the new careplan module + tests | Active |
| 2026-07-18 | code-reviewer | GATE: 0 Blocker, 9 Major, 4 Minor, 3 Info. Majors: slot capacity semantics (M1), TOCTOU (M2), owner-not-checked clash (M3), double owner_resolver (M4), empty-candidates partial write (M5), care-plan writes bypass audit spine (M6), self-asserted actor_role authz (M7), fasting interleave (M8), BR-08 dependency ordering unimplemented (M9). Positives: OI-19 predicate genuinely swappable, BR-05 enforced both paths, BR-07 1:1 preserved | Active |
| 2026-07-18 | security-reviewer | GATE: 0 Blocker, 2 Major, 3 Minor, 2 Info. Confirmed proceed-gate authz is a REAL control (not dead), doctor-only boundary holds both paths, no PII/secrets, no unvalidated model output. Majors: audit-spine bypass on plan/task creation (M1), self-asserted actor_role not bound to authenticated principal (M2, -> FR-18). Minors: estimator range-guard, PHI-in-reasoning latent, confirmed_by not verified | Active |
| 2026-07-18 | orchestrator | Triaged. MUST-FIX in careplan: capacity per-hour (cM1), owner-clash (cM3), empty-candidates rollback (cM5), route plan/task writes through audit spine (cM6/sM1), resolve owner once (cM4), + minors (gate write order, dup _now, estimator range-guard, CANCELLED/DONE slot filter). DEFER as follow-up tasks: actor_role->authenticated principal (cM7/sM2 = FR-18/agent-core), fasting breaks-fast attribute (cM8 = data-model/spec), BR-08 dependency modeling (cM9 = spec/data-model), TOCTOU atomic alloc (cM2 = state/OI-15). Sending careplan-dev back with the must-fix list | Active |
| 2026-07-18 | orchestrator | Registered follow-ups on board: TASK-031 (bind authz to authenticated principal, agent-core), TASK-032 (fasting-safety + dependency modeling, data-modeler), TASK-033 (atomic slot alloc, data-modeler). Rows read back and confirmed | Active |
| 2026-07-18 | careplan-dev | Fix round: all 5 MUST-FIX Majors + 4 minors fixed test-first. New tools create_care_plan/create_task/activate_care_plan route generation through the executor (audited); per-hour throughput capacity; owner-clash guard; graceful empty-candidates (plan stays DRAFT); owner resolved once; estimator range-guard; live-slot filter. Deferred items carry docstring notes. Reports 34 careplan / 103 total pass, ruff clean | Active |
| 2026-07-18 | orchestrator | VERIFIED fix round against git+code: scope still only careplan src + 5 tests (no protected-dir edits). Re-ran pytest: 34 careplan / 103 total passed, 0 regressions; ruff clean. Spot-read care_plan.py (audit-spine routing real) and slots.py (per-hour cap + owner-clash + live-filter real) - fixes genuine, not test-massaged. REVIEW GATE resolved: 0 Blockers; must-fix Majors fixed; remaining Majors deferred to TASK-031/032/033 | Active |
| 2026-07-18 | orchestrator | SECRET SCAN (pattern-based, no gitleaks on host) over careplan src + 5 tests: no credential patterns, no forbidden files, no real PII. One `sk-` hit was a false positive (substring of synthetic "front-desk-staff"). CLEAN | Active |
| 2026-07-18 | orchestrator | FLOW COMPLETE. spec-guardian -> careplan-dev (test-first) -> qa-test (green, 97%) -> code+security review (0 Blocker; fixed/deferred) -> secret-scan (clean). All ACs satisfied+verified. NOT committed/PR/merged per mission - reserved for Khang. TASK-008 stays Active pending Khang commit(scope careplan) + PR + merge. Note: discard incidental .pyc/SOURCES.txt churn before commit | Active |
| 2026-07-18 | orchestrator | MISSION COMPLETE (flow) - board audited 1:1: TASK-008 Active, TASK-031/032/033 Planned, all task files and board rows agree. Handoff to Khang for commit + PR + merge | Active |
| 2026-07-18 | careplan-dev | Fix round, test-first for every MUST-FIX: (1) slots.py capacity is now an hourly-throughput count (`_hour_bucket`), not overlap-based; (2) slots.py added an owner-clash check (task.owner_id vs candidate resource, true overlap on a different resource) for cM3; (3) care_plan.py/slots.py: empty `candidates_for` is a graceful failed `ActionResult` (audited `FAILED:allocate_slot`), never a raised exception - CarePlan stays DRAFT, no orphan ACTIVE plan, documented rollback contract ("never promote, never delete" - no cross-entity transaction primitive at this layer); (4) added `create_care_plan`/`create_task`/`activate_care_plan` tools, routed through ActionExecutor (audited, no new constraint-checker rule); (5) `sequence_orders` resolves `owner_resolver` exactly once per order and threads it via `SequencedOrder.owner_id` into Task creation. Minors: (6) gate.py now runs `assert_transition` once, before any Payment write; (7) gate.py imports the shared `_now()` from `models.entities` instead of redefining; (8) added `durations.validate_duration_minutes` (BR-14/NFR-SEC-20 range guard), applied in both sequencing.py and slots.py; (9) slots.py excludes CANCELLED/DONE task slots from capacity/clash via `_slot_is_live`. Added docstring preconditions (TASK-031 actor_role, TASK-032 fasting/dependency scope) per the deferred-items list. 12 new/changed tests. `pytest -k careplan` = 34 passed; full suite = 103 passed, 0 regressions; `ruff check` careplan+tests = All checks passed. No edits outside `src/vaic/agents/careplan/` and `tests/test_careplan_*.py` | Active |
| 2026-07-18 | orchestrator | Merged origin/main into the branch to prepare PR #5 for merge: resolved a task-ID clash where this branch's TASK-031/032/033 follow-ups collided with TASK-031 already registered from TASK-016's review (renumbered this branch's bind-authz follow-up to TASK-034, kept 032/033). Owner corrected from ad hoc "Khang" to the routing-table seat `careplan-dev`. Discovered the merge exposed a SEMANTIC conflict git could not flag: TASK-016 (merged separately) made `patient_id` a required field on `Diagnosis`/`ServiceOrder`/`Slot`/`Payment`; this branch's careplan writes predate that change and constructed those entities without it - 25 of 132 tests failed post-merge with pydantic `ValidationError: patient_id Field required`, not a text conflict | Merge blocked |
| 2026-07-18 | orchestrator | Fixed the integration gap in `src/vaic/agents/careplan/{orders,slots,gate}.py`: each write site now resolves `patient_id` from its linked record (Diagnosis from Appointment, ServiceOrder from Diagnosis, Slot/Payment from Task's CarePlan) instead of trusting a caller-supplied value, consistent with TASK-016's "denormalized, Own-scope resolves directly" invariant. Updated the now-stale test fixtures in 5 careplan test files (they predated TASK-016 and built entities without `patient_id`) to construct real linked records. `pytest -q`: 132 passed, 0 failures. `ruff check src tests`: all checks passed (also fixed one pre-existing import-order issue in `tests/test_intake.py` while running ruff --fix). Committed as `cee1f06` on the branch | Fixed; suite green |
| 2026-07-18 | orchestrator | Merged into main via PR #5, with the integration fix commit included | Done |

## Result

Care Plan Agent (FR-03 backend capture, FR-04 task-list generation/sequencing, FR-05 proceed gate,
FR-08 slot allocation) implemented in `src/vaic/agents/careplan/`, merged to `main` via PR #5.
Review gate closed with 0 Blockers; must-fix majors fixed in the same PR; three deferred items
tracked as follow-ups: TASK-031 (patient_id invariant, distinct from this task's original TASK-031
number - renumbered to avoid the ID clash), TASK-032 (fasting-safety + dependency modeling),
TASK-033 (atomic slot allocation), TASK-034 (bind actor_role to authenticated principal, this
task's original TASK-031).
