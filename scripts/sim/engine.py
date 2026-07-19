"""Real-time clinic activity simulator for the VAIC PostgreSQL store.

This is a *demo data generator*, not application code. It keeps the live database looking like a
working clinic by driving the real care-pathway state machines (see
`src/vaic/models/transitions.py`) forward on every tick:

    patient arrives -> appointment (BOOKED)
        -> CONSULT queue ticket (WAITING -> CALLED -> IN_SERVICE -> DONE)
        -> diagnosis + care plan + service orders + tasks
        -> one SERVICE queue ticket per task, issued in sequence as the previous task finishes
        -> tasks run to DONE -> care plan COMPLETED -> patient leaves

Balance (why it does not explode)
---------------------------------
The clinic is modelled as an M/M/c queue per department:

* Each department has a fixed number of *servers* (concurrent CALLED/IN_SERVICE tickets). Throughput
  is therefore bounded no matter how many patients are waiting.
* Each in-service ticket finishes only after its (time-compressed) service duration has elapsed, so
  work drains at a realistic, staggered pace instead of all at once.
* Arrivals are admission-controlled: new patients are only created while the number of patients
  currently in the system (WIP) is below `SIM_WIP_CAP`, and the mean arrival rate is kept below the
  total service capacity. In-rate therefore tracks out-rate and the queues stay bounded.

Everything it writes is synthetic (see the name banks below). It only ever INSERTs new rows and
UPDATEs the status of rows it created; it never deletes or truncates anything.

Usage (normally via ``simulate.sh``)::

    python engine.py bootstrap   # create the fake departments (idempotent)
    python engine.py tick        # advance the world by one step (for cron)
    python engine.py loop        # advance continuously (real-time feel)
    python engine.py status      # print live queue metrics and the balance budget

Connection comes from POSTGRES_HOST/PORT/NAME/USER/PASSWORD (same vars as the app), or DATABASE_DSN.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import random
import sys
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime

import asyncpg

# --------------------------------------------------------------------------------------------------
# Configuration - every knob is an env var with a default. simulate.sh surfaces the common ones.
# --------------------------------------------------------------------------------------------------


def _f(name: str, default: float) -> float:
    return float(os.environ.get(name, default))


def _i(name: str, default: int) -> int:
    return int(os.environ.get(name, default))


# Fixed namespace so bootstrap is idempotent: department UUIDs are derived from their code.
_DEPT_NS = uuid.UUID("11111111-2222-3333-4444-555555555555")

# Departments (each is one queue with its own server pool). capacity = concurrent CALLED/IN_SERVICE.
DEPARTMENTS: list[dict] = [
    {"code": "CONS", "label": "General Consultation", "capacity": _i("SIM_CAP_CONS", 3)},
    {"code": "LAB", "label": "Laboratory", "capacity": _i("SIM_CAP_LAB", 2)},
    {"code": "IMG", "label": "Diagnostic Imaging", "capacity": _i("SIM_CAP_IMG", 2)},
    {"code": "CARD", "label": "Cardiology", "capacity": _i("SIM_CAP_CARD", 1)},
]

# service_type code prefix -> department code that runs it.
_SERVICE_ROUTING = {
    "BLOOD_TEST": "LAB",
    "URINE_TEST": "LAB",
    "X_RAY": "IMG",
    "MRI": "IMG",
    "ULTRASOUND": "IMG",
    "ECG": "CARD",
}

# Timing. A D-minute service completes D * SIM_SEC_PER_MIN real seconds after it enters service.
SEC_PER_MIN = _f("SIM_SEC_PER_MIN", 3.0)
CALL_DELAY_SEC = _f("SIM_CALL_DELAY_SEC", 6.0)  # CALLED -> IN_SERVICE settle (patient walks in)
CONSULT_MINUTES = _i("SIM_CONSULT_MINUTES", 15)  # matches AVERAGE_CONSULT_MINUTES in the app

# Admission control / arrivals.
ARRIVALS_PER_TICK = _f("SIM_ARRIVALS_PER_TICK", 0.25)  # expected new patients per tick (Poisson)
WIP_CAP = _i("SIM_WIP_CAP", 40)  # hard ceiling on patients-in-system
MIN_ORDERS = _i("SIM_MIN_ORDERS", 1)  # service orders (tasks) per patient, inclusive range
MAX_ORDERS = _i("SIM_MAX_ORDERS", 4)
NO_SHOW_PROB = _f("SIM_NO_SHOW_PROB", 0.05)  # chance a called consult patient is a no-show

LOOP_INTERVAL_SEC = _f("SIM_INTERVAL_SEC", 15.0)

_PRIORITY_WEIGHTS = [("ROUTINE", 0.80), ("URGENT", 0.15), ("EMERGENCY", 0.05)]
_PRIORITY_RANK = {"EMERGENCY": 0, "URGENT": 1, "ROUTINE": 2}
_PRIORITY_INFIX = {"EMERGENCY": "E-", "URGENT": "U-", "ROUTINE": ""}

_SPECIALTIES = ["cardiology", "dermatology", "pediatrics", "general_medicine", "orthopedics"]

# Synthetic Vietnamese-style names, matching the personas already seeded (e.g. "Bui Quang Hung").
_SURNAMES = ["Nguyen", "Tran", "Le", "Pham", "Hoang", "Bui", "Do", "Ho", "Ngo", "Vu", "Dang"]
_MIDDLES = ["Quang", "Minh", "Ngoc", "Huu", "Thi", "Van", "Trong", "Duc", "Thanh", "Gia"]
_GIVENS = ["Hung", "Yen", "Tuan", "Quan", "Khanh", "Anh", "Linh", "Nam", "Ha", "Dung", "Mai"]


def _random_name() -> str:
    return f"{random.choice(_SURNAMES)} {random.choice(_MIDDLES)} {random.choice(_GIVENS)}"


def _poisson(mean: float) -> int:
    """Knuth's small-mean Poisson sampler - number of arrivals in one tick."""
    if mean <= 0:
        return 0
    import math

    limit = math.exp(-mean)
    k, prod = 0, 1.0
    while True:
        k += 1
        prod *= random.random()
        if prod <= limit:
            return k - 1


