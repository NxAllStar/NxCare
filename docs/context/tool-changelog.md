# Tool changelog - VAIC - AI Care Pathway Coordinator

A dated log of every change to the dependencies, tooling, and infrastructure of this project: what
changed, why, and how it was verified.

This is the file that answers "it worked last week, what changed?" The answer is almost never in
the application code. Record the change here at the time it is made, because reconstructing it
afterwards from lockfile diffs and pipeline logs costs a day.

Updated via `/sync-context`, and directly by `/deploy`.

| Date | Change | Why | Verified by |
|------|--------|-----|-------------|
| 2026-07-18 | Harness bootstrap (greenfield): 20-agent L roster, flags ai/ui/db/posix, GitHub/PR, Redis+SimPy+Python+React stack | Set up the operating harness over the existing spec set | scaffolder dry-run 0 conflicts; hooks smoke-tested |
| 2026-07-18 | Roster effort profile = Default (cost-model table): gates opus/high (+debugger xhigh), dev sonnet/high, spec-guardian/qa-test sonnet/medium, db-seeder/history-tracker haiku/low | Chosen by Team lead at intake | this file (record) |
| 2026-07-18 | Removed merge-manager (solo project), db-engineer + /db-migration (Redis has no schema migrations) | Keep the roster to fielded seats; no orphan agents | routing/roster tables + quality gate |
| 2026-07-18 | Model-provider retention posture: NONE recorded - no provider approved for Confidential+ (model sovereignty undecided) | KI-01; model-policy classification is advisory until Team lead sets it | KI-01 / TASK-002 |
| 2026-07-18 | Documented multi-developer concurrency: git-workflow.md "Parallel development" section, AGENTS.md Git note, master-plan claim-before-start note, stakeholders delivery-team update | Project is now worked by multiple developers simultaneously | this file (record); docs updated |
| 2026-07-18 | RECOMMENDATION open: field the `merge-manager` agent (skipped at bootstrap as solo) once concurrent PR volume is steady | Multiple developers means concurrent PRs; a single serialized merge gate prevents dropped-work merges | pending Team-lead decision |
| 2026-07-18 | Defined the rounded app (spec 1.4): one responsive role-gated web app; FR-18..22 supporting features; design system Tailwind + shadcn/ui; added TASK-013..015 to the board | Core was well-specified but app shape, auth, supporting features, and visual design were gaps | spec 1.4; tech-stack.md + frontend.md updated |
| 2026-07-18 | Added dependency `simpy>=4.1` (MIT, permissive) for TASK-006 simulator; ran `pip install -e .` (editable) so `python -m vaic.*` works | Simulator needs a discrete-event engine; editable install fixes the run-harness import | licence MIT permissive (ratified pending KI-03); pytest 52 passed; CLI deterministic |
| 2026-07-18 | TASK-013 auth backend done: `src/vaic/auth/` (accounts + demo seed, sessions, permission matrix + Own/Assigned/Team/All scope, AuthService; Unauthorized->401, Forbidden->403); `src/vaic/auth/` assigned to agent-core-dev in the routing table | FR-18 demo auth + server-side authz; login UI is TASK-015 | pytest 70 passed; ruff clean; orchestrator-verified fail-closed authz |

<!-- Include: dependency upgrades, tool and runtime version changes, CI configuration changes,
     infrastructure and hosting changes, database migrations, and pinned scanner or image versions.
     A version bump with no recorded reason is a version bump nobody dares to revert. -->
