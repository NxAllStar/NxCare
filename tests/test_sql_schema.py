"""SQLAlchemy/schemas.sql parity and durable-store smoke tests (TASK-032, resolves OI-15).

Structural tests (`test_models_*`) always run - they never touch a database, just compare parsed
`schemas.sql` table/column names against `vaic.state.sql.models`, so drift between the DDL and the
ORM models is caught without any infrastructure.

`test_create_schema_against_live_postgres` is the real, non-mocked check (testing.md's Integration
layer: "real datastore, mocked external providers" - there is no external provider here, just a
database). It is skipped unless `VAIC_TEST_DB_URL` points at a disposable PostgreSQL instance, so a
plain `pytest` run never requires one:

    docker run --rm -d --name vaic-test-pg -e POSTGRES_PASSWORD=test -e POSTGRES_USER=test \\
        -e POSTGRES_DB=vaic_test -p 15433:5432 postgres:16-alpine
    export VAIC_TEST_DB_URL=postgresql+pg8000://test:test@127.0.0.1:15433/vaic_test
    pytest tests/test_sql_schema.py
    docker rm -f vaic-test-pg
"""

from __future__ import annotations

import os
import re
import uuid
from datetime import UTC, datetime
from pathlib import Path

import pytest

sqlalchemy = pytest.importorskip("sqlalchemy")

from vaic.state.sql import models  # noqa: E402
from vaic.state.sql.engine import create_schema  # noqa: E402

_SCHEMA_PATH = Path(__file__).resolve().parents[1] / "src/vaic/state/sql/schemas.sql"
_TABLE_RE = re.compile(r"CREATE TABLE (\w+) \((.*?)\n\);", re.DOTALL)


def _parsed_tables() -> dict[str, list[str]]:
    """table_name -> [column_name, ...], parsed from schemas.sql (comments stripped first)."""
    sql = _SCHEMA_PATH.read_text(encoding="utf-8")
    code = "\n".join(line.split("--", 1)[0] for line in sql.splitlines())
    tables: dict[str, list[str]] = {}
    for name, body in _TABLE_RE.findall(code):
        columns = []
        for raw_line in body.splitlines():
            line = raw_line.strip().rstrip(",")
            if not line:
                continue
            first_token = line.split()[0]
            columns.append(first_token.strip('"'))  # "end" is quoted in the DDL
        tables[name] = columns
    return tables


# Entity class name -> schemas.sql table name. Explicit (not a pluralization guess) because
# English pluralization is irregular (Diagnosis -> diagnoses, AuditLogEntry -> audit_log_entries).
_ENTITY_TABLE = {
    "Patient": "patients",
    "IntakeSession": "intake_sessions",
    "Appointment": "appointments",
    "Diagnosis": "diagnoses",
    "ServiceOrder": "service_orders",
    "ServiceType": "service_types",
    "CarePlan": "care_plans",
    "Task": "tasks",
    "Slot": "slots",
    "Payment": "payments",
    "Resource": "resources",
    "DisruptionEvent": "disruption_events",
    "Notification": "notifications",
    "AuditLogEntry": "audit_log_entries",
    "ScanEvent": "scan_events",
}


def test_schemas_sql_has_one_table_per_entity_in_the_model_registry():
    from vaic.models.entities import ENTITIES

    expected = {_ENTITY_TABLE[e.__name__] for e in ENTITIES}
    assert set(_ENTITY_TABLE) == {e.__name__ for e in ENTITIES}, (
        "the _ENTITY_TABLE map in this test is out of sync with vaic.models.entities.ENTITIES"
    )
    parsed = set(_parsed_tables())
    assert parsed == expected, f"schemas.sql tables {parsed} != expected {expected}"


def test_sqlalchemy_models_match_schemas_sql_tables_and_columns():
    parsed = _parsed_tables()
    modeled = models.Base.metadata.tables

    assert set(parsed) == set(modeled), (
        f"table name mismatch: schemas.sql={set(parsed)} models.py={set(modeled)}"
    )
    for table_name, expected_columns in parsed.items():
        actual_columns = [c.name for c in modeled[table_name].columns]
        assert actual_columns == expected_columns, (
            f"{table_name}: schemas.sql columns {expected_columns} != "
            f"models.py columns {actual_columns}"
        )


def test_schemas_sql_gives_every_foreign_key_an_explicit_on_delete_action():
    sql = _SCHEMA_PATH.read_text(encoding="utf-8")
    code = "\n".join(line.split("--", 1)[0] for line in sql.splitlines())
    references = re.findall(r"REFERENCES\s+\w+\s*\([^)]*\)(?:\s+ON DELETE \w+)?", code)
    assert references, "expected at least one FK in schemas.sql"
    for ref in references:
        assert "ON DELETE" in ref, f"FK with no explicit referential action: {ref!r}"


# ---- real, disposable PostgreSQL only - never mocked, per testing.md ----------------------------

@pytest.mark.skipif(
    not os.environ.get("VAIC_TEST_DB_URL"),
    reason="set VAIC_TEST_DB_URL to a disposable Postgres to run this (see module docstring)",
)
def test_create_schema_against_live_postgres():
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import Session

    from vaic.state.sql.models import AppointmentRow, PatientRow

    engine = create_engine(os.environ["VAIC_TEST_DB_URL"])
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE"))
        conn.execute(text("CREATE SCHEMA public"))
    create_schema(engine)

    patient_id = uuid.uuid4()
    with Session(engine) as session:
        session.add(
            PatientRow(
                id=patient_id, full_name="Nguyen Van A", patient_code="VAIC-TEST1",
                created_at=datetime.now(UTC),
            )
        )
        session.commit()
        fetched = session.get(PatientRow, patient_id)
        assert fetched is not None
        assert fetched.patient_code == "VAIC-TEST1"

        session.add(
            AppointmentRow(
                id=uuid.uuid4(), patient_id=uuid.uuid4(), specialty="cardiology",
                created_at=datetime.now(UTC),
            )
        )
        with pytest.raises(Exception, match="(?i)foreign key|violat"):
            session.commit()
        session.rollback()