def _dept_id(code: str) -> uuid.UUID:
    return uuid.uuid5(_DEPT_NS, code)


def _route_department(service_code: str) -> str:
    prefix = service_code.rsplit("_", 1)[0]  # "BLOOD_TEST_004" -> "BLOOD_TEST"
    return _SERVICE_ROUTING.get(prefix, "LAB")


# --------------------------------------------------------------------------------------------------
# In-memory reference caches, loaded once per process.
# --------------------------------------------------------------------------------------------------


@dataclass
class Reference:
    resources_by_type: dict[str, list[uuid.UUID]] = field(default_factory=dict)
    all_resources: list[uuid.UUID] = field(default_factory=list)
    service_types: list[dict] = field(default_factory=list)  # {id, code, default_duration_min}
    dept_capacity: dict[str, int] = field(default_factory=dict)

    def pick_resource(self, *types: str) -> uuid.UUID:
        pool: list[uuid.UUID] = []
        for t in types:
            pool.extend(self.resources_by_type.get(t, []))
        if not pool:
            pool = self.all_resources
        return random.choice(pool)

    def pick_service_for(self, dept_code: str) -> dict:
        matching = [s for s in self.service_types if _route_department(s["code"]) == dept_code]
        return random.choice(matching or self.service_types)


async def load_reference(conn: asyncpg.Connection) -> Reference:
    ref = Reference()
    for row in await conn.fetch("SELECT id, type FROM resources"):
        ref.resources_by_type.setdefault(row["type"], []).append(row["id"])
        ref.all_resources.append(row["id"])
    for row in await conn.fetch(
        "SELECT id, code, default_duration_min FROM service_types ORDER BY code"
    ):
        ref.service_types.append(dict(row))
    ref.dept_capacity = {d["code"]: d["capacity"] for d in DEPARTMENTS}
    return ref


# --------------------------------------------------------------------------------------------------
# Bootstrap - the fake departments the queue needs (the table ships empty).
# --------------------------------------------------------------------------------------------------


