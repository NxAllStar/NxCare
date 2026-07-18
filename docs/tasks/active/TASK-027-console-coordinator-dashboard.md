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
| 2026-07-18 | orchestrator | Resumed: reconciled board vs git (branch feat/TASK-027-console-coordinator-dashboard @ 309e1cf, clean, on 026 tip; row Active matches file; scope lock present - not re-run). Confirmed foundation: AIChip, ScreenState, Card, StatusChip, Button primitives + lib/api mock pattern exist. Dispatched frontend-ui-dev to build the dashboard test-first per To-do + Acceptance criteria, honoring the 4 scope-lock constraints (no invented N, AI-label all model content, no raw model HTML, build from primitives), node v22 for Vite/Vitest. | Dispatched |
| 2026-07-18 | frontend-ui-dev | Built SCR-06 test-first: mock-data layer under src/console/dashboard/ (types, fixtures, auditStore append-only, proposals decide+dequeue, heatmap ticker, reasoningStream); HeatmapPane, ApprovalQueuePane, ReasoningStreamPane; rewrote CoordinatorDashboardScreen off the stub. Added 2 shared primitives (Heatmap, StreamingText) exported from index.ts + tested. i18n keys added VI/EN. N left unresolved (2 PENDING_APPROVAL + 1 AUTO_APPLIED as fixed demo data, no computed N). Reported vitest 247 tests green + tsc clean under node v22.21.1 (implementer run, to be re-verified by qa gate). | Built |
| 2026-07-18 | orchestrator | Verified diff independently against HEAD: scope confined to console/ + components/primitives/ + i18n/ (no patient-app, settings, hook, or rule edits); no dangerouslySetInnerHTML in rendered code (only a comment noting its absence); no hardcoded hex in new files. Proceeding to qa gate. | Verified |
| 2026-07-18 | qa-test | GATE PASS. Independent run under node v22.21.1: `vitest run` = 39 files / 247 tests passed, 0 failed/skipped; `tsc -b --noEmit` exit 0, no errors. Mapped every acceptance criterion to an asserting test (append-only proven by mutation-throws + unchanged-snapshot; reject-confirm proven decide not called pre-confirm; LLM-error holds plan + shows paused banner; role gating coordinator/admin allow + doctor/technician/patient forbid across CoordinatorDashboardScreen.test + ConsoleApp.test). No gaps. | Pass |
| 2026-07-18 | code-reviewer | Read-only code-quality gate on the working-tree diff (uncommitted). 0 blockers, 0 majors. Minors: HeatmapPane ignores the loaded data.heatmap and runs its own ticker; Heatmap keys cells by concatenated labels not id; triggeredAt rendered in UTC not VN local; audit actor falls back to a fabricated coordinator/unknown identity when no session. Info: arbitrary text-[11px]/tracking (matches existing repo convention), clearInterval side effect inside a setState updater, error-state doc comment vs actual unmount behaviour. Hard gates pass: no native <select>, no raw data table beyond the sanctioned Heatmap primitive, no hardcoded hex, no inline-style token bypass, no raw title=, no emoji, no dangerouslySetInnerHTML. Append-only + approve/reject + LLM-error hold + role-gating covered by tests; no real network calls. | Pass (minors only) |

