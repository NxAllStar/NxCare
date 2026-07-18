/**
 * Mock authentication/session stub (FR-18, patient path only - TASK-021).
 *
 * No backend exists. This module simulates a login call with latency and a
 * failure mode, and is the ONLY place demo credentials live. Every export
 * below is a stand-in for a future real endpoint.
 *
 * Security note (spec 10 SCR-08 "Error" state): a failed login returns the
 * SAME generic error regardless of whether the patient code exists - this
 * is deliberate, not an oversight. Never branch the error message on
 * "code not found" vs "wrong password" (no account enumeration).
 */

import { DEMO_PATIENTS } from './fixtures';
import type { Patient } from './types';

export interface Session {
  patient: Patient;
  role: 'patient';
  issuedAt: string;
}

interface DemoCredential {
  patientCode: string;
  password: string;
}

// Synthetic demo credentials only - never real accounts (agent-guardrails.md).
const DEMO_CREDENTIALS: DemoCredential[] = [
  { patientCode: 'BN-000123', password: 'demo1234' },
  { patientCode: 'BN-000456', password: 'demo1234' },
];

export class InvalidCredentialsError extends Error {
  constructor() {
    // Generic message - deliberately does not say which field was wrong,
    // nor whether the account exists (spec 10 SCR-08 States > Error).
    super('invalid-credentials');
    this.name = 'InvalidCredentialsError';
  }
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * TODO: replace with a real API call (FR-18 authentication and session).
 * Demo-only: validates against the in-memory DEMO_CREDENTIALS list and
 * returns a mock session for the matching patient.
 */
export async function login(patientCode: string, password: string): Promise<Session> {
  await delay(150);

  const trimmedCode = patientCode.trim();
  const credential = DEMO_CREDENTIALS.find((c) => c.patientCode === trimmedCode);
  const patient = DEMO_PATIENTS.find((p) => p.patientCode === trimmedCode);

  // Same failure for "no such code" and "wrong password" - see class doc.
  if (!credential || !patient || credential.password !== password) {
    throw new InvalidCredentialsError();
  }

  return {
    patient,
    role: 'patient',
    issuedAt: new Date().toISOString(),
  };
}

/** TODO: replace with a real API call that invalidates the server-side session (FR-18). */
export async function logout(): Promise<void> {
  await delay(50);
}

/** Quick-select demo accounts for the SCR-08 "account or role selector" - demo/local only. */
export function listDemoAccounts(): Array<{ patientCode: string; displayName: string }> {
  return DEMO_PATIENTS.map((p) => ({ patientCode: p.patientCode, displayName: p.fullName }));
}
