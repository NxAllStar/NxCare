# tech-researcher - Research evidence on queue transparency in patient-facing healthcare systems, with focus on QMS (quality management system) standards and patient experience impact.

- agent_type: tech-researcher
- agent_id: a9349e7d3d2e0b176
- finished: 2026-07-18 12:46:55
- transcript: /home/vuongchu/.claude/projects/-data-hdd-16t-vuongchu-civil-vaic/f2ce16f6-bd11-4373-b26a-65cbb41a2c73/subagents/agent-a9349e7d3d2e0b176.jsonl

## Prompt

```
Research evidence on queue transparency in patient-facing healthcare systems, with focus on QMS (quality management system) standards and patient experience impact.

Look for:
1. **QMS standards**: ISO, ACHS, or local healthcare standards that mention wait-time transparency, patient communication, or queue position disclosure. What do they recommend or require?
2. **Patient experience research**: studies on how queue position / wait-time information affects patient anxiety, satisfaction, and behavior (e.g., do patients leave early if they see a long queue?)
3. **Existing implementations**: how healthcare platforms (urgent care, dental, vaccination clinics) handle this. Approaches to ETA accuracy and reordering transparency.
4. **Pitfalls**: cases where queue transparency backfired (e.g., unrealistic ETAs, frequent reordering eroding trust).

Provide cited evidence—links, study names, standard references—that the brainstormer can use to ground the trade-off analysis.

Constraint: this research is for an ADR decision. Keep it focused on the specific decision (what transparency model), not a full healthcare IT survey."
```

## Response

