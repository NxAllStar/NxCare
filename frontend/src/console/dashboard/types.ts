/**
 * SCR-06 coordinator dashboard mock-data shapes (TASK-027). Console-only -
 * deliberately kept under `src/console/` rather than `src/lib/api/` so it
 * never touches patient-app code (task instructions).
 *
 * Enum values are English UPPER_SNAKE_CASE (coding-standards.md).
 *
 * Scope lock (spec-guardian, 2026-07-18): the blast-radius threshold N is
 * UNRESOLVED in the specs (OI-03). `DisruptionEventStatus` marks each event
 * as `PENDING_APPROVAL` (> N, needs approval - appears in the queue) or
 * `AUTO_APPLIED` (<= N, invisible on this screen) as FIXED demo data; this
 * module never computes a real N.
 */
import type { StaffRole } from '../access';

export const DisruptionEventStatus = {
  /** Blast radius above the (unresolved) threshold - awaits coordinator/admin approval. */
  PENDING_APPROVAL: 'PENDING_APPROVAL',
  /** Blast radius at or below the (unresolved) threshold - applied without a human gate;
   * never surfaced in the approval queue (spec 10 SCR-06 - only the > N tier has a surface here). */
  AUTO_APPLIED: 'AUTO_APPLIED',
  APPROVED: 'APPROVED',
  REJECTED: 'REJECTED',
} as const;
export type DisruptionEventStatus = (typeof DisruptionEventStatus)[keyof typeof DisruptionEventStatus];

/** One candidate re-plan action the Disruption Agent proposes. Always
 * model-produced - render only alongside an AIChip (NFR-USE-05). */
export interface RePlanOption {
  id: string;
  label: string;
  description: string;
}

/** `DisruptionEvent` (spec 08 data model) - the re-plan proposal shown in
 * the approval queue (FR-09, FR-10, FR-12). */
export interface DisruptionEvent {
  id: string;
  status: DisruptionEventStatus;
  /** Count of affected patients/tasks - display data only, never a computed
   * real N (scope lock item 1). */
  blastRadius: number;
  areaLabel: string;
  triggeredAt: string; // ISO 8601
  /** Disruption Agent's candidate actions - model-produced. */
  options: RePlanOption[];
  /** Disruption Agent's plain-language rationale - model-produced, always
   * AIChip-labelled wherever rendered (NFR-USE-05). */
  aiReason: string;
}

export type AuditDecision = 'APPROVED' | 'REJECTED';

/** The identity making an approve/reject decision (BR-22, FR-13 minimum
 * fields: actor identity + role). Demo staff has no numeric account id
 * (StaffAuthContext.ts) - the role is the stable synthetic identity in this
 * single-account-per-role demo. */
export interface ApprovalActor {
  actorId: string;
  actorRole: StaffRole;
  actorDisplayName: string;
}

/**
 * `AuditLogEntry` (spec 08 data model) subset written on every approve or
 * reject (BR-22, FR-13). Append-only (BR-23, auditStore.ts) - this is the
 * seed SCR-07/TASK-030 will later read.
 *
 * `aiRationale` is carried over verbatim from the proposal's own `aiReason`
 * at decision time, never re-generated (scope lock item 3).
 */
export interface AuditEntry extends ApprovalActor {
  id: string;
  decision: AuditDecision;
  targetEventId: string;
  timestamp: string; // ISO 8601
  aiRationale: string;
}

// ---------------------------------------------------------------------------
// Load heatmap (Resource entity, spec 08 data model) - areas x time slots.
// ---------------------------------------------------------------------------

/** 1 = lowest load (heat-1, green) .. 6 = highest load (heat-6, red) -
 * spec 10 "Visual design direction": sequential green -> amber -> red. */
export type HeatLevel = 1 | 2 | 3 | 4 | 5 | 6;

export interface HeatmapCell {
  id: string; // stable across ticks: `${areaId}:${timeSlot}`
  areaId: string;
  areaLabel: string;
  timeSlot: string; // e.g. "08:00"
  loadLevel: HeatLevel;
  /** Tabular-number display value, e.g. "82%" - paired with `loadLevel` so
   * colour is never the sole signal (frontend.md). */
  valueLabel: string;
}

export interface HeatmapGrid {
  tickId: string;
  generatedAt: string; // ISO 8601
  areas: string[]; // row labels, in display order
  timeSlots: string[]; // column labels, in display order
  cells: HeatmapCell[];
}
