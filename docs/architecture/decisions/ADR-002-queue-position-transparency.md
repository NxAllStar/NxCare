---
title: "ADR-002: Queue position and confidence-gated ETA display (OI-22)"
status: Proposed
date: 2026-07-18
deciders: []
tags: [adr, ux, forecast, transparency]
---

# ADR-002: Queue position and confidence-gated ETA display

## Context

Patients in a queueing system experience anxiety when they have no visibility into their position or wait time. VAIC's simulator and forecast tools (FR-07) provide the machinery to answer both questions, but the task frame (TASK-017) surfaces a tension: showing a precise ETA invites expectation mismatch when the actual wait diverges, and reordering (FR-09, FR-06) invalidates a shown position constantly, potentially eroding trust.

The grounding is already in place:

- **FR-07's forecast contract** already mandates every ETA/load figure carry `{value, confidence, provenance, source: LLM|BASELINE}`, range-checked, with explicit `LOW_CONFIDENCE` fallback (BR-14, BR-15). Any transparency model must consume this contract, not invent its own.
- **FR-06 Journey Agent** is already event-driven (BR-12), pushing ETA changes with a reason on re-plan, and accepting reorderings only within dependency limits. Notifications already carry a reason (BR-21, FR-11 AC-11.1).
- **FR-09 Disruption Agent** already gates aggressive re-plans (blast-radius approval, FR-10 Coordinator gating).
- **Task.sequence_index, owner_id, execution_status** are deterministic Redis state, already pushed through the Journey Agent's event channel.
- **NFR-PERF-03** flags per-request LLM calls as expensive ("hard if calling the LLM directly; needs cache/small model/precompute"), leaving the perf budget unfixed (OI-05, open).

The real decision is not "what number to show" but **what promise to make, on what cadence, from what data path, and how to degrade when the forecast admits low confidence.**

QMS standards (NSQHS-2, ISO-9001, ACHS) mandate proactive communication but do not specify a transparency mechanism. Patient-experience literature shows ETA display alone does not move satisfaction; what matters is expectation-matching and explanation of cause. A critical gap exists: no rigorous study measures patient trust impact of visible re-sequencing — this is exactly the gap VAIC's ai-governance eval requirement (evaluating user-facing model output before rollout) must close.

## Decision

Implement queue-position and wait-time transparency using an **adaptive confidence-gated ladder**:

