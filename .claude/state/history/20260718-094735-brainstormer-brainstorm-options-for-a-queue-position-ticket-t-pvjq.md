# brainstormer - Brainstorm options for a queue-position / ticket transparency model in VAIC (an AI care pathway coordinator for patient triage and scheduling).

- agent_type: brainstormer
- agent_id: aa9d38e0324e2bd94
- finished: 2026-07-18 09:47:35
- transcript: /home/vuongchu/.claude/projects/-data-hdd-16t-vuongchu-civil-vaic/f2ce16f6-bd11-4373-b26a-65cbb41a2c73/subagents/agent-aa9d38e0324e2bd94.jsonl

## Prompt

```
Brainstorm options for a queue-position / ticket transparency model in VAIC (an AI care pathway coordinator for patient triage and scheduling).

The goal is to balance two tensions: (1) patients want to know how many are ahead of them and how long the wait will be, which builds confidence and reduces anxiety; (2) doctors have variable consultation times, queues reorder frequently, and providing a precise ETA invites complaints when reality diverges.

The simulator (TASK-006) models hourly load and has a forecast tool (FR-07) that predicts wait time and no-show risk.

Constraints:
- Real-time queries must be cheap (the UI calls this frequently during the patient's wait)
- ETA accuracy matters — too-optimistic estimates erode trust faster than no estimate
- Scope: this brainstorm produces an ADR + a candidate FR for phase 3 or the backlog

Diverge to at least 3 options. For each, identify:
- What the patient sees (e.g., "positions ahead" vs "ETA in minutes" vs "ahead in queue + doctor's next available slot")
- How you compute and update it (e.g., real-time vs polled, cached vs fresh)
- The trade-off: what does it cost? What does it gain?

Score each against: (1) accuracy / trust, (2) implementation cost, (3) patient benefit, (4) operational fit (does it help or hinder doctors/coordinators?).

Then recommend which to adopt for a Phase 3 experiment, and why.

The session log will record your output; please produce a structured summary: options as a table or list, the score matrix, and the recommendation with reasoning."
```

## Response

