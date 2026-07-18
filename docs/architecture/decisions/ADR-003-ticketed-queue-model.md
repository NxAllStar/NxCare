---
title: "ADR-003: Ticketed multi-queue model - QueueTicket, department-scoped shared queues (OI-22)"
status: Proposed
date: 2026-07-18
deciders: []
tags: [adr, data-model, queue, ticketing, careplan]
---

<!-- ADRs are written 100% in English (see .claude/rules/docs-workflow.md). -->

# ADR-003: Ticketed multi-queue model - QueueTicket and department-scoped shared queues

An ADR is immutable once its status is `Accepted`, and the immutability is hook-enforced. A change
of mind means a NEW ADR that supersedes this one; this one keeps its text and is marked
`Superseded by ADR-MMM`. Land every edit BEFORE the flip to `Accepted`.

## Context

The real patient journey is a hub-and-spoke round trip, not a single appointment:

```
[Q] general doctor  ->  care plan  ->  [Q] exam 1
   (first consult)      (Tasks)        [Q] exam 2 ... -> all results DONE
        ^                                                      |
        +---------------- [Q] final read-out <-----------------+
             (a SECOND consult with the same general doctor)
```

At every `[Q]` the patient takes a **numbered ticket**, each desk **announces the current number on a
screen**, and a patient without a phone can still register at a desk and hold a paper ticket. Ticket
IDs are department-scoped and human-readable, e.g. `DepB-00001` ("Department B, number 1"). Emergency
patients must be served ahead of routine ones.

What the current data model (`docs/specs/08-data-model.md`, `src/vaic/models/entities.py`) can and
cannot express:

- **Exams already queue.** A `CarePlan` holds `Task`s, each owned by a `Resource`; `owner_queue`
  (`src/vaic/state/repository.py:42`) computes a per-owner queue. So the "wait in line for each exam"
  legs exist in spirit.
- **Consults do not queue.** `Appointment` has no `owner_id` and no ordering key, so neither the
  first general-doctor queue nor the queue for any exam desk can be attached to it. There is also no
  way to model the **return consult** for the final read-out: `Appointment`'s state machine is
  terminal at `DONE`.
- **No ticket identity.** Nothing stores a `ticket_number`/label. A wall-announced number is a
  durable, human-readable token, not a computed position.
- **No priority pre-emption.** `owner_queue` orders strictly by `sequence_index` and ignores
  `Patient.priority_level`; an EMERGENCY patient does not currently cut any line.
- **No department identity.** `Resource.department_id` is a bare UUID with no code/label, so there is
  nothing to render "DepB" from.

Already fixed by an earlier decision and therefore **not up for debate here**: how the position and
ETA are *displayed* to the patient. **ADR-002** (Proposed) sets the confidence-gated display ladder
(ordinal position always; ETA band only when high-confidence and no active disruption). This ADR
decides the queue *structure* the position is computed from; ADR-002's presentation policy sits
unchanged on top of it, with one refinement noted under Consequences.

The forecast/notification grounding is fixed elsewhere and reused as-is: FR-07 ETA contract
(`{value, confidence, provenance, source}`), FR-06 event-driven Journey notifications, FR-17
patient-code scan flipping `Task` `PENDING -> IN_PROGRESS`.

## Decision

Introduce a first-class **`QueueTicket`** entity and a small **`Department`** entity, model every wait
as a ticket in a **department-scoped shared queue**, and treat the patient's journey status as
**derived, never stored**.

1. **`QueueTicket` (polymorphic, mirrors the existing `Payment.subject_type`/`subject_id` pattern):**

   | Field | Notes |
   |-------|-------|
   | `id` | PK |
   | `patient_id` | set at desk registration; denormalized for Own-scope (TASK-016). Phone stays optional, so a no-phone walk-in is a normal `Patient` row |
   | `department_id` | FK -> `Department`; **the queue scope and number series** |
   | `capability` | optional service-capability key; when a department's rooms are not interchangeable, it splits the queue (skill-based routing). Null = one queue for the whole department |
   | `priority_band` | `ROUTINE` / `URGENT` / `EMERGENCY`, copied from `Patient.priority_level` at issue; **drives both the number series and the sort** |
   | `subject_type` | `CONSULT` / `SERVICE` |
   | `subject_id` | FK -> `Appointment` (consult) or `Task` (exam) |
   | `ticket_seq` | monotonic int within `(department, priority_band, day)` |
   | `ticket_label` | rendered token: `DepB-00001` (routine), `DepB-E-00001` (emergency) |
   | `status` | `WAITING` / `CALLED` / `IN_SERVICE` / `DONE` / `SKIPPED` |
   | `called_by_owner_id` | FK -> `Resource`; **null until called** - the room that pulled the ticket |
   | `issued_at` / `called_at` | `issued_at` is the FIFO tiebreaker within a band |

