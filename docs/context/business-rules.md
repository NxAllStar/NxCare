# Business rules - VAIC - AI Care Pathway Coordinator

The behavioral rules this system enforces, each with the source that authorized it. A rule that
lives only in code is a rule the next agent will break without knowing it existed.

Numbered BR-NN, stable forever: a rule that is superseded is marked, never renumbered and never
deleted. Downstream files (tasks, findings, tests) cite these IDs.

Updated via `/sync-context` whenever behavior-affecting logic changes.

| ID | Rule | Source | Status | Enforced in |
|----|------|--------|--------|-------------|
| BR-01 | <the rule, stated as a testable invariant> | <FR-NN or ADR-NNN> | Active | <module or test that enforces it> |
| BR-05 | Only doctors create or amend `Diagnosis` and `ServiceOrder`; AI never adds, removes, or changes a service | [FR-03](../specs/05-functional-requirements.md#fr-03) | Active | `src/vaic/tools/constraint_checker.py` (`_check_create_service_order`) and the careplan `create_service_order` tool |
| BR-06 | Amending orders after a care plan already exists regenerates the affected part of the plan; the old tasks are marked `CANCELLED`, their IDs are kept | [FR-03](../specs/05-functional-requirements.md#fr-03), [FR-04](../specs/05-functional-requirements.md#fr-04) | Active | Aspirational - in scope for TASK-008, not yet written |
| BR-07 | Care Plan Agent never adds or drops services beyond the doctor's orders | [FR-04](../specs/05-functional-requirements.md#fr-04) | Active | `src/vaic/agents/careplan/` |
| BR-08 | Task order must respect dependency and fasting constraints | [FR-04](../specs/05-functional-requirements.md#fr-04) | Active | `src/vaic/agents/careplan/` (sequencing) |
| BR-09 | Task duration comes from the Forecast tool ([FR-07](../specs/05-functional-requirements.md#fr-07)), never guessed by an LLM | [FR-04](../specs/05-functional-requirements.md#fr-04) | Active | Aspirational - in scope for TASK-008, not yet written |
| BR-10 | `UNPAID` tasks never enter the real queue and never count toward an owner's load or ETA | [FR-05](../specs/05-functional-requirements.md#fr-05) | Active | `src/vaic/models/entities.py` (`Task.is_locked`/`in_queue`), `src/vaic/state/repository.py` (`owner_queue`/`owner_load_minutes`), `src/vaic/tools/constraint_checker.py` (`_check_start_task`) |
| BR-11 | The app processes no money; only an authorised source (staff, counter, hospital system) flips the flag to `PAID`; no agent flips it | [FR-05](../specs/05-functional-requirements.md#fr-05), [AS-02](../specs/11-assumptions-constraints.md) | Active | `src/vaic/agents/careplan/` (payment-confirmation tool) |
| BR-16 | Never allocate a patient into a closed room or beyond capacity | [FR-08](../specs/05-functional-requirements.md#fr-08) | Active | `src/vaic/tools/constraint_checker.py` (`_check_allocate_slot`, closed-room half) and `src/vaic/agents/careplan/` (capacity/no-clash half) |
| BR-36 | Payment confirmation is a staff scan of `patient_code` at the counter - a distinct scan that happens BEFORE and differently from FR-17's room-presence scan; recorded via `Payment.confirmed_by`/`confirmed_at` | [FR-05](../specs/05-functional-requirements.md#fr-05), [OI-19](../specs/11-assumptions-constraints.md#oi-19) | Active | Aspirational - in scope for TASK-008, not yet written; which staff role may perform the scan is still open per OI-19 |

<!-- "Status" is Active or Superseded (by BR-NN). Rules are appended, never edited in place: the
     history of what was true when is what makes an old defect explicable. -->

<!-- A rule with no "enforced in" is aspirational. Either point at the code that enforces it, or
     open a task to write that code. -->
