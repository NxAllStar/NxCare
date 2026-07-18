---
title: "TASK-007: Intake triage + slot recommendation + emergency escalation"
status: Active
fr: "FR-01, FR-02, BF-05"
owner: intake-dev
deps: "TASK-004, TASK-005"
priority: P1
phase: 2
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-007: Intake triage + slot recommendation + emergency escalation

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree. Read the board row back after writing it.

## Goal

Conversational intake that triages the patient, recommends the least-crowded consult slot, and
escalates emergencies out of the normal flow.

## Inputs and context

- Related FR: [FR-01](../../specs/05-functional-requirements.md#fr-01),
  [FR-02](../../specs/05-functional-requirements.md#fr-02); flow
  [BF-05](../../specs/04-business-flows.md) (emergency escalation).
- Related files and modules: `src/vaic/agents/intake/` (exclusive owner).
- Consumes: agent/tool framework + constraint checker + audit (TASK-004), forecast tool
  `estimate_wait`/`get_queue_state` (TASK-005). Freeze those signatures at the Day-0 contract session.
- Hands off the intake state object to the Care Plan lane (TASK-008): agree the shape before coding.

## To do

- [ ] Intake conversation + triage routing (FR-01).
- [ ] Least-crowded consult-slot recommendation via the forecast tool (FR-02).
- [ ] Emergency escalation path (BF-05): detect, escalate, bypass normal routing, audit-log it.
- [ ] Tests first (pytest) naming the acceptance criterion each proves; external providers mocked.

## Acceptance criteria

- [ ] Tracks FR-01 and FR-02 acceptance criteria and the BF-05 escalation flow.
- [ ] Every consequential action routes through the constraint checker and lands in the audit log.
- [ ] Slot recommendation is grounded in the forecast tool, not invented.

## Decisions and blockers

Contract session (Day-0), signatures frozen against the deps - do not redesign:

- D1 Framework (TASK-004): agents subclass `Agent(name, executor)` and override `perceive(event)`
  and `reason(perception) -> list[Action]`. Every consequential action is an `Action{tool, actor,
  params, reasoning}` executed via `ActionExecutor.execute` - which routes closed-action-space ->
  `ConstraintChecker.check` -> `tool.run` -> `AuditLog.record`. Going through the executor is what
  satisfies AC "routes through the constraint checker and lands in the audit log". Intake does NOT
  call the checker or audit directly.
- D2 Own tools inside scope: intake defines its own `Tool(name, input_model, handler)` instances and
  registers them into a `ToolRegistry`, entirely inside `src/vaic/agents/intake/`. `src/vaic/tools/`
  is not edited (agent-core scope).
- D3 Constraint checker has no intake rules today; unknown tools default to `Decision(allowed=True)`.
  Adding an intake-specific checker rule would edit agent-core's file (out of scope). Capacity,
  opening-hours, and emergency-bypass guards therefore live in the intake tool handlers' own
  validation, and every action still routes through the executor for the audit trail. If a
  deterministic checker rule is judged necessary, route back to the orchestrator - do not edit the
  checker.
- D4 Forecast (TASK-005): ETA comes only from `estimate_wait(repo, owner_id: UUID, hour: int,
  llm: ForecastLLM) -> ForecastResult{value, confidence, provenance, source}`. Keyed by owner
  (a `Resource`), not specialty: FR-02 ranking maps specialty -> candidate owner Resources, calls
  `estimate_wait` per owner/hour, sorts ascending by ETA (BR-03: numbers never invented). The
  `ForecastLLM` protocol is mocked in every test (no network).
- D5 Discrepancy vs the brief: there is NO `get_queue_state` function in TASK-005. The equivalents
  are `owner_queue(repo, owner_id)` and `owner_load_minutes(repo, owner_id)` from `vaic.state`.
  Recorded so nobody hunts for a symbol that does not exist.
- D6 Handoff object (to TASK-008) already exists in the data model (TASK-003): `IntakeSession
  {patient_id, transcript, structured_triage{specialty, priority_level, constraints},
  emergency_suspected}`, plus `Appointment{patient_id, specialty, status=PROPOSED, ...}`. No new
  entity is created; `src/vaic/models/entities.py` is not edited (data-modeler scope). A missing
  field is routed back, not added here.
- D7 OI-09 open: the escalation MECHANISM (BF-05) is in scope and implemented; the clinical
  red-flag list CONTENT is a clinician decision (OI-09, owner SH-02). Intake ships a small,
  clearly-marked placeholder red-flag signal set flagged OI-09-pending - not a clinical authority.
- D8 Privacy: `IntakeSession.transcript` and `structured_triage` are Sensitive PII / untrusted
  content (NFR-SEC-11). Patient messages are data, never instructions (AC-01.3). No transcript text
  or PII in the audit log actor/reasoning, logs, or tests; tests use synthetic data only.

Post spec-guardian (2026-07-18), resolving its two findings:

- D9 Staff-confirmation gate (resolves spec-guardian finding 1; BR-02, BF-01 step 5, AC-01.1).
  Intake NEVER transitions an `Appointment` to `BOOKED` on its own authority. The booking tool
  requires an explicit staff-confirmation input (`staff_confirmed` set by a `role_coordinator`
  action) AND `emergency_suspected == False`; without confirmation it yields at most `PROPOSED`
  and refuses `BOOKED`. Intake only DEFINES/CONSUMES the confirmation signal - the desk-confirmation
  UI is out of scope (FR-12 / frontend-ui-dev). Rejecting confirmation returns to slot re-proposal.
- D10 Denials are audited, not silent (resolves spec-guardian finding 2; FR-13, BF-05 audit).
  A consequential guard VIOLATION - book beyond capacity (BR-04), book under emergency (AC-01.2),
  or book without staff confirmation (BR-02) - makes the tool handler raise `ToolError`, so
  `ActionExecutor` records a `FAILED:<tool>` audit entry with the reason. A legitimate "no slots
  available today" (AC-02.2) is a valid EMPTY result returned normally (audited as success) with a
  suggest-another-day payload - that is not a violation. Emergency escalation is its own tool routed
  through the executor so the escalation itself is audited (BF-05).
- D11 Agreed public API for `src/vaic/agents/intake/` (qa-test and intake-dev both honour these
  import names/signatures exactly; internals may be refined but a signature change routes back to
  the orchestrator). All Pydantic models use `extra="forbid"`. No network in any of these; the two
  LLM seams are Protocols, mocked in tests.
  - `triage.py`: `class TriageLLM(Protocol): def extract(self, prompt: dict) -> dict`;
    `class TriageResult(BaseModel){specialty: str, priority_level: PriorityLevel,
    constraints: list[str], emergency_suspected: bool}`;
    `def extract_triage(transcript: str, llm: TriageLLM) -> TriageResult` - transcript is passed as
    DATA in a delimited region, model output schema-validated (reject, not coerce), then the
    deterministic emergency check may OVERRIDE the model to force `emergency_suspected=True`
    (FR-01 "model flags, code checks"). Injection text never alters control flow (AC-01.3).
  - `emergency.py`: `RED_FLAG_SIGNALS: frozenset[str]` (placeholder, OI-09-pending in comments);
    `def detect_emergency(transcript: str, priority: PriorityLevel) -> bool`.
  - `slots.py`: `class SlotProposal(BaseModel){owner_id: UUID, hour: int, eta_minutes: float,
    source: str, confidence: float}`;
    `def recommend_slots(repo, specialty: str, candidate_owner_ids: list[UUID], hours: list[int],
    llm: ForecastLLM) -> list[SlotProposal]` - ETA only from `estimate_wait` (BR-03), drops
    unavailable/over-capacity owners (BR-04), sorted ascending by `eta_minutes`, `[]` when none
    (AC-02.2).
  - `agent.py`: `class IntakeAgent(Agent)` wiring the intake tools into the injected
    `ActionExecutor`; a factory that builds the `ToolRegistry` with the intake tools
    `book_appointment` and `escalate_emergency` (handlers enforcing D9/D10).

Follow-ups raised by the review gate (cross-lane - NOT fixed in intake scope; owner + task each):

- B1 (Major, code-reviewer) Consult-appointment capacity is unenforceable per-owner-per-hour with
  the current entity shape: `book_appointment`'s guard counts `owner_queue` (Tasks), but a booked
  `Appointment` never enters that queue and `Appointment` has no `owner_id`, so N confirmed bookings
  can pile onto one owner/hour (BR-04/BR-16 gap). Needs an `Appointment` <-> owner/slot link
  (data-modeler, spec 08) before the booking path is relied on; close at integration with TASK-008.
  Interim: intake documents the limitation in the guard so it is not misread as full enforcement.
- B2 (Major, security-reviewer) `staff_confirmed` and `emergency_suspected` are caller-supplied
  booleans not bound to an authenticated `role_coordinator` identity or to the deterministic triage
  result. The value-only guard is only as strong as caller discipline (ASVS v5.0.0 authz; API5:2023
  analogue). Full fix binds the confirm signal to FR-18 auth (TASK-013, `src/vaic/auth/`, Done) and
  the emergency flag to the triage verdict, at the point the Action is built - a
  Coordinator/agent-core integration concern. Route to agent-core; close before any real booking
  path ships. By design under D9 intake only defines/consumes the signal.
- B3 (Minor, security-reviewer) `Action.reasoning` is a free-text channel written verbatim into the
  append-only audit log; D8's "no PII in reasoning" rests on caller discipline, not a control. Add a
  sanitisation/contract at the audit boundary (agent-core scope, `src/vaic/tools/audit.py`).
  Intake's own handlers echo only UUIDs/codes today.

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator | Created task file from template so the Intake lane can claim it | Planned |
| 2026-07-18 | Vuong (intake-dev) | Claimed task; verified deps TASK-004, TASK-005 Done and their code present; branch feat/TASK-007-intake-triage-slot-escalation off cnv-dev | Active |
| 2026-07-18 | orchestrator | Verified premises: clean tree, correct branch, single worktree, intake dir clean slate. Read FR-01/FR-02/BF-05/FR-07 acceptance criteria + froze TASK-004/005 signatures (D1-D8). Found get_queue_state does not exist (D5) | Contract locked |
| 2026-07-18 | orchestrator | Dispatched spec-guardian to lock scope against docs/specs (FR-01, FR-02, BF-05) | Dispatched |
| 2026-07-18 | spec-guardian | Scope-lock returned: 2 findings - (1) staff-confirmation gate BR-02/BF-01-step-5 unnamed in D1-D8; (2) capacity/emergency denials must be audited, not silent. No spec-vs-doc drift found | Gate passed w/ findings |
| 2026-07-18 | orchestrator | Resolved both findings: D9 (booking gated on staff_confirmed + not-emergency, intake never self-BOOKs), D10 (guard violations raise ToolError -> audited FAILED), D11 (froze intake public API for qa-test + intake-dev) | Findings resolved |
| 2026-07-18 | qa-test | Wrote tests/test_intake.py (24 tests, 605 lines) test-first against D11; every AC named. Flagged 3 tool-input-schema assumptions D11 left open (book_appointment params, escalate_emergency={patient_id,specialty} only, capacity=owner_queue vs capacity_per_hour) | RED (ModuleNotFoundError) |
| 2026-07-18 | orchestrator | Verified independently: test_intake.py present, RED for the right reason, 70 existing tests still green. Dispatched intake-dev to implement to green | Verified; dispatched |
| 2026-07-18 | intake-dev | Created src/vaic/agents/intake/{__init__,triage,emergency,slots,agent}.py implementing D11 API. escalate_emergency does not create a DisruptionEvent (no patient_id field there) - flagged, not worked around | GREEN 26 intake / 96 full |
| 2026-07-18 | orchestrator | Verified: 96 passed, ruff clean, diff scoped to intake+tests+docs. NOTE out-of-scope edit: .gitignore gained `**/__pycache__/` (benign, does not untrack already-tracked .pyc) - flagged for Vuong. Dispatched code-reviewer + security-reviewer in parallel | Verified; review gate |
| 2026-07-18 | code-reviewer | Gate: no Blockers. 1 Major (book_appointment capacity guard counts owner task-queue while booking writes an Appointment that never enters it; hour unused -> over-capacity booking reachable, BR-04/BR-16). 3 Minor (booked appt loses owner/slot_start; PROPOSED->BOOKED state-machine bypass; out-of-scope .gitignore). Behaviour/injection/audit paths sound | Reviewed - Major to resolve |
| 2026-07-18 | security-reviewer | Gate: no Blockers, approve w/ follow-up. 1 Major (staff_confirmed/emergency_suspected are caller-supplied booleans, not bound to authed coordinator or triage result - full fix needs FR-18 auth binding, cross-lane). 1 Minor (Action.reasoning free-text PII channel). Injection, PII egress, no-BOOKED-bypass, audited denials verified CLEAN | Reviewed - Major to route |
| 2026-07-18 | orchestrator | Disposition: both Majors are cross-lane (Appointment<->owner/slot data-model link; FR-18 auth binding of the confirm/emergency signals) - registered as follow-ups (B1, B2), not hacked in intake scope. Sec Minor reasoning-PII registered (B3). In-scope Minors (state-machine, slot_start) sent back to intake-dev | Findings triaged |
| 2026-07-18 | qa-test | Wrote `tests/test_intake.py` test-first against the frozen D11 API (`triage.py`, `emergency.py`, `slots.py`, `agent.py`): 24 tests covering AC-01.1 (schema-valid + malformed-LLM rejection + extra-field rejection), AC-01.2 (emergency blocks booking), AC-01.3 (injection text is data, deterministic-check equality assertion), AC-02.1 (ascending ETA sorted, eta pinned to `estimate_wait` output - BR-03), AC-02.2 (empty result when unavailable/at-capacity - BR-04), D9 staff-confirmation gate (no-confirm blocked/not booked, confirmed+no-emergency books, emergency blocks even confirmed), D10 (parametrized: every blocked booking leaves a FAILED/BLOCKED audit entry with a reason; "no slots" contrasted as a normal empty return, not audited), BF-05+FR-13 (escalate_emergency audited, bypasses booking), D8 privacy (escalate_emergency schema rejects a `transcript` field via extra=forbid; no audit entry ever contains transcript text). External LLM seams mocked (`FakeTriageLLM`, `FakeForecastLLM`, no network). `ruff check tests/test_intake.py` clean. `pytest tests/test_intake.py` fails at collection with `ModuleNotFoundError: No module named 'vaic.agents.intake'` (RED for the right reason - module does not exist yet); `pytest --ignore=tests/test_intake.py` still 70 passed (no regression to existing suites) | RED confirmed |
| 2026-07-18 | intake-dev | Implemented `src/vaic/agents/intake/` (`triage.py`, `emergency.py`, `slots.py`, `agent.py`, `__init__.py`) exactly against the frozen D11 API to turn `tests/test_intake.py` green, without editing any test. `extract_triage` builds a delimited-region prompt (`instructions` vs `data.patient_transcript`), schema-validates via `TriageResult.model_validate` (reject not coerce, extra=forbid), then `detect_emergency` may only override `emergency_suspected` upward (FR-01 "model flags, code checks"; AC-01.3 injection text never downgrades or bypasses). `emergency.py` ships `RED_FLAG_SIGNALS` as an explicit OI-09-pending placeholder set, owned by SH-02, not this lane. `recommend_slots` is a pure query (never touches the audit log): ETA comes only from `estimate_wait` (BR-03), drops unavailable/at-capacity owners via `Resource.is_available` + `capacity_per_hour` vs `owner_queue` length (BR-04), sorted ascending, `[]` when none qualify (AC-02.2). `agent.py` wires `IntakeAgent(Agent)` to the injected `ActionExecutor` and `build_intake_registry(repo)` registers `book_appointment` (guard order: emergency -> availability/capacity -> staff_confirmed, each violation raises `ToolError` so the executor audits `FAILED:book_appointment` with a reason, D9/D10) and `escalate_emergency` (input schema `{patient_id, specialty}` only, `extra=forbid` structurally keeps transcript text out of params and therefore out of the audit log, D8; routed through the executor so the escalation itself is audited under action name `escalate_emergency`, BF-05/FR-13). `pytest tests/test_intake.py -q`: 26 passed (24 nominal tests, the D10 denial test is parametrized x3). `ruff check src/vaic/agents/intake/`: all checks passed. Full suite `pytest -q`: 96 passed, no regression to the prior 70. Diff scoped exclusively to `src/vaic/agents/intake/` (new) plus this session-log row; no `src/vaic/tools`, `src/vaic/forecast`, `src/vaic/state`, `src/vaic/models`, or `src/vaic/agents/core` edits; no secrets or PII in the diff | GREEN |
| 2026-07-18 | intake-dev | Follow-up fix to the two in-scope Minor findings from the review gate. Fix 1 (code-reviewer Minor #3, state-machine bypass): `_book_appointment` in `agent.py` now creates the `Appointment` with `status=PROPOSED` first, saves it, then calls `assert_transition(APPOINTMENT_TRANSITIONS, PROPOSED, BOOKED)` (imported read-only from `models.transitions`, not modified - the edge exists in the table) before re-saving an updated copy with `status=BOOKED` under the SAME `id` (`InMemoryRepository.save` keys by id, so `repo.list(Appointment)` still returns exactly one row - existing test `test_book_appointment_with_staff_confirmation_and_no_emergency_is_booked` unaffected). Fix 2 (code-reviewer Minor #2, lost `slot_start`): the same re-save sets `slot_start` from a new `_BOOKING_REFERENCE_DATE` (fixed UTC `2026-01-01`) plus `timedelta(hours=params.hour)` - deterministic, not timezone-ambiguous, documented inline as a demo placeholder for the real calendar day a production booking would use. B1 (capacity-guard limitation) legibility: added an inline comment at the `capacity_per_hour` check in `agent.py`'s `_book_appointment` and at `_has_room` in `slots.py` stating the guard counts `owner_queue` (Tasks) not booked Appointments, pending the Appointment<->owner/slot data-model link (B1) - guard LOGIC unchanged, no entity/checker edit. B2 (auth binding) and B3 (audit reasoning PII) left untouched, out of scope. `pytest tests/test_intake.py -q`: 26 passed, no test edited. `pytest -q` (full suite): 96 passed, no regression. `ruff check src/vaic/agents/intake/`: initially 1 E501 (line too long) on the model_copy call, fixed by extracting the update dict to a local variable; re-run: all checks passed. Diff confined to `src/vaic/agents/intake/agent.py` and `src/vaic/agents/intake/slots.py` (comments + the booking construction) plus this session-log row; no edits to `tests/`, `src/vaic/models/`, `src/vaic/tools/`, `src/vaic/forecast/`, `src/vaic/state/`, `src/vaic/agents/core/`, or `.gitignore` (the tracked `.gitignore`/`__pycache__` diffs pre-date this session, carried over from the prior review-gate note, not touched here); no secrets or PII in the diff; not committed | GREEN |
| 2026-07-18 | orchestrator | Re-verified after fix: full suite 96 passed, ruff clean, diff scoped to intake+tests+docs(+.gitignore). Secret-scan gate: gitleaks unavailable, ran pattern scan (credentials/keys/.env/conn-strings) over src/vaic/agents/intake/ + tests/test_intake.py - CLEAN; security-reviewer independently confirmed no secrets and synthetic-only test data | Secret-scan clean |
| 2026-07-18 | orchestrator | ORCHESTRATION COMPLETE - all gates run and logged (spec-guardian, qa-test RED->GREEN, code+security review, secret-scan). No Blockers. Handing back to Vuong for review/commit/merge decision. Task stays Active (unmerged, open decisions B1/B2). NOT committed, NOT merged, per mission | Handed back to Vuong |

## Result

<Filled when the task moves to Done.>
