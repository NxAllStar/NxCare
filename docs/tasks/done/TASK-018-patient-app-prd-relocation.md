---
title: "TASK-018: Relocate patient-app IA/sitemap + feature-architecture into a governed PRD"
status: Done
fr: FR-12
owner: ba-analyst
deps: "-"
priority: P2
phase: 2
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-018: Relocate patient-app IA/sitemap + feature-architecture into a governed PRD

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree.

## Goal

Move the two stray patient-app design documents from the repo root into a governed PRD under
`docs/requirements/`, and link spec 10 out to it instead of leaving the detail duplicated and stray.

## Inputs and context

- Related FR: [FR-12](../../specs/05-functional-requirements.md#fr-12) (coordinator dashboard + all
  UI screens); the patient surface screens SCR-01/SCR-02 in spec 10.
- Related spec: [10-ui-ux-wireframes.md](../../specs/10-ui-ux-wireframes.md) - Accepted v1.4 contract.
- Source files (repo root, untracked, to be relocated):
  - `Patient_GoldenPath_IA_Sitemap.md` - VI golden-path / IA / sitemap, 5-tab nav, Home dual-mode
    dashboard/Live Companion, screen-by-screen P0/P1/P2, Claude-Design constraints.
  - `Patient_Mobile_App_Feature_Architecture.md` - companion feature architecture v2, modules M1-M10.
- Templates: `docs/templates/PRD.md`.
- Rules: `.claude/rules/docs-workflow.md` (no new doc structures outside the map; new files start
  from a template; links are relative paths), `.claude/rules/agent-guardrails.md`.

## To do

- [x] Decide one merged PRD vs two linked documents (record the decision below).
- [x] Shape the relocated content to the `docs/templates/PRD.md` structure (source-requirement link,
      context, scope with explicit out-of-scope, detailed requirements table, user flow, references).
      Preserve the Vietnamese content; the PRD frame/headings follow docs-workflow conventions. Done:
      `docs/requirements/PRD-FR-12-patient-mobile-app.md`.
- [x] Relocate both source files under `docs/requirements/`. Content relocation done by ba-analyst
      into the PRD; physical removal of the two now-superseded untracked root files completed by the
      orchestrator (which has Bash) via plain `rm`, after verifying the PRD captured all source
      content (line count and distinctive-string check). No `git add`/`git rm`/commit was run.
- [x] Edit `docs/specs/10-ui-ux-wireframes.md` to link OUT to the new PRD from SCR-01, SCR-02, and
      the "Visual design direction" section, instead of duplicating detail. Do NOT restate the PRD
      tables in spec 10; do NOT alter accepted screen inventory / traceability semantics - links only.
      Done: three one-line "Related" links added, no other content changed.
- [x] If the relocation materially changes the contract (new requirement detail promoted into the
      spec set), add a row to `docs/specs/13-revision-history.md` per docs-workflow.md. If it is a
      pure relocation + linkout with no contract change, state that instead of inventing a version.
      Decision: pure relocation + linkout, no revision-history row added - see Decisions below.

## Acceptance criteria

- [x] `Patient_GoldenPath_IA_Sitemap.md` and `Patient_Mobile_App_Feature_Architecture.md` no longer
      exist at the repo root; their content lives under
      `docs/requirements/PRD-FR-12-patient-mobile-app.md`. Verified: both `ls` return "No such file".
- [x] The new PRD file(s) follow `docs/templates/PRD.md` (frontmatter + section shape) and use
      relative links. Met: `docs/requirements/PRD-FR-12-patient-mobile-app.md`.
- [x] Spec 10 SCR-01, SCR-02, and "Visual design direction" each carry a relative link to the new
      PRD; no PRD detail is duplicated into spec 10; accepted content is otherwise unchanged. Met.
- [x] Revision-history is updated IF and only if the contract changed; the decision is recorded here.
      Met: decided not to update, reasoning recorded in Decisions and blockers.
- [x] No secrets and no real personal data introduced; no `git add`/commit performed. Met: synthetic
      demo persona only, no `git add`/commit/mv run.

## Decisions and blockers

