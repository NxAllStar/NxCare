---
title: "TASK-005: Forecast tool (LLM-as-a-tool) + grounding contract"
status: Done
fr: "FR-07"
owner: forecast-dev
deps: TASK-004
priority: P0
phase: 1
created: 2026-07-18
tags: [task]
---

# TASK-005: Forecast tool (LLM-as-a-tool) + grounding contract

## Goal

Implement the forecast tool (ETA / hourly load / no-show) as an LLM-with-reasoning exposed as a tool,
enforcing the retrieve-reason-validate grounding contract from FR-07 (OI-20 resolved).

## Inputs and context

- FR-07 + its "Grounding contract" in `docs/specs/05-functional-requirements.md`; NFR-SEC-20.
- Builds on TASK-003 (models/state) and TASK-004 (tools framework). Owns `src/vaic/forecast/`.

## Acceptance criteria

- [x] `estimate_wait(room)` / load / no-show return `{value, confidence, provenance, source}`.
- [x] Three phases: retrieve observed features (deterministic) -> LLM reason returns
      `{value, confidence, cited_features[]}` -> validate (range + monotonic sanity + provenance).
- [x] A violation (out-of-range, or a cited feature not in the retrieved set) rejects the LLM value
      and falls back to a deterministic baseline flagged `LOW_CONFIDENCE`.
- [x] The LLM client is mocked in tests; runs deterministically (fixed seed). Tests + ruff green.

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | forecast-dev | Implemented `src/vaic/forecast/` (`features.py` retrieve, `llm.py` ForecastLLM protocol + LLMEstimate schema, `validate.py` range/monotonic-sanity/provenance checks, `tool.py` `estimate_wait()`). TDD: wrote `tests/test_forecast.py` first (RED, ImportError), then implemented to GREEN. Covers happy path, out-of-range, provenance failure, monotonic-sanity failure, LLM-unavailable, malformed-schema, and determinism/edge cases (empty queue, no history, unknown resource, invalid hour). | `python3 -m pytest -q`: 40 passed (13 new). `python3 -m ruff check src tests`: All checks passed. No files touched outside `src/vaic/forecast/` and `tests/`. |

## Result

Delivered `src/vaic/forecast/` implementing FR-07 as an LLM-as-a-tool with the three-phase grounding
contract: `features.py` (retrieve), `llm.py` (`ForecastLLM` protocol + `LLMEstimate` schema),
`validate.py` (range + monotonic-sanity + provenance checks, deterministic baseline), `tool.py`
(`estimate_wait` -> `{value, confidence, provenance, source}`). Any LLM failure, malformed output, or
failed check falls back to a `LOW_CONFIDENCE` baseline (`source=BASELINE`). `tests/test_forecast.py`
= 13 tests with a fake LLM (no network). Orchestrator-verified: `pytest` 40 passed, `ruff` clean;
read `tool.py`/`validate.py` to confirm the checks genuinely reject (not a dead control); diff
confined to `src/vaic/forecast/` + `tests/`. No git yet -> formal code/security review gates run
before the first real PR. File moved to docs/tasks/done/.
