---
title: "TASK-020: Author /design-system project command and register it in AGENTS.md"
status: Done
fr: FR-12
owner: orchestrator
deps: "TASK-018, TASK-019"
priority: P2
phase: 2
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-020: Author /design-system project command

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree.

## Goal

Create a reusable `.claude/commands/design-system.md` project command that surfaces the consolidated
design context in one shot, and register it in the AGENTS.md commands table so it is discoverable the
same way as the existing commands.

## Inputs and context

- Depends on TASK-018 (PRD path to point at for screen-level detail) and TASK-019 (concrete token
  locations inside `frontend/`).
- Command format reference: existing files in `.claude/commands/` (e.g. `scaffold-feature.md`,
  `implement-fr.md`) - frontmatter `description` + `argument-hint`, then the body.
- Spec 10 "Visual design direction" table/section to surface.
- Rules: creating a `.claude/commands/` file and editing the AGENTS.md commands table is explicitly
  requested by the owner this session. It is NOT a settings/hook/rule/agent-definition edit, so it is
  not self-escalation. Authored by the orchestrator because `.claude/` maintenance is within the
  orchestrator grant, whereas neither dev agent's scope (`frontend/src/`, `docs/`) covers it.

## To do

- [x] Write `.claude/commands/design-system.md` following the existing command file format.
- [x] The command surfaces: (a) the spec 10 "Visual design direction" direction (link, not a full
      copy of accepted content), (b) the concrete token values now living under `frontend/`
      (design-tokens.json, src/index.css [relocated globals.css], tailwind.config.ts, README, with
      their real paths from TASK-019), (c) a pointer to the relocated patient IA/sitemap PRD from
      TASK-018 for screen-level detail.
- [x] Register the command in the AGENTS.md commands table alongside `/implement-fr`, `/new-task`, etc.
- [x] Use relative links; no duplication of accepted spec content beyond a short pointer.

## Acceptance criteria

- [x] `.claude/commands/design-system.md` exists, matches the format of the other command files
      (frontmatter `description` + `argument-hint`, then body), and links to the spec 10 direction,
      the frontend token files (correct paths), and the PRD.
- [x] AGENTS.md commands table has a row for the new command (`/design-system [focus]`).
- [x] All links resolve to real files created/relocated by TASK-018 and TASK-019 - verified: all six
      relative link targets return OK from the command file location.
- [x] No settings/hook/rule/agent-definition file changed; no secrets; no commit performed. The only
      edits were the new command file and the AGENTS.md commands-table row.

## Decisions and blockers

- Authored by the orchestrator, not a dev subagent: `.claude/commands/` and the AGENTS.md contract
  file fall outside both candidate seats' scopes (`frontend-ui-dev` = `frontend/src/`, `ba-analyst`
  = `docs/`), and `.claude/` maintenance is within the orchestrator grant. Handing an out-of-scope
  edit to a dev agent would itself be a guardrail defect, so the orchestrator did it directly.
- Command accepts an optional `[focus]` argument but works with none; it links rather than copies
  accepted spec tables, so the spec stays the single contract.
- Deps TASK-018 and TASK-019 both reached Done before this task started, so every referenced path
  and the PRD name exist.

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator | Registered task; blocked on TASK-018 + TASK-019 | Planned |
| 2026-07-18 | orchestrator | Deps TASK-018 + TASK-019 verified Done; wrote `.claude/commands/design-system.md` surfacing the three authoritative layers (spec-10 direction, frontend tokens, patient PRD) with relative links | Command created |
| 2026-07-18 | orchestrator | Added `/design-system [focus]` row to the AGENTS.md commands table; verified all six command links resolve and the AGENTS row is present | Registered and verified |
| 2026-07-18 | orchestrator | Flipped frontmatter Planned -> Done, checked to-do/AC, moved file to `done/`, updated board row, re-read to confirm | Done |

## Result

Created `.claude/commands/design-system.md`, a project command that surfaces the consolidated design
system in one shot: layer 1 the spec-10 "Visual design direction" (linked, not copied), layer 2 the
concrete tokens now under `frontend/` (`design-tokens.json` source-of-truth, `src/index.css` CSS
variables, `tailwind.config.ts` theme, `README.md` sync note), layer 3 the patient-app IA/sitemap
`docs/requirements/PRD-FR-12-patient-mobile-app.md`. Registered as `/design-system [focus]` in the
AGENTS.md commands table. All six relative links verified resolving. No commit performed - staging
deferred to the owner's explicit authorization.
