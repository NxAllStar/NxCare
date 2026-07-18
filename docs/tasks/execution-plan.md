---
title: "Execution plan - 5-6 person parallel build"
---

# Execution plan - 5-6 person parallel build

<!-- Written 100% in English (see .claude/rules/task-tracking.md). -->

Coordination companion to `master-plan.md`. The board and the individual task files remain the
source of truth for state; this file only assigns lanes and orders the waves so multiple people can
work Claude Code against this repo without colliding. When this file and the board disagree, the
board wins.

## The model: 5 people, 5 orchestrators, disjoint territories

Each of the 5 people runs their own orchestrator. This is allowed by `git-workflow.md` ("Only one
orchestrator drives at a time ... if several developers each run an orchestrator, they must work
disjoint task sets so two orchestrators never dispatch against the same task or module") on ONE hard
condition: each orchestrator owns a disjoint territory of modules that no other orchestrator touches.
An orchestrator decomposes its own lane and dispatches specialist workers, but only inside its
territory. Cross-territory edits are how one orchestrator silently reverts another's work.

`master-plan.md` is the one shared file everyone edits (one row each) - resolve its conflicts by
keeping BOTH rows, never one side. `src/vaic/models/entities.py` is the other shared file - only the
Simulator + Data territory changes it; everyone else reads it, and the shape is frozen Day-0.

## Territories (disjoint by module)

| # | Territory / orchestrator | Owns these modules (exclusive) | Tasks |
|---|--------------------------|--------------------------------|-------|
| 1 | Care Plan (critical path) | `src/vaic/agents/careplan/` | TASK-008, then TASK-027 (FR-23 generation) |
| 2 | Journey | `src/vaic/agents/journey/` | TASK-009, then TASK-028 (FR-23 rebalance) |
| 3 | Intake + Coordinator | `src/vaic/agents/intake/`, `src/vaic/agents/core/` | TASK-007, TASK-010 |
| 4 | Simulator + Data | `src/vaic/simulator/`, `src/vaic/state/`, `src/vaic/models/` | TASK-016 (first), TASK-012 |
| 5 | Frontend + QA | `frontend/src/`, `tests/`, `e2e/` | TASK-024, TASK-029 |

Governance sign-offs (TASK-002, ratifying TASK-026) are owner decisions, not build work - handled
outside the orchestrators. TASK-016 (adds a patient link every lane reads) is done FIRST by
territory 4, Day 1, before the other lanes wire deep into the entities.

## Rules that keep 5 orchestrators from colliding

1. **Never edit another territory's module.** If Care Plan needs a change in `models/`, it asks
   territory 4; it does not edit `models/` itself. This is the most important rule.
2. **Claim before starting** - owner + `Active` on the board row AND the task file, together. No two
   orchestrators on the same task.
3. **The two shared files** - `master-plan.md` (one row each; keep BOTH on conflict) and
   `models/entities.py` (only territory 4 writes; frozen Day-0).
4. **One merge at a time**, recomputed against the current `main` tip; the author never merges their
   own change - a different person reviews and merges.
5. **Day-0 freeze first**, then all 5 orchestrators run in parallel.

## Critical path

Care Plan (TASK-008) -> Journey (TASK-009) -> Eval/demo (TASK-012). Care Plan is the bottleneck:
Journey and the demo both wait on it, and it carries the FR-23 generation half. Give it the strongest
person and unblock it first.

## Day-0 contract freeze (before any agent code)

Not a document or a ceremony - a 30-minute session where all lane owners confirm the exact function
signatures and data shapes they will share, and agree that changing any of them afterwards is a
coordinated change through the owning lane, never a quiet per-lane edit. These already exist from the
Phase 1 work (TASK-003/004/005); the freeze confirms them and stops them moving mid-build.

The failure this prevents: five lanes build in parallel for two days, then integration day finds
Intake wrote `patient.triage_level` while Care Plan reads `patient.severity`, the forecast return
shape drifted, and Journey emitted a tool the checker rejects. Each is a small fix, but they all
surface at once, at the worst time, and each belongs to a different owner.

### 1. The intake -> careplan -> journey state shape

Owner of changes: data-modeler (`src/vaic/state/`, `src/vaic/models/`). The three agent lanes pass a
patient's data down a chain through the shared repository:

```python
# src/vaic/state/repository.py
class Repository(ABC):
    def save(self, entity: T) -> T: ...
    def get(self, model_cls: type[T], entity_id: UUID) -> T | None: ...
    def list(self, model_cls: type[T], **filters) -> list[T]: ...
    def delete(self, model_cls: type[T], entity_id: UUID) -> bool: ...
```

Freeze: agree which entity fields (`Patient`, `CarePlan`, `Task`, ... in `models/entities.py`) carry
the handoff - what Intake writes that Care Plan reads, and what Care Plan writes that Journey reads. A
new field mid-build is a data-modeler change (TASK-016 territory), not a quiet per-lane addition.

### 2. The forecast tool signature

Owner of changes: forecast-dev (`src/vaic/forecast/`). Every lane that needs a wait time or ETA calls
the same function:

```python
# src/vaic/forecast/tool.py
def estimate_wait(repo: Repository, owner_id: UUID, hour: int, llm: ForecastLLM) -> ForecastResult: ...

class ForecastResult(BaseModel):
    value: float          # ETA in minutes
    confidence: float
    provenance: str
    source: Literal["LLM", "BASELINE"]
```

Freeze: intake-dev (slot rec), careplan-dev (FR-23 generation), journey-dev (FR-23 rebalance), and
simulator-dev all consume this. If FR-23 needs a `get_queue_state` alongside `estimate_wait`, define
it now so nobody stubs a private copy. A rename after wiring breaks four lanes at once.

### 3. The constraint-checker + audit spine

Owner of changes: agent-core-dev (`src/vaic/agents/core/`, `src/vaic/tools/`). No agent writes to
state directly; it emits an `Action`, and the executor runs closed-action-space check -> constraint
checker -> tool -> audit:

```python
# src/vaic/tools/action.py
class Action(BaseModel):
    tool: str
    actor: str            # agent name, never a secret / PII
    params: dict
    reasoning: str

# src/vaic/agents/core/executor.py
class ActionExecutor:
    def execute(self, action: Action) -> ActionResult: ...   # allowed? ok? output, audit_id
```

Freeze: intake, careplan, journey, and coordinator lanes all produce `Action` and read `ActionResult`
back. Agree the `Action` shape and, critically, the set of valid `tool` names in the closed action
space (`constraint_checker.py`: `start_task`, `scan_patient`, `allocate_slot`, `create_service_order`,
`execute_replan`). A tool name the checker does not know is blocked as "outside the action space", so
new tools are a coordinated agent-core change, not a per-lane addition.

### 4. FR-23 derivation (blocks the FR-23 lanes only)

`station_wait` is derived and transient: `queue_length_paid x avg_service_time`, PAID-only (BR-10),
grounded via FR-07. Requires the lead to ratify the TASK-026 v2.0 spec first. No FR-23 code
(TASK-027/028) before that sign-off.

## Waves

Wave 1 (all 5 orchestrators in parallel, no cross-deps): territory 1 TASK-008, territory 2 stub on
the frozen handoff, territory 3 TASK-007 + TASK-010, territory 4 TASK-016 first then TASK-012 harness
scaffold against mock agents, territory 5 TASK-024. Owner (separately): TASK-002, TASK-026 approval.

Wave 2: territory 2 TASK-009 (integrates on the landed Care Plan), then FR-23 TASK-027 (territory 1)
+ TASK-028 (territory 2), and territory 5 wires the patient app to live agent APIs (replacing the
mock-data layer).

Wave 3: end-to-end run in the simulator, TASK-012 A/B eval vs FIFO, demo script, TASK-029 coordinator
console, final `code-reviewer` + `security-reviewer` + `/secret-scan` on the full diff.

## Coordination discipline (from `.claude/rules/`)

- Claim before start: set owner + `Active` on the board row AND the task file together, then re-read
  the row. Never start a task someone else holds `Active`.
- Branch per task; Conventional Commits; never commit to `main`.
- One PR merged at a time, recomputed against the current `main` tip; the author never merges their
  own change; inspect with `git diff main...<branch>` (three dots).
- Session-log every gate run in the task file - a gate is "passed" only when logged.
- The standard feature flow per lane: `spec-guardian` locks scope -> implement test-first ->
  `qa-test` -> `code-reviewer` + `security-reviewer` in parallel -> `/secret-scan` -> PR. Run it with
  `/implement-fr FR-NN`.
- Daily (or twice-daily) standup around the board given the hackathon timeline.

## Push and merge checkpoints (when to do what)

Git is manual here on purpose - nothing pushes, merges, or flips status on its own. The moments:

| Moment | You do | You do NOT |
|--------|--------|------------|
| Claim a task | Set owner + `Active` in the board row AND the task file, together; re-read the row | Start on a task someone else holds `Active` |
| While building | Commit to your task branch often (Conventional Commits); `git fetch && git rebase origin/main` at least daily | Commit to `main` (the hook blocks it) |
| Feature flow green | Push your branch (`git push -u origin <branch>`), open a PR with `gh` | Open a PR before tests + `code-reviewer` + `security-reviewer` + `/secret-scan` are green |
| PR approved | Ask ANOTHER person to review and merge; rebase on current `main` first | Merge your own PR (git-workflow.md: the author never merges) |
| After any merge | Whoever merged re-reads `master-plan.md` and confirms every status still matches; move the done file to `done/` | Assume the merge kept another branch's status flip - it can silently revert it |

Rule of thumb: **commit early and often, push when the flow is green, let someone else merge, reconcile the board after every merge.**
