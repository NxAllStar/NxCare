---
title: "Master plan - VAIC - AI Care Pathway Coordinator"
---

# Master plan

<!-- Written 100% in English (see .claude/rules/task-tracking.md). -->

The board. Every task in the project has exactly one row here, and that row's Status must always
equal the `status:` in the task file's frontmatter. The five valid states are defined in
`docs/templates/TASK.md`: `Planned | Active | Blocked | Pending | Done`.

**Multiple developers work this board at once.** Claim a task before you start: set its `owner` and
flip it to `Active` here and in the task file together. Do not start a task another person already
holds `Active`. One owner per task; module ownership follows the routing table in `AGENTS.md`. See
`.claude/rules/git-workflow.md` (Parallel development) for the full discipline.

## Phases

| Phase | Goal | Status |
|-------|------|--------|
| 1 | Foundation: framework decision, governance, data model + Redis state, agent/tool framework, forecast tool, simulator | Active |
| 2 | Must-have demo slice: intake -> consult -> care plan -> proceed gate -> journey -> disruption -> dashboard | Planned |
| 3 | Eval (A/B vs FIFO), metrics, demo script and polish | Planned |

## Task index

| Task | Title | Owner | Deps | Priority | Phase | Status |
|------|-------|-------|------|----------|-------|--------|
| TASK-001 | Decide agent framework (LangGraph vs FastAPI tool-loop) -> ADR (spec OI-18) | tech-researcher | - | P0 | 1 | Active |
| TASK-002 | Set governance policy: model sovereignty, residency, licences, IP ownership (KI-01..04) | ba-analyst | - | P0 | 1 | Planned |
| TASK-003 | Data model + Redis state interface (entities from spec 08) | data-modeler | TASK-001 | P0 | 1 | Done |
| TASK-004 | Agent/tool framework + deterministic constraint checker + audit log (FR-13) | agent-core-dev | TASK-001, TASK-003 | P0 | 1 | Done |
| TASK-005 | Forecast tool (LLM-as-a-tool) + retrieve-reason-validate grounding contract (FR-07) | forecast-dev | TASK-004 | P0 | 1 | Done |
| TASK-006 | SimPy simulator world + synthetic seed + metrics harness | simulator-dev | TASK-003 | P0 | 1 | Done |
| TASK-007 | Intake + slot recommendation + emergency escalation (FR-01, FR-02, BF-05) | intake-dev | TASK-004, TASK-005 | P1 | 2 | Planned |
| TASK-008 | Care Plan + proceed gate + slot allocation (FR-03, FR-04, FR-05, FR-08) | careplan-dev | TASK-004, TASK-006 | P1 | 2 | Planned |
| TASK-009 | Journey + notifications + patient-code scan + SMS (FR-06, FR-11, FR-15, FR-17) | journey-dev | TASK-008 | P1 | 2 | Planned |
| TASK-010 | Coordinator + Disruption tiered autonomy (FR-09, FR-10) | agent-core-dev | TASK-004, TASK-005 | P1 | 2 | Planned |
| TASK-011 | Frontend: chat, timeline, coordinator dashboard (FR-12 + screens) - SUPERSEDED by TASK-021..024 (patient-only re-scope, 2026-07-18) | frontend-ui-dev | TASK-007, TASK-008 | P1 | 2 | Pending |
| TASK-012 | A/B eval vs FIFO baseline + demo script + metrics | simulator-dev | TASK-010, TASK-011 | P2 | 3 | Planned |
| TASK-013 | Auth + role-based access: login, session, server-side authz (FR-18) | agent-core-dev | TASK-003, TASK-004 | P1 | 2 | Done |
| TASK-014 | Rounded-app features: reschedule/cancel, notifications center, settings+VI/EN, patient search (FR-19..22) - SUPERSEDED by TASK-023 (patient slice) + dropped staff search, 2026-07-18 | frontend-ui-dev | TASK-011, TASK-013 | P2 | 2 | Pending |
| TASK-015 | Design system + app shell (Tailwind + shadcn/ui, nav, i18n) per spec 10 - SUPERSEDED by TASK-021 (patient app foundation/shell), 2026-07-18 | frontend-ui-dev | TASK-011 | P2 | 2 | Pending |
| TASK-016 | Denormalize a resolvable patient link onto Diagnosis/ServiceOrder/Slot/Payment/AuditLogEntry so Own-scope covers them (from TASK-013) | data-modeler | TASK-003 | P2 | 2 | Planned |
| TASK-017 | Brainstorm: queue-position / ticket transparency model (patients-ahead + doctor anticipated load) -> ADR + candidate FR (OI-22) | brainstormer | - | P2 | 2 | Planned |
| TASK-018 | Relocate patient-app IA/sitemap + feature-architecture into a governed PRD; link spec 10 out to it | ba-analyst | - | P2 | 2 | Done |
| TASK-019 | Scaffold frontend/ (Vite+React+TS+Tailwind+shadcn) plumbing-only; relocate design tokens into it | frontend-ui-dev | - | P2 | 2 | Done |
| TASK-020 | Author /design-system project command + register it in AGENTS.md commands table | orchestrator | TASK-018, TASK-019 | P2 | 2 | Done |
| TASK-021 | Patient app foundation, shell, 5-tab nav, patient login, i18n VI/EN, mock-data layer, shared primitives (patient-only re-scope) | frontend-ui-dev | TASK-019 | P1 | 2 | Done |
| TASK-022 | Patient P0 golden-path screens: home dual-mode, journey (SCR-02), assistant, intake (SCR-01), book, checkin | frontend-ui-dev | TASK-021 | P1 | 2 | Done |
| TASK-023 | Patient P1 screens: notifications (SCR-09), settings (SCR-10), journey-step, results, meds, recovery, billing (display-only), family, prep | frontend-ui-dev | TASK-022 | P2 | 2 | Done |
| TASK-024 | Patient UI QA: Vitest suite + Playwright golden-path e2e + code/security review gates + secret-scan | qa-test | TASK-022, TASK-023 | P1 | 2 | Planned |
| TASK-025 | Patient app visual upgrade to iOS-native design (all screens + shell) per owner design | frontend-ui-dev | TASK-023 | P2 | 2 | Done |
| TASK-026 | Hospital web console foundation, shell, staff login, role routing (SCR-03..07 stubs) | frontend-ui-dev | TASK-021, TASK-013 | P1 | 2 | Active |
| TASK-027 | Console SCR-06 coordinator dashboard: heatmap + approval queue + reasoning stream (flagship) | frontend-ui-dev | TASK-026 | P1 | 2 | Planned |
| TASK-028 | Console SCR-03 consult and orders + SCR-04 doctor worklist | frontend-ui-dev | TASK-026 | P1 | 2 | Planned |
| TASK-029 | Console SCR-05 technician task view | frontend-ui-dev | TASK-026 | P2 | 2 | Planned |
| TASK-030 | Console SCR-07 admin and audit console (audit search + simulator seed/config, role split) | frontend-ui-dev | TASK-026 | P2 | 2 | Planned |
| TASK-031 | Console QA: Vitest sweep + Playwright golden-path e2e + review gates + secret-scan | qa-test | TASK-027, TASK-028, TASK-029, TASK-030 | P1 | 2 | Planned |

<!-- Update the Status column on EVERY status change, in the same change as the task file. -->

<!-- This is the most conflict-prone file in the repository: every task branch edits one row of it,
     so the rows collide constantly, and a merge that resolves the collision by taking one side
     reverts a status flip with no error at all. After every merge, re-read this board and confirm
     that each task file's frontmatter status still equals its row here, and that the files in
     docs/tasks/done/ and the Done rows agree one-to-one. When two branches each add a row, the
     resolution is both rows, never one side of the file. -->
