"""Runnable, narrated demo of BF-02 -> BF-03 (FR-03/FR-04/FR-08/FR-23): a doctor enters a patient's
diagnosis and test orders, and the Care Plan Agent immediately checks station load and proposes the
first route.

Standalone: builds its own in-memory `Repository` and FastAPI app (same pattern as
`tests/test_careplan_routes.py`), so it runs without a live server or Postgres. This is the
"kiem tra flow ung dung truc tiep" deliverable - it exercises the real `/api/careplan/generate` and
`/api/careplan/patient/{id}/active` handlers, not a re-implementation of their logic.

Run: `uv run python scripts/demo_careplan_flow.py`
"""

from __future__ import annotations

import json
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from vaic.api.careplan_routes import build_careplan_router
from vaic.api.demo_state import DEMO_CAREPLAN_STATIONS, seed_demo_careplan_stations
from vaic.models import Appointment, ServiceType
from vaic.state import InMemoryRepository


def _seed_service_catalog(repo: InMemoryRepository) -> None:
    """A small, realistic ServiceType catalog (normally synced from Postgres - demo_state.py)."""
    repo.save(ServiceType(
        code="BLOOD_TEST", display_label="Xet nghiem mau",
        requires_fasting=True, turnaround_minutes=45, default_duration_min=10,
    ))
    repo.save(ServiceType(
        code="XRAY", display_label="Chup X-quang",
        requires_fasting=False, turnaround_minutes=15, default_duration_min=15,
    ))
    repo.save(ServiceType(
        code="ULTRASOUND", display_label="Sieu am bung",
        requires_fasting=True, turnaround_minutes=0, default_duration_min=20,
    ))


def _print_step(title: str) -> None:
    print(f"\n=== {title} ===")


def main() -> None:
    repo = InMemoryRepository()
    seed_demo_careplan_stations(repo)  # 3 fixed technician/room stations, FR-08 capacity model
    _seed_service_catalog(repo)

    app = FastAPI()
    app.include_router(build_careplan_router(repo))
    client = TestClient(app)

    patient_id = uuid4()
    appointment = repo.save(Appointment(patient_id=patient_id, specialty="general"))

    _print_step("1. Bac si nhap ID benh nhan + chan doan + danh sach chi dinh")
    print(f"patient_id = {patient_id}")
    print("conditions = ['sot cao', 'dau bung']")
    print("service_type_names = ['Xet nghiem mau', 'Chup X-quang', 'Sieu am bung']")

    response = client.post(
        "/api/careplan/generate",
        json={
            "patient_id": str(patient_id),
            "appointment_id": str(appointment.id),
            "diagnosed_by": str(uuid4()),
            "actor_role": "role_doctor",
            "conditions": ["sot cao", "dau bung"],
            "service_type_names": ["Xet nghiem mau", "Chup X-quang", "Sieu am bung"],
        },
    )
    response.raise_for_status()
    generated = response.json()

    _print_step("2. AI (Care Plan Agent) kiem tra tai tram va de xuat lo trinh dau tien")
    print(f"care_plan_id = {generated['carePlanId']}  status = {generated['status']}")
    print(f"3 tram xet nghiem san sang: {[str(s) for s in DEMO_CAREPLAN_STATIONS]}")
    for step in generated["route"]:
        print(
            f"  #{step['sequenceIndex']} {step['serviceTypeLabel']:<20} "
            f"tram={step['resourceId']}  bat_dau={step['start']}  "
            f"thoi_luong={step['durationMin']} phut"
        )

    _print_step("3. Man hinh benh nhan doc lai lo trinh (GET /patient/{id}/active)")
    active = client.get(f"/api/careplan/patient/{patient_id}/active")
    active.raise_for_status()
    body = active.json()
    for task in body["tasks"]:
        print(
            f"  {task['serviceTypeLabel']:<20} trang_thai={task['executionStatus']:<8} "
            f"thanh_toan={task['paymentStatus']}"
        )
    print("\n(payment_status = UNPAID mac dinh - FR-05/BR-10: task LOCKED cho toi khi nhan vien "
          "quet ma xac nhan thanh toan, khong tinh vao hang doi cho toi luc do)")

    _print_step("Full JSON (/active)")
    print(json.dumps(body, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