| 2026-07-18 | security-reviewer | Read-only security/privacy gate on the working-tree diff. CLEAN on all four primary concerns: (1) model/reasoning content rendered text-only, no dangerouslySetInnerHTML/innerHTML/eval (LLM01:2025); (2) fixtures synthetic, no secrets/real PII, no PII-in-logs; (3) human-in-the-loop gate defense-in-depth - approve/reject enabled only while PENDING_APPROVAL at UI AND service layer, reject-confirm, audit append-only with actor+role+decision+target+timestamp+carried rationale (ai-governance Auditability, FR-13/BR-22/BR-23); (4) error path holds plan, applies nothing. 0 blockers, 0 majors. Info (carry to backend TASK-010/004, not this mock task): server must derive audit actor from authenticated session not a client default (ASVS v5.0.0 ch8); real decision endpoint needs per-object server-side authz (API5:2023 BFLA) - client-hidden buttons are UX not authz. | Pass |
| 2026-07-18 | orchestrator | Both review gates PASS (no blocker/major). Disposition: routing 3 cheap flagship-quality Minors back to frontend-ui-dev - (1) HeatmapPane ignores loaded data.heatmap/dead field; (3) triggeredAt shown in UTC not VN local; (4) audit actor fabricated as coordinator/unknown when session null (audit-actor integrity, also security Info). Deferring Minor (2) cell-key-by-label as a backlog note (no current collision) and the 2 security Info items to the backend integration task. | Routed |
| 2026-07-18 | orchestrator | Resumed. Reconciled board vs git: branch feat/TASK-027-console-coordinator-dashboard @ 309e1cf, row Active matches file. Work is uncommitted in the working tree (5 modified + Heatmap/StreamingText primitives, console/dashboard/, screen test untracked) - the prior gates ran on the working-tree diff. Outstanding before Done: (a) frontend-ui-dev to fix the 3 routed Minors, (b) re-verify qa + reviews on the delta, (c) /secret-scan (not yet run). Dispatching frontend-ui-dev to fix the 3 Minors. | Resumed |
| 2026-07-18 | frontend-ui-dev | Fixed the 3 routed Minors, test-first. (1) Heatmap wiring: `heatmap.ts` `useHeatmapTicker` now takes an `initialGrid` (the loaded `DashboardData.heatmap`) and a new pure `nextHeatmapGrid(current)` advances that same grid forward on each tick (no more disconnected internal tick-index state); `HeatmapPane` takes an `initialGrid` prop instead of ticking from a hardcoded default; `CoordinatorDashboardScreen` now stores `data.heatmap` in state and passes it into `HeatmapPane`, so the previously-loaded-but-ignored field is genuinely consumed. (2) `triggeredAt` in `ApprovalQueuePane` now formats via `Intl.DateTimeFormat` with `timeZone: 'Asia/Ho_Chi_Minh'` (was `toISOString().slice(11,16)`, i.e. UTC); `tabular-nums` class kept on the `<time>` element. (3) Audit actor integrity: `ApprovalQueuePane`'s `actor` prop is now `ApprovalActor \| null`; `CoordinatorDashboardScreen` derives it only from the real `StaffAuthProvider` session and passes `null` when there is none, with no fabricated fallback; `runDecision` no-ops and every approve/reject control disables when `actor` is `null`, so no audit entry can ever be written with a placeholder identity - defensive only, since SCR-06 sits behind the TASK-026 role guard. Added/updated tests: `heatmap.test.ts` (ticker seeds from and advances the given grid, not tick 0), `HeatmapPane.test.tsx` (renders from caller-supplied `initialGrid`), `ApprovalQueuePane.test.tsx` (VN-local `triggeredAt` rendering; null-actor disables controls and never calls `decide`), `CoordinatorDashboardScreen.test.tsx` (heatmap cell from loaded data renders; audit entry carries the real session's role/displayName, never `'unknown'`; without a session, approve/reject stay disabled; the pre-existing dequeue test now seeds a session since actions require one). No other files touched. `node -v` = v22.21.1; `vitest run` = 39 files / 254 tests passed, 0 failed (up from the prior 247, +7 for the new/updated cases); `tsc -b --noEmit` exit 0. Grepped the diff for hardcoded hex, emoji, `dangerouslySetInnerHTML` - none found. | Fixed |

