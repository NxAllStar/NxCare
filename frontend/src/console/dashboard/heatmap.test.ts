/**
 * Proves the heatmap re-scales on a mock real-time tick (TASK-027
 * acceptance criteria: "heatmap renders and re-scales on tick").
 */
import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { DEMO_HEATMAP_TICKS } from './fixtures';
import { HEATMAP_TICK_COUNT, heatmapGridAtTick, useHeatmapTicker } from './heatmap';

describe('heatmapGridAtTick (pure)', () => {
  it('returns the fixed demo grid for tick 0', () => {
    expect(heatmapGridAtTick(0)).toBe(DEMO_HEATMAP_TICKS[0]);
  });

  it('cycles through the demo sequence, wrapping at the end', () => {
    expect(heatmapGridAtTick(HEATMAP_TICK_COUNT)).toBe(DEMO_HEATMAP_TICKS[0]);
    expect(heatmapGridAtTick(HEATMAP_TICK_COUNT + 1)).toBe(DEMO_HEATMAP_TICKS[1]);
  });

  it('a later tick shows different load values for at least one cell (a real re-scale, not a static grid)', () => {
    const tick0 = heatmapGridAtTick(0);
    const tick1 = heatmapGridAtTick(1);
    const cellId = tick0.cells[0].id;
    const before = tick0.cells.find((c) => c.id === cellId)!;
    const after = tick1.cells.find((c) => c.id === cellId)!;
    expect(after.loadLevel).not.toBe(before.loadLevel);
    expect(after.valueLabel).not.toBe(before.valueLabel);
  });
});

describe('useHeatmapTicker (mock real-time refresh, seeded from the loaded grid as source of truth)', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('starts at the caller-supplied initial grid (the loaded mock-data layer) and advances to the next demo grid after the interval elapses', () => {
    const { result } = renderHook(() => useHeatmapTicker(DEMO_HEATMAP_TICKS[0], 1000));
    expect(result.current).toBe(DEMO_HEATMAP_TICKS[0]);

    act(() => {
      vi.advanceTimersByTime(1000);
    });
    expect(result.current).toBe(DEMO_HEATMAP_TICKS[1]);

    act(() => {
      vi.advanceTimersByTime(1000);
    });
    expect(result.current).toBe(DEMO_HEATMAP_TICKS[2]);
  });

  it('ticks forward from the loaded grid it was given, not always from tick 0 (source of truth, not a parallel disconnected series)', () => {
    const { result } = renderHook(() => useHeatmapTicker(DEMO_HEATMAP_TICKS[1], 1000));
    expect(result.current).toBe(DEMO_HEATMAP_TICKS[1]);

    act(() => {
      vi.advanceTimersByTime(1000);
    });
    expect(result.current).toBe(DEMO_HEATMAP_TICKS[2]);
  });

  it('clears its interval on unmount (no leaked timer)', () => {
    const { unmount } = renderHook(() => useHeatmapTicker(DEMO_HEATMAP_TICKS[0], 1000));
    const clearSpy = vi.spyOn(window, 'clearInterval');
    unmount();
    expect(clearSpy).toHaveBeenCalled();
  });
});