1. **Ordinal position always shown** ("3 patients ahead of you") — deterministic, cheap, computed from Redis `Task.sequence_index` and pushed event-driven through Journey Agent's existing notification channel.
2. **ETA band shown only when both conditions hold**: FR-07 returns high-confidence with source `LLM`, AND no open `DisruptionEvent` touches the patient's owner/room (i.e., no active re-plan).
3. **On degrade**: when either condition fails, the ETA band silently drops, leaving position visible (or optionally the qualitative load bucket from FR-02's slot-recommendation logic).

Build this as a **policy layer** on top of Option C's data path (position + cached ETA band), reusing FR-07's confidence/source tagging and FR-09's `DisruptionEvent` emission.

## Options considered

| Option | What patient sees | Compute / update | Cost / Gain | Chosen |
|--------|-------------------|------------------|-------------|--------|
| **A: Ordinal only** | "3 patients ahead" (no time) | Deterministic Redis counter; pushed on event | Costs nothing; can never be wrong; gives no sense of *when* | - |
| **B: Precise ETA live** | "Estimated wait: 22 minutes" | Fresh LLM call per UI poll | Highest info value; NFR-PERF-03 flags as expensive; single-point misses erode trust (exact risk FR-07's contract tries to mitigate) | - |
| **C: Position + cached band** | "3 ahead - roughly 20-35 min" | Position (cheap, real-time) + ETA recomputed on cadence/delta and cached | Cheap real-time reads; range hedges misses; moderate build (cache + refresh trigger, reuses FR-07) | Building-block |
| **D: Qualitative bucket** | "Low / moderate / high wait" | Reuses FR-02's hourly specialty×hour bucketing; no new compute | Cheapest, hardest to be wrong about; weakest patient benefit | Fallback target |
| **E: Adaptive confidence-gated** | Position always; band only when LLM-sourced + high-confidence + no active disruption | C's data path + gating policy on FR-07's confidence/source and FR-09's `DisruptionEvent` | Automatically hides exactly during windows most likely to cause misses (active re-plans, low-confidence forecasts); no new grounding, reuses existing contracts | **Chosen** |

## Consequences

**Positive**:
- Resolves the core tension by design: patients get a number exactly when the system has grounds to trust it, and get an honest signal (position) when it doesn't, rather than choosing between "always show a risky ETA" and "never show one."
- Costs almost nothing beyond existing commitments: FR-07's contract already returns `confidence` and `source`; FR-09 already emits `DisruptionEvent`; FR-06/FR-11 already push notifications event-driven.
- Directly targets the stated failure mode: a miss can only happen on a band the system already marked high-confidence, which is rare and defensible, not the class of miss caused by mid-re-plan churn or a `BASELINE` fallback.
- Operationally transparent: uses the same disruption/audit machinery FR-09/FR-13 already require; no new doctor/coordinator surface.
- Reversible: a threshold and a data path, not a data-model commitment. Disable the band entirely (degrade to A), tighten/loosen confidence threshold, or change the degrade target (D instead of A) all as config edits, not rebuilds.

**Negative and trade-offs**:
- Introduces a cache and refresh-trigger logic (from C): one new component, moderate operational surface (monitoring cache hit rate, invalidation correctness).
- Delays transparency for low-confidence cases: a patient in a queue where the forecast is uncertain sees position but not time, which may feel less helpful than either "always show a conservative band" (C) or "always show position" (A).
- The confidence threshold is a config knob; setting it too high (never show a band) reproduces the A-only outcome; setting it too low (show bands on borderline-confident forecasts) risks the B-outcome (mis-trust). Empirical tuning in Phase 3 eval is necessary.

**Follow-up work**:
- Implement cache + refresh cadence (TASK: journey-dev + forecast-dev).
- Candidate FR (for ba-analyst to expand into spec 05): "Patient sees queue position and confidence-gated ETA display (OI-22)," referencing FR-02, FR-06, FR-07, FR-09, FR-11, BR-03/14/15/21, NFR-PERF-03/04, OI-05.
- Critical eval case set (TASK-012, Phase 3): measure patient trust/satisfaction impact of visible re-sequencing, and validate that confidence-gating hides bands exactly in the windows most likely to cause misses. This eval is mandatory before shipping FR-06's reorder-with-reason in production (per ai-governance.md).
- If OI-05 (perf budget) gets fixed with tight freshness demands, revisit: a <500ms-fresh band may not be achievable on-demand, forcing degrade to A/D-only until forecast-cost collapses.
- If Phase-3 eval shows forecast-LLM confidence is high-enough often-enough to make the gate rarely trigger, simplify to C (always show band) and drop the adaptive logic.

## References

- [TASK-017: Brainstorm queue-position / ticket transparency](../../tasks/active/TASK-017-queue-transparency-brainstorm.md) — the decision context and evidence.
- [FR-02: Intake slot recommendation](../../../specs/05-functional-requirements.md#fr-02)
- [FR-06: Journey Agent notifications](../../../specs/05-functional-requirements.md#fr-06)
- [FR-07: Forecast tool (LLM-as-a-tool)](../../../specs/05-functional-requirements.md#fr-07)
- [FR-09: Disruption Agent](../../../specs/05-functional-requirements.md#fr-09)
- [FR-11: Timeline and notifications](../../../specs/05-functional-requirements.md#fr-11)
- [FR-13: Audit log](../../../specs/05-functional-requirements.md#fr-13)
- [BR-03: Event-driven architecture](../../../specs/04-business-flows.md#br-03)
- [BR-14, BR-15: ETA grounding and fallback](../../../specs/04-business-flows.md#br-14)
- [BR-21: Notification reason inclusion](../../../specs/04-business-flows.md#br-21)
- [NFR-PERF-03, NFR-PERF-04: Performance constraints](../../../specs/07-non-functional-requirements.md#nfr-perf)
- [OI-05: Performance target unfixed](../../../specs/11-assumptions-constraints.md#oi-05)
- [OI-22: Queue position transparency (observation item)](../../../specs/07-backlog.md#oi-22)
- [AI-governance eval requirements](../../rules/ai-governance.md) — mandatory eval before shipping user-facing model output.
