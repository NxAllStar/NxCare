---
title: "TASK-017: Brainstorm - queue-position / ticket transparency model"
status: Done
fr: "-"
owner: brainstormer
deps: "-"
priority: P2
phase: 2
created: 2026-07-18
tags: [task, brainstorm]
---

# TASK-017: Brainstorm - queue-position / ticket transparency model

This is a BRAINSTORM/decision task, not an implementation task. Output is an ADR (via `/new-adr`) and
a candidate FR that `ba-analyst` writes up afterwards. Do not write product code.

## The idea (from the Team lead)

A unifying tracking layer so everyone sees the same queue truth:
- A patient sees how many people are ahead of them and how long they will wait.
- A doctor sees how many patients they should anticipate.
It replaces the real-world experience of holding a paper number with no visibility. Resolves OI-22.

## Frame it against what already exists (start grounded, not from zero)

Much of the data already exists, so this is largely a transparency/UX layer plus a modeling decision:
- `vaic.state.owner_queue(owner_id)` gives the ordered queue per room/doctor; `owner_load_minutes` the load.
- FR-07 forecast gives ETA; `Patient.priority_level` is ROUTINE/URGENT/EMERGENCY.
- The payment gate excludes `LOCKED`/unpaid tasks from the queue (BR-10).
- Tasks are per service step (each has an `owner_id` and a queue), and agents re-sequence dynamically.

## Questions to resolve (the point of this task)

1. **Granularity**: one ticket per visit, or a fresh number at each station (consult/lab/imaging)?
   Our task-per-step model leans per-station - but decide it, do not assume.
