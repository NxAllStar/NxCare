/**
 * Mock proactive-prep stub (/prep/:id, PMA-M2 - TASK-023).
 *
 * No backend exists yet - every export is marked for replacement.
 */
import { DEMO_PREP_REMINDERS } from './fixtures';
import type { PrepReminder } from './types';

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** TODO: replace with a real API call (GET /appointments/:id/prep - PMA-M2). */
export async function getPrepReminder(appointmentId: string): Promise<PrepReminder | null> {
  await delay(80);
  return DEMO_PREP_REMINDERS.find((r) => r.appointmentId === appointmentId) ?? null;
}
