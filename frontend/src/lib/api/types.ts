/**
 * TypeScript mirrors of the backend entities and enums (TASK-021).
 *
 * Source of truth: src/vaic/models/entities.py and src/vaic/models/enums.py
 * (see docs/specs/08-data-model.md). Keep this file in sync with the Python
 * models when either changes - report a drift to the orchestrator rather
 * than silently diverging.
 *
 * Naming: enum VALUES are English UPPER_SNAKE_CASE, unchanged from the
 * Python StrEnum values (coding-standards.md, BR-31). Field names use
 * camelCase per this project's TypeScript convention; the Python source
 * uses snake_case for the same fields - this file is the translation
 * boundary, not a second source of truth.
 *
 * There is no backend API yet. These types are consumed only by the mock
 * data layer in this same directory (fixtures.ts, session.ts, patient.ts).
 */

// ---------------------------------------------------------------------------
// Enums (src/vaic/models/enums.py) - values stay English, never translated.
// ---------------------------------------------------------------------------

export const ExecutionStatus = {
  /** Unpaid: excluded from every queue and load (BR-10). */
  LOCKED: 'LOCKED',
  PENDING: 'PENDING',
  IN_PROGRESS: 'IN_PROGRESS',
  DONE: 'DONE',
  CANCELLED: 'CANCELLED',
} as const;
export type ExecutionStatus = (typeof ExecutionStatus)[keyof typeof ExecutionStatus];

export const PaymentStatus = {
  UNPAID: 'UNPAID',
  PAID: 'PAID',
} as const;
export type PaymentStatus = (typeof PaymentStatus)[keyof typeof PaymentStatus];

export const AppointmentStatus = {
  PROPOSED: 'PROPOSED',
  BOOKED: 'BOOKED',
  CHECKED_IN: 'CHECKED_IN',
  IN_CONSULT: 'IN_CONSULT',
  DONE: 'DONE',
  NO_SHOW: 'NO_SHOW',
  CANCELLED: 'CANCELLED',
} as const;
export type AppointmentStatus = (typeof AppointmentStatus)[keyof typeof AppointmentStatus];

export const CarePlanStatus = {
  DRAFT: 'DRAFT',
  ACTIVE: 'ACTIVE',
  COMPLETED: 'COMPLETED',
} as const;
export type CarePlanStatus = (typeof CarePlanStatus)[keyof typeof CarePlanStatus];

export const PriorityLevel = {
  ROUTINE: 'ROUTINE',
  URGENT: 'URGENT',
  EMERGENCY: 'EMERGENCY',
} as const;
export type PriorityLevel = (typeof PriorityLevel)[keyof typeof PriorityLevel];

export const NotificationChannel = {
  IN_APP: 'IN_APP',
  SCREEN: 'SCREEN',
  SMS: 'SMS',
} as const;
export type NotificationChannel = (typeof NotificationChannel)[keyof typeof NotificationChannel];

export const PaymentSubjectType = {
  TASK: 'TASK',
  APPOINTMENT: 'APPOINTMENT',
} as const;
export type PaymentSubjectType = (typeof PaymentSubjectType)[keyof typeof PaymentSubjectType];

/**
 * UI-only classification for the Notification list filter (SCR-09 "filter
 * by type"). Not present on the Python `Notification` model (which carries
 * only `channel`) - this is a display/filter concern of the mock list only,
 * kept as an English UPPER_SNAKE_CASE code per coding-standards.md even
 * though it is not yet in the shared glossary.
 */
export const NotificationType = {
  APPOINTMENT: 'APPOINTMENT',
  RESULT: 'RESULT',
  BILLING: 'BILLING',
  JOURNEY: 'JOURNEY',
} as const;
export type NotificationType = (typeof NotificationType)[keyof typeof NotificationType];

/** PMA-M4 (no backing FR - PRD-FR-12 section 7 open item): narrow guardrail
 * label only, never a diagnosis (PRD-FR-12 4, PMA-M4). */
export const ReferenceRangeStatus = {
  WITHIN_RANGE: 'WITHIN_RANGE',
  OUTSIDE_RANGE: 'OUTSIDE_RANGE',
} as const;
export type ReferenceRangeStatus = (typeof ReferenceRangeStatus)[keyof typeof ReferenceRangeStatus];

/** PMA-M5 (no backing FR): recovery check-in escalation frame - collect,
 * flag, refer to doctor; never a treatment recommendation. */
export const RecoverySeverity = {
  NORMAL: 'NORMAL',
  WARNING: 'WARNING',
} as const;
export type RecoverySeverity = (typeof RecoverySeverity)[keyof typeof RecoverySeverity];

