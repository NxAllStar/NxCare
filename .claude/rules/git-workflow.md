---
paths:
  - "src/vaic/**/*.py"
  - "frontend/src/**/*.{ts,tsx}"
  - "tests/**/*.py"
  - "e2e/**/*.ts"
---
# Git workflow

Branching and PR mechanics on top of `conventional-commits.md` (commit format, loaded always). The
AGENTS.md "Git" section is the contract; this rule adds the project's specifics.

<!-- This repo is not yet under git. When it is initialised, set the commit identity recorded in
     docs/context/tool-changelog.md before the first commit. -->

## Branches

- Default branch: `main`. Never commit or push directly to it (the `guard-main-commit` hook blocks it).
- One branch per task, named `feat/TASK-NNN-<slug>`, `fix/TASK-NNN-<slug>`, `chore/...` matching the
  commit type.
- Parallel dev agents each get an isolated git worktree and one branch per task - never two agents in
  one checkout.

## Commits

- Conventional Commits, imperative lowercase subject <= 72 chars. Types and the project scope list are
  in `conventional-commits.md` (scopes: `intake, careplan, journey, forecast, agent-core, simulator,
  frontend, data, specs, agents, infra`).
- The `check-commit-msg` hook validates the message; a rejected commit is a malformed message, not a
  reason to route around the hook.
- No AI attribution in commit messages or PR descriptions.

## Pull requests (GitHub, `gh`)

- Work lands through a reviewed PR. The agent that authored a change never merges it.
- Inspect a PR with `git diff main...<branch>` (three dots, merge-base to tip).
- A PR opens only after the standard feature flow: `spec-guardian` locked scope, tests green,
  `code-reviewer` + `security-reviewer` passed, `/secret-scan` clean. CI (GitHub Actions) is green and
  terminal before merge - pending is not green.
- When two branches both edit `docs/tasks/master-plan.md` (or any list/board), the resolution is BOTH
  additions, never one side.

## Parallel development (multiple developers and agents)

This repository is worked on by **multiple developers concurrently** (and by parallel agents). The
board and the module ownership map are what keep that from turning into silently dropped work.

- **Claim before you start.** `docs/tasks/master-plan.md` is the shared coordination point. Before
  touching code, set the task's `owner` and flip its status to `Active` in BOTH the task file
  frontmatter and its board row, in one change. Two people never hold the same task `Active`; if a
  task is already `Active` under someone else, pick another or coordinate - do not open a second
  branch for it.
- **One task, one branch, one owner.** Module ownership follows the routing table in `AGENTS.md`. If
  your task needs to change a module another task owns, coordinate through that owner or the
  orchestrator - never edit across the boundary, because two branches editing one module is how a
  merge silently reverts the other's work.
- **Never two actors in one file at once.** Serialize when in doubt. Parallel agents get an isolated
  git worktree per task (the orchestrator enforces this); humans get separate branches.
- **Sync early and often.** Rebase your branch on `main` (or merge `main` in) at least daily and
  again right before opening a PR, so conflicts surface small instead of at merge time.
- **Merge one PR at a time**, each recomputed against the *current* `main` tip (`git diff main...HEAD`,
  three dots). Two merges computed against the same base is the classic dropped-work bug. The author
  of a change never merges it; a second person reviews and merges.
- **After every merge, reconcile the board.** Re-read `master-plan.md` and confirm each task file's
  frontmatter status still equals its row, and that `docs/tasks/done/` and the Done rows agree 1:1.
- **Only one orchestrator drives at a time.** If several developers each run an agent orchestrator,
  they must work disjoint task sets (claimed on the board) so two orchestrators never dispatch against
  the same task or module.

<!-- With steady concurrent PR volume, consider fielding the `merge-manager` agent as the single
     serialized merge gate (it was skipped at bootstrap as a solo project). See
     docs/context/tool-changelog.md and roster.md's merge-manager gate before adding it. -->

