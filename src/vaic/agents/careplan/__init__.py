"""Care Plan Agent: FR-03 (order capture), FR-04 (task generation + sequencing),
FR-05 (proceed gate / paid flag), FR-08 (slot allocation).

The Care Plan Agent optimises HOW a signed set of orders is carried out, never WHAT is carried
out (CO-02, BR-07): every write here either records a doctor-signed clinical fact unchanged, or
sequences/slots/gates it. No function in this package invents, drops, or re-targets a service.
"""

from __future__ import annotations

from .care_plan import (
    ActivateCarePlanIn,
    CarePlanResult,
    CreateCarePlanIn,
    CreateTaskIn,
    build_activate_care_plan_tool,
    build_create_care_plan_tool,
    build_create_task_tool,
    generate_care_plan,
)
from .durations import DurationEstimator
from .gate import (
    DEFAULT_AUTHORISED_PAYMENT_ROLES,
    ConfirmPaymentIn,
    build_confirm_payment_tool,
    is_authorised_payment_confirmer,
)
from .orders import (
    CaptureResult,
    CreateDiagnosisIn,
    CreateServiceOrderIn,
    build_create_diagnosis_tool,
    build_create_service_order_tool,
    capture_diagnosis_and_orders,
)
from .sequencing import SequencedOrder, sequence_orders
from .slots import (
    AllocateSlotIn,
    SlotCandidate,
    allocate_task_slot,
    build_allocate_slot_tool,
)

__all__ = [
    "ActivateCarePlanIn",
    "CarePlanResult",
    "CreateCarePlanIn",
    "CreateTaskIn",
    "build_activate_care_plan_tool",
    "build_create_care_plan_tool",
    "build_create_task_tool",
    "generate_care_plan",
    "DurationEstimator",
    "DEFAULT_AUTHORISED_PAYMENT_ROLES",
    "ConfirmPaymentIn",
    "build_confirm_payment_tool",
    "is_authorised_payment_confirmer",
    "CaptureResult",
    "CreateDiagnosisIn",
    "CreateServiceOrderIn",
    "build_create_diagnosis_tool",
    "build_create_service_order_tool",
    "capture_diagnosis_and_orders",
    "SequencedOrder",
    "sequence_orders",
    "AllocateSlotIn",
    "SlotCandidate",
    "allocate_task_slot",
    "build_allocate_slot_tool",
]
