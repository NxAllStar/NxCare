"""FR-04 task sequencing (TASK-008), BR-07/BR-08/BR-09.

AC-04.1: blood (fasting, turnaround 45') + ultrasound + x-ray -> blood first, x-ray inserted
during the turnaround wait, ultrasound after.
AC-04.2 (negative): a single ultrasound order never grows extra service tasks.

TASK-008 fix round: cM4 (owner_resolver resolved exactly once per order, carried on
SequencedOrder.owner_id) and sec-m1/BR-14 (a non-positive estimated duration is rejected here,
before any Task or Slot can be built from it).
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from vaic.agents.careplan.sequencing import sequence_orders
from vaic.models import ServiceOrder, ServiceType


def _order_and_type(code: str, **type_kw) -> tuple[ServiceOrder, ServiceType]:
    diagnosis_id = uuid4()
    st = ServiceType(code=code, display_label=code, **type_kw)
    order = ServiceOrder(patient_id=uuid4(), diagnosis_id=diagnosis_id, service_type_id=st.id,
                          ordered_by=uuid4())
    return order, st


def test_ac_04_1_fasting_first_then_gap_filled_then_remainder():
    blood = _order_and_type("BLOOD_TEST", requires_fasting=True, turnaround_minutes=45)
    ultrasound = _order_and_type("ULTRASOUND", requires_fasting=False)
    xray = _order_and_type("XRAY", requires_fasting=False)

    durations = {"BLOOD_TEST": 10, "ULTRASOUND": 40, "XRAY": 15}

    def estimate(service_type, owner_id):
        return durations[service_type.code]

    sequenced = sequence_orders(
        [blood, ultrasound, xray],
        estimate_duration=estimate,
        owner_resolver=lambda order, st: uuid4(),
    )

    assert [s.service_type.code for s in sequenced] == ["BLOOD_TEST", "XRAY", "ULTRASOUND"]
    assert [s.sequence_index for s in sequenced] == [0, 1, 2]
    # durations came only from the injected estimator (BR-09) - never guessed
    assert [s.duration_min for s in sequenced] == [10, 15, 40]


def test_ac_04_2_single_order_never_gains_extra_tasks():
    ultrasound = _order_and_type("ULTRASOUND", requires_fasting=False)

    sequenced = sequence_orders(
        [ultrasound],
        estimate_duration=lambda st, owner_id: 20,
        owner_resolver=lambda order, st: uuid4(),
    )

    assert len(sequenced) == 1
    assert sequenced[0].service_type.code == "ULTRASOUND"
    assert sequenced[0].order.id == ultrasound[0].id


def test_sequencing_never_reorders_two_independent_non_fasting_orders():
    ultrasound = _order_and_type("ULTRASOUND", requires_fasting=False)
    xray = _order_and_type("XRAY", requires_fasting=False)

    sequenced = sequence_orders(
        [ultrasound, xray],
        estimate_duration=lambda st, owner_id: 10,
        owner_resolver=lambda order, st: uuid4(),
    )

    assert [s.service_type.code for s in sequenced] == ["ULTRASOUND", "XRAY"]


def test_gap_fill_tries_shortest_first_and_skips_what_no_longer_fits():
    # gap = 20; candidates are tried shortest-duration-first: B (10) fits, leaving 10 minutes of
    # capacity; A (15) no longer fits in what remains, so it falls through to the tail.
    blood = _order_and_type("BLOOD_TEST", requires_fasting=True, turnaround_minutes=20)
    a = _order_and_type("A", requires_fasting=False)
    b = _order_and_type("B", requires_fasting=False)
    durations = {"BLOOD_TEST": 5, "A": 15, "B": 10}

    sequenced = sequence_orders(
        [blood, a, b],
        estimate_duration=lambda st, owner_id: durations[st.code],
        owner_resolver=lambda order, st: uuid4(),
    )

    assert [s.service_type.code for s in sequenced] == ["BLOOD_TEST", "B", "A"]


def test_cm4_owner_resolver_is_called_exactly_once_per_order():
    xray = _order_and_type("XRAY", requires_fasting=False)
    calls: list = []
    owners = iter([uuid4(), uuid4(), uuid4()])  # a stateful/round-robin resolver

    def owner_resolver(order, service_type):
        owner = next(owners)
        calls.append(owner)
        return owner

    sequenced = sequence_orders(
        [xray], estimate_duration=lambda st, owner_id: 10, owner_resolver=owner_resolver,
    )

    assert len(calls) == 1  # resolved once, not once for duration + once again for task creation
    assert sequenced[0].owner_id == calls[0]


def test_sec_m1_negative_duration_from_estimator_is_rejected():
    xray = _order_and_type("XRAY", requires_fasting=False)

    with pytest.raises(ValueError, match="range"):
        sequence_orders(
            [xray],
            estimate_duration=lambda st, owner_id: -5,
            owner_resolver=lambda order, st: uuid4(),
        )


def test_sec_m1_absurdly_large_duration_from_estimator_is_rejected():
    xray = _order_and_type("XRAY", requires_fasting=False)

    with pytest.raises(ValueError, match="range"):
        sequence_orders(
            [xray],
            estimate_duration=lambda st, owner_id: 10_000,
            owner_resolver=lambda order, st: uuid4(),
        )
