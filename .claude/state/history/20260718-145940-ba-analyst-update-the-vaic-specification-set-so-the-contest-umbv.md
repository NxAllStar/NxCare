# ba-analyst - Update the VAIC specification set so the contest brief becomes the explicit guiding source the product evolves around, with full traceability to existing requirements. This is a docs-only change under docs/specs/. We are on branch `specs-cnv` (not main).

- agent_type: ba-analyst
- agent_id: a5d34f17f446df5f2
- finished: 2026-07-18 14:59:40
- transcript: /home/vuongchu/.claude/projects/-data-hdd-16t-vuongchu-civil-vaic/efdd2a60-1afe-4596-986c-4c3c0b6c4e4d/subagents/agent-a5d34f17f446df5f2.jsonl

## Prompt

```
Update the VAIC specification set so the contest brief becomes the explicit guiding source the product evolves around, with full traceability to existing requirements. This is a docs-only change under docs/specs/. We are on branch `specs-cnv` (not main).

CONTEXT: The owner supplied the original contest brief and wants "our product to evolve around the core features / requirements from the contest as a guideline." The existing spec (docs/specs/01-overview.md and 05-functional-requirements.md) is already well-aligned. DO NOT invent new FRs or restate requirements. Instead, anchor the contest brief verbatim and map its 5 core features to the existing FRs, flagging any genuine coverage gap.

THE CONTEST BRIEF (source of truth to capture):

Problem Statement — Hospitals lack a unified, real-time view of how patients move through the system. Appointment, registration, clinic, lab, and imaging data sit in silos. Result: patients bunch up in the same slots while others go unused; patients get routed to the wrong area and backtrack; patients wait with no visibility into how long it will take. Goal: build a smart coordination system connecting appointments, check-in, clinics, labs, imaging, and real-time department status into one system.

Core Features:
1. Appointment Coordination — distribute patients across doctors, specialties, and time slots; prevent overcrowding at popular times while other slots stay empty; balance load dynamically based on real demand, not fixed scheduling.
2. Patient Routing — route based on symptoms, priority level, patient category, and required services; direct patients to the correct area from the first step; eliminate repeated trips and wrong-queue errors.
3. Wait-Time Estimation — analyze number of patients waiting, average consultation time, and clinic/equipment status; forecast expected service time per patient; display via app, digital screen, or SMS.
4. Service-Sequencing Recommendations — auto-order tests/procedures (blood work, ultrasound, X-ray, CT, MRI, etc.); base sequencing on wait times, fasting requirements, result turnaround time, and equipment availability; example: draw blood → X-ray while blood processes → ultrasound → return to doctor once all results ready; minimize idle waiting and backtracking.
5. Real-Time Adjustment — re-coordinate the plan when a clinic is overloaded, equipment fails, a doctor's schedule shifts, or an emergency arrives; keep all downstream steps (routing, sequencing, wait estimates) updated automatically.

Success Metrics: reduced average patient wait time; reduced congestion across departments; increased clinic and equipment utilization; patients able to actively track their own care pathway in real time.

WHAT TO DO:
1. Read docs/specs/01-overview.md fully and skim 05-functional-requirements.md for the FR titles.
2. In 01-overview.md, add a new section titled "Contest brief (guiding source)" that (a) states this brief is the guiding requirement the product evolves around, and (b) contains a traceability table mapping each of the 5 core features to the FRs that satisfy it. Based on my analysis the mapping is: Feature 1 -> FR-02, FR-08; Feature 2 -> FR-01, FR-06; Feature 3 -> FR-07 (forecast) + FR-11/FR-15 (display via app/screen/SMS); Feature 4 -> FR-04 (AC-04.1 encodes the blood→X-ray→ultrasound example); Feature 5 -> FR-09, FR-10. Verify each mapping against the actual FR text before writing it. Also map the four success metrics to the existing G-01..G-04 goals and the Success metrics table.
3. Flag any genuine gap. Note candidate: the brief's "patient category" (e.g. child/elderly/insurance class) in Feature 2 — check whether FR-01's triage record ({specialty, priority_level, constraints}) covers it; if not, record it as an open issue in 11-assumptions-constraints.md rather than silently adding scope.
4. Keep the existing bilingual VI/EN style consistent with the rest of 01-overview.md. Follow all writing conventions: English identifiers, no emoji, no em dash (use "-"), sentence-case headings, relative-path cross-links.
5. Add a revision-history entry in docs/specs/13-revision-history.md describing this change.
6. Do NOT touch any Accepted ADR or anything outside docs/specs/.

Report back: exactly which files/sections you changed, the traceability mapping you wrote, and any gap you flagged.
```

## Response

```
This is complete and well-formed. Summary of the work follows.

## What changed

**`docs/specs/01-overview.md`**
- Inserted a new `## Contest brief (guiding source) {#contest-brief}` section between "Success metrics" and "Judging criteria" (lines 91-137). It states the brief is the guiding requirement source the product evolves around, quotes the brief **verbatim** in English (not translated, to avoid disputing wording), and adds two traceability tables plus a gap callout.
- Updated `## References` to cite the contest brief as a source, linking to the new section.

**`docs/specs/11-assumptions-constraints.md`**
- Added `OI-23` to the Open issues table: the brief's Feature 2 "patient category" (child/elderly/insurance class) has no explicit field in FR-01's triage schema `{specialty, priority_level, constraints}`; needs Team lead confirmation whether to add a field or treat it as covered by `constraints`.

**`docs/specs/13-revision-history.md`**
- Added version row `1.5` (author `ba-analyst`, approval `Team lead (pending review)`) and two rows in "Changes by section" for `01` and `11`.

No FR text, ADR, or file outside `docs/specs/` was touched. `docs/requirements/` contains only `docs/templates/PRD.md` (no PRDs exist yet for any FR), so there was nothing to sync there.

## Traceability mapping written

| Brief core feature | Satisfied by | Verified against |
|---|---|---|
| 1. Appointment Coordination | FR-02, FR-08 | FR-02 ranks slots by forecast load; FR-08 `allocate_slot()` bounds by doctor/room capacity |
| 2. Patient Routing | FR-01, FR-06 | FR-01 triage schema routes by symptom/priority/constraint; FR-06 Journey Agent prevents backtracking mid-pathway |
| 3. Wait-Time Estimation | FR-07, FR-11, FR-15 | FR-07 forecasts ETA/load/no-show; FR-11 is the in-app display (in scope); FR-15 (screen/SMS) is Could-priority and explicitly out of scope this release per `01-overview.md` "Out of scope" |
| 4. Service-Sequencing Recommendations | FR-04 | AC-04.1 literally encodes the brief's blood-draw -> X-ray -> ultrasound example |
| 5. Real-Time Adjustment | FR-09, FR-10 | FR-09 Disruption Agent re-plans on overload/failure/schedule shift/emergency with tiered autonomy; FR-10 Coordinator Agent keeps downstream state consistent |

Success metrics mapped to G-01 (avg wait time), G-02 (congestion), G-03 (utilization), and G-04 (patient tracking) plus the existing Success metrics table rows; noted that G-04 has no dedicated quantified row (qualitative only, via FR-06/FR-11/FR-17).

## Gap flagged

Contest brief Feature 2 says routing should also consider "patient category" (e.g. child/elderly/insurance class). FR-01's triage output schema is `{specialty, priority_level, constraints}` with no explicit patient-category field. This was **not** silently added as scope - it's recorded as `OI-23` in `docs/specs/11-assumptions-constraints.md`, owned by Team lead, blocking any future extension of FR-01's schema.
```
