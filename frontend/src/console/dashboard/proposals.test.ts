/**
 * Proves the mock approval-queue service's BR-22/FR-09/AC-09.3 contract
 * (TASK-027 acceptance criteria).
 */
import { beforeEach, describe, expect, it } from 'vitest';
import { resetAuditStoreForTest, listAuditEntries } from './auditStore';
import { DEMO_HEATMAP_TICKS } from './fixtures';
import { decideProposal, listPendingProposals, ProposalNotPendingError, resetProposalsForTest } from './proposals';
import type { ApprovalActor } from './types';

const COORDINATOR: ApprovalActor = {
  actorId: 'coordinator',
  actorRole: 'coordinator',
  actorDisplayName: 'DPV Pham Thu Ha (demo)',
};

beforeEach(() => {
  resetProposalsForTest();
  resetAuditStoreForTest();
});

describe('proposals (BR-22 approve/reject is one-tap and audited)', () => {
  it('only PENDING_APPROVAL events (never AUTO_APPLIED) are ever in the queue - scope lock item 1', () => {
    const queue = listPendingProposals();
    expect(queue.length).toBeGreaterThan(0);
    expect(queue.every((event) => event.status === 'PENDING_APPROVAL')).toBe(true);
    expect(queue.some((event) => event.id === 'disruption-0003')).toBe(false); // AUTO_APPLIED fixture
  });

  it('approving a PENDING_APPROVAL proposal writes an audit entry carrying the proposal\'s own AI rationale, and dequeues it', async () => {
    const before = listPendingProposals();
    const target = before[0];

    const entry = await decideProposal(target.id, 'APPROVED', COORDINATOR);

    expect(entry.decision).toBe('APPROVED');
    expect(entry.targetEventId).toBe(target.id);
    expect(entry.actorId).toBe(COORDINATOR.actorId);
    expect(entry.actorRole).toBe(COORDINATOR.actorRole);
    expect(entry.aiRationale).toBe(target.aiReason); // carried over, not regenerated
    expect(listAuditEntries()).toHaveLength(1);

    const after = listPendingProposals();
    expect(after.find((e) => e.id === target.id)).toBeUndefined();
    expect(after).toHaveLength(before.length - 1);
  });

  it('rejecting a PENDING_APPROVAL proposal writes an audit entry and dequeues it, holding the heatmap/resource state unchanged (AC-09.3)', async () => {
    const before = listPendingProposals();
    const target = before[1];
    const heatmapBefore = JSON.stringify(DEMO_HEATMAP_TICKS);

    const entry = await decideProposal(target.id, 'REJECTED', COORDINATOR);

    expect(entry.decision).toBe('REJECTED');
    expect(entry.targetEventId).toBe(target.id);
    expect(entry.aiRationale).toBe(target.aiReason);

    const after = listPendingProposals();
    expect(after.find((e) => e.id === target.id)).toBeUndefined();
    expect(JSON.stringify(DEMO_HEATMAP_TICKS)).toBe(heatmapBefore); // untouched
  });

  it('rejects deciding a proposal that is not PENDING_APPROVAL (already decided or unknown)', async () => {
    const target = listPendingProposals()[0];
    await decideProposal(target.id, 'APPROVED', COORDINATOR); // now dequeued / no longer pending

    await expect(decideProposal(target.id, 'APPROVED', COORDINATOR)).rejects.toBeInstanceOf(
      ProposalNotPendingError,
    );
    // No second audit entry was written for the rejected re-decision attempt.
    expect(listAuditEntries()).toHaveLength(1);
  });

  it('rejects deciding an unknown proposal id', async () => {
    await expect(decideProposal('does-not-exist', 'APPROVED', COORDINATOR)).rejects.toThrow(
      'proposal-not-found:does-not-exist',
    );
  });
});
