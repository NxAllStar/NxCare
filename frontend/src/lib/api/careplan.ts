/**
 * Real Care Plan backend client (TASK-038): the seam that makes a doctor's order on the staff
 * console show on the patient's Journey screen immediately.
 *
 * Talks to `src/vaic/api/careplan_routes.py` and `patient_routes.py`:
 * - `resolvePatient` maps a scannable `patientCode` to the canonical UUID both the console and the
 *   patient app must share (without it the two surfaces address different patients).
 * - `fetchActiveCarePlan` reads the patient's active plan (own-scope on the server, NFR-SEC-05).
 * - `openCarePlanStream` opens the SSE channel; the server pushes `careplan.updated` and the caller
 *   refetches. The event carries no clinical data - it is only a "refresh now" hint.
 * - `generateCarePlan` is the console's write path (doctor signs orders).
 *
 * The base URL comes from `VITE_API_BASE_URL` - anything Vite exposes to the client is PUBLIC by
 * definition (tech-stack.md), so only a plain HTTP base URL belongs here.
 */
import { PaymentSubjectType } from './types';
import type { CarePlan, Payment, Task } from './types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export interface ResolvedPatient {
  patientId: string;
  appointmentId: string;
  patientCode: string;
}

export interface PatientTaskOut {
  taskId: string;
  serviceTypeCode: string;
  serviceTypeLabel: string;
  resourceId: string;
  start: string | null;
  durationMin: number;
  sequenceIndex: number;
  executionStatus: Task['executionStatus'];
  paymentStatus: Task['paymentStatus'];
}

interface ActiveCarePlanResponse {
  carePlanId: string;
  status: string;
  tasks: PatientTaskOut[];
}

export interface GenerateCarePlanParams {
  patientId: string;
  appointmentId: string;
  diagnosedBy: string;
  conditions: string[];
  serviceTypeNames: string[];
}

/** The care plan plus its tasks/payments, mapped to the shapes the patient screens already render. */
export interface CarePlanView {
  carePlan: CarePlan;
  tasks: Task[];
  payments: Payment[];
  // The backend tasks unmapped, so a caller that needs fields the FE `Task` shape drops (e.g. the
  // companion journey needs `serviceTypeCode` to label a room per service) can still reach them.
  // Optional only so lightweight test builders need not synthesize them; the real fetch always sets it.
  rawTasks?: PatientTaskOut[];
}

/** Mint-or-lookup the patient's canonical id by scannable code. */
export async function resolvePatient(patientCode: string): Promise<ResolvedPatient> {
  const response = await fetch(`${API_BASE_URL}/api/patients/resolve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ patientCode }),
  });
  if (!response.ok) {
    throw new Error(`patient resolve failed: ${response.status}`);
  }
  return (await response.json()) as ResolvedPatient;
}

/**
 * Read the patient's active care plan. Returns null on 404 (no active plan) so the caller shows the
 * empty state - the same UX as before, now backed by a real miss instead of a fixture miss.
 */
export async function fetchActiveCarePlan(patientId: string): Promise<CarePlanView | null> {
  const response = await fetch(`${API_BASE_URL}/api/careplan/patient/${patientId}/active`);
  if (response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new Error(`active care plan request failed: ${response.status}`);
  }
  const body = (await response.json()) as ActiveCarePlanResponse;
  return mapActiveCarePlan(body, patientId);
}

/** Open the SSE stream; returns a cleanup function that closes it. Refetch on every event. */
export function openCarePlanStream(patientId: string, onUpdate: () => void): () => void {
  if (typeof EventSource === 'undefined') {
    // Non-browser / test environment without EventSource: no live push, caller keeps its last read.
    return () => {};
  }
  const source = new EventSource(`${API_BASE_URL}/api/careplan/patient/${patientId}/stream`);
  source.onmessage = () => onUpdate();
  return () => source.close();
}

/** Doctor's write path: sign a diagnosis + ordered tests and get the proposed route back. */
export async function generateCarePlan(params: GenerateCarePlanParams): Promise<{ carePlanId: string }> {
  const response = await fetch(`${API_BASE_URL}/api/careplan/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      patient_id: params.patientId,
      appointment_id: params.appointmentId,
      diagnosed_by: params.diagnosedBy,
      actor_role: 'role_doctor',
      conditions: params.conditions,
      service_type_names: params.serviceTypeNames,
    }),
  });
  if (!response.ok) {
    throw new Error(`care plan generate failed: ${response.status}`);
  }
  const body = (await response.json()) as { carePlanId: string };
  return { carePlanId: body.carePlanId };
}

function mapActiveCarePlan(body: ActiveCarePlanResponse, patientId: string): CarePlanView {
  const carePlan: CarePlan = {
    id: body.carePlanId,
    patientId,
    diagnosisId: '',
    status: body.status as CarePlan['status'],
    assignedStaff: [],
    createdAt: '',
  };
  const tasks: Task[] = body.tasks.map((task) => ({
    id: task.taskId,
    carePlanId: body.carePlanId,
    serviceOrderId: '',
    ownerId: task.resourceId,
    executionStatus: task.executionStatus,
    paymentStatus: task.paymentStatus,
    estimatedDurationMin: task.durationMin,
    sequenceIndex: task.sequenceIndex,
    dependsOn: [],
    createdAt: task.start ?? '',
    label: task.serviceTypeLabel,
  }));
  // A proceed-gate flag per task (AS-02: display only), synthesized from the task's own payment
  // status so the Journey screen's chip/banner keep working without a second round-trip.
  const payments: Payment[] = body.tasks.map((task) => ({
    id: `payment-${task.taskId}`,
    subjectType: PaymentSubjectType.TASK,
    subjectId: task.taskId,
    amount: null,
    status: task.paymentStatus,
    confirmedBy: null,
    confirmedAt: null,
  }));
  return { carePlan, tasks, payments, rawTasks: body.tasks };
}