```
# Brainstorm: queue-position / ticket transparency model for VAIC

## What's already settled (frames the decision)

Read: `docs/specs/05-functional-requirements.md` (FR-02, FR-06, FR-07, FR-09, FR-11), `docs/specs/04-business-flows.md` (BF-03, BF-04), `docs/specs/07-non-functional-requirements.md` (NFR-PERF-01..04, NFR-SEC-12/13/15), `docs/specs/08-data-model.md` (`Task`, `Slot`, `Appointment`), `docs/specs/11-assumptions-constraints.md` (OI-05), `docs/specs/10-ui-ux-wireframes.md` (SCR-02), `docs/architecture/decisions/ADR-001-agent-framework.md`, `docs/tasks/done/TASK-006-simulator.md`.

- **The forecast number is never free-floating.** FR-07's grounding contract already mandates every ETA/load figure carry `{value, confidence, provenance, source: LLM|BASELINE}`, range- and monotonicity-checked, with an explicit `LOW_CONFIDENCE` fallback path (BR-14, BR-15). Any option that shows a number must consume this contract, not invent its own.
- **The forecast-LLM call is explicitly flagged as too slow/expensive for per-request use.** NFR-PERF-03 says `<500ms` is "hard if calling the LLM directly; needs cache/small model/precompute" — the perf budget itself is still unfixed (OI-05, open). This is the binding constraint on "cheap real-time queries."
- **Queue position is not a forecast question at all.** `Task.sequence_index`, `owner_id`, `execution_status`, and `Slot` are deterministic state (`docs/specs/08-data-model.md`), already updated by events (scan, payment flip, disruption re-plan). An ordinal position is a cheap Redis read/counter — no LLM in the path.
- **Journey Agent is already event-driven, not polled** (BR-12), and already pushes ETA changes with a reason on re-plan (BR-21, FR-11 AC-11.1). Disruption events (FR-09) already carry a blast-radius/approval gate before they touch a patient's plan. Any transparency model should reuse this push channel rather than inventing a new poll loop.
- **Not yet decided**: performance targets (OI-05) and the threshold N for disruption auto-execute (OI-03) — both affect how aggressively an ETA can be trusted right before or during a re-plan.

The real decision is not "what number do we show" — it's **what promise are we making, on what cadence, computed from what data path, and how does it degrade automatically when the forecast admits low confidence.**

## Options

| # | Option | What the patient sees | How it's computed / updated | Cost / gain |
|---|---|---|---|---|
| A | **Ordinal position only** | "3 patients ahead of you" (no time) | Deterministic count from `Task.sequence_index`/`owner_id`/`execution_status` in Redis; pushed on every relevant event (scan, payment, reorder) via the existing Journey Agent channel; a pull refresh is a cheap counter read | Costs almost nothing to build or run (no forecast call in the query path); can never be factually wrong, but gives no sense of *when* |
| B | **Precise ETA in minutes, per request** | "Estimated wait: 22 minutes" | Calls the forecast-LLM tool (or its cache) fresh on every UI poll; consumes FR-07's `{value, confidence, source}` directly | Highest information value; but NFR-PERF-03 already flags this as expensive to keep fresh, and a precise number that misses is exactly the complaint vector the prompt warns about |
| C | **Position + cached ETA band** | "3 ahead - roughly 20-35 min" | Ordinal position (cheap, real-time) + a forecast value recomputed on a fixed cadence or on significant queue delta (e.g. every 60s / on owner-queue change), cached in Redis; UI reads the cache, never calls the LLM per request | Cheap real-time reads; a range hedges against single-point misses; moderate build cost (a cache + refresh trigger, reusing FR-07's tool) |
| D | **Qualitative load bucket only** | "Low / moderate / high wait" chip, reusing the same hourly-load bucketing already computed for FR-02's least-crowded slot ranking | No new compute - reuses FR-02's existing specialty×hour load classification; updated on the same cadence as slot recommendations | Cheapest of the numeric-adjacent options, hardest to be "wrong" about, but weakest patient benefit - front-desk still fields "how long exactly" questions |
| E | **Adaptive, confidence-gated ladder (position always; band only when the forecast is confident and no live disruption)** | Ordinal position always shown; a time band shown on top of it only when FR-07 returns `source: LLM` with confidence above a threshold and no open `DisruptionEvent` touches this patient's owner/room; otherwise it silently drops to position-only (or shows the qualitative bucket) until confidence recovers | Built as a *policy* on top of option C's cache/tool path - no new grounding machinery, since it only reads fields FR-07 (BR-14/15) and FR-09 already mandate; pushed via the existing event-driven Journey Agent channel so no new polling cost | Slightly more logic than C, but it is the only option that automatically hides itself exactly during the windows most likely to cause a trust-eroding miss (active re-plans, `LOW_CONFIDENCE`/`BASELINE` forecasts) |

## Score matrix

Scale: `++` strong, `+` good, `o` neutral/acceptable, `-` weak, `--` poor.

| Option | Accuracy / trust | Implementation cost | Patient benefit | Operational fit | Reversibility |
|---|---|---|---|---|---|
| A - ordinal only | ++ (can't be factually wrong) | ++ (near-zero, existing fields) | - (no sense of time) | + (nothing for coordinators/doctors to react to) | ++ (pure additive, subsumed by every other option) |
| B - precise ETA, live | - (single point number, exactly the "too-optimistic" risk flagged) | - (fights NFR-PERF-03 head-on; needs a cache to even be feasible) | ++ (most informative when right) | - (a bad miss becomes a front-desk complaint, tied to unresolved OI-03/OI-05) | o (cheap to change technically, but reputational cost of a shown-then-wrong number is hard to walk back) |
| C - position + cached band | + (a range absorbs normal variance) | o (one cache + refresh trigger, reuses FR-07) | + (useful without over-promising) | + (coordinators unaffected; doctors unaffected) | + (band width/cadence are tunable; degrades gracefully to A) |
| D - qualitative bucket | + (vague enough to rarely be "wrong") | ++ (reuses FR-02's existing bucketing, no new path) | o/- (front-desk still fields "how long exactly") | + (invisible operationally) | ++ (trivially replaceable later) |
| E - adaptive confidence-gated ladder | ++ (never shows a confident number when the system itself is not confident, or mid-re-plan) | o (policy layer on C's substrate; no new grounding) | + (full band most of the time, safe degrade the rest) | ++ (auto-hides exactly during FR-09 disruption windows, which is when doctors/coordinators are already busy re-planning - no extra load on them) | ++ (a policy over existing mandated fields; changing the threshold is a config edit, not a rebuild) |

## Recommendation: Option E, built on Option C's data path, for the Phase 3 experiment

Adopt the confidence-gated ladder: **ordinal position is always shown** (cheap, always correct, reuses `Task` state already pushed through the event-driven Journey Agent channel), and **the time band is shown only when FR-07 returns a high-confidence, `LLM`-sourced value and no open `DisruptionEvent` touches the patient's owner/room** — otherwise it silently degrades to the ordinal count (or the qualitative bucket, D, as the degrade target) rather than showing a number the system itself would flag as `LOW_CONFIDENCE` or `BASELINE`.

Why this one, against the stated tensions:

- It resolves the core tension directly instead of picking a side: patients get a number **exactly when the system has grounds to trust it**, and get an honest, still-useful signal (position) when it doesn't — rather than either always showing a risky precise ETA (B) or never showing one (A/D alone).
- It costs almost nothing beyond what's already committed: FR-07's grounding contract already returns `confidence` and `source`; FR-09 already emits `DisruptionEvent`s with a blast-radius gate; FR-06/FR-11 already push notifications event-driven. E is a **consumption policy** over three things the spec already mandates, not new infrastructure - the only new work is the cache/refresh cadence (shared with C) and the gating logic.
- It directly targets the stated failure mode ("too-optimistic estimates erode trust faster than no estimate") by construction: a miss can only happen on a band the system already marked as high-confidence, which is the class of miss that's actually rare and defensible, not the class caused by mid-re-plan churn or a `BASELINE` fallback.
- Operationally it costs coordinators and doctors nothing extra - it uses the same disruption/audit machinery FR-09/FR-13 already require, so there is no new dashboard, no new approval step, no new doctor-facing surface.
- Reversibility is the deciding factor per the weighting instruction: E is a threshold and a data path, not a data-model or architecture commitment. Turning the band off entirely degrades to A (already the safest fallback); tightening or loosening the confidence threshold is a config change; nothing here is "cheap now, hard to undo later" the way B is (a patient population that gets used to seeing precise minutes is expensive to walk back from once a bad-miss incident happens - B is exactly the "cheap and hard to undo" case the framing calls out for scrutiny).

## What would change my mind

- **OI-05 gets fixed with a tight freshness requirement** (e.g. ETA must reflect state within seconds) that makes even a 60s-cached band stale enough to mislead - that would push toward A/D only until a faster forecast path exists.
- **Phase-3 eval evidence** (via `tech-researcher` + the simulator's ETA-MAE metric, already built in TASK-006) shows the forecast tool's real-world confidence is high enough, often enough, that the gate in E rarely triggers a degrade - in which case C alone (always show the band) becomes defensible and E's extra logic is overhead without benefit.
- **User testing shows patients tolerate visible uncertainty better than expected** (e.g., a band with a visible "confidence: building" state performs as well as full hiding) - that would argue for softening E's degrade behavior (show a wider band instead of hiding it) rather than dropping to ordinal-only.
- **Forecast-LLM cost/latency collapses** (a distilled/small model, per NFR-PERF-03's own suggested mitigation) to the point where per-request calls are cheap - that removes the reason to cache at all and simplifies C/E's substrate, though the confidence-gating logic in E would still be worth keeping since it targets trust, not just cost.

## Feeds into

- A candidate FR for the backlog (working title: "queue position and confidence-gated ETA display"), extending FR-06/FR-11's existing timeline-notification contract, owned by `journey-dev` (display/push logic) with `forecast-dev` supplying the cached, confidence/source-tagged value per FR-07's existing contract. It should reference FR-02, FR-06, FR-07, FR-09, FR-11, BR-03, BR-14, BR-15, BR-21, NFR-PERF-03/04, and open issue OI-05.
- An ADR (via `/new-adr`) recording the option table above, the chosen policy (E over C's substrate), and the reversal condition (drop the confidence gate, or drop the band entirely back to A) exactly as ADR-001 models the pattern.
```
