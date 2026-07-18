/**
 * Mock read stubs for the patient's own data (TASK-021 foundation layer).
 *
 * Every function below is a placeholder the later screen batches (TASK-022,
 * TASK-023) call into. All of them are scoped by `patientId` and only ever
 * return data belonging to that patient - fixtures for other patients are
 * structurally absent from the result, not merely hidden in the UI
 * (NFR-SEC-05: the server is the real gate, this is a convenience mirror of
 * that same discipline in the mock layer).
 *
 * No backend exists yet - every export is marked for replacement.
 */

import {
  DEMO_APPOINTMENTS,
  DEMO_CARE_PLANS,
  DEMO_NOTIFICATIONS,
  DEMO_PATIENTS,
  DEMO_PAYMENTS,
  DEMO_TASKS,
} from './fixtures';
import { AppointmentStatus } from './types';
import type { Appointment, CarePlan, Notification, Patient, Payment, Task } from './types';

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** TODO: replace with a real API call (GET /patients/:id, own-scope only - NFR-SEC-05). */
export async function getPatient(patientId: string): Promise<Patient | null> {
  await delay(80);
  return DEMO_PATIENTS.find((p) => p.id === patientId) ?? null;
}

/** TODO: replace with a real API call (GET /patients/:id/notifications - FR-20). */
export async function listNotifications(patientId: string): Promise<Notification[]> {
  await delay(80);
  return DEMO_NOTIFICATIONS.filter((n) => n.patientId === patientId);
}

/** TODO: replace with a real API call (GET /patients/:id/appointments - FR-19). */
export async function listAppointments(patientId: string): Promise<Appointment[]> {
  await delay(80);
  return DEMO_APPOINTMENTS.filter((a) => a.patientId === patientId);
}

/** TODO: replace with a real API call (GET /patients/:id/care-plan - FR-04). */
export async function getActiveCarePlan(patientId: string): Promise<CarePlan | null> {
  await delay(80);
  return DEMO_CARE_PLANS.find((c) => c.patientId === patientId) ?? null;
}

/** TODO: replace with a real API call (GET /care-plans/:id/tasks - FR-04, FR-06). */
export async function listTasksForCarePlan(carePlanId: string): Promise<Task[]> {
  await delay(80);
  return DEMO_TASKS.filter((t) => t.carePlanId === carePlanId).sort(
    (a, b) => a.sequenceIndex - b.sequenceIndex,
  );
}

/** TODO: replace with a real API call (GET /patients/:id/payments - FR-05, AS-02: flag only). */
export async function listPaymentsForTasks(taskIds: string[]): Promise<Payment[]> {
  await delay(80);
  return DEMO_PAYMENTS.filter((p) => taskIds.includes(p.subjectId));
}

/**
 * TODO: replace with a real API call (PATCH /appointments/:id - FR-19
 * reschedule, own scope only). Read-only against the fixture list: returns
 * a new Appointment object rather than mutating shared state, so repeated
 * calls in tests stay deterministic.
 */
export async function rescheduleAppointment(appointmentId: string, newSlotStart: string): Promise<Appointment> {
  await delay(150);
  const existing = DEMO_APPOINTMENTS.find((a) => a.id === appointmentId);
  if (!existing) {
    throw new Error(`appointment-not-found:${appointmentId}`);
  }
  return { ...existing, slotStart: newSlotStart, status: AppointmentStatus.BOOKED };
}

/**
 * TODO: replace with a real API call (PATCH /appointments/:id - FR-19
 * cancel, own scope only). The UI is responsible for confirming with the
 * patient before calling this (spec 10 cross-cutting rules: destructive
 * actions need confirmation).
 */
export async function cancelAppointment(appointmentId: string): Promise<Appointment> {
  await delay(150);
  const existing = DEMO_APPOINTMENTS.find((a) => a.id === appointmentId);
  if (!existing) {
    throw new Error(`appointment-not-found:${appointmentId}`);
  }
  return { ...existing, status: AppointmentStatus.CANCELLED };
}