async def bootstrap(conn: asyncpg.Connection) -> None:
    for d in DEPARTMENTS:
        await conn.execute(
            """
            INSERT INTO departments (id, code, display_label)
            VALUES ($1, $2, $3)
            ON CONFLICT (code) DO UPDATE SET display_label = EXCLUDED.display_label
            """,
            _dept_id(d["code"]),
            d["code"],
            d["label"],
        )
    codes = ", ".join(f"{d['code']}(x{d['capacity']})" for d in DEPARTMENTS)
    print(f"bootstrap: {len(DEPARTMENTS)} departments ready -> {codes}")


# --------------------------------------------------------------------------------------------------
# Small insert helpers.
# --------------------------------------------------------------------------------------------------


async def _next_patient_code(conn: asyncpg.Connection) -> str:
    row = await conn.fetchval(
        "SELECT patient_code FROM patients WHERE patient_code ~ '^NXC-[0-9]+$' "
        "ORDER BY (substring(patient_code from 5))::int DESC LIMIT 1"
    )
    n = (int(row[4:]) + 1) if row else 0
    return f"NXC-{n:05d}"


def _weighted_priority() -> str:
    r, cum = random.random(), 0.0
    for level, w in _PRIORITY_WEIGHTS:
        cum += w
        if r <= cum:
            return level
    return "ROUTINE"


async def _next_ticket_seq(
    conn: asyncpg.Connection, dept_id: uuid.UUID, priority: str, subject_type: str, day: datetime
) -> int:
    day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
    count = await conn.fetchval(
        """
        SELECT count(*) FROM queue_tickets
        WHERE department_id = $1 AND priority_band = $2 AND subject_type = $3
          AND issued_at >= $4 AND issued_at < $4 + interval '1 day'
        """,
        dept_id,
        priority,
        subject_type,
        day_start,
    )
    return int(count) + 1


async def _issue_ticket(
    conn: asyncpg.Connection,
    *,
    patient_id: uuid.UUID,
    dept_code: str,
    priority: str,
    subject_type: str,
    subject_id: uuid.UUID,
    now: datetime,
    capability: str | None = None,
) -> uuid.UUID:
    dept_id = _dept_id(dept_code)
    seq = await _next_ticket_seq(conn, dept_id, priority, subject_type, now)
    label = f"{dept_code}-{_PRIORITY_INFIX[priority]}{seq:05d}"
    ticket_id = uuid.uuid4()
    await conn.execute(
        """
        INSERT INTO queue_tickets
            (id, patient_id, department_id, capability, priority_band, subject_type, subject_id,
             ticket_seq, ticket_label, status, issued_at)
        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,'WAITING',$10)
        """,
        ticket_id,
        patient_id,
        dept_id,
        capability,
        priority,
        subject_type,
        subject_id,
        seq,
        label,
        now,
    )
    return ticket_id


async def _notify(conn, patient_id, body, reason, now, channel="IN_APP") -> None:
    await conn.execute(
        "INSERT INTO notifications (id, patient_id, channel, body, reason, created_at) "
        "VALUES ($1,$2,$3,$4,$5,$6)",
        uuid.uuid4(),
        patient_id,
        channel,
        body,
        reason,
        now,
    )


async def _audit(conn, actor, action, target_id, patient_id, reasoning, now) -> None:
    await conn.execute(
        "INSERT INTO audit_log_entries (id, actor, action, target_id, patient_id, reasoning, "
        "created_at) VALUES ($1,$2,$3,$4,$5,$6,$7)",
        uuid.uuid4(),
        actor,
        action,
        target_id,
        patient_id,
        reasoning,
        now,
    )


# --------------------------------------------------------------------------------------------------
# Arrivals.
# --------------------------------------------------------------------------------------------------


