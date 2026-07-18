/**
 * Mock health-records stub (/results, /medications, /recovery - PMA-M4/M5,
 * no backing FR yet, PRD-FR-12 section 7 open item - TASK-023).
 *
 * Narrow safety guardrail carried by every caller of this module (never
 * loosen it here): a lab result is only ever labelled within/outside its
 * reference range, never a diagnosis or prognosis; the recovery check-in
 * frame only collects -> flags -> refers to a doctor, and never advises
 * treatment (PRD-FR-12 4, PMA-M4/PMA-M5).
 *
 * No backend exists yet - every export is marked for replacement.
 */
import { DEMO_LAB_RESULTS, DEMO_MEDICATIONS, DEMO_RECOVERY_CHECKINS } from './fixtures';
import type { LabResult, Medication, RecoveryCheckIn } from './types';

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** TODO: replace with a real API call (GET /patients/:id/results - PMA-M4). */
export async function listLabResults(patientId: string): Promise<LabResult[]> {
  await delay(80);
  return DEMO_LAB_RESULTS.filter((r) => r.patientId === patientId);
}

/** TODO: replace with a real API call (GET /patients/:id/medications - PMA-M5). */
export async function listMedications(patientId: string): Promise<Medication[]> {
  await delay(80);
  return DEMO_MEDICATIONS.filter((m) => m.patientId === patientId);
}

/** TODO: replace with a real API call (GET /patients/:id/recovery-checkins - PMA-M5). */
export async function listRecoveryCheckIns(patientId: string): Promise<RecoveryCheckIn[]> {
  await delay(80);
  return DEMO_RECOVERY_CHECKINS.filter((c) => c.patientId === patientId);
}
