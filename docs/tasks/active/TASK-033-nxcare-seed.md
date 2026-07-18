---
title: "TASK-033: Create the nxcare database and seed synthetic rows via SQLAlchemy"
status: Active
fr: "-"
owner: tuan.nguyen15
deps: TASK-032
priority: P2
phase: 2
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-033: Create the nxcare database and seed synthetic rows via SQLAlchemy

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree. Read the board row back after writing it.

## Goal

On the local/dev PostgreSQL instance the human owner pointed at, create a new `nxcare` database,
run `schemas.sql` (TASK-032) against it, and seed every table with 10-50 synthetic rows respecting
FK dependency order, so the schema can be inspected with real data.

## Inputs and context

- Depends on [TASK-032](../done/TASK-032-sqlalchemy-durable-store.md): `src/vaic/state/sql/
  schemas.sql`, `models.py`, `engine.py`.
- Connection: host/port/user/password supplied by the human owner directly in-session (explicit,
  scoped authorization for this specific action, per agent-guardrails.md's gated-actions rule).
  **Never written to any file, commit, task log, or session log in this repo** - only used
  transiently via environment variables at invocation time (agent-guardrails.md: secrets are never
  hardcoded, never reproduced even partially in a report).
- Target database name: `nxcare` (new, not the existing database at that instance - avoids
  colliding with whatever else runs on that shared instance).
- Seed data is synthetic and deterministic (a fixed RNG seed), per data-model.md - no real personal
  data, ever.

## To do

- [ ] Write `src/vaic/state/sql/seed.py`: a deterministic (seeded RNG) generator producing 10-50
      rows per table, inserted in FK dependency order, entirely through SQLAlchemy (no raw
      hand-built INSERT strings).
- [ ] Create the `nxcare` database on the target instance (`CREATE DATABASE`, run against the
      server's maintenance connection since it cannot run inside a transaction).
- [ ] Run `create_schema()` (TASK-032) against `nxcare`.
- [ ] Run the seed script against `nxcare` and verify row counts land in the 10-50 range per table.
- [ ] Record the row counts achieved (not the credentials) in this file's session log.

## Acceptance criteria

- [ ] The `nxcare` database exists on the target instance with all 15 tables from `schemas.sql`.
- [ ] Every table holds between 10 and 50 rows, verified by a `SELECT count(*)` per table.
- [ ] No credential value appears anywhere in this repository (grepped before commit).

## Decisions and blockers

- The human owner explicitly authorized connecting to this specific external-looking host after
  being warned about the risk of colliding with another project's database (the instance's default
  database name suggested a different, unrelated service); they confirmed it is a local/dev
  instance and asked for a NEW database (`nxcare`) rather than reusing the existing one, which
  avoids that collision risk entirely.
- Credentials were pasted in the chat transcript by the human. Per this repo's rules that only
  binds agent BEHAVIOR (never write secrets to files/commits/logs) - it does not retroactively
  scrub the chat transcript, which is outside this repo's control. Recommended the human rotate the
  password if this instance is anything other than a fully disposable local sandbox.

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | tuan.nguyen15 | Claimed task, branched `feat/TASK-033-nxcare-seed` off `feat/TASK-032-sqlalchemy-durable-store` (depends on its schema) | Active |

## Result

<Filled when the task moves to Done.>
