---
description: Create the skeleton of a feature module (entry point, library module, component, failing test).
argument-hint: <feature-slug>
---

Scaffold the feature **$1**. If $1 is empty, ask for the feature slug and stop.

Follow the layout in `.claude/rules/coding-standards.md`:

1. The entry point (route handler, controller, or command): input validation and delegation only.
   No business logic lives here.
2. The library module that holds the business logic, one directory per feature, testable without
   the transport layer.
3. The user-facing component, built from the existing design-system primitives rather than new
   one-off styles, when the feature has a user interface.
4. A failing pytest (backend), Vitest (frontend) test that names the acceptance criterion of the FR it serves. It
   fails first; the implementation is what makes it pass.

Register the owner agent for the domain in the routing table if this feature is not covered by an
existing entry:

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

Scaffolding creates structure, not behavior. Leave the logic unimplemented rather than filling it
with a plausible guess.
