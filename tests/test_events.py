"""Unit tests for the in-process care-plan event bus (TASK-038 real-time seam).

Driven synchronously on one thread with no bound loop, exactly the fallback path documented in
`events.py`: `publish` then `get_nowait` observes delivery without an event loop.
"""

from __future__ import annotations

from asyncio import QueueEmpty
from uuid import uuid4

import pytest

from vaic.api.events import CarePlanEventBus


def test_publish_delivers_to_subscriber_of_that_patient():
    bus = CarePlanEventBus()
    patient_id = uuid4()
    queue = bus.subscribe(patient_id)

    bus.publish(patient_id, {"type": "careplan.updated"})

    assert queue.get_nowait() == {"type": "careplan.updated"}


def test_publish_is_isolated_per_patient():
    bus = CarePlanEventBus()
    mine, other = uuid4(), uuid4()
    mine_queue = bus.subscribe(mine)
    other_queue = bus.subscribe(other)

    bus.publish(mine, {"carePlanId": "cp-1"})

    assert mine_queue.get_nowait() == {"carePlanId": "cp-1"}
    with pytest.raises(QueueEmpty):
        other_queue.get_nowait()


def test_every_subscriber_of_a_patient_receives_the_event():
    bus = CarePlanEventBus()
    patient_id = uuid4()
    first = bus.subscribe(patient_id)
    second = bus.subscribe(patient_id)

    bus.publish(patient_id, {"e": 1})

    assert first.get_nowait() == {"e": 1}
    assert second.get_nowait() == {"e": 1}


def test_unsubscribe_stops_delivery_and_clears_the_bucket():
    bus = CarePlanEventBus()
    patient_id = uuid4()
    queue = bus.subscribe(patient_id)

    bus.unsubscribe(patient_id, queue)

    assert bus.subscriber_count(patient_id) == 0
    bus.publish(patient_id, {"e": 1})
    with pytest.raises(QueueEmpty):
        queue.get_nowait()


def test_publish_to_a_patient_with_no_subscribers_is_a_noop():
    bus = CarePlanEventBus()
    # Must not raise even though nobody is listening.
    bus.publish(uuid4(), {"e": 1})