- **One-PRD-vs-two: ONE merged PRD.** Rationale: the two source files describe the same product
  surface (the patient mobile app) and are not independent - the IA/sitemap document states outright
  that its foundation is the feature-architecture document ("Nền tảng: file
  `Patient_Mobile_App_Feature_Architecture.md` (v2)") and exists to turn that architecture into a
  golden path, IA, and sitemap. Splitting them into two PRDs would force every reader to hold both
  open to understand either one, and would duplicate the module-to-screen mapping in two places that
  could drift. A single PRD (`docs/requirements/PRD-FR-12-patient-mobile-app.md`), with the
  feature-architecture content folded into section 4 (Detailed requirements) and the IA/sitemap/golden
  path content folded into sections 3 and 5 (Scope, User flow), keeps one coherent, traceable document
  per `docs/templates/PRD.md`'s one-document-per-feature shape.
- **Revision-history: NOT updated.** This is a pure relocation-plus-linkout: the three edits to spec
  10 add one "Related" link line each to SCR-01, SCR-02, and "Visual design direction" - no accepted
  screen inventory, traceability matrix, element, or state was changed, and no new FR was added to
  `05-functional-requirements.md`. The PRD itself carries new elaboration detail (modules, golden
  path, etc.), but it lives in `docs/requirements/` at `status: Draft`, not in the accepted spec
  contract - promoting any of it into a formal FR is explicitly left open in the PRD's section 7
  (Open questions), for a human to decide, not asserted here.
- **Root-file removal: CLEARED by the orchestrator.** The ba-analyst seat has no Bash/file-delete
  tool, so it correctly stopped at `Blocked` rather than claiming a move it could not perform. The
  orchestrator (which has Bash) verified the PRD had captured all source content - PRD 576 lines vs
  530 source lines, and every distinctive source marker present (Live Companion, M1..M10, "Nền tảng",
  sitemap, golden path) - then deleted the two now-superseded untracked files with plain `rm`. This
  is the completion of the authorized move (content relocated, originals removed), not a new
  destructive action. No `git rm`/`git add`/commit was run.
- Relationship to existing board work: this PRD is the patient-app requirements source that the
  future FR-12 screen build-out (TASK-011, TASK-015) will consume. This task does NOT implement
  screens.
- Findings requiring a human decision (recorded in full in the PRD's section 7, listed here for
  board visibility): (1) Module 6 (Payments) describes real in-app online payment, which conflicts
  with the accepted FR-05/AS-02 no-money-in-app constraint; (2) no quantified success metrics exist in
  the source brief; (3) several modules (Medical Records, Medication & Recovery, Family/Bring-someone,
  Contextual Consent, Proactive Prep, Live Companion Mode) describe capability with no matching FR in
  spec 05 yet; (4) "Why am I waiting?" (module 3) overlaps the already-open OI-22/TASK-017
  queue-transparency brainstorm and the two should be reconciled before either is built; (5) the
  source IA document references a sibling `Clinician_GoldenPath_IA_Sitemap.md` file that was not
  found in this repository.

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator | Registered task; dispatched ba-analyst for Phase 1 relocation | Planned -> Active |
| 2026-07-18 | ba-analyst | Read both root source files, `docs/templates/PRD.md`, `.claude/rules/docs-workflow.md`, spec 10, spec 05 (FR-12 and neighbours), spec 04 (BF-05), spec 11 (assumptions/open issues) | Decided ONE merged PRD (rationale recorded below); identified payment-scope conflict (M6 vs FR-05/AS-02), missing metrics, several modules with no matching FR, and overlap with OI-22/TASK-017 |
| 2026-07-18 | ba-analyst | Wrote `docs/requirements/PRD-FR-12-patient-mobile-app.md`: merged both source documents into the `docs/templates/PRD.md` shape (context, goals/metrics, scope incl. explicit out-of-scope, detailed requirements incl. full sitemap and module table, user flow incl. golden path, technical constraints incl. visual direction and cross-surface consistency, open questions, references); preserved all Vietnamese content verbatim | PRD created |
| 2026-07-18 | ba-analyst | Edited `docs/specs/10-ui-ux-wireframes.md`: added one "Related" link line each to SCR-01, SCR-02, and "Visual design direction", pointing at the new PRD; no other content touched | Three link-outs added; accepted screen inventory, traceability, elements, and states unchanged |
| 2026-07-18 | ba-analyst | Attempted to relocate the two root files with plain `mv` per the to-do; this agent's toolset for the session is Read/Write/Edit/Grep/Glob only, with no Bash and no file-delete/move tool (consistent with the "no Bash, docs-only" agent persona) | Could not physically remove the two root files; content is fully captured in the PRD, so the correct remaining action is a plain `rm` of both (not a move, since nothing further needs the content) - flagged as a blocker, task set to `Blocked`, not `Done` |
| 2026-07-18 | ba-analyst | Updated task frontmatter (`Planned` -> `Blocked`) and `docs/tasks/master-plan.md` TASK-018 row (`Active` -> `Blocked`) in the same change; re-read both to confirm they agree | Board and task file agree: `Blocked` |
| 2026-07-18 | orchestrator | Verified PRD captured all source content (576 vs 530 lines; distinctive markers present) and that spec-10 diff is link-only against accepted content; deleted the two superseded untracked root files with plain `rm`; confirmed both gone via `ls` | Move completed; blocker cleared |
| 2026-07-18 | orchestrator | Flipped frontmatter `Blocked` -> `Done`, checked the two remaining criteria, moved file to `docs/tasks/done/`, updated board row to `Done`, re-read to confirm agreement | Done |

## Result

Relocated the two stray patient-app design documents from the repo root into one governed PRD,
`docs/requirements/PRD-FR-12-patient-mobile-app.md` (merged, per the recorded one-PRD decision), and
linked spec 10 out to it from SCR-01, SCR-02, and the "Visual design direction" section (three
additive link-outs, accepted content otherwise unchanged). Both root files deleted after content
capture was verified. No revision-history bump (pure relocation + linkout). No commit performed -
staging/commit deferred to the owner's explicit authorization. Five human-decision findings recorded
in the PRD section 7 and echoed above (M6 payment-scope conflict, missing metrics, unmapped modules,
OI-22/TASK-017 overlap, missing clinician sitemap sibling) - not resolved by this task.
