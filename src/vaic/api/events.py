"""In-process pub/sub so a patient's screen can be pushed a refresh the moment a doctor's order
(POST /api/careplan/generate) writes a new plan for them - the FR-04 handoff, observed live.

Single-process only, matching the demo `Repository`: subscribers are `asyncio.Queue`s held in
memory, keyed by `patient_id`. Not durable and not cross-process - a Redis pub/sub layer is where
this goes once the app is more than one worker (noted, not built: the durable-store choice OI-15 is
still open). Losing the queues on restart is acceptable here: a client reconnects its `EventSource`
and refetches `/active`, so the stream is a "refresh now" hint, never the source of truth.

Thread-safety: FastAPI runs the synchronous `/generate` handler in a worker thread, while the SSE
generator consuming a queue runs on the event loop. Delivering across that boundary uses
`loop.call_soon_threadsafe`; the serving loop is bound once at app startup (`bind_loop`). Without a
bound running loop - unit tests that drive `publish` directly on one thread - it falls back to a
same-thread `put_nowait`, which is why the tests can assert delivery without an event loop.
"""

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

logger = logging.getLogger(__name__)


class CarePlanEventBus:
    """Fan-out of care-plan change events to the SSE subscribers of a single patient."""

    def __init__(self) -> None:
        self._subscribers: dict[UUID, set[asyncio.Queue]] = {}
        self._loop: asyncio.AbstractEventLoop | None = None

    def bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Record the serving event loop once, at startup, for threadsafe cross-thread delivery."""
        self._loop = loop

    def subscribe(self, patient_id: UUID) -> asyncio.Queue:
        """Register a new queue for `patient_id`; the caller must `unsubscribe` it when done."""
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers.setdefault(patient_id, set()).add(queue)
        return queue

    def unsubscribe(self, patient_id: UUID, queue: asyncio.Queue) -> None:
        """Drop a queue; remove the patient's bucket once its last subscriber leaves."""
        subscribers = self._subscribers.get(patient_id)
        if not subscribers:
            return
        subscribers.discard(queue)
        if not subscribers:
            self._subscribers.pop(patient_id, None)

    def subscriber_count(self, patient_id: UUID) -> int:
        return len(self._subscribers.get(patient_id, ()))

    def publish(self, patient_id: UUID, event: dict) -> None:
        """Deliver `event` to every current subscriber of `patient_id` (a no-op if none)."""
        # Copy the set: delivery may hop threads and a concurrent (un)subscribe must not mutate the
        # set mid-iteration.
        for queue in list(self._subscribers.get(patient_id, ())):
            self._deliver(queue, event)

    def _deliver(self, queue: asyncio.Queue, event: dict) -> None:
        loop = self._loop
        if loop is not None and loop.is_running():
            loop.call_soon_threadsafe(queue.put_nowait, event)
        else:
            queue.put_nowait(event)