| 2026-07-18 | qa-test | GATE PASS (re-verified independently, not on implementer's counts). Used node v22.13.0 (conda env `hoang-openhands`; local default node is v12, no v22.21.1 available, but the memory-mandated "v22 on PATH" constraint is met). `vitest run` = 39 test files / 254 tests passed, 0 failed, 0 skipped - matches implementer's reported delta (+7 over the prior 247). `tsc -b --noEmit` exit code 0, no errors. Read the 3 changed test files directly: `heatmap.test.ts` asserts `useHeatmapTicker` starts at the caller-supplied initial grid and advances forward from it (not tick 0); `HeatmapPane.test.tsx` asserts the pane renders from an `initialGrid` prop, not an internal default; `ApprovalQueuePane.test.tsx` asserts `triggeredAt` renders as `08:02` (VN local) for a `01:02:00.000Z` UTC input, and that a `null` actor disables both approve/reject and `decide` is never called; `CoordinatorDashboardScreen.test.tsx` asserts the audit entry's `actorRole`/`actorDisplayName` come from the seeded staff session and `actorId` is never `'unknown'`, and that without a session approve/reject stay disabled. Previously-covered criteria unaffected by this delta and still passing: append-only audit (`auditStore.test.ts`), reject-confirm and role gating coordinator/admin allow vs doctor/technician/patient forbid (`ConsoleApp.test.tsx`, `CoordinatorDashboardScreen.test.tsx`), LLM-error holds plan + shows paused banner (`CoordinatorDashboardScreen.test.tsx`). No source or test files edited during this gate run. No coverage gap found. | Pass |

| 2026-07-18 | security-reviewer | Re-verified security/privacy gate on the 3-Minor delta (working tree, uncommitted). Audit-actor integrity fix CONFIRMED: `actor` derived strictly from the real StaffAuthProvider session (`session.role`/`displayName`), the fabricated 'unknown'/'coordinator' fallback removed; `actor: ApprovalActor | null`, and `runDecision` short-circuits `if (!actor) return` before any `decide`/audit write while every approve/reject/confirm control disables on `!actor` - so no audit entry can be written with a placeholder identity. Audit store remains append-only (BR-23): only `appendAuditEntry` writes, entries `Object.freeze`d, no exported update/delete path; `resetAuditStoreForTest` is test-only and not on any screen barrel. Four primary concerns still hold: (1) reasoning/model content text-only via StreamingText/Heatmap, no dangerouslySetInnerHTML/innerHTML/eval (LLM01:2025); (2) fixtures synthetic (demo areas + '(demo)' staff names, no secrets/real PII), no PII in logs; (3) HITL defense-in-depth intact - approve/reject enabled only while PENDING_APPROVAL at UI AND service layer (ProposalNotPendingError), reject-confirm, audit carries actor+role+decision+target+timestamp+carried rationale (FR-13/BR-22/BR-23; ai-governance Auditability); (4) VN-local time render is presentation-only, error path holds the plan and applies nothing. 0 blockers, 0 majors, 0 new findings. 2 prior Info items still carried to backend TASK-010/004 (server-derived actor, ASVS v5.0.0 ch8; per-object server-side authz, API5:2023 BFLA). Note (Info, not this diff): untracked 568KB NxCare.html design export at repo root - scanned, no secret patterns; should not be committed. | Pass |

| 2026-07-18 | code-reviewer | Re-review (read-only) of the 3-Minor delta on the working tree. PASS - all three fixes confirmed, no regressions, no new findings. (1) HeatmapPane consumes the loaded DashboardData.heatmap via `initialGrid` -> `useHeatmapTicker` seeded from it, advancing the SAME grid with pure `nextHeatmapGrid` (findIndex-by-tickId, falls back to tick 0 on an unknown grid); no disconnected internal tick-index remains. (2) `triggeredAt` renders in Asia/Ho_Chi_Minh via `Intl.DateTimeFormat` (hour12:false), NaN-safe fallback to raw ISO, `dateTime` keeps machine ISO, tabular-nums retained. (3) `actor: ApprovalActor | null` derived strictly from StaffAuthProvider session (role/displayName), no fabricated fallback; `runDecision` short-circuits `if(!actor) return`, and approve/reject/confirm disable on `!actor`. Hard gates hold: no native <select>, no raw title=, no inline-style token bypass, no hardcoded hex, no emoji/em-dash, no dangerouslySetInnerHTML (only the sanctioned token-based Heatmap primitive `<table>` and plain-text StreamingText). Deferred Minor (cell keyed by concatenated labels) intentionally not re-raised. Tests cover each fix (heatmap seed/advance, VN-local time, null-actor disabled+no decide, audit actor from real session). Could NOT execute Vitest in THIS env (installed node is v12/v20 only; toolchain needs v22 - a v20 transitive-dep ESM error blocks the run); relied on prior qa-test v22 run (254 passed) + static verification. 0 blockers, 0 majors, 0 minors. | Pass |

| 2026-07-18 | orchestrator | /secret-scan GATE PASS on the working-tree change set (26 changed/new frontend files, since untracked dashboard files are not in `git diff`). No credential patterns (sk-/AKIA/AIza/ghp_/glpat-/xox/JWT-shaped/BEGIN PRIVATE KEY/hardcoded password|api_key|secret|token assignments); no forbidden file types (.env*/.pem/.key/.jks/.p12/.tfvars); fixtures confirmed synthetic by security-reviewer. Clean, type-only scan, no value printed. | Pass |
| 2026-07-18 | orchestrator | ALL GATES GREEN and recorded: qa (254 tests, tsc 0) re-verified, code-review PASS (0 findings), security-review PASS (0 findings), secret-scan PASS. All 6 acceptance criteria met on mock data. Implementation complete; task stays Active. Remaining before Done are human-gated and NOT taken on agent authority: commit the working tree (exclude the pre-existing untracked root file NxCare.html - do NOT `git add -A`; both reviewers flagged it out-of-scope, secret-free), open the PR (`git diff main...feat/TASK-027-console-coordinator-dashboard`, three dots), human review + merge, then close-out. Proof boundary holds: do NOT mark FR-09/10/13 Done system-wide off this UI/mock task. | Gates green |

## Result

<Filled at Done.>
