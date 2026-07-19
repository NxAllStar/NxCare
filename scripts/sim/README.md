# Real-time clinic data simulator

A standalone demo-data generator that keeps the live PostgreSQL store looking like a **working
clinic**: patients arrive, book an appointment, take a queue number, move through consult and their
tests, and finish - with arrivals **balanced** against completions so the queues stay realistic and
never explode.

It is deliberately **not** application code. It drives the same care-pathway state machines the app
enforces (`src/vaic/models/transitions.py`) but lives entirely under `scripts/sim/`. Every row it
writes is synthetic; it only ever INSERTs new rows and UPDATEs the status of rows it created. It
never deletes, truncates, or touches pre-existing (legacy) data.

## Files

| File | Role |
|------|------|
| `simulate.sh` | The runner. Loads DB connection from `.env`, picks the venv Python, dispatches. |
| `engine.py` | The async (`asyncpg`) simulation engine: bootstrap, tick, loop, status. |

## Quick start

```bash
cd scripts/sim

./simulate.sh bootstrap   # one-time: create the 4 fake departments the queue needs
./simulate.sh status      # show live queue depth per department + the balance budget
./simulate.sh loop        # run continuously in the foreground (real-time feel)
```

`bootstrap` is required once because the `departments` table ships empty, and a `queue_ticket`
cannot exist without a department. It is idempotent (fixed UUIDs, `ON CONFLICT`), so re-running is
safe.

## Running it for real

Two ways to keep it ticking:

**1. Cron (one tick per minute)** - survives reboots, no supervisor needed:

```bash
./simulate.sh install-cron   # prints the exact line, then:
crontab -e
# * * * * * /abs/path/scripts/sim/simulate.sh once >> /tmp/vaic-sim.log 2>&1
```

**2. Continuous loop (smoother, sub-minute cadence)** - run under a supervisor
(`systemd`, `pm2`, `nohup`, `tmux`):

```bash
nohup ./simulate.sh loop >> /tmp/vaic-sim.log 2>&1 &
```

Both do the same work per tick; the loop just ticks more often (`SIM_INTERVAL_SEC`, default 15s).

## The lifecycle each tick drives

```
arrival ─▶ appointment (BOOKED)
        ─▶ CONSULT ticket   WAITING ─▶ CALLED ─▶ IN_SERVICE ─▶ DONE
        ─▶ diagnosis + care plan + N service orders + N tasks
        ─▶ SERVICE ticket per task, issued one at a time as the previous task finishes
        ─▶ task            LOCKED ─▶ PENDING ─▶ IN_PROGRESS ─▶ DONE
        ─▶ all tasks done ─▶ care plan COMPLETED ─▶ patient leaves the system
```

Appointment status is kept in lock-step with the consult ticket (`CHECKED_IN` on call,
`IN_CONSULT` in service, `DONE` on completion; a small share become `NO_SHOW`). Slots, payments,
scan events, notifications, and audit-log entries are written along the way so the whole schema
looks alive.

## Why it stays balanced (and does not explode)

The clinic is an **M/M/c queue per department**:

- **Bounded servers.** Each department serves at most `capacity` patients at once
  (`CONS=3, LAB=2, IMG=2, CARD=1` by default). Throughput is capped no matter how long the line is.
- **Time-compressed service.** A test of `D` minutes occupies a server for `D x SIM_SEC_PER_MIN`
  real seconds (default 3s/min -> a 30-min MRI clears in ~90s). Work drains at a staggered, lifelike
  pace instead of all at once.
- **Admission control.** New patients are only created while patients-in-system (WIP) is below
  `SIM_WIP_CAP`, and the mean arrival rate is held below total service capacity. In-rate therefore
  tracks out-rate; the backlog stays small and bounded.
- **Sequential tests.** A patient joins each test's queue only after finishing the previous one, so
  demand arrives gradually rather than in a burst.

`./simulate.sh status` prints the **balance budget**: the sustainable arrival rate implied by your
capacity/timing settings versus the configured rate, and flags `BALANCED` or `OVERLOADED`.

## Tuning (environment variables)

Export any of these before calling `simulate.sh` (or put them in the crontab line / service unit):

| Variable | Default | Meaning |
|----------|---------|---------|
| `SIM_ARRIVALS_PER_TICK` | `0.25` | Expected new patients per tick (Poisson). |
| `SIM_INTERVAL_SEC` | `15` | Loop tick interval, seconds. |
| `SIM_SEC_PER_MIN` | `3.0` | Real seconds per simulated service-minute (lower = faster). |
| `SIM_WIP_CAP` | `40` | Max patients in the system before arrivals pause. |
| `SIM_CALL_DELAY_SEC` | `6` | CALLED -> IN_SERVICE settle time. |
| `SIM_CONSULT_MINUTES` | `15` | Consult service duration. |
| `SIM_MIN_ORDERS` / `SIM_MAX_ORDERS` | `1` / `4` | Tests ordered per patient (inclusive range). |
| `SIM_NO_SHOW_PROB` | `0.05` | Chance a called consult patient is a no-show. |
| `SIM_CAP_CONS/LAB/IMG/CARD` | `3/2/2/1` | Servers (concurrency) per department. |
| `SIM_SEED` | - | Seed the RNG for reproducible runs. |
| `SIM_PYTHON` | repo `.venv` | Python interpreter to use (must have `asyncpg`). |
| `SIM_ENV_FILE` | repo `.env` | Where to read `POSTGRES_*` from. |

### Example: a fast, dense demo (things happen in seconds)

```bash
SIM_INTERVAL_SEC=2 SIM_SEC_PER_MIN=0.5 SIM_ARRIVALS_PER_TICK=0.5 ./simulate.sh loop
```

If `status` reports `OVERLOADED`, either lower `SIM_ARRIVALS_PER_TICK` or raise a department's
capacity (`SIM_CAP_*`).

## Connection

`simulate.sh` reads `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_NAME`, `POSTGRES_USER`,
`POSTGRES_PASSWORD` from the repo `.env` (the same variables the app uses). Alternatively export a
single `DATABASE_DSN=postgresql://user:pass@host:port/db`. Nothing is hard-coded and no credentials
live in these files.
```