```
## Research: Queue Transparency in Patient-Facing Healthcare Systems

### Context assumed
I read `docs/specs/04-business-flows.md` and `docs/specs/05-functional-requirements.md` to ground this in VAIC's actual decision surface: FR-06 (Journey Agent proactively pushes ETA and *proposes reordering within dependency limits, with a reason*) and FR-07 (Forecast Agent, grounded/range-checked ETA, `LOW_CONFIDENCE` flag on rejection). The relevant ADR question is narrow: **how much of the queue/ETA/reorder mechanics should the patient-facing Journey Agent surface, and how**, not a general healthcare-IT queueing survey. No project data was sent externally; only public sources were queried.

---

### 1. QMS standards - what I could and could not verify

- **NSQHS Standard 2 - Partnering with Consumers** (Australian Commission on Safety and Quality in Health Care) requires organisations to "communicate with consumers in a way that supports effective partnerships" and to give consumers information to support their own care decisions. [Partnering with Consumers Standard](https://www.safetyandquality.gov.au/national-standards/nsqhs-standards/partnering-consumers-standard) - general principle of proactive, comprehensible communication, but **I could not find a clause that specifically mandates wait-time or queue-position disclosure**. Treat "communicate proactively about care" as the applicable principle, not a literal wait-time requirement.
- **ISO 9001 in healthcare**: applied as a general QMS certifying the *service process*, and studies associate ISO 9001 certification with higher patient satisfaction and more systematic appointment-scheduling review. [ISO 9001 in Healthcare - Riddle Compliance](https://riddlecompliance.com/iso-9001-in-healthcare-implementing-a-quality-management-system/); [Effect of ISO 9001 and EFQM on hospital performance - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC4706847/). **I could not find an ISO 9001 clause naming wait-time transparency or queue-position disclosure specifically** - it is inferred via general "continual improvement of the patient experience," not a hard requirement.
- **ACHS / EQuIP**: I could not locate ACHS/EQuIP criteria text mentioning wait-time or queue disclosure specifically; ACHS material found was scope/structure-level only. [ACHS accreditation overview](https://www.achs.org.au/our-services/accreditation-and-standards).

**Bottom line for the ADR**: no QMS standard found *mandates* a specific transparency mechanism (queue position vs. ETA-only vs. silent). The standards establish a general duty to communicate proactively and support patient understanding - which supports *some* transparency but does not dictate FR-06's specific design (full position vs. banded ETA vs. reorder explanation).

### 2. Patient experience research - direct evidence

- **RCT, Emergency Department, Saudi Arabia (n=190)**: providing an estimated wait time at triage produced **no statistically significant difference in overall satisfaction** (p=0.962), even though 81.4% of patients said they preferred seeing an ETA displayed. The paper's own conclusion: *managing perceptions of wait time is "inconsequential" to satisfaction improvement on its own* - satisfaction tracked more with whether the actual wait matched or beat expectation than with the mere presence of a number. [Effect of the provision of estimated waiting time on patient satisfaction - PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC11864359/)
- **Iranian RCT on a queue management system**: with the system, perceived wait time was *significantly shorter* than actual wait; without it, perceived wait was *significantly longer* than actual - i.e., transparency compresses the perception gap, and that gap (not the raw number) is what drives satisfaction. [Effect of QMS on patient satisfaction - PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8464010/)
- **Patient-centred needs assessment (Calder-Sprackman et al., 2021)**: 70% of low-acuity ED patients wanted a better wait-time estimate *and an explanation of the reason for the wait*, not just a number - explanation of cause matters as much as the ETA itself. [Availability of ED wait-time information - Wiley](https://onlinelibrary.wiley.com/doi/10.1155/2021/8883933) (I could not fetch full text past the abstract-level search summary; treat this as a secondary citation pending full-text verification).
- **Uncertainty/control literature**: waiting "in ignorance" produces perceived powerlessness; giving patients partial control/information reduces stress - the mechanism cited repeatedly across the ED literature for why ETA display helps anxiety even when it doesn't move top-line satisfaction. Same source set as above.

**Implication for FR-06**: the evidence supports giving patients *an ETA with a reason*, but warns that satisfaction is gated on **expectation-matching**, not on transparency alone - an inaccurate or frequently-revised ETA can be worse than a stable, conservative one. This is directly relevant to VAIC's `LOW_CONFIDENCE` flag path (05-functional-requirements.md AC-07.4): when forecast falls back to the deterministic baseline, the patient-facing message should probably say so plainly rather than presenting a possibly-wrong LLM number with false confidence.

### 3. Existing implementations

- **QLess** (commercial virtual-queue vendor, used in healthcare): gives patients a projected wait computed from real-time data, sends notifications when the wait changes and when it's their turn, and lets them wait off-site. [QLess healthcare](https://www.qless.com/industry/healthcare/), [QLess wait-time reduction](https://www.qless.com/how-a-patient-queue-management-system-improves-healthcare-waits/). This is the closest commercial analogue to FR-06's "escort + notify" pattern, though I could not verify QLess's internal accuracy/reliability metrics from public docs - vendor marketing copy is the only source found, not an independent evaluation.
- I could not verify specific NHS or Solv/Zocdoc implementation details on queue-position display or reorder transparency from primary sources within this search; general claims found were vendor-blog level, not documented in an official product spec I could point to. Flagging this as unverified rather than asserting it.

### 4. Pitfalls - direct and inferred

- **Expectation mismatch dominates satisfaction, not display of ETA itself**: the RCT above shows a wait "longer than expected" produces the lowest satisfaction regardless of whether an ETA was shown - i.e., an ETA that turns out wrong can be worse than no ETA, because it sets and then violates an expectation. [PMC11864359](https://pmc.ncbi.nlm.nih.gov/articles/PMC11864359/)
- **Reordering and fairness perception**: general queue-management commentary (vendor-level, not peer-reviewed - flagging weaker source quality) argues that visible reordering, even when urgency-justified, risks a "queue equity" perception problem where patients who see others move ahead lose trust unless the reason is explained. I could not verify this claim against a primary/academic source (the one dedicated piece found, queueworx.com, returned HTTP 403 and could not be read in full - so treat this point as a plausible mechanism worth testing in VAIC's eval set, not an established finding).
- **A recent simulation study (arXiv 2604.00215) building an agentic AI urgency-reordering queue system for outpatient departments reports strong operational metrics (94.2% of critical patients seen within 10 minutes vs 30.8% under FCFS) but explicitly does not report any patient-facing transparency, trust, or satisfaction metric** - the evaluation is throughput-only, on synthetic patients. [arXiv:2604.00215](https://arxiv.org/abs/2604.00215) This is itself the pitfall to name in the ADR: it is easy to build and simulate a reordering engine (as FR-06/FR-09 do) while never measuring whether patients tolerate or trust the reordering it produces - the exact gap VAIC's AI-governance eval requirement (ai-governance.md, "Evaluation before rollout") is meant to close, since FR-06's reorder-with-reason behavior is user-facing model output that changes behavior and therefore needs a frozen eval case set, not "three examples in a chat window."

---

### What this means for the ADR (grounded, not prescriptive)

Evidence supports:
1. Show an ETA, not silence - the anxiety/control literature is consistent on this.
2. Pair every ETA and every reorder with a stated reason - the 70%-of-patients-want-an-explanation finding and FR-06's existing design ("proposes reordering... notifies the patient with a reason") already align with the evidence.
3. Do not oversell precision - since satisfaction hinges on expectation-matching, a `LOW_CONFIDENCE`/baseline-fallback ETA (already in FR-07's contract) should be visibly hedged to the patient, not shown with the same confidence as a grounded number - this is not proven by a specific study but follows directly from the "wait longer than expected produces the lowest satisfaction" finding.
4. No standard I could verify (ISO 9001, ACHS, NSQHS) mandates a specific transparency mechanism, so the choice between full-queue-position, ETA-band, or ETA-plus-reason is a product decision constrained only by the general "communicate proactively" duty, not a compliance requirement - the brainstormer should not treat this as a compliance-driven decision.
5. Reorder-frequency and reorder-trust is the biggest evidence gap: I found no rigorous study measuring patient trust impact of visible re-sequencing (only a vendor blog I could not access, and a simulation paper that measured throughput but not trust). This is a genuine unknown that the ADR should flag as needing VAIC's own eval case set (per ai-governance.md) rather than assumed from literature.

Files referenced (read-only, no edits made): `/data_hdd_16t/vuongchu/civil/vaic/docs/specs/04-business-flows.md`, `/data_hdd_16t/vuongchu/civil/vaic/docs/specs/05-functional-requirements.md`.
```
