/**
 * Real authentication/session client (FR-18, patient path).
 *
 * Backs onto `src/vaic/api/auth_routes.py` via `apiFetch` (`client.ts`). `login` exchanges
 * `patientCode`/`password` for a bearer token (`POST /auth/login`), stores it with
 * `setAuthToken`, then hydrates the full `Patient` record (`GET /patients/:id`) so the rest of
 * the app can render a name/priority level without a second round trip on every screen.
 *
 * This patient app only ever accepts `Role.PATIENT` accounts - a successful login for any other
 * role (e.g. a doctor's `Resource.username`) is treated the same as invalid credentials, since
 * there is no patient record to hydrate a `Session` from here.
 *
 * Security note (spec 10 SCR-08 "Error" state): a failed login returns the SAME generic error
 * regardless of whether the patient code exists or the role is wrong - this mirrors the backend's
 * own no-enumeration behavior (`auth_routes.py`).
 */

import { apiFetch, setAuthToken } from './client';
import type { Patient } from './types';

export interface Session {
  patient: Patient;
  role: 'patient';
  issuedAt: string;
}

interface LoginResponse {
  accessToken: string;
  tokenType: string;
  role: string;
  patientId: string | null;
  resourceId: string | null;
}

export class InvalidCredentialsError extends Error {
  constructor() {
    // Generic message - deliberately does not say which field was wrong,
    // nor whether the account exists (spec 10 SCR-08 States > Error).
    super('invalid-credentials');
    this.name = 'InvalidCredentialsError';
  }
}

/** Real API call: `POST /auth/login` then `GET /patients/:id` to hydrate the session. */
export async function login(patientCode: string, password: string): Promise<Session> {
  let auth: LoginResponse;
  try {
    auth = await apiFetch<LoginResponse>('/auth/login', {
      method: 'POST',
      body: { patientCode: patientCode.trim(), password },
    });
  } catch {
    throw new InvalidCredentialsError();
  }

  if (auth.role !== 'role_patient' || !auth.patientId) {
    throw new InvalidCredentialsError();
  }

  setAuthToken(auth.accessToken);

  try {
    const patient = await apiFetch<Patient>(`/patients/${auth.patientId}`);
    return {
      patient,
      role: 'patient',
      issuedAt: new Date().toISOString(),
    };
  } catch (error) {
    setAuthToken(null);
    throw error;
  }
}

/** Real API call: `POST /auth/logout` (stateless server-side - see `auth_routes.py`), then drops the local token. */
export async function logout(): Promise<void> {
  try {
    await apiFetch<void>('/auth/logout', { method: 'POST' });
  } finally {
    setAuthToken(null);
  }
}

/** Real API call: `GET /auth/demo-accounts` - quick-select demo accounts for the SCR-08 selector. */
export async function listDemoAccounts(): Promise<Array<{ patientCode: string; displayName: string }>> {
  return apiFetch<Array<{ patientCode: string; displayName: string }>>('/auth/demo-accounts');
}