async def _current_wip(conn: asyncpg.Connection) -> int:
    """Distinct patients still in the system: an open ticket or an unfinished task."""
    return int(
        await conn.fetchval(
            """
            SELECT count(*) FROM (
                SELECT patient_id FROM queue_tickets
                    WHERE status IN ('WAITING','CALLED','IN_SERVICE')
                UNION
                SELECT cp.patient_id FROM tasks t JOIN care_plans cp ON cp.id = t.care_plan_id
                    WHERE t.execution_status IN ('LOCKED','PENDING','IN_PROGRESS')
            ) q
            """
        )
    )


async def admit_arrivals(conn: asyncpg.Connection, ref: Reference, now: datetime) -> int:
    wip = await _current_wip(conn)
    if wip >= WIP_CAP:
        return 0
    headroom = WIP_CAP - wip
    n = min(_poisson(ARRIVALS_PER_TICK), headroom)
    for _ in range(n):
        await _admit_one(conn, ref, now)
    return n


async def _admit_one(conn: asyncpg.Connection, ref: Reference, now: datetime) -> None:
    patient_id = uuid.uuid4()
    code = await _next_patient_code(conn)
    priority = _weighted_priority()
    await conn.execute(
        "INSERT INTO patients (id, full_name, phone, patient_code, priority_level, created_at) "
        "VALUES ($1,$2,$3,$4,$5,$6)",
        patient_id,
        _random_name(),
        f"+8490{random.randint(1000000, 9999999)}",
        code,
        priority,
        now,
    )
    appt_id = uuid.uuid4()
    await conn.execute(
        """
        INSERT INTO appointments
            (id, patient_id, specialty, status, payment_status, owner_id, slot_start, created_at)
        VALUES ($1,$2,$3,'BOOKED','PAID',$4,$5,$6)
        """,
        appt_id,
        patient_id,
        random.choice(_SPECIALTIES),
        ref.pick_resource("DOCTOR"),
        now,
        now,
    )
    await _issue_ticket(
        conn,
        patient_id=patient_id,
        dept_code="CONS",
        priority=priority,
        subject_type="CONSULT",
        subject_id=appt_id,
        now=now,
    )
    await _notify(conn, patient_id, f"Welcome {code}. Please wait for your consult number.",
                  "arrival", now)
    await _audit(conn, "sim/front-desk", "patient.arrived", appt_id, patient_id,
                 f"walk-in, priority {priority}", now)


# --------------------------------------------------------------------------------------------------
# Ticket advancement - the M/M/c server loop, run per department.
# --------------------------------------------------------------------------------------------------


@dataclass
class TickStats:
    arrivals: int = 0
    consults_done: int = 0
    services_done: int = 0
    tasks_issued: int = 0
    called: int = 0
    plans_completed: int = 0
    no_shows: int = 0


async def _service_seconds(conn, ticket) -> float:
    """How long this ticket occupies a server, in real seconds (time-compressed)."""
    if ticket["subject_type"] == "CONSULT":
        minutes = CONSULT_MINUTES
    else:
        minutes = await conn.fetchval(
            "SELECT estimated_duration_min FROM tasks WHERE id = $1", ticket["subject_id"]
        )
        minutes = minutes or CONSULT_MINUTES
    return max(float(minutes), 1.0) * SEC_PER_MIN


