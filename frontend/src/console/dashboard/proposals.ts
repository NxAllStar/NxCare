/**
 * Mock approval-queue service (SCR-06, BR-22, FR-09, FR-10, FR-12). No
 * backend exists yet - every export is marked for replacement (mirrors the
 * `src/lib/api/` mock-layer convention, kept under `src/console/` per the
 * task's scope).
 *
 * Only `PENDING_APPROVAL` events are ever queued (scope lock item 1 - the
 * `AUTO_APPLIED` tier never reaches this module's queue).
 */
import { appendAuditEntry } from './auditStore';
import { DEMO_DISRUPTION_EVENTS } from './fixtures';
import { DisruptionEventStatus, type ApprovalActor, type AuditDecision, type AuditEntry, type DisruptionEvent } from './types';

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function cloneEvent(event: DisruptionEvent): DisruptionEvent {
  return { ...event, options: event.options.map((o) => ({ ...o })) };
}

function seedAllEvents(): DisruptionEvent[] {
  return DEMO_DISRUPTION_EVENTS.map(cloneEvent);
}

// The full demo event set (every status, including AUTO_APPLIED and, after a
// decision, APPROVED/REJECTED) - kept as ONE list with a status field, not a
// separate "queue" array items are deleted from, so `decideProposal` mirrors
// the real DisruptionEvent state machine (PENDING_APPROVAL -> APPROVED /
// REJECTED) instead of destroying the record. `listPendingProposals` is a
// filtered VIEW of this list.
let events: DisruptionEvent[] = seedAllEvents();

/** TODO: replace with a real API call (GET the Coordinator's pending
 * approval queue, FR-10/FR-12). Only `PENDING_APPROVAL` events are ever
 * returned (scope lock item 1 - `AUTO_APPLIED` never appears here). Returns
 * a defensive copy so callers cannot mutate the module's own state directly. */
export function listPendingProposals(): DisruptionEvent[] {
  return events.filter((event) => event.status === DisruptionEventStatus.PENDING_APPROVAL).map(cloneEvent);
}

export class ProposalNotPendingError extends Error {
  constructor(eventId: string) {
    super(`proposal-not-pending:${eventId}`);
    this.name = 'ProposalNotPendingError';
  }
}

/**
 * Approves or rejects a `PENDING_APPROVAL` proposal (BR-22): one call does
 * both the audit write and the dequeue. Rejects any other status (TASK-027
 * acceptance criteria: "enabled only while PENDING_APPROVAL") rather than
 * silently accepting a stale or already-decided proposal.
 *
 * On reject, the underlying plan/resource state (the heatmap fixtures) is
 * never touched here (AC-09.3) - this function's only side effects are the
 * audit write and the in-memory queue removal.
 *
 * TODO: replace with a real API call (POST the Coordinator's decision,
 * FR-09/FR-10; BR-22 one-tap approve/reject, audited).
 */
export async function decideProposal(
  eventId: string,
  decision: AuditDecision,
  actor: ApprovalActor,
): Promise<AuditEntry> {
  await delay(60);

  const event = events.find((e) => e.id === eventId);
  if (!event) {
    throw new Error(`proposal-not-found:${eventId}`);
  }
  if (event.status !== DisruptionEventStatus.PENDING_APPROVAL) {
    throw new ProposalNotPendingError(eventId);
  }

  const entry = appendAuditEntry({
    ...actor,
    decision,
    targetEventId: event.id,
    aiRationale: event.aiReason, // carried over, never regenerated (scope lock item 3)
  });

  // Immutable state transition (PENDING_APPROVAL -> decision), not a
  // deletion - `listPendingProposals` filters it out of the queue view from
  // here on, matching BR-22 "removes the proposal from the queue".
  events = events.map((e) => (e.id === eventId ? { ...e, status: decision } : e));

  return entry;
}

/** Test-only reset so each test starts from the seeded fixture set. */
export function resetProposalsForTest(): void {
  events = seedAllEvents();
}
