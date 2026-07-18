/**
 * Proves the mock audit store's append-only contract (BR-23, FR-13, TASK-027
 * acceptance criteria: "The mock audit store is append-only: a written entry
 * is never mutated or deleted").
 */
import { beforeEach, describe, expect, it } from 'vitest';
import { appendAuditEntry, listAuditEntries, resetAuditStoreForTest } from './auditStore';

const ACTOR = { actorId: 'coordinator', actorRole: 'coordinator' as const, actorDisplayName: 'DPV Pham Thu Ha (demo)' };

beforeEach(() => {
  resetAuditStoreForTest();
});

describe('auditStore (BR-23 append-only)', () => {
  it('writes an entry with the minimum required fields: actor identity + role, decision, target id, timestamp, carried rationale', () => {
    const entry = appendAuditEntry({
      ...ACTOR,
      decision: 'APPROVED',
      targetEventId: 'disruption-0001',
      aiRationale: 'reason carried from the proposal',
    });

    expect(entry.actorId).toBe(ACTOR.actorId);
    expect(entry.actorRole).toBe(ACTOR.actorRole);
    expect(entry.decision).toBe('APPROVED');
    expect(entry.targetEventId).toBe('disruption-0001');
    expect(entry.aiRationale).toBe('reason carried from the proposal');
    expect(typeof entry.timestamp).toBe('string');
    expect(entry.timestamp.length).toBeGreaterThan(0);
  });

  it('a second write does not mutate or remove the first (append-only)', () => {
    const first = appendAuditEntry({
      ...ACTOR,
      decision: 'APPROVED',
      targetEventId: 'disruption-0001',
      aiRationale: 'first reason',
    });
    const firstSnapshot = { ...first };

    appendAuditEntry({
      ...ACTOR,
      decision: 'REJECTED',
      targetEventId: 'disruption-0002',
      aiRationale: 'second reason',
    });

    const entries = listAuditEntries();
    expect(entries).toHaveLength(2);
    expect(entries[0]).toEqual(firstSnapshot);
    expect(entries[0].targetEventId).toBe('disruption-0001');
    expect(entries[1].targetEventId).toBe('disruption-0002');
  });

  it('a previously read entry is frozen - an in-place mutation attempt throws rather than silently corrupting history', () => {
    const entry = appendAuditEntry({
      ...ACTOR,
      decision: 'APPROVED',
      targetEventId: 'disruption-0001',
      aiRationale: 'reason',
    });

    expect(() => {
      (entry as { decision: string }).decision = 'REJECTED';
    }).toThrow();
    expect(listAuditEntries()[0].decision).toBe('APPROVED');
  });

  it('has no exported update or delete function - the only mutator is appendAuditEntry', async () => {
    const moduleExports = await import('./auditStore');
    const exportNames = Object.keys(moduleExports);
    expect(exportNames).toContain('appendAuditEntry');
    expect(exportNames.some((name) => /update|delete|remove|clear/i.test(name) && !/ForTest/.test(name))).toBe(
      false,
    );
  });
});
