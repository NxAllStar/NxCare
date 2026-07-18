---
paths:
  - "src/vaic/state/**"
  - "src/vaic/models/**"
---

# Data model

Applies to schema, migrations, and model definitions. ORM: none (Redis key-value + Pydantic models; durable store TBD - see docs/specs OI-15).

## The schema follows the documented model

`docs/specs/08-data-model.md` holds the ERD and the data dictionary; the schema implements it. A
schema change that the dictionary does not describe is a schema change nobody agreed to. If the
model needs to change, change the document in the same pull request.

## Conventions

- Naming is consistent across every entity and follows the Pydantic/Python idiom rather than a
  per-model preference. Pick it once; do not relitigate per model. There is no ORM (Redis key-value
  + Pydantic models; a durable store is not yet chosen - spec OI-15), so keep persistence behind the
  `src/vaic/state` interface so the store can be swapped without touching domain code.
- Enumerated values are declared enums, not free-text strings with a comment. A status column that
  accepts any string will eventually hold every string.
- Every foreign key has an explicit referential action; the default is rarely what was intended.
- Index against the actual query shape - the real WHERE, ORDER BY, and JOIN columns - not against
  every column and not against a guess (performance.md).
- Money is never a float. Dates are stored with an explicit timezone or as UTC, decided once.
- Nullability is a decision, not an oversight: a nullable column is a state the code must handle.

## Migrations

- Every schema change ships as a migration. Never hand-edit a database to match the code, and never
  edit a migration that has already run anywhere but a throwaway local database.
- Forward-only. A mistake is fixed by a new migration, not by rewriting history.
- One pull request carries all three: the migration, the data-dictionary update, and the seed
  update. A migration that lands without its seed leaves every teammate with a broken local
  database.
- Destructive migrations (dropping a column or table, narrowing a type, deleting rows) are gated:
  they need an explicit request, a backup, and an expand-then-contract plan - add the new shape,
  migrate the data, cut over, and only then remove the old shape in a later change.
- A database reset is never run against anything but a local or ephemeral test database, and never
  without being asked (agent-guardrails.md).

## Seeds

- Seed data is synthetic, deterministic, and idempotent: running the seed twice leaves the same
  state, and it never depends on random values that make a failure unreproducible.
- Seeds target local and development databases only. There is no seed path that can reach
  production.
- No real personal data in a seed, ever. Not a scrubbed export, not a "just the names" subset.

## This project's entities

The source of truth is `docs/specs/08-data-model.md` (ERD, data dictionary, state machines). Do not
duplicate it here; implement it there and change the document in the same PR as any model change.

Core entities: `Patient` (with `patient_code`, `priority_level`), `IntakeSession` (with
`emergency_suspected`), `Appointment`, `Diagnosis`, `ServiceOrder`, `ServiceType`, `CarePlan`,
`Task`, `Slot`, `Payment` (a proceed-gate flag, not money - AS-02), `Resource`, `DisruptionEvent`,
`Notification`, `AuditLogEntry`, `ScanEvent`.

Model-specific invariants that are also guardrails (enforce at the write boundary, not in a prompt):

- Only a doctor path creates a `ServiceOrder`; no agent adds/drops/changes a service (CO-02, BR-05).
- `Task.execution_status` and `Appointment.status`, `CarePlan.status`, `DisruptionEvent.status` move
  only along the state machines in spec 08. Enum values are English `UPPER_SNAKE_CASE`.
- A `Task` with `payment_status = UNPAID` is `LOCKED`: excluded from every queue and every load/ETA
  calculation until an authorised source flips the flag (BR-10, BR-11).
- `AuditLogEntry` is append-only; no actor edits a recorded decision (BR-23).
- A `ScanEvent` cannot update a `LOCKED` task and only the task owner may create it (BR-26, BR-27).

## Redis and durability note

This build uses Redis for state and events; there are no relational migrations. The generic
migration discipline above applies the day a durable store is chosen (spec OI-15) - treat that choice
as an expand-then-contract migration, decided via `/new-adr`.
