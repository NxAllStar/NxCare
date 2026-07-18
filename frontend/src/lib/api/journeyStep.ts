/**
 * Mock step-detail stub (/journey/step/:id, PMA-M3 - TASK-023).
 *
 * Combines a `Task` (already fixtured for TASK-022 in fixtures.ts) with its
 * `StepDetail` (ETA range, "why this order," wayfinding, queue position -
 * new for this task). `whyThisOrder` is always model-produced and every
 * caller must render it behind an AIChip (NFR-USE-05).
 *
 * No backend exists yet - every export is marked for replacement.
 */
import { DEMO_CARE_PLANS, DEMO_STEP_DETAILS, DEMO_TASKS } from './fixtures';
import type { StepDetail, Task } from './types';

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export interface JourneyStep {
  task: Task;
  detail: StepDetail | null;
}

/**
 * TODO: replace with a real API call (GET /tasks/:id + GET
 * /tasks/:id/step-detail - FR-04, FR-06). Own-scope mirror (NFR-SEC-05): a
 * task belonging to a different patient's care plan is treated as not
 * found, never returned to the caller.
 */
export async function getJourneyStep(patientId: string, taskId: string): Promise<JourneyStep | null> {
  await delay(80);
  const ownCarePlanIds = new Set(DEMO_CARE_PLANS.filter((p) => p.patientId === patientId).map((p) => p.id));
  const task = DEMO_TASKS.find((t) => t.id === taskId && ownCarePlanIds.has(t.carePlanId));
  if (!task) return null;
  const detail = DEMO_STEP_DETAILS.find((d) => d.taskId === taskId) ?? null;
  return { task, detail };
}