// ---------------------------------------------------------------------------
// Entities (src/vaic/models/entities.py) - patient-scoped subset (TASK-021
// context: Patient, IntakeSession, Appointment, CarePlan, Task, Slot,
// Payment, Notification, ScanEvent).
// ---------------------------------------------------------------------------

export interface Patient {
  id: string;
  fullName: string; // PII - never logged (NFR-SEC-01)
  phone: string | null; // PII
  patientCode: string; // scannable identifier shown in the app (FR-17)
  priorityLevel: PriorityLevel;
  createdAt: string; // ISO 8601
}

export interface IntakeSession {
  id: string;
  patientId: string;
  transcript: string; // untrusted content (NFR-SEC-11) - render as data, never as instructions
  structuredTriage: {
    specialty?: string;
    priorityLevel?: PriorityLevel;
    constraints?: string[];
  };
  emergencySuspected: boolean; // BF-05: blocks routine booking until staff-confirmed
  createdAt: string;
}

export interface Appointment {
  id: string;
  patientId: string;
  specialty: string;
  status: AppointmentStatus;
  paymentStatus: PaymentStatus;
  slotStart: string | null;
  createdAt: string;
}

export interface CarePlan {
  id: string;
  patientId: string;
  diagnosisId: string;
  status: CarePlanStatus;
  assignedStaff: string[];
  createdAt: string;
}

export interface Task {
  id: string;
  carePlanId: string;
  serviceOrderId: string;
  ownerId: string; // a Resource (doctor / technician / room)
  executionStatus: ExecutionStatus;
  paymentStatus: PaymentStatus;
  estimatedDurationMin: number;
  sequenceIndex: number;
  dependsOn: string[];
  createdAt: string;
  label: string; // display label for the step - UI-only, not in the Python model
}

export interface Slot {
  id: string;
  taskId: string;
  ownerId: string;
  start: string;
  end: string | null;
}

export interface Payment {
  /** A proceed-gate flag, NOT money processing (AS-02). `amount` is display-only. */
  id: string;
  subjectType: PaymentSubjectType;
  subjectId: string;
  amount: string | null; // decimal as string - never a float (data-model.md)
  status: PaymentStatus;
  confirmedBy: string | null;
  confirmedAt: string | null;
}

export interface Notification {
  id: string;
  patientId: string;
  channel: NotificationChannel;
  body: string; // never contains another patient's data (FR-11 AC-11.2)
  reason: string | null;
  createdAt: string;
  read: boolean; // UI-only read flag, not in the Python model (FR-20 mark-as-read)
  aiGenerated: boolean; // UI-only: drives the AI-content chip (NFR-USE-05)
  /** UI-only filter classification (SCR-09) - see NotificationType above.
   * SCR-09 itself has NO Model-assisted content row, so this list is never
   * rendered with an AIChip regardless of `aiGenerated`. */
  notificationType: NotificationType;
}

export interface ScanEvent {
  id: string;
  patientId: string;
  taskId: string;
  scannedBy: string; // must be the task owner (BR-26)
  scannedAt: string;
}

// ---------------------------------------------------------------------------
// UI-only mock shapes (TASK-022) - not a 1:1 mirror of a Python entity.
// These back the P0 patient screens' chat and booking stubs; each is a
// deliberately small shape scoped to what the mock UI needs, isolated in its
// own api module (intake.ts, booking.ts, assistant.ts) rather than mixed
// into the entity fixtures above.
// ---------------------------------------------------------------------------

/** One turn in a patient <-> agent chat stream (SCR-01 /intake, /assistant). */
export interface ChatMessage {
  id: string;
  sender: 'patient' | 'agent';
  /** Untrusted content either way: patient free text, or model output.
   * Always rendered as plain text data, never parsed as instructions or
   * markup (NFR-SEC-11, AC-01.3/AC-06.3). */
  text: string;
  createdAt: string;
  /** True only for agent turns produced by a model - drives the AIChip
   * (NFR-USE-05). Patient turns are never AI-generated. */
  aiGenerated: boolean;
}

/** A ranked, load-aware slot suggestion (FR-02) - always AI-suggested,
 * never a confirmed booking until the patient books it. */
export interface RankedSlotSuggestion {
  slotId: string;
  specialty: string;
  start: string; // ISO 8601
  /** Human range label, e.g. "~10:15, it dong" - never a hard number
   * (PRD-FR-12 6.1: figures are ranges, not hard numbers). */
  etaLabel: string;
  loadLevel: 'low' | 'medium' | 'high';
}