2. **Shared queue, pooled rooms.** A department's multiple interchangeable rooms draw from **one**
   queue (M/M/c, not c x M/M/1): lower average wait, FIFO fairness, no idle room while anyone waits.
   This is why `DepB-00001` is one series per department rather than per room. Heterogeneous rooms are
   handled by `capability`, not by separate per-room series.

3. **Owner bound at call time.** The specific room is unknown at issue; it is set in
   `called_by_owner_id` when a free room calls the next ticket. Consequently, for `SERVICE` tickets
   **`Task.owner_id` moves from plan-time assignment to call-time binding** - the one substantive
   change to the care-plan allocation flow (`src/vaic/agents/careplan/slots.py`).

4. **Ordering is field-driven, never label-driven.** The serving order within a `(department,
   capability)` queue is `(priority_band DESC, issued_at ASC)`. The band is *rendered into* the label
   (`-E-`) for humans and screens, but the sort reads the field. A late-arriving EMERGENCY still
   precedes an earlier ROUTINE; number != serving order.

5. **Number allocation via Redis, persisted to Postgres.** `INCR queue:{dept}:{band}:{yyyymmdd}`
   yields `ticket_seq` in the real-time store; the issued `QueueTicket` row is persisted to Postgres
   for durability and audit - consistent with the existing "Redis for real-time, Postgres durable"
   split (spec 08 persistence notes, OI-15).

6. **Round trip is explicit.** The journey is a sequence of tickets under one `patient_code`: a
   `CONSULT` ticket -> N `SERVICE` tickets -> a second `CONSULT` ticket for the final read-out. The
   final read-out is a distinct `Appointment` (a return consult), not a reopened terminal one.

7. **Patient journey status is derived, not stored.** There is **no** status enum on `Patient`. The
   patient's current state is computed from their active tickets, so it can never drift from the
   ticket state machines (the drift a stored column would invite whenever a `ScanEvent` flips a task
   but a second write is missed). The summary is precedence-ordered so that a patient who is in
   several states at once (e.g. awaiting a blood result while queued for X-ray) resolves
   deterministically:

   ```
   IN_SERVICE       (any ticket IN_SERVICE)                      -- highest
   > CALLED         (any ticket CALLED, en route to the room)
   > WAITING        (any ticket WAITING)                          -- "in line"
   > RESULTS_PENDING (a DONE exam still within turnaround_minutes)
   > IDLE           (registered, nothing active)                  -- "free"
   > DONE           (visit complete / discharged)                 -- lowest
   ```

   When the coordinator dashboard (FR-12) needs this at scale, it is materialised as a **derived,
   cache-only** read-model in Redis, rebuilt from the Journey Agent's events (BR-03) and invalidated
   on every ticket transition - never an authoritative field. A supporting invariant belongs on the
   tickets, not on the patient: **at most one `QueueTicket` per patient may be `CALLED` or
   `IN_SERVICE` at a time** (you cannot be served in two rooms at once).

## Options considered

| Option | Pros | Cons |
|--------|------|------|
| **A (chosen): `QueueTicket` + `Department`, department-scoped shared queue, owner-at-call, derived status** | One ordering rule and one number policy for consults and exams; models the round trip directly; mirrors the existing `Payment` polymorphic pattern; matches the `DepB-00001` numbering; pooled rooms minimise wait; status cannot drift | New entity plus repository/constraint-checker awareness; requires the plan-time -> call-time owner shift in `careplan/slots.py` |
| **B: queue columns on `Appointment` and `Task` (no shared entity)** | Smallest diff; ships fastest for a demo showing only the first consult | Duplicates ordering/priority logic across two entities; the return consult still needs a second `Appointment`; two queue mechanisms to keep in sync; no single place to enforce pre-emption |
| **C: separate queue per room (per-room numbering)** | Trivially "a queue is a room" | Higher average wait and broken FIFO fairness ("wrong line" overtaking); idle rooms under uneven load; contradicts the chosen department-level `DepB-00001` IDs |
| **D: keep owner pre-assigned at plan time** | No change to `careplan/slots.py` | Defeats pooling - a ticket bound to a specific room cannot be served by whichever room is free; forces per-room queues (collapses into C) |
| **E: store a journey-status enum on `Patient`** | One cheap indexed read for the dashboard; simple mental model | A second source of truth that drifts from the ticket state machines; lossy when the patient is in several states at once; overlaps three existing status fields |

