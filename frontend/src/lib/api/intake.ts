/**
 * Intake Agent chat client (SCR-01, FR-01, FR-02, BF-05 - TASK-022).
 *
 * Calls the real backend (`src/vaic/api/intake_routes.py`), which wires the actual Intake Agent
 * triage/slot logic against a real LLM provider when configured - this module no longer contains
 * any triage or emergency-detection logic of its own (that would be duplicated business logic).
 *
 * The base URL comes from `VITE_API_BASE_URL` (`.env.example`) - anything Vite exposes to the
 * client is PUBLIC by definition (tech-stack.md), so nothing beyond a plain HTTP base URL belongs
 * here.
 *
 * Security (AC-01.3/AC-06.3): the patient's `text` is sent as the request body's untrusted DATA and
 * is never interpreted client-side; the backend treats it as data too (NFR-SEC-11).
 */
import type { IntakeTurnResult } from './types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

export async function sendIntakeMessage(patientText: string): Promise<IntakeTurnResult> {
  const response = await fetch(`${API_BASE_URL}/api/intake/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: patientText }),
  });

  if (!response.ok) {
    throw new Error(`intake chat request failed: ${response.status}`);
  }

  return (await response.json()) as IntakeTurnResult;
}
