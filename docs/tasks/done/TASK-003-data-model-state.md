---
title: "TASK-003: Data model + Redis state interface"
status: Done
fr: "-"
owner: data-modeler
deps: TASK-001
priority: P0
phase: 1
created: 2026-07-18
tags: [task]
---

# TASK-003: Data model + Redis state interface

## Goal

Implement the entities and enums from `docs/specs/08-data-model.md` as Pydantic models, plus a
framework-agnostic state repository (in-memory now, Redis-swappable) so a durable store choice
(spec OI-15) stays reversible.

## Inputs and context

- Related FR: foundation for all FRs; entities per [spec 08](../../specs/08-data-model.md)
- Related files: `src/vaic/models/`, `src/vaic/state/`, `tests/`
- Proceeds on the framework-agnostic layer (safe under either ADR-001 option).

## To do

- [x] `pyproject.toml`, package skeleton, ruff config.
- [x] Enums matching spec 08 glossary (English UPPER_SNAKE_CASE).
- [x] Pydantic entities for all 15 entities + ScanEvent.
- [x] State-transition tables + validator for Task / Appointment / CarePlan / DisruptionEvent.
- [x] Repository interface + in-memory store; Redis store behind the same interface.
- [x] Tests: model validation, state-machine invariants, LOCKED-task exclusion, repo round-trip.

## Acceptance criteria

- [x] Entities and enums match spec 08; enum values are English UPPER_SNAKE_CASE.
- [x] An `UNPAID` task is `LOCKED` and excluded from queue/load (BR-10).
- [x] State transitions are validated; an illegal transition raises.
- [x] Persistence is behind an interface; swapping the store needs no domain change.
- [x] Tests green; coverage on models/state meaningful.

## Decisions and blockers

- DECISION: persistence behind `state.Repository`; in-memory impl for tests/dev, Redis impl for the
  running demo. No framework import in this layer (safe under ADR-001 either option).
- DECISION: `Payment` is a proceed-flag record - no money fields beyond a display-only amount (AS-02).

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | data-modeler | Implemented models, enums, transitions, repository (memory + redis), and tests | see Result |
| 2026-07-18 | data-modeler | Ran gates: `ruff check src tests` clean; `pytest` 17 passed | green -> Done |

## Result

Delivered the framework-agnostic data + state foundation:
- `src/vaic/models/` - 15 entities + `ScanEvent` (Pydantic, `extra="forbid"`), enums as `StrEnum`
  (English UPPER_SNAKE_CASE), and the four state machines with a validator (`assert_transition`).
- `src/vaic/state/` - `Repository` ABC; `InMemoryRepository` (deep-copy isolation) and
  `RedisRepository` (lazy `redis` import) behind one interface; `owner_queue` / `owner_load_minutes`
  encode BR-10 (unpaid/LOCKED tasks excluded from queue and load).
- `pyproject.toml` (pydantic, redis; pytest/ruff dev), ruff config.
- Tests: `tests/test_models.py`, `tests/test_transitions.py`, `tests/test_state.py` - 17 passing,
  ruff clean. Verified: unpaid task is LOCKED and out of queue/load; illegal transitions raise.

No git yet, so no PR; commit when the repo is initialised. Follow-up: the Redis path is not run
against a live server in tests (no server) - integration test deferred to when Redis runs in the
Docker harness (TASK-006/devops). File moved to docs/tasks/done/.
