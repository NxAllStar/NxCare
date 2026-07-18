# Known issues - VAIC - AI Care Pathway Coordinator

Issues, quirks, and environment gotchas that are known and not yet fixed, together with what to do
about them in the meantime.

Record the WORKAROUND, not just the symptom. An environment gotcha discovered once and left
unwritten gets rediscovered, at full cost, by every agent and every new engineer who hits it: the
build that only succeeds behind a specific wrapper, the test suite that fails under a sandbox that
blocks loopback, the parallelism flag that avoids an out-of-memory kill. Write it down the FIRST
time it is found.

Updated via `/sync-context`. Nothing is deleted: a fixed issue is marked Fixed and keeps its entry,
because the same symptom will come back and the old entry is what makes it recognizable.

| Issue | Symptom | Workaround | Status | Discovered |
|-------|---------|-----------|--------|------------|
| KI-01 model sovereignty undecided | `model-policy.md` names no approved model per data class ("Undecided") | Table is ADVISORY until Team lead sets it (TASK-002). Demo data is synthetic so no real PHI is at risk now; never send real Confidential+ data to any model. | Open | 2026-07-18 |
| KI-02 data residency undecided | the DATA_RESIDENCY policy is not set; no processing-region boundary | Advisory; Vietnam expected for production. Decide before any real data enters (TASK-002). | Open | 2026-07-18 |
| KI-03 dependency licence policy undecided | `ip-compliance.md` allow/deny lists not set by the org | Do not add a dependency with a non-permissive licence until the lists are set (TASK-002). | Open | 2026-07-18 |
| KI-04 IP ownership undecided | ownership of agent-authored code not stated | Flag before any external sharing/handoff; resolve with the org (TASK-002). | Open | 2026-07-18 |
| Read deny also blocks .env.example | agents cannot Read `.env.example` (deny `Read(**/.env.*)`) | Harmless - it is placeholders; agents use the template in the repo. Edit `.env.example` via shell if needed. | Open | 2026-07-18 |
| Agent framework not chosen | LangGraph vs FastAPI tool-loop unresolved (spec OI-18) | Keep framework code behind the agent-core interface; decide via TASK-001 -> ADR before building the runtime. | Open | 2026-07-18 |
| Running modules needs the package installed | `python -m vaic.simulator.run` fails with `No module named 'vaic'` in a fresh shell (pytest works because pyproject sets pythonpath=src) | Run `pip install -e .` once (editable install), or prefix with `PYTHONPATH=src`. | Workaround in place | 2026-07-18 |
| Own-scope denies some patient-facing entities | Under Own scope a patient cannot resolve their own `Diagnosis`/`ServiceOrder`/`Slot`/`Payment`/`AuditLogEntry` (no direct/one-hop patient link in the data model) | Auth `is_own` fails CLOSED (denies), which is safe - not a leak. Add a resolvable patient link via TASK-016 to enable Own-scope for these. | Open | 2026-07-18 |

<!-- Status: Open | Workaround in place | Fixed (link the fix). -->

<!-- Never record a credential, a secret value, or real customer data here as part of a repro. -->
