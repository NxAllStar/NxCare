/**
 * Combined initial load for SCR-06 (TASK-027). No backend exists yet - this
 * composes the mock heatmap tick 0, the mock approval queue, and the mock
 * reasoning transcript behind one async call, the shape the real
 * Coordinator/Disruption-agent endpoints will eventually fill (TASK-010).
 *
 * `CoordinatorDashboardScreen` accepts this function as an injectable prop
 * (default = this export) so tests can simulate an LLM failure by supplying
 * a rejecting loader, without a global mutable "simulate failure" flag.
 */
import { DEMO_REASONING_TRANSCRIPT } from './fixtures';
import { heatmapGridAtTick } from './heatmap';
import { listPendingProposals } from './proposals';
import type { DisruptionEvent, HeatmapGrid } from './types';

export interface DashboardData {
  heatmap: HeatmapGrid;
  proposals: DisruptionEvent[];
  reasoningTranscript: string;
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** TODO: replace with real API calls (GET the Coordinator's live load +
 * approval queue + reasoning stream, FR-09/FR-10/FR-12). */
export async function loadDashboardData(): Promise<DashboardData> {
  await delay(120);
  return {
    heatmap: heatmapGridAtTick(0),
    proposals: listPendingProposals(),
    reasoningTranscript: DEMO_REASONING_TRANSCRIPT,
  };
}
