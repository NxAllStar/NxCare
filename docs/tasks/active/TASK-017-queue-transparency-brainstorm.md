---
title: "TASK-017: Brainstorm - queue-position / ticket transparency model"
status: Planned
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

## Result

<Filled when the brainstorm concludes: the decision, the ADR link, and the candidate-FR outline.>