async def advance_department(
    conn: asyncpg.Connection, ref: Reference, dept_code: str, now: datetime, stats: TickStats
) -> None:
    dept_id = _dept_id(dept_code)
    capacity = ref.dept_capacity[dept_code]
    tickets = await conn.fetch(
        """
        SELECT id, patient_id, subject_type, subject_id, status, called_at, priority_band
        FROM queue_tickets
        WHERE department_id = $1 AND status IN ('WAITING','CALLED','IN_SERVICE')
        FOR UPDATE
        """,
        dept_id,
    )

    # 1) Complete in-service tickets whose service time has elapsed; settle CALLED -> IN_SERVICE.
    for t in tickets:
        if t["status"] not in ("CALLED", "IN_SERVICE") or t["called_at"] is None:
            continue
        elapsed = (now - t["called_at"]).total_seconds()
        if t["status"] == "IN_SERVICE" and elapsed >= await _service_seconds(conn, t):
            await _complete_ticket(conn, ref, t, now, stats)
        elif t["status"] == "CALLED" and elapsed >= CALL_DELAY_SEC:
            await conn.execute(
                "UPDATE queue_tickets SET status='IN_SERVICE' WHERE id=$1", t["id"]
            )
            if t["subject_type"] == "CONSULT":
                await _sync_appointment(conn, t["subject_id"], "IN_CONSULT")
            else:
                await _set_task_status(conn, t["subject_id"], "IN_PROGRESS")

    # 2) Fill any free servers from the waiting line, in ADR-003 serving order.
    busy = int(
        await conn.fetchval(
            "SELECT count(*) FROM queue_tickets WHERE department_id=$1 "
            "AND status IN ('CALLED','IN_SERVICE')",
            dept_id,
        )
    )
    if busy >= capacity:
        return
    waiting = await conn.fetch(
        """
        SELECT id, patient_id, subject_type, subject_id, priority_band
        FROM queue_tickets
        WHERE department_id = $1 AND status = 'WAITING'
        ORDER BY CASE priority_band WHEN 'EMERGENCY' THEN 0 WHEN 'URGENT' THEN 1 ELSE 2 END,
                 issued_at ASC
        LIMIT $2
        """,
        dept_id,
        capacity - busy,
    )
    for t in waiting:
        # A called consult patient may be a no-show; services always show (already on-site).
        if t["subject_type"] == "CONSULT" and random.random() < NO_SHOW_PROB:
            await conn.execute("UPDATE queue_tickets SET status='SKIPPED' WHERE id=$1", t["id"])
            await _sync_appointment(conn, t["subject_id"], "NO_SHOW")
            await _audit(conn, "sim/consult-desk", "patient.no_show", t["id"], t["patient_id"],
                         "called but did not present", now)
            stats.no_shows += 1
            continue
        owner = ref.pick_resource("DOCTOR" if t["subject_type"] == "CONSULT" else "ROOM",
                                  "TECHNICIAN", "EQUIPMENT")
        await conn.execute(
            "UPDATE queue_tickets SET status='CALLED', called_by_owner_id=$2, called_at=$3 "
            "WHERE id=$1",
            t["id"],
            owner,
            now,
        )
        if t["subject_type"] == "CONSULT":
            await _sync_appointment(conn, t["subject_id"], "CHECKED_IN")
        else:
            await _record_scan(conn, ref, t, owner, now)
        await _notify(conn, t["patient_id"], "Your number has been called. Please proceed.",
                      "called", now, channel="SCREEN")
        stats.called += 1


async def _complete_ticket(conn, ref, ticket, now, stats: TickStats) -> None:
    await conn.execute("UPDATE queue_tickets SET status='DONE' WHERE id=$1", ticket["id"])
    if ticket["subject_type"] == "CONSULT":
        await _sync_appointment(conn, ticket["subject_id"], "DONE")
        await _spawn_care_pathway(conn, ref, ticket["patient_id"], ticket["subject_id"], now, stats)
        stats.consults_done += 1
    else:
        await _finish_task(conn, ref, ticket["subject_id"], ticket["patient_id"], now, stats)
        stats.services_done += 1


# --------------------------------------------------------------------------------------------------
# Appointment / task coupling.
# --------------------------------------------------------------------------------------------------

_APPT_ALLOWED = {
    "CHECKED_IN": {"BOOKED"},
    "IN_CONSULT": {"CHECKED_IN"},
    "DONE": {"IN_CONSULT"},
    "NO_SHOW": {"BOOKED"},
}


async def _sync_appointment(conn, appt_id, to_status) -> None:
    cur = await conn.fetchval("SELECT status FROM appointments WHERE id=$1", appt_id)
    if cur in _APPT_ALLOWED.get(to_status, set()):
        await conn.execute("UPDATE appointments SET status=$2 WHERE id=$1", appt_id, to_status)


_TASK_ALLOWED = {
    "PENDING": {"LOCKED"},
    "IN_PROGRESS": {"PENDING"},
    "DONE": {"IN_PROGRESS"},
}


