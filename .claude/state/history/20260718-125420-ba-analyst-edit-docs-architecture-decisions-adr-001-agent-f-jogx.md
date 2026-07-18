# ba-analyst - Edit `docs/architecture/decisions/ADR-001-agent-framework.md` (currently status: Proposed - editable, do NOT change the status, leave it Proposed). This records a third option considered in the agent-framework decision. All the research is already done and given below - do not re-research; just fold it in faithfully, matching the ADR's existing tone (no emoji, no em dash - use "-", English, sentence-case headings).

- agent_type: ba-analyst
- agent_id: a095c54821ed5c09b
- finished: 2026-07-18 12:54:20
- transcript: /home/vuongchu/.claude/projects/-data-hdd-16t-vuongchu-civil-vaic/fa1dd17d-60aa-4eca-ab7d-451b04281eb9/subagents/agent-a095c54821ed5c09b.jsonl

## Prompt

```
Edit `docs/architecture/decisions/ADR-001-agent-framework.md` (currently status: Proposed - editable, do NOT change the status, leave it Proposed). This records a third option considered in the agent-framework decision. All the research is already done and given below - do not re-research; just fold it in faithfully, matching the ADR's existing tone (no emoji, no em dash - use "-", English, sentence-case headings).

CONTEXT: The decision stays LangGraph. We are (a) adding PocketFlow as a formally-considered Option C in the options table, and (b) rewriting the reversal condition so the named fallback is PocketFlow rather than a from-scratch FastAPI loop.

The framework choice turns on two demo-critical primitives the specs demand: interrupt-and-resume for tiered human-in-the-loop approval (FR-09, blast radius > N), and streaming reasoning (demo step 3). LangGraph provides both as first-class primitives with a checkpointer. PocketFlow does NOT provide these in its core - they are cookbook patterns you assemble yourself - so it is closer to Option B (hand-rolled) than to Option A. Its one genuine advantage over LangGraph: its shared store is a plain dict, which maps to Redis with zero impedance mismatch, removing LangGraph's one named negative (Redis/state reconciliation).

TASKS:

1. In the "Options considered" table, add a new row for Option C:
   - Option: "C PocketFlow (~100-line graph lib, zero deps), isolated behind agent-core"
   - Pros: "Minimal (~100 lines, zero dependencies, ~56KB) and fully transparent - readable and debuggable under time pressure; shared store is a plain dict that serialises straight to Redis, so it removes Option A's state/checkpoint reconciliation friction; constraint checker slots in as a node or exec() wrapper; no vendor lock-in, trivial to point at both the hosted API and self-hosted Qwen; isolation-behind-agent-core ethos fits its compose-your-own philosophy"
   - Cons: "Does NOT provide the two demo-critical primitives as core features - interrupt/resume and streaming are cookbook patterns you build and debug yourself (this is why it is nearer Option B than Option A); no built-in checkpointer; you own all the plumbing, which is the cost the framework was meant to save under a hackathon deadline"

2. Add a short sentence to the Decision section (after the existing decision paragraph) noting that PocketFlow (Option C) was considered and is retained as the documented fallback - see the reversal condition - because its Graph primitive plus plain-dict Redis mapping is a safer fallback than a from-scratch loop, while it does not supply the interrupt/resume and streaming primitives Option A is chosen for.

3. In the "Consequences" section, rewrite the "Reversal condition" bullet. Current text: "if LangGraph debugging blocks the demo build, fall back to Option B. Because agents and tools are framework-agnostic by this ADR, the fallback is a change to agent-core only - not a rewrite. A reversal is a new ADR superseding this one." New version: keep the same structure but name PocketFlow (Option C) as the preferred fallback ahead of the from-scratch Option B loop, because its Graph primitive and trivial plain-dict Redis mapping gets ~80% of the way with ~100 readable lines, and the isolation behind agent-core keeps the reversal a change to agent-core only, not a rewrite. Still note a reversal is a new ADR superseding this one.

4. Append one session-log row to the backing task file `docs/tasks/active/TASK-001-agent-framework-decision.md` (read it first to match its table format). Row content: date 2026-07-18, who "ba-analyst", what "Added PocketFlow as Option C to ADR-001 and named it the reversal fallback; ADR still Proposed", result "ADR-001 updated, awaiting Team-lead acceptance". Do NOT change TASK-001 status or the master-plan board row.

Do NOT flip ADR-001 to Accepted. Do NOT edit any other file. Do NOT touch TASK-017 or the master-plan board. Report exactly which files you changed and paste the new Option C row and the rewritten reversal bullet back to me for verification.
```

## Response

```
Files changed:

- `/data_hdd_16t/vuongchu/civil/vaic/docs/architecture/decisions/ADR-001-agent-framework.md` (status left as `Proposed`)
- `/data_hdd_16t/vuongchu/civil/vaic/docs/tasks/active/TASK-001-agent-framework-decision.md` (session-log row appended only; status untouched, still `Active`)

No other file was touched (TASK-017 and `docs/tasks/master-plan.md` are unchanged).

New Option C row in the "Options considered" table:

| Option | Pros | Cons |
|--------|------|------|
| C PocketFlow (~100-line graph lib, zero deps), isolated behind agent-core | Minimal (~100 lines, zero dependencies, ~56KB) and fully transparent - readable and debuggable under time pressure; shared store is a plain dict that serialises straight to Redis, so it removes Option A's state/checkpoint reconciliation friction; constraint checker slots in as a node or exec() wrapper; no vendor lock-in, trivial to point at both the hosted API and self-hosted Qwen; isolation-behind-agent-core ethos fits its compose-your-own philosophy | Does NOT provide the two demo-critical primitives as core features - interrupt/resume and streaming are cookbook patterns you build and debug yourself (this is why it is nearer Option B than Option A); no built-in checkpointer; you own all the plumbing, which is the cost the framework was meant to save under a hackathon deadline |

Sentence added to the Decision section (after the existing decision paragraph):

"PocketFlow (Option C) was considered and is retained as the documented fallback - see the reversal condition - because its Graph primitive plus plain-dict Redis mapping is a safer fallback than a from-scratch loop, while it does not supply the interrupt/resume and streaming primitives Option A is chosen for."

Rewritten reversal-condition bullet in Consequences:

"Reversal condition (named, so it is a decision not a hope): if LangGraph debugging blocks the demo build, fall back to Option C (PocketFlow) ahead of Option B's from-scratch loop - its Graph primitive and trivial plain-dict Redis mapping gets ~80% of the way there with ~100 readable lines. Because agents and tools are framework-agnostic by this ADR, the fallback is a change to `agent-core` only - not a rewrite. A reversal is a new ADR superseding this one."

Session-log row appended to TASK-001 (no status change):

| 2026-07-18 | ba-analyst | Added PocketFlow as Option C to ADR-001 and named it the reversal fallback; ADR still Proposed | ADR-001 updated, awaiting Team-lead acceptance |
```