## Consequences

- **Positive:**
  - One queue abstraction serves both consult and exam legs, with a single priority-aware ordering
    rule, so EMERGENCY pre-emption is enforced in exactly one place instead of not at all.
  - The wall-announced number, the no-phone paper token, and the app's live position are the same
    stored `ticket_label` viewed three ways; the separate emergency series keeps the no-phone
    "my number minus now-serving" arithmetic valid even when emergencies pre-empt.
  - Journey status is always consistent because it is computed from the tickets, and it still keeps
    the full richness (results-pending, called, etc.) that a single stored enum would flatten.
  - Reuses existing patterns and infrastructure: `Payment`-style polymorphism, Redis counters,
    FR-17 scan-to-start, FR-06/FR-07 notification and ETA contracts. ADR-002's display ladder is
    unaffected in intent.
  - Pooled department queues reduce average wait versus per-room lines, at no modelling cost.

- **Negative and trade-offs:**
  - **The central cost:** `Task.owner_id` shifts from plan-time to call-time for `SERVICE` tickets.
    `careplan/slots.py` (`allocate_task_slot`, capacity/clash checks) and any consumer that assumes a
    task's owner is fixed at planning must change. This is a real behavioural change to FR-08, not an
    additive column.
  - A new entity widens the model from 15 to 17 entities (`QueueTicket`, `Department`) and adds a
    join the repository and constraint checker must learn.
  - `Slot` (plan-time time slots) and `QueueTicket` (live queue position) now coexist; their
    relationship for exams must be defined so they do not drift (a planned slot vs an actual call).
  - Deriving journey status costs a per-patient read across their tickets; the dashboard at scale
    needs the Redis read-model (cache invalidation to monitor), which is real operational surface.
  - `capability`-based sub-queues are specified but not required for the blood-test case; leaving the
    field unused until needed risks an untested path.

- **Follow-up work:**
  - Update `docs/specs/08-data-model.md` in the same PR as the entity change: add `QueueTicket` and
    `Department`, add `Appointment.owner_id`, reinterpret `Appointment.slot_start` as a *recommended
    arrival window* (not a reservation), and extend the `Appointment` state machine for the return
    read-out consult. Log it in `docs/specs/13-revision-history.md`.
  - Entity + ORM + Alembic migration (`data-modeler` + `agent-core-dev`): `QueueTicket`/`Department`
    tables, `Appointment.owner_id`, generated with `alembic revision --autogenerate` on the baseline
    set up in this branch and hand-checked.
  - Refactor `owner_queue` to order by `(priority_band, issued_at)` and to read the `QueueTicket`
    queue; refactor `careplan/slots.py` for call-time owner binding (`careplan-dev`).
  - Add the derived-status query (`patient_journey_status`) and the "at most one active ticket"
    invariant to the constraint checker (`agent-core-dev`); wire the Redis read-model into FR-12.
  - Refine **ADR-002**: its ordinal position is computed from the `QueueTicket` queue, not raw
    `Task.sequence_index`. Because ADR-002 is still `Proposed`, land that one-line data-path note
    before either ADR flips to `Accepted`.
  - Candidate FR (for `ba-analyst`): "Patient takes a department-scoped numbered ticket at each
    queue; desks announce and call by priority-aware order (OI-22)," referencing FR-02, FR-08, FR-17,
    and ADR-002/ADR-003.

## References

- [ADR-002: Queue position and confidence-gated ETA display (OI-22)](ADR-002-queue-position-transparency.md) - the complementary display-policy decision this ADR sits under.
- [ADR-001: Agent framework](ADR-001-agent-framework.md)
- [08 Data model](../../../specs/08-data-model.md) - entities, `Payment` polymorphic pattern, persistence notes (OI-15).
- `src/vaic/models/entities.py`, `src/vaic/state/sql/models.py` - current entity + ORM shape.
- `src/vaic/state/repository.py` - `owner_queue`, to become priority-aware.
- `src/vaic/agents/careplan/slots.py` - FR-08 allocation, to become call-time owner binding.
- [FR-02: Intake slot recommendation](../../../specs/05-functional-requirements.md#fr-02)
- [FR-08: Slot allocation](../../../specs/05-functional-requirements.md#fr-08)
- [FR-12: Coordinator dashboard](../../../specs/05-functional-requirements.md#fr-12)
- [FR-17: Patient-code scan](../../../specs/05-functional-requirements.md#fr-17)
- [OI-22: Queue position / ticket transparency](../../../specs/11-assumptions-constraints.md#oi-22)
