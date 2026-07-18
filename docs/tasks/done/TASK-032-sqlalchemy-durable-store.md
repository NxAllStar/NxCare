---
title: "TASK-032: SQLAlchemy-backed relational schema for a durable store"
status: Done
fr: "-"
owner: tuan.nguyen15
deps: "-"
priority: P2
phase: 2
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-032: SQLAlchemy-backed relational schema for a durable store

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree. Read the board row back after writing it.

## Goal

Give the project a concrete relational schema (PostgreSQL) for every entity in
`docs/specs/08-data-model.md`, with `schemas.sql` as the authoritative DDL source and SQLAlchemy
models mapped onto it, so a durable store option now exists behind `src/vaic/state` without
disturbing the Redis path already in use. This resolves [OI-15](../../specs/11-assumptions-constraints.md#oi-15)
(durable store beyond Redis) in favor of PostgreSQL/SQLAlchemy.

## Inputs and context

- Related spec: [08-data-model.md](../../specs/08-data-model.md) (entities, data dictionary, state
  machines) - the schema below implements it field-for-field.
- Related open issue: [OI-15](../../specs/11-assumptions-constraints.md#oi-15).
- Related rule: `.claude/rules/data-model.md` ("keep persistence behind `src/vaic/state`"),
  `.claude/rules/tech-stack.md` ("no ORM... a durable store is not yet chosen").
- Base branch: `cnv-dev`, at the tip that does NOT yet include the (unmerged) TASK-016 patient-link
  denormalization on `Diagnosis`/`ServiceOrder`/`Slot`/`Payment`/`AuditLogEntry`. Building on top of
  an unmerged branch was avoided per git-workflow.md; the schema matches the entities as committed on
  `cnv-dev` today.
- Connection: `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` (read from the environment at
  runtime - never read from `.env` by an agent; the process loads `.env` itself, per
  agent-guardrails.md).
- Driver choice: `pg8000` (pure-Python, BSD-3-Clause) rather than `psycopg2` (LGPL) - LGPL sits in
  the copyleft/denied bucket in `.claude/rules/model-policy.md`'s dependency table pending a Team
  lead ruling (ip-compliance.md); `pg8000` avoids that question entirely. `sqlalchemy` itself is
  MIT. Both are added as an optional `sql` extra, not a core dependency - Redis remains the only
  store the app requires by default.

## To do

- [x] Write `src/vaic/state/sql/schemas.sql`: one `CREATE TYPE ... AS ENUM` per enum in
      `src/vaic/models/enums.py`, one `CREATE TABLE` per entity in `ENTITIES`
      (`src/vaic/models/entities.py`), explicit `ON DELETE` action on every FK, unique constraints
      where the dictionary implies uniqueness (`patient_code`, `ServiceType.code`), indexes on the
      columns the codebase actually filters/joins on (`patient_id` everywhere, scope predicates in
      `src/vaic/auth/scope.py`; `owner_id`/`execution_status` for queue queries in
      `src/vaic/state/repository.py`).
- [x] Write `src/vaic/state/sql/models.py`: SQLAlchemy 2.0 declarative models mirroring
      `schemas.sql` column-for-column (for future querying/reporting use).
- [x] Write `src/vaic/state/sql/engine.py`: `get_engine()` building a `postgresql+pg8000://` URL
      from the five `DB_*` env vars, and `create_schema(engine)` executing `schemas.sql` verbatim -
      the SQL file is the source of truth, SQLAlchemy is the executor, not an independent schema
      generator (`metadata.create_all()` is deliberately not used for table creation).
- [x] Add `sqlalchemy` and `pg8000` as an optional dependency group in `pyproject.toml`.
- [x] Prove it end-to-end against a real (disposable, local-only) PostgreSQL instance - not mocked,
      per testing.md's Integration layer - then tear the instance down.
- [x] Update `docs/specs/08-data-model.md` and `docs/specs/11-assumptions-constraints.md` (OI-15) and
      `docs/specs/13-revision-history.md` in the same change.

## Acceptance criteria

- [x] `schemas.sql` creates one table per entity in `docs/specs/08-data-model.md`, runnable against a
      real PostgreSQL instance with no manual fix-up.
- [x] SQLAlchemy models in `models.py` match `schemas.sql` table and column names exactly (checked by
      an automated test, not by eyeballing).
- [x] `create_schema()` is exercised against a real, disposable PostgreSQL container in the test
      suite: tables are created, a row round-trips, and an FK violation is rejected by the database.
- [x] OI-15 in `docs/specs/11-assumptions-constraints.md` is marked resolved, referencing this task.

## Decisions and blockers

- Chose PostgreSQL (per the human owner's direction) and `pg8000` over `psycopg2` for the license
  reason above.
- `schemas.sql` intentionally omits FKs for `diagnosed_by`, `ordered_by`, `confirmed_by`,
  `decided_by`: the dictionary describes them as "the doctor" / "the signing doctor" / "an
  authorised source" / "the approving coordinator" without naming a persisted table those resolve
  to in spec 08 (no `Account` entity exists there - `Account` lives only in `src/vaic/auth`, not in
  the data model). Documented as a deliberate omission, not an oversight, per data-model.md
  ("nullability is a decision"). `owner_id` and `scanned_by` DO get an FK to `resources`, since the
  dictionary explicitly says "FK -> Resource" for both.
- `AuditLogEntry.target_id` and `Payment.subject_id` are polymorphic (any entity; Task or
  Appointment respectively) per spec 08, so neither gets an FK at all - same reasoning as the
  "deliberately no FK" bullet above, not an oversight. Every FK that DOES exist uses
  `ON DELETE RESTRICT` (the schema's default correctness bias - no silent cascade data loss in a
  healthcare demo); revisit to `SET NULL` on `AuditLogEntry`'s links once TASK-016 adds a real FK
  there (BR-23 requires the log entry to survive even if its subject is later removed).
- Follow-up: once TASK-016 merges into `cnv-dev`, `schemas.sql`/`models.py` need a follow-up change
  adding the denormalized `patient_id` column (with an FK + index) to `diagnoses`, `service_orders`,
  `slots`, `payments`, and a nullable one to `audit_log_entries`, mirroring
  `src/vaic/models/entities.py`. Not done here to avoid building this branch on top of an unmerged
  branch.
- This task does NOT add a `SqlRepository` implementing `vaic.state.Repository` (i.e. the app does
  not actually start reading/writing through Postgres yet) - out of scope: the request was
  specifically "create the necessary tables from a schemas.sql", not "add a second live backend".
  If a real durable-store cutover is wanted, that is a new, larger task built on top of this one.

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | tuan.nguyen15 | Claimed task, branched `feat/TASK-032-sqlalchemy-durable-store` off `cnv-dev` | Active |
| 2026-07-18 | tuan.nguyen15 | Wrote `schemas.sql` (15 tables, 10 enum types, explicit FK actions, indexes on actual query-shape columns), `models.py`, `engine.py`, `sql` optional dependency group | Done |
| 2026-07-18 | tuan.nguyen15 | Ran `.venv/bin/python -m pytest -q`: 73 passed, 1 skipped (the live-DB test, skipped without `VAIC_TEST_DB_URL`) | Passed |
| 2026-07-18 | tuan.nguyen15 | Ran `.venv/bin/python -m ruff check .`: all checks passed | Passed |
| 2026-07-18 | tuan.nguyen15 | Spun a disposable `postgres:16-alpine` container (port 15433, local-only), ran `create_schema()` against it: all 15 tables created; manually round-tripped a `Patient` row and confirmed an FK violation on `appointments.patient_id` was rejected by the database; re-ran `tests/test_sql_schema.py` with `VAIC_TEST_DB_URL` set - 4/4 passed (including the live-DB test); tore the container down (`docker rm -f`) | Passed |
| 2026-07-18 | tuan.nguyen15 | Updated `docs/specs/08-data-model.md` (persistence notes, open points) and `docs/specs/11-assumptions-constraints.md` (moved OI-15 to Resolved issues) and `docs/specs/13-revision-history.md` (v2.2) in the same change | Done |

## Result

Delivered: `src/vaic/state/sql/schemas.sql` (PostgreSQL DDL, the source of truth - 15 tables, 10
native enum types, explicit `ON DELETE` action on every FK, indexes matched to the query shapes
`src/vaic/auth/scope.py` and `src/vaic/state/repository.py` actually use), `models.py` (SQLAlchemy
2.0 declarative models mirroring it column-for-column), `engine.py` (`get_engine()` from `DB_HOST`/
`DB_PORT`/`DB_USER`/`DB_PASSWORD`/`DB_NAME`, `create_schema()` executing `schemas.sql` verbatim), and
`tests/test_sql_schema.py` (structural parity tests that always run, plus a live-PostgreSQL
integration test gated on `VAIC_TEST_DB_URL`). `sqlalchemy` + `pg8000` added as an optional `sql`
dependency group (`pip install -e ".[sql]"`) - Redis remains the app's default, required store.

Resolved [OI-15](../../specs/11-assumptions-constraints.md#oi-15): durable store = PostgreSQL via
SQLAlchemy. Verified end-to-end against a real, disposable local PostgreSQL container (not mocked):
schema creation, a row round-trip, and FK-violation rejection all confirmed, then the container was
torn down.

Follow-up recorded (not done here, to avoid building on an unmerged branch): once TASK-016 merges,
`schemas.sql`/`models.py` need the denormalized `patient_id` column added to `diagnoses`,
`service_orders`, `slots`, `payments` (with FK + index) and, nullable, to `audit_log_entries`,
mirroring `src/vaic/models/entities.py`.

Out of scope by design: no `SqlRepository` implementing `vaic.state.Repository` was added - the app
does not read/write through Postgres yet, only the schema exists. A live cutover is a separate,
larger task.

Commit: pending (not yet committed at task-close time - see the session's git history for the
actual commit hash once created).