2. **Medium / tracking**: an online system tracked exam-to-exam (VAIC's premise) vs the paper baseline
   it replaces. What do real hospital Queue Management Systems (QMS) actually do? (-> tech-researcher.)
3. **Interactions**: does "people ahead of you" count `LOCKED`/unpaid tasks? How is priority
   pre-emption (emergency jumping the queue) shown honestly? When agents re-sequence, a patient's
   position changes - how to display a moving number WITHOUT eroding trust (a jumpy number is worse
   than none)?
4. Doctor-facing: is "anticipated count" the confirmed/paid queue only, or include not-yet-paid and
   forecast no-shows (FR-07)?

## Deliverable

- A trade-off matrix over the options (per-visit vs per-station; how to present a changing position),
  scored against VAIC's constraints (trust, the existing task/queue model, demo believability).
- A recommendation, captured as an ADR.
- A candidate FR outline (input/output, business rules, acceptance criteria incl. a negative case)
  handed to `ba-analyst` to add to spec 05 - NOT written here.
- `tech-researcher`: cited evidence on real hospital ticket/QMS models (per-visit vs per-station,
  paper vs digital, how position/wait is shown).

## Notes / blockers

- Do not invent the ticket semantics; that is exactly what this task decides.
- No new FR is added to spec 05 until this brainstorm concludes (keeps traceability honest).

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator | Created task file and queued brainstormer + tech-researcher | Dispatching agents now |
| 2026-07-18 | maintainer | Reconciled duplicate TASK-017 file: merged the stray `TASK-017.md` into this one (kept for naming convention + richer content) and deleted the stray | One file per task restored |
| 2026-07-18 | brainstormer | Diverged 5 options: (A) ordinal-only; (B) precise-live-ETA; (C) position+cached-band; (D) qualitative-load-bucket; (E) confidence-gated-adaptive. Scored on accuracy/trust, implementation cost, patient benefit, operational fit, reversibility. Recommendation: Option E (ordinal position always shown; ETA band shown only when FR-07 returns high-confidence + no active disruption). Frames the real decision as "what promise are we making, on what cadence, computed from what data path, how does it degrade when forecast admits low confidence?" | Trade-off matrix + score matrix + reversal conditions (OI-05 freshness requirement, Phase-3 eval evidence, patient tolerance for visible uncertainty, forecast cost collapse) |
| 2026-07-18 | tech-researcher | Verified QMS standards (NSQHS-2 Partnering with Consumers, ISO-9001 healthcare, ACHS/EQuIP): general "communicate proactively" duty but no specific transparency mechanism mandate. Patient-experience RCTs (Saudi Arabia n=190, Iran): ETA display alone does not move satisfaction (p=0.962), but expectation-matching + explanation of cause does. 70% of low-acuity ED patients want ETA *and* explanation of why. Reorder-transparency + patient trust is a major evidence gap (no rigorous study found); simulator arXiv paper on agentic reordering reports 94.2% critical cases within 10 min vs 30.8% FCFS but zero patient-facing satisfaction/trust measurement — exactly the gap VAIC's ai-governance eval requirement should close before shipping FR-06. | Evidence supports ETA+reason pairing; no compliance mandate for specific mechanism; major eval gap flagged for candidate FR |

## Result

Brainstorm complete.

**ADR drafted**: [ADR-002: Queue position and confidence-gated ETA display](../../architecture/decisions/ADR-002-queue-position-transparency.md). Decision: implement Option E (adaptive confidence-gated ladder) — ordinal position always shown; ETA band shown only when FR-07 returns high-confidence + no active disruption. Reuses FR-07's grounding contract and FR-09's disruption events; degrades gracefully to position-only. Identifies critical follow-up: Phase-3 eval case set to measure patient trust impact of visible re-sequencing (mandatory before shipping FR-06 in production per ai-governance.md).

**Candidate FR outline** (for ba-analyst expansion into spec 05):

**Title**: Queue position and confidence-gated ETA display (OI-22)

**Scope**: Patient-facing display (Journey Agent, FR-06, FR-11) showing queue position and wait-time estimate.

**Inputs**:
- Queue state: `Task.sequence_index`, `owner_id`, `execution_status` (Redis)
- ETA + confidence: FR-07 Forecast tool (`value`, `confidence`, `source: LLM|BASELINE`)
- Active disruptions: FR-09 `DisruptionEvent` (whether patient's owner/room is being re-planned)

**Outputs**: Notification to patient with:
- Always: ordinal position ("You are patient 3 in the queue")
- Conditionally (when `FR-07.source == LLM` AND `FR-07.confidence >= threshold` AND no open `DisruptionEvent` touches patient's owner): ETA band ("Estimated wait: 20-35 minutes")
- On degrade: position only, or position + qualitative load bucket (FR-02's "low/moderate/high wait")

**Acceptance criteria**:
- [ ] Position is deterministic and updated event-driven via Journey Agent push
- [ ] ETA band appears only when confidence/source conditions met
- [ ] Band silently hides (no banner, no "confidence low" message) when conditions fail
- [ ] ETA band is cached, refreshed on cadence or queue-delta, not per-request
- [ ] Notification includes reason for wait or ETA change (per FR-11 AC-11.1)

**Negative case**: When forecast is `BASELINE`-sourced (deterministic baseline, not LLM), no ETA band is shown, even if value is stable; position-only is shown instead.

**Business rules**:
- Confidence threshold for ETA display is configurable (tuned in Phase-3 eval).
- ETA cache TTL and refresh trigger are jointly configured with forecast-dev (FR-07 SLA, OI-05 perf budget).
- Phase-3 eval (TASK-012) measures patient trust/satisfaction impact and validates that confidence-gating hides bands in active-re-plan windows.

**Dependencies**: FR-02 (slot recommendation, qualitative load), FR-06 (Journey Agent), FR-07 (Forecast + grounding contract), FR-09 (Disruption events), FR-11 (Notifications), FR-13 (audit log for degrade reasons).

**Cross-links**: [ADR-002](../../architecture/decisions/ADR-002-queue-position-transparency.md), [TASK-012 (Phase-3 eval)](../../tasks/active/TASK-012-eval-baseline.md), [ai-governance.md](../../rules/ai-governance.md) (mandatory eval before rollout of user-facing model output).

---

**Status**: Ready for ba-analyst to expand into formal FR 23 (or next available) in spec 05, following the candidate outline above. Brainstorm task complete; mark TASK-017 Done.