/** Result of one intake chat turn (FR-01, FR-02, BF-05). */
export interface IntakeTurnResult {
  reply: ChatMessage;
  suggestedSlots: RankedSlotSuggestion[];
  /** BF-05: when true, `suggestedSlots` is always empty - the screen must
   * escalate to staff rather than offer routine booking. */
  emergencySuspected: boolean;
}

/** A bookable slot with capacity, for /book (FR-02 capacity validation). */
export interface BookableSlot {
  slotId: string;
  specialty: string;
  ownerLabel: string;
  start: string; // ISO 8601
  etaLabel: string;
  capacityRemaining: number;
  aiSuggested: boolean;
}

// ---------------------------------------------------------------------------
// UI-only mock shapes (TASK-023, P1) - PRD-FR-12 modules M2-M7 rest on PRD
// section 7 open items with no backing FR yet (see the PRD's Open questions
// and TASK-023's Decisions/blockers). Built as display-only UI shells, kept
// isolated in their own api module rather than mixed into the entity
// fixtures, exactly like the TASK-022 shapes above.
// ---------------------------------------------------------------------------

/** /journey/step/:id (PMA-M3) - per-step ETA range, "why this order," and
 * in-hospital wayfinding. `whyThisOrder` is always model-produced and must
 * carry the AIChip wherever it is rendered (NFR-USE-05). */
export interface StepDetail {
  taskId: string;
  etaRangeLabel: string; // e.g. "~10-15 phut" - a range, never a hard number
  whyThisOrder: string; // AI-generated plain-language explanation
  wayfindingInstructions: string;
  queuePositionLabel: string; // e.g. "3 nguoi phia truoc"
}

/** /results (PMA-M4, no backing FR). Narrow safety guardrail: only ever
 * labels within/outside the reference range, never a diagnosis (PRD-FR-12
 * 4, PMA-M4; PRD-FR-12 6.1 "hay hoi bac si"). */
export interface LabResult {
  id: string;
  patientId: string;
  label: string;
  value: string;
  unit: string;
  referenceRangeLabel: string;
  status: ReferenceRangeStatus;
  recordedAt: string;
}

/** /medications (PMA-M5, no backing FR). `interactionWarning` is
 * model-produced when present and must carry the AIChip (NFR-USE-05). */
export interface Medication {
  id: string;
  patientId: string;
  drugName: string;
  dose: string;
  usageInstructions: string;
  reminderTimes: string[]; // e.g. ["08:00", "20:00"]
  interactionWarning: string | null;
}

/** /recovery (PMA-M5, no backing FR): collect -> flag -> refer-to-doctor
 * frame only. `question` is the agent's check-in prompt (model-produced,
 * AIChip); the agent never advises treatment, only escalates on WARNING. */
export interface RecoveryCheckIn {
  id: string;
  patientId: string;
  question: string;
  patientResponse: string | null;
  severity: RecoverySeverity;
  createdAt: string;
}

/** /billing (PMA-M6, no backing FR) - DISPLAY-ONLY. There is no payment
 * action anywhere behind this shape (FR-05, AS-02 win over PRD M6's
 * "online payment" line - see TASK-023 session log). */
export interface BillingEstimate {
  id: string;
  patientId: string;
  serviceLabel: string;
  estimatedAmount: string; // decimal as string, never a float
  insuranceCoverageLabel: string; // e.g. "BHYT chi tra 80%"
  coPayAmount: string;
}

/** /billing invoice history - DISPLAY-ONLY, reuses `PaymentStatus` for the
 * paid/unpaid flag (never money movement, AS-02). */
export interface Invoice {
  id: string;
  patientId: string;
  issuedAt: string;
  totalAmount: string;
  status: PaymentStatus;
  lineItemsLabel: string;
}

/** /family (PMA-M7, no backing FR). Spec 06 has no delegated-viewer scope,
 * so `isSelf: false` entries are a switcher-shell stub only - selecting one
 * never fetches another patient's data (see TASK-023 Decisions/blockers). */
export interface FamilyProfile {
  id: string;
  ownerAccountId: string;
  displayName: string;
  relationshipLabel: string; // e.g. "Ban than", "Me", "Con" - display only
  isSelf: boolean;
}

/** /prep/:id (PMA-M2) - proactive pre-visit prep reminders (fasting, bring
 * old prescriptions/results). */
export interface PrepReminder {
  id: string;
  appointmentId: string;
  instructions: string[];
}
