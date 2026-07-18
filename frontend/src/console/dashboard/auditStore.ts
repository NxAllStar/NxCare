/**
 * Mock, in-memory, APPEND-ONLY audit store (BR-23, FR-13) for the SCR-06
 * approve/reject flow. This is the seed SCR-07/TASK-030 will later read -
 * proof boundary (spec-guardian): this proves the UI/mock append-only SHAPE
 * only, not a persistent tamper-evident log (that needs TASK-010/TASK-004).
 *
 * "Append-only" here means exactly two things, both enforced by this
 * module's surface: (1) there is no exported update or delete function -
 * the only way to change the store is `appendAuditEntry`, and (2) every
 * entry returned to a caller is frozen, so an accidental in-place mutation
 * of a previously-read entry throws instead of silently corrupting history.
 */
import type { ApprovalActor, AuditDecision, AuditEntry } from './types';

let entries: AuditEntry[] = [];
let nextId = 1;

export interface AppendAuditEntryInput extends ApprovalActor {
  decision: AuditDecision;
  targetEventId: string;
  /** Carried over from the proposal's own AI rationale - never regenerated
   * at decision time (scope lock item 3). */
  aiRationale: string;
}

/** Writes one audit entry and returns it. Never mutates or removes any
 * previously written entry (BR-23). */
export function appendAuditEntry(input: AppendAuditEntryInput): AuditEntry {
  const entry: AuditEntry = Object.freeze({
    ...input,
    id: `audit-${nextId++}`,
    timestamp: new Date().toISOString(),
  });
  entries = [...entries, entry];
  return entry;
}

/** Read-only snapshot, oldest first - matches the write order (append-only). */
export function listAuditEntries(): readonly AuditEntry[] {
  return entries;
}

/** Test-only reset so each test starts from a clean, isolated store. Not
 * exported from any barrel consumed by screens - tests import it directly. */
export function resetAuditStoreForTest(): void {
  entries = [];
  nextId = 1;
}