async def _set_task_status(conn, task_id, to_status) -> None:
    cur = await conn.fetchval("SELECT execution_status FROM tasks WHERE id=$1", task_id)
    if cur in _TASK_ALLOWED.get(to_status, set()):
        await conn.execute("UPDATE tasks SET execution_status=$2 WHERE id=$1", task_id, to_status)


async def _record_scan(conn, ref, ticket, owner, now) -> None:
    if ticket["subject_type"] != "SERVICE":
        return
    await conn.execute(
        "INSERT INTO scan_events (id, patient_id, task_id, scanned_by, scanned_at) "
        "VALUES ($1,$2,$3,$4,$5)",
        uuid.uuid4(),
        ticket["patient_id"],
        ticket["subject_id"],
        owner,
        now,
    )


# --------------------------------------------------------------------------------------------------
# Care pathway: created when a consult finishes, then drained task by task.
# --------------------------------------------------------------------------------------------------


async def _spawn_care_pathway(conn, ref, patient_id, appt_id, now, stats: TickStats) -> None:
    priority = await conn.fetchval("SELECT priority_level FROM patients WHERE id=$1", patient_id)
    doctor = ref.pick_resource("DOCTOR")
    diagnosis_id = uuid.uuid4()
    await conn.execute(
        "INSERT INTO diagnoses (id, patient_id, appointment_id, conditions, diagnosed_by, "
        "created_at) VALUES ($1,$2,$3,'[]'::jsonb,$4,$5)",
        diagnosis_id,
        patient_id,
        appt_id,
        doctor,
        now,
    )
    care_plan_id = uuid.uuid4()
    await conn.execute(
        "INSERT INTO care_plans (id, patient_id, diagnosis_id, status, assigned_staff, created_at) "
        "VALUES ($1,$2,$3,'ACTIVE','[]'::jsonb,$4)",
        care_plan_id,
        patient_id,
        diagnosis_id,
        now,
    )

    n_orders = random.randint(MIN_ORDERS, MAX_ORDERS)
    first_task_id: uuid.UUID | None = None
    first_service_code: str | None = None
    prev_task_id: uuid.UUID | None = None
    for idx in range(n_orders):
        dept_code = random.choice(["LAB", "IMG", "CARD"])
        svc = ref.pick_service_for(dept_code)
        order_id = uuid.uuid4()
        await conn.execute(
            "INSERT INTO service_orders (id, patient_id, diagnosis_id, service_type_id, "
            "ordered_by, signed_at) VALUES ($1,$2,$3,$4,$5,$6)",
            order_id,
            patient_id,
            diagnosis_id,
            svc["id"],
            doctor,
            now,
        )
        task_id = uuid.uuid4()
        # First task is PENDING (ready to queue now); the rest are LOCKED behind their predecessor.
        status = "PENDING" if idx == 0 else "LOCKED"
        depends = f'["{prev_task_id}"]' if prev_task_id else "[]"
        await conn.execute(
            """
            INSERT INTO tasks (id, care_plan_id, service_order_id, owner_id, execution_status,
                payment_status, estimated_duration_min, sequence_index, depends_on, created_at)
            VALUES ($1,$2,$3,$4,$5,'PAID',$6,$7,$8::jsonb,$9)
            """,
            task_id,
            care_plan_id,
            order_id,
            ref.pick_resource("ROOM", "TECHNICIAN", "EQUIPMENT"),
            status,
            svc["default_duration_min"],
            idx,
            depends,
            now,
        )
        await conn.execute(
            "INSERT INTO payments (id, patient_id, subject_type, subject_id, amount, status) "
            "VALUES ($1,$2,'TASK',$3,$4,'PAID')",
            uuid.uuid4(),
            patient_id,
            task_id,
            round(random.uniform(20, 200), 2),
        )
        if idx == 0:
            first_task_id, first_service_code = task_id, svc["code"]
        prev_task_id = task_id

    # Only the first task joins a queue now; later tasks join as earlier ones finish.
    if first_task_id is not None:
        await _issue_service_ticket(conn, patient_id, first_task_id, first_service_code, priority,
                                    now)
        stats.tasks_issued += 1
    await _notify(conn, patient_id, f"Care plan ready: {n_orders} test(s) scheduled.", "care_plan",
                  now)
    await _audit(conn, "sim/care-plan-agent", "care_plan.created", care_plan_id, patient_id,
                 f"{n_orders} tasks sequenced", now)


