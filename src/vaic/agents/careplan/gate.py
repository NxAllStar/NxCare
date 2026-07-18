"""FR-05: the proceed gate (paid flag) - a flag, never money processing (AS-02, BR-11).

`confirm_payment` is the staff counter-scan capability (BR-36) that flips a TASK's
`Payment.status` to `PAID` and unlocks it: `Task.execution_status` `LOCKED` -> `PENDING`. It is a
DIFFERENT, EARLIER tool from FR-17's `scan_patient` (journey-dev's room-presence scan,
`PENDING` -> `IN_PROGRESS`): same QR code, different scanner, different timing, different effect
(see FR-05 spec, "Confirmation mechanism"). This module never reuses or edits `scan_patient`.

`constraint_checker.py` has no rule keyed `"confirm_payment"` (it is agent-core-dev's file, out of
this module's scope - see the TASK-008 task file decision), so BR-11 ("only an authorised source
flips PAID; no agent flips it") is enforced INSIDE this handler, via a NAMED, swappable predicate.
OI-19 (which exact staff role may scan) is still open in the spec - swap
`is_authorised_payment_confirmer` for the constructor argument of `build_confirm_payment_tool` the
day it is decided; no other code in this package needs to change.

Precondition (TASK-031, agent-core/FR-18 - not this task's scope): `ConfirmPaymentIn.actor_role` is
trusted here exactly as given. This module assumes it was already populated server-side from the
authenticated session before the tool is ever invoked - never taken verbatim from an unauthenticated
caller. Binding `actor_role` to the real authenticated principal is TASK-031's job; until it lands,
`is_authorised_payment_confirmer` is only as trustworthy as whatever sets `actor_role` upstream.
"""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from pydantic import BaseModel

from ...models import (
    TASK_TRANSITIONS,
    ExecutionStatus,
    InvalidTransition,
    Payment,
    PaymentStatus,
    PaymentSubjectType,
    Task,
    assert_transition,
)
from ...models.entities import _now  # the one shared `_now()` (m4) - never re-defined per module
from ...state import Repository
from ...tools import Tool, ToolError

# Default, narrow reading of OI-19: front-desk / coordinator staff only - never an agent name and
# never a clinical role (BR-11 forbids any agent from flipping PAID). This is a WIRED DEFAULT, not
# the OI-19 ruling itself; the Team lead's later decision may widen or narrow this set.
DEFAULT_AUTHORISED_PAYMENT_ROLES = frozenset({"role_staff", "role_coordinator"})


def is_authorised_payment_confirmer(actor_role: str) -> bool:
    """Default OI-19 predicate: is `actor_role` an authorised payment-confirmation source?

    Swap this callable (pass a different one into `build_confirm_payment_tool`) once OI-19 names
    the exact staff role(s); nothing else in this module needs to change.
    """
    return actor_role in DEFAULT_AUTHORISED_PAYMENT_ROLES


class ConfirmPaymentIn(BaseModel):
    task_id: UUID
    actor_role: str
    confirmed_by: UUID  # the authorised staff/system source - Payment.confirmed_by (BR-36)


def build_confirm_payment_tool(
    is_authorised: Callable[[str], bool] = is_authorised_payment_confirmer,
) -> Tool:
    def handler(params: ConfirmPaymentIn, repo: Repository) -> dict:
        if not is_authorised(params.actor_role):  # BR-11
            raise ToolError(
                f"actor role '{params.actor_role}' is not an authorised payment source - BR-11"
            )

        task = repo.get(Task, params.task_id)
        if task is None:
            raise ToolError("unknown task")

        # m1: the state-machine guard runs BEFORE any write, and is the ONLY guard (no separate
        # ad hoc `!= LOCKED` check duplicating it later) - so a future relaxation of what counts as
        # a valid starting state cannot leave a Payment committed as PAID with no matching task
        # transition. TASK_TRANSITIONS[LOCKED] = {PENDING, CANCELLED}, so this rejects anything
        # that is not currently LOCKED, same as before, from one place.
        try:
            assert_transition(TASK_TRANSITIONS, task.execution_status, ExecutionStatus.PENDING)
        except InvalidTransition as exc:
            raise ToolError(
                f"task is {task.execution_status.value}, expected LOCKED (unpaid) - BR-10"
            ) from exc

        existing = repo.list(
            Payment, subject_type=PaymentSubjectType.TASK, subject_id=params.task_id
        )
        payment = existing[0] if existing else Payment(
            subject_type=PaymentSubjectType.TASK, subject_id=params.task_id
        )
        payment.status = PaymentStatus.PAID
        payment.confirmed_by = params.confirmed_by
        payment.confirmed_at = _now()
        payment = repo.save(payment)

        task.payment_status = PaymentStatus.PAID
        task.execution_status = ExecutionStatus.PENDING
        task = repo.save(task)

        return {"payment_id": str(payment.id), "task_id": str(task.id)}

    return Tool("confirm_payment", ConfirmPaymentIn, handler)
