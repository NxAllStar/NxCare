"""Patient-code scan tool (FR-17): the deterministic effect behind a station scan.

The scan is a human action (doctor/technician). Validation and the state change are deterministic
code, never a model call (FR-17 "Validate and update status: deterministic"). Authorisation -
owner-only (BR-26), not LOCKED (BR-27), must be PENDING - is enforced by the shared constraint
checker's `scan_patient` rule (agent-core) BEFORE this handler runs, so this tool only runs on an
already-authorised scan. Here we additionally verify the presented code matches the task's patient,
record the `ScanEvent`, and advance `PENDING -> IN_PROGRESS` along the state machine.
"""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from ...models import (
    TASK_TRANSITIONS,
    CarePlan,
    ExecutionStatus,
    Patient,
    ScanEvent,
    Task,
    assert_transition,
)
from ...state import Repository
from ...tools import Tool, ToolError, ToolRegistry

# Matches the constraint-checker rule name (agent-core), so the gate applies.
SCAN_TOOL = "scan_patient"


class ScanPatientIn(BaseModel):
    """Input for `scan_patient`. `patient_code` is validated data, never an instruction (FR-17)."""

    model_config = ConfigDict(extra="forbid")

    task_id: UUID
    scanned_by: UUID  # must be the task owner - enforced by the constraint checker (BR-26)
    patient_code: str


def _scan_patient(params: ScanPatientIn, repo: Repository) -> dict:
    """Verify the code matches the task's patient, record the scan, advance to IN_PROGRESS.

    Runs only after the constraint checker has confirmed the task exists, is not LOCKED, is PENDING,
    and the scanner is the owner. A code that does not match the task's patient is rejected here.
    """
    task = repo.get(Task, params.task_id)
    if task is None:  # defensive - the checker already verified existence
        raise ToolError("unknown task")

    care_plan = repo.get(CarePlan, task.care_plan_id)
    patient = repo.get(Patient, care_plan.patient_id) if care_plan is not None else None
    if patient is None or patient.patient_code != params.patient_code:
        # The presented code does not identify the patient this task belongs to (FR-17 validation).
        raise ToolError("patient code does not match the task's patient")

    repo.save(
        ScanEvent(patient_id=patient.id, task_id=task.id, scanned_by=params.scanned_by)
    )

    assert_transition(TASK_TRANSITIONS, task.execution_status, ExecutionStatus.IN_PROGRESS)
    task.execution_status = ExecutionStatus.IN_PROGRESS
    repo.save(task)

    return {
        "task_id": str(task.id),
        "patient_id": str(patient.id),
        "execution_status": task.execution_status.value,
    }


def register_journey_tools(registry: ToolRegistry) -> ToolRegistry:
    """Register the Journey Agent's domain tools on `registry` and return it (for chaining)."""
    registry.register(Tool(SCAN_TOOL, ScanPatientIn, _scan_patient))
    return registry
