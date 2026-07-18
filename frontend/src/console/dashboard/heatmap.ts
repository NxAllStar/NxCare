/**
 * Load heatmap ticking (SCR-06, NFR-PERF-04 "real-time"). No backend/socket
 * exists yet - the "real-time" update is a mock tick through a fixed,
 * deterministic sequence of demo grids (fixtures.ts), not a random walk, so
 * the sequence is reproducible in tests and the demo alike.
 */
import { useEffect, useState } from 'react';
import { DEMO_HEATMAP_TICKS } from './fixtures';
import type { HeatmapGrid } from './types';

/** Pure: the grid shown at a given tick index, cycling through the fixed
 * demo sequence. TODO: replace with a real API call / subscription (GET or
 * WS the Coordinator's live Resource load, FR-12, NFR-PERF-04). */
export function heatmapGridAtTick(tickIndex: number): HeatmapGrid {
  const ticks = DEMO_HEATMAP_TICKS;
  return ticks[((tickIndex % ticks.length) + ticks.length) % ticks.length];
}

export const HEATMAP_TICK_COUNT = DEMO_HEATMAP_TICKS.length;

/** Pure: the grid that follows `current` in the fixed demo sequence
 * (wrapping at the end). Advances relative to whatever grid is CURRENTLY
 * shown - so a tick always continues from the loaded mock-data layer's own
 * grid, never from an index kept separately from it. An unrecognised
 * `current` (not one of the fixed demo ticks) falls back to the start of
 * the sequence rather than throwing. */
export function nextHeatmapGrid(current: HeatmapGrid): HeatmapGrid {
  const currentIndex = DEMO_HEATMAP_TICKS.findIndex((tick) => tick.tickId === current.tickId);
  return heatmapGridAtTick(currentIndex + 1);
}

/**
 * Advances on a fixed interval, mocking a real-time refresh (spec 10 SCR-06
 * "Cập nhật thời gian thực"). Seeded from `initialGrid` - the grid the
 * mock-data layer actually loaded (`DashboardData.heatmap`) - and every tick
 * updates THAT grid forward (`nextHeatmapGrid`), so the ticker is never a
 * parallel series disconnected from what was loaded.
 */
export function useHeatmapTicker(initialGrid: HeatmapGrid, intervalMs = 4000): HeatmapGrid {
  const [grid, setGrid] = useState(initialGrid);

  // Re-seed if the caller loads a different initial grid (e.g. a fresh
  // dashboard load), so the ticker never keeps ticking a stale series.
  useEffect(() => {
    setGrid(initialGrid);
  }, [initialGrid]);

  useEffect(() => {
    const id = window.setInterval(() => {
      setGrid((current) => nextHeatmapGrid(current));
    }, intervalMs);
    return () => window.clearInterval(id);
  }, [intervalMs]);

  return grid;
}
