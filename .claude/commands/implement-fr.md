---
description: Plan and implement a functional requirement end-to-end against its acceptance criteria.
argument-hint: <FR-id> (e.g. FR-03)
---

Implement functional requirement **$1**.

If $1 is empty, list the functional requirements that have no task yet and ask which one to
implement. Do not guess.

1. Read FR $1 in `docs/specs/05-functional-requirements.md`: inputs, outputs, business rules,
   acceptance criteria, use case. Read the matching PRD in `docs/requirements/` if one exists.
2. Dispatch `spec-guardian` to lock the scope and the acceptance criteria before any code is
   written. An FR with no observable acceptance criteria is not ready to implement: stop and
   escalate.
3. Register the work with `/new-task` (it starts at `status: Planned`), then set it to `Active`
   when implementation begins.
4. Assign the specialist agent per the routing table:

| Work | Owner |
|---|---|
| FR-01 Intake triage, FR-02 slot recommendation, BF-05 emergency escalation | `intake-dev` |
| FR-03 diagnosis/order capture (backend), FR-04 Care Plan, FR-05 proceed gate, FR-08 slot allocation | `careplan-dev` |
| FR-06 Journey Agent, FR-11 notifications, FR-15 SMS, FR-17 patient-code scan | `journey-dev` |
| FR-07 forecast-LLM tool + grounding contract | `forecast-dev` |
| FR-09 Disruption Agent, FR-10 Coordinator, FR-13 audit log, shared agent/tool framework, constraint checker | `agent-core-dev` |
| FR-12 coordinator dashboard + all UI screens | `frontend-ui-dev` |
| SimPy simulator, eval/metrics, run harness | `simulator-dev` |
| Data entities, Redis state model | `data-modeler` |
| Synthetic reference/seed data (local/dev only) | `db-seeder` |
| Unit and e2e tests | `qa-test` |
| Docker Compose / CI harness | `devops` |
| Requirement-drift check before and after a feature | `spec-guardian` |
| Code review / security review (parallel gate) | `code-reviewer` / `security-reviewer` |
| Root-cause on failing tests or incidents | `debugger` |
| Options + trade-off analysis for a decision | `brainstormer` (+ `tech-researcher` for evidence) -> ADR |
| Spec and PRD upkeep | `ba-analyst` |
| Route, supervise, record | `orchestrator` |

5. Implement test-first: pytest (backend), Vitest (frontend) for the business rules, Playwright for the
   user-visible flow. The test names the acceptance criterion it proves and fails before the
   implementation exists.
6. Comply with `.claude/rules/`. The change is a proposal: a human reviews and decides.
7. Run `/test`, then `/review-changes`.
8. Do not deploy. Append the session-log rows to the task file and report which acceptance
   criteria are now met and which are not.