async def _issue_service_ticket(conn, patient_id, task_id, service_code, priority, now) -> None:
    dept_code = _route_department(service_code)
    await _issue_ticket(
        conn,
        patient_id=patient_id,
        dept_code=dept_code,
        priority=priority,
        subject_type="SERVICE",
        subject_id=task_id,
        now=now,
        capability=service_code,
    )
    await conn.execute(
        "INSERT INTO slots (id, patient_id, task_id, owner_id, start) "
        "SELECT $1,$2,$3,owner_id,$4 FROM tasks WHERE id=$3",
        uuid.uuid4(),
        patient_id,
        task_id,
        now,
    )


async def _finish_task(conn, ref, task_id, patient_id, now, stats: TickStats) -> None:
    await _set_task_status(conn, task_id, "DONE")
    await conn.execute(
        "UPDATE slots SET \"end\"=$2 WHERE task_id=$1 AND \"end\" IS NULL", task_id, now
    )
    care_plan_id = await conn.fetchval("SELECT care_plan_id FROM tasks WHERE id=$1", task_id)

    # Unlock and queue the next task in this care plan, if any.
    nxt = await conn.fetchrow(
        """
        SELECT t.id, cp.patient_id AS patient_id, st.code AS service_code, p.priority_level
        FROM tasks t
        JOIN care_plans cp ON cp.id = t.care_plan_id
        JOIN patients p ON p.id = cp.patient_id
        JOIN service_orders so ON so.id = t.service_order_id
        JOIN service_types st ON st.id = so.service_type_id
        WHERE t.care_plan_id = $1 AND t.execution_status = 'LOCKED'
        ORDER BY t.sequence_index ASC
        LIMIT 1
        """,
        care_plan_id,
    )
    if nxt is not None:
        await _set_task_status(conn, nxt["id"], "PENDING")
        await _issue_service_ticket(conn, nxt["patient_id"], nxt["id"], nxt["service_code"],
                                    nxt["priority_level"], now)
        stats.tasks_issued += 1
        return

    # No task left locked: if all tasks are DONE, the care plan is complete.
    remaining = await conn.fetchval(
        "SELECT count(*) FROM tasks WHERE care_plan_id=$1 AND execution_status <> 'DONE'",
        care_plan_id,
    )
    if remaining == 0:
        cur = await conn.fetchval("SELECT status FROM care_plans WHERE id=$1", care_plan_id)
        if cur == "ACTIVE":
            await conn.execute("UPDATE care_plans SET status='COMPLETED' WHERE id=$1", care_plan_id)
            await _notify(conn, patient_id, "All tests complete. Thank you.", "completed", now)
            await _audit(conn, "sim/journey-agent", "care_plan.completed", care_plan_id,
                         patient_id, "all tasks done", now)
            stats.plans_completed += 1


# --------------------------------------------------------------------------------------------------
# Tick / loop / status.
# --------------------------------------------------------------------------------------------------


async def run_tick(conn: asyncpg.Connection, ref: Reference) -> TickStats:
    now = datetime.now(UTC)
    stats = TickStats()
    async with conn.transaction():
        # Drain existing work first (frees servers), then admit new arrivals.
        for dept in DEPARTMENTS:
            await advance_department(conn, ref, dept["code"], now, stats)
        stats.arrivals = await admit_arrivals(conn, ref, now)
    return stats


