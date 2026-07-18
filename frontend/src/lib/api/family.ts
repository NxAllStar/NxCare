/**
 * Mock family-switcher stub (/family, PMA-M7 - no backing FR, TASK-023).
 *
 * Spec 06 (access control) has no delegated-viewer scope: nothing in this
 * module ever returns another patient's Own-scope data (Appointment,
 * CarePlan, Task, Notification, ...). `listFamilyProfiles` returns only
 * profile LABELS (id, display name, relationship) for the switcher shell;
 * there is deliberately no `getFamilyMemberJourney`-style function here,
 * because building one would be the exact cross-patient access this task
 * is told not to implement (see TASK-023 Decisions/blockers).
 *
 * No backend exists yet - every export is marked for replacement.
 */
import { DEMO_FAMILY_PROFILES } from './fixtures';
import type { FamilyProfile } from './types';

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** TODO: replace with a real API call (GET /accounts/:id/family-profiles - PMA-M7). */
export async function listFamilyProfiles(accountId: string): Promise<FamilyProfile[]> {
  await delay(80);
  return DEMO_FAMILY_PROFILES.filter((p) => p.ownerAccountId === accountId);
}
