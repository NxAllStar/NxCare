---
title: "TASK-027: Console SCR-06 coordinator dashboard (flagship)"
status: Active
fr: FR-12
owner: frontend-ui-dev
deps: TASK-026
priority: P1
phase: 2
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-027: Console SCR-06 coordinator dashboard (flagship)

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree. Read the board row back after writing it:
a board write can fail silently while the task file lands.

## Goal

Replace the SCR-06 stub with the real coordinator dashboard - the signature surface of the whole
product: a real-time load heatmap, a re-plan approval queue with blast radius and one-tap
approve/reject, and a live Disruption-Agent reasoning stream - built to a high UX bar on demo mock
data, inside the console shell delivered by TASK-026.

## Inputs and context

- Related FR: [FR-09](../../specs/05-functional-requirements.md#fr-09) (Disruption Agent, tiered
  autonomy, blast radius > N needs coordinator approval), [FR-10](../../specs/05-functional-requirements.md#fr-10)
  (Coordinator), [FR-12](../../specs/05-functional-requirements.md#fr-12) (dashboard), [FR-13](../../specs/05-functional-requirements.md#fr-13) (audit)
- Screen spec: [spec 10 SCR-06](../../specs/10-ui-ux-wireframes.md#scr-06-coordinator-dashboard) -
  layout, elements, states, model-assisted elements. Visible to `coordinator` + `admin` (per the
  role->screen contract locked in TASK-026).
- Business rules: BR-22 (approve/reject is one-tap and audited), the blast-radius > N human-in-the-loop
  gate (`.claude/rules/ai-governance.md` "Human in the loop", FR-09).
- Design: `frontend/design-tokens.json`, `frontend/src/components/primitives/`, spec 10 "Visual design
  direction" (heatmap sequential green->amber->red; AI-labelled content; live reasoning as calm
  readable streamed text; tabular numbers). Desktop-first multi-pane.
- Foundation to build on: `frontend/src/console/` (shell, StaffAuthProvider, role guard, the SCR-06
  route + stub). This task fills the CoordinatorDashboardScreen.

## To do

- [ ] Console mock-data layer for the dashboard (synthetic only): resource/area load series for the
      heatmap, a set of `DisruptionEvent` re-plan proposals each with blast radius + options + reason,
      and a streamed reasoning transcript. Model this after `frontend/src/lib/api/` patterns; keep it
      under `src/console/` so it does not touch patient code.
- [ ] Load heatmap pane: areas x time, sequential green->amber->red scale, updates on a mock
      real-time tick, tabular numbers, accessible (colour is never the sole signal - pair with a
      label/value; keyboard reachable; AA contrast).
- [ ] Approval queue pane: one row per proposal showing blast radius, the option(s), and the reason;
      an AI chip on model-produced content; one-tap approve and reject controls that are ENABLED ONLY
      when the proposal's `status === PENDING_APPROVAL` (spec 06 approve/reject condition). Reject
      requires a confirmation (every proposal in this queue is large-impact by definition - the
      confirm applies to every reject here). Each approve/reject writes a mock audit entry then
      removes the proposal from the queue; on reject the underlying plan/resource state is held
      unchanged (AC-09.3).
- [ ] Live reasoning stream pane: streams the Disruption-Agent chain-of-thought as calm readable
      text, clearly labelled AI reasoning, read-only. A "thinking" indicator while streaming.
- [ ] States: empty (calm heatmap, no proposals), loading (skeleton), error (LLM-failure banner
      "auto-coordination paused, current plan held" - hold, do not auto-apply), success (proposal
      resolved, heatmap eases). No-permission is already handled by the TASK-026 route guard.
- [ ] Vitest coverage: heatmap renders and re-scales on tick; approve and reject each write an audit
      entry and dequeue the proposal; reject-large shows the confirm; reasoning stream renders labelled
      AI text; the LLM-error state holds the plan and shows the paused banner.

## Acceptance criteria

<!-- Observable, testable outcomes, not process steps. -->

- [ ] `coordinator` and `admin` see the real dashboard (heatmap + approval queue + reasoning stream)
      at the SCR-06 route; `doctor`/`technician`/`patient` still cannot reach it (TASK-026 contract).
- [ ] Approving or rejecting a proposal is a single tap, enabled only while the proposal is
      `PENDING_APPROVAL`, is recorded to a (mock) audit entry, and the proposal leaves the queue
      (BR-22, FR-12). Rejecting asks for confirmation first. The mock audit entry records at minimum:
      actor identity + role, decision, target `DisruptionEvent` id, and timestamp; the proposal's own
      AI rationale is carried over, not re-generated. The mock audit store is append-only (BR-23): a
      written entry is never mutated or deleted (it is the seed SCR-07/TASK-030 will later read).
- [ ] All model-produced content (proposals, reasons, reasoning stream) carries a visible AI label
      distinct from confirmed facts (NFR-USE-05); no raw model text is rendered as HTML.
- [ ] The heatmap uses the semantic sequential scale and never encodes state by colour alone; numbers
      are tabular; the panes meet WCAG AA contrast and are keyboard operable.
- [ ] On mock LLM failure the dashboard holds the current plan and shows the "auto-coordination
      paused" banner rather than applying anything.
- [ ] Built from shared primitives/tokens (add a primitive if one is genuinely missing, exported and
      tested); no emoji; patient app unaffected. Typecheck + Vitest pass under node v22, recorded in
      the log.

## Decisions and blockers

- Mock data only - there is no backend in `frontend/`. The dashboard consumes a console mock-data
  layer; wiring to the real Coordinator/Disruption agents (TASK-010) is a later integration task, not
  this one.
- If the heatmap or streamed-reasoning need would be better served by a new shared primitive
  (e.g. a Heatmap or a StreamingText primitive), create it in `src/components/primitives/`, export and
  test it (frontend.md), rather than a one-off in the screen.
- Scope lock (spec-guardian, 2026-07-18): the blast-radius threshold N is UNRESOLVED in the specs
  (OI-03). This UI task must NOT invent a settled N. The mock layer marks each event as pending
  (`> N`, needs approval) vs auto-applied (`<= N`, invisible on this screen) as fixed demo data; it
  does not compute a real N. Only the `> N` / `PENDING_APPROVAL` tier appears in the approval queue
  (matches spec 10 SCR-06 - the auto-applied tier has no surface here).
- Proof boundary (spec-guardian): this task proves the UI/mock contract ONLY. Do NOT mark FR-09,
  FR-10, or FR-13 "Done" system-wide off this task - a mock audit array proves the UI shape, not the
  real agent's blast-radius computation, the Coordinator's real tool-loop, or persistent tamper-
  evident append-only audit. Those need the backend integration task (TASK-010 / TASK-004).
- The "no raw model text rendered as HTML" requirement is traceable to agent-guardrails.md ("Model
  output is a proposal") + NFR-USE-05, not a literal FR-12 clause - correct to honor, attribute it so.

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator | Registered (Planned). Sequenced first of the real screens - the demo centerpiece. Blocked on TASK-026 close-out (shares the console shell; serialize). | Planned |
| 2026-07-18 | orchestrator | TASK-026 closed Done. Flipped to Active; branch feat/TASK-027-console-coordinator-dashboard stacked off the 026 tip (1a6fd57) so it has the console shell. Dispatched spec-guardian to lock the flagship scope (human-in-the-loop blast-radius gate, AI-labelling, audit-on-approve) before frontend-ui-dev builds. | Active |
| 2026-07-18 | spec-guardian | Scope lock (read-only): no contradiction with FR-09/10/12/13 or spec 10 SCR-06. Locked 4 additions into this file - (1) N is unresolved (OI-03); mock marks pending vs auto-applied, does not compute N; (2) approve/reject enabled only while PENDING_APPROVAL; (3) mock audit entry min fields = actor+role, decision, DisruptionEvent id, timestamp, carried rationale, append-only (BR-23); (4) UI/mock proof boundary - do NOT mark FR-09/10/13 Done system-wide off this task. Dispatching frontend-ui-dev to build. | Locked |

## Result

<Filled at Done.>