async def print_status(conn: asyncpg.Connection, ref: Reference) -> None:
    now = datetime.now(UTC)
    wip = await _current_wip(conn)
    print(f"=== VAIC clinic simulator - {now.isoformat(timespec='seconds')} ===")
    print(f"patients in system (WIP): {wip} / cap {WIP_CAP}")
    rows = await conn.fetch(
        """
        SELECT d.code,
               count(*) FILTER (WHERE q.status='WAITING')    AS waiting,
               count(*) FILTER (WHERE q.status='CALLED')     AS called,
               count(*) FILTER (WHERE q.status='IN_SERVICE') AS in_service
        FROM departments d
        LEFT JOIN queue_tickets q
          ON q.department_id = d.id AND q.status IN ('WAITING','CALLED','IN_SERVICE')
        GROUP BY d.code ORDER BY d.code
        """
    )
    print(f"{'dept':6} {'cap':>4} {'waiting':>8} {'called':>7} {'in_service':>11}")
    for r in rows:
        cap = ref.dept_capacity.get(r["code"], 0)
        print(f"{r['code']:6} {cap:>4} {r['waiting']:>8} {r['called']:>7} {r['in_service']:>11}")

    # Balance budget: sustainable arrival rate vs configured arrival rate.
    svc_cap = sum(d["capacity"] for d in DEPARTMENTS if d["code"] != "CONS")
    avg_min = (sum(s["default_duration_min"] for s in ref.service_types)
               / max(len(ref.service_types), 1))
    services_per_sec = svc_cap / (avg_min * SEC_PER_MIN) if avg_min else 0
    avg_tasks = (MIN_ORDERS + MAX_ORDERS) / 2
    sustainable_per_tick = services_per_sec * LOOP_INTERVAL_SEC / max(avg_tasks, 1)
    print(
        f"\nbalance: {svc_cap} service servers, avg {avg_min:.0f} min/test, "
        f"{SEC_PER_MIN:.1f}s/min compression"
    )
    verdict = (
        "BALANCED"
        if ARRIVALS_PER_TICK <= sustainable_per_tick
        else "OVERLOADED - raise capacity or lower SIM_ARRIVALS_PER_TICK"
    )
    print(
        f"  sustainable arrivals ~= {sustainable_per_tick:.2f}/tick  |  "
        f"configured = {ARRIVALS_PER_TICK:.2f}/tick ({verdict})"
    )


def _log_tick(stats: TickStats) -> None:
    ts = datetime.now(UTC).strftime("%H:%M:%S")
    print(
        f"[{ts}] +{stats.arrivals} arrive | {stats.called} called | "
        f"{stats.consults_done} consults done | {stats.tasks_issued} tasks queued | "
        f"{stats.services_done} tests done | {stats.plans_completed} plans complete | "
        f"{stats.no_shows} no-show",
        flush=True,
    )


async def _connect() -> asyncpg.Connection:
    dsn = os.environ.get("DATABASE_DSN")
    if dsn:
        return await asyncpg.connect(dsn, timeout=15)
    return await asyncpg.connect(
        host=os.environ.get("POSTGRES_HOST", "localhost"),
        port=_i("POSTGRES_PORT", 5432),
        database=os.environ.get("POSTGRES_NAME", "nxcare"),
        user=os.environ.get("POSTGRES_USER", "nxcare"),
        password=os.environ.get("POSTGRES_PASSWORD", ""),
        timeout=15,
    )


async def main_async(command: str) -> None:
    seed = os.environ.get("SIM_SEED")
    if seed:
        random.seed(int(seed))
    conn = await _connect()
    try:
        ref = await load_reference(conn)
        if command == "bootstrap":
            await bootstrap(conn)
        elif command == "status":
            await print_status(conn, ref)
        elif command == "tick":
            _log_tick(await run_tick(conn, ref))
        elif command == "loop":
            print(f"loop: tick every {LOOP_INTERVAL_SEC:.0f}s (Ctrl-C to stop)", flush=True)
            while True:
                _log_tick(await run_tick(conn, ref))
                await asyncio.sleep(LOOP_INTERVAL_SEC)
        else:
            raise SystemExit(f"unknown command: {command}")
    finally:
        await conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="VAIC real-time clinic data simulator")
    parser.add_argument("command", choices=["bootstrap", "tick", "loop", "status"])
    args = parser.parse_args()
    try:
        asyncio.run(main_async(args.command))
    except KeyboardInterrupt:
        print("\nstopped.", file=sys.stderr)


if __name__ == "__main__":
    main()
