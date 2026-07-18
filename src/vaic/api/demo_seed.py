"""Idempotent Postgres demo seed (local/dev only - no real patient data, agent-guardrails.md).

Seeds fixed-id `Patient`/`Resource` rows (mirrors `demo_state.py`'s Redis/in-memory seed), and real
login credentials (`auth/credential_store.py`) for five demo accounts - one per role, plus a second
patient account - so the FR-18 login screen and Own/Assigned/Team scope checks all resolve against
real, hashed-password-backed rows instead of an in-memory, unlinked directory.

`ensure_demo_seed()` runs once per process (via the sync bridge's dedicated loop -
`state/sql/sync_adapter.py`) the first time `api/deps.py::get_current_account`'s dependency chain
needs it; if Postgres is unreachable it logs and re-raises, since without a credentials table there
is nothing a login can succeed against.
"""

from __future__ import annotations

from uuid import UUID

from ..auth.credential_store import ensure_table, upsert_credential
from ..auth.roles import Role
from ..models import Patient, PriorityLevel, Resource, ResourceType
from ..state.sql.sync_adapter import PostgresRepositorySyncAdapter, get_bridge_engine, run_coro

# Same synthetic ids/patient_codes the frontend mock layer originally used
# (frontend/src/lib/api/fixtures.ts DEMO_PATIENTS) - kept in step so a demo login resolves to a
# Patient the UI already knows how to render. `demo1234` is the shared demo password for all five
# accounts below - never a real credential (agent-guardrails.md).
DEMO_PATIENT_ID = UUID("00000000-0000-0000-0000-0000000000f1")
DEMO_PATIENT_2_ID = UUID("00000000-0000-0000-0000-0000000000f2")
DEMO_DOCTOR_RESOURCE_ID = UUID("00000000-0000-0000-0000-000000000001")
DEMO_TECHNICIAN_RESOURCE_ID = UUID("00000000-0000-0000-0000-000000000002")
_DEMO_PASSWORD = "demo1234"

_DEMO_ACCOUNT_IDS = {
    "BN-000123": UUID("10000000-0000-0000-0000-000000000001"),
    "BN-000456": UUID("10000000-0000-0000-0000-000000000002"),
    "demo_doctor": UUID("10000000-0000-0000-0000-000000000003"),
    "demo_technician": UUID("10000000-0000-0000-0000-000000000004"),
    "demo_coordinator": UUID("10000000-0000-0000-0000-000000000005"),
    "demo_admin": UUID("10000000-0000-0000-0000-000000000006"),
}


def seed_demo_postgres_data(adapter: PostgresRepositorySyncAdapter) -> None:
    """Re-saving the same fixed ids just overwrites with the same values - safe to call often."""
    for patient_id, full_name, patient_code in (
        (DEMO_PATIENT_ID, "Nguyen Van A", "BN-000123"),
        (DEMO_PATIENT_2_ID, "Tran Thi B", "BN-000456"),
    ):
        if adapter.get(Patient, patient_id) is None:
            adapter.save(
                Patient(
                    id=patient_id,
                    full_name=full_name,
                    patient_code=patient_code,
                    priority_level=PriorityLevel.ROUTINE,
                )
            )
    for resource_id in (DEMO_DOCTOR_RESOURCE_ID, DEMO_TECHNICIAN_RESOURCE_ID):
        if adapter.get(Resource, resource_id) is None:
            adapter.save(
                Resource(
                    id=resource_id,
                    type=ResourceType.DOCTOR,
                    department_id=resource_id,  # synthetic, demo-only
                    is_available=True,
                    capacity_per_hour=6,
                )
            )


async def _seed_demo_credentials() -> None:
    """The async half of the seed - table creation plus the five upserts, run on the bridge
    engine/loop (see module docstring) so it never touches the native-async singleton from a
    different loop (`state/postgres.py`'s docstring on why that specific mix is unsafe)."""
    from ..state.postgres import build_sessionmaker  # local: only needed for this bridge-bound call

    engine = get_bridge_engine()
    await ensure_table(engine)
    sessionmaker = build_sessionmaker(engine)

    # Username IS patient_code for patient accounts (product decision) - a patient logs in with
    # the same code shown throughout the app, no separate identifier to remember.
    await upsert_credential(
        id=_DEMO_ACCOUNT_IDS["BN-000123"],
        username="BN-000123",
        password=_DEMO_PASSWORD,
        role=Role.PATIENT,
        patient_id=DEMO_PATIENT_ID,
        sessionmaker=sessionmaker,
    )
    await upsert_credential(
        id=_DEMO_ACCOUNT_IDS["BN-000456"],
        username="BN-000456",
        password=_DEMO_PASSWORD,
        role=Role.PATIENT,
        patient_id=DEMO_PATIENT_2_ID,
        sessionmaker=sessionmaker,
    )
    await upsert_credential(
        id=_DEMO_ACCOUNT_IDS["demo_doctor"],
        username="demo_doctor",
        password=_DEMO_PASSWORD,
        role=Role.DOCTOR,
        resource_id=DEMO_DOCTOR_RESOURCE_ID,
        sessionmaker=sessionmaker,
    )
    await upsert_credential(
        id=_DEMO_ACCOUNT_IDS["demo_technician"],
        username="demo_technician",
        password=_DEMO_PASSWORD,
        role=Role.TECHNICIAN,
        resource_id=DEMO_TECHNICIAN_RESOURCE_ID,
        sessionmaker=sessionmaker,
    )
    await upsert_credential(
        id=_DEMO_ACCOUNT_IDS["demo_coordinator"],
        username="demo_coordinator",
        password=_DEMO_PASSWORD,
        role=Role.COORDINATOR,
        sessionmaker=sessionmaker,
    )
    await upsert_credential(
        id=_DEMO_ACCOUNT_IDS["demo_admin"],
        username="demo_admin",
        password=_DEMO_PASSWORD,
        role=Role.ADMIN,
        sessionmaker=sessionmaker,
    )


_seeded = False


def ensure_demo_seed() -> None:
    """Idempotent, process-wide: seeds Patient/Resource rows plus the five demo login credentials.
    Called once (guarded by `_seeded`) from `api/deps.py` the first time auth is needed."""
    global _seeded
    if _seeded:
        return
    seed_demo_postgres_data(PostgresRepositorySyncAdapter())
    run_coro(_seed_demo_credentials())
    _seeded = True
