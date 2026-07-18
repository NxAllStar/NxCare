/**
 * Proves HeatmapPane renders and re-scales on the mock real-time tick
 * (TASK-027 acceptance criteria).
 */
import { act, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { I18nProvider } from '@/i18n';
import { DEMO_HEATMAP_TICKS } from '../fixtures';
import type { HeatmapGrid } from '../types';
import { HeatmapPane } from './HeatmapPane';

function renderPane(intervalMs = 1000, initialGrid: HeatmapGrid = DEMO_HEATMAP_TICKS[0]) {
  return render(
    <I18nProvider>
      <HeatmapPane initialGrid={initialGrid} tickIntervalMs={intervalMs} />
    </I18nProvider>,
  );
}

describe('HeatmapPane (SCR-06 load heatmap)', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders the heatmap with tick-0 values and a title', () => {
    renderPane();
    expect(screen.getByText('Bản đồ tải')).toBeInTheDocument();
    expect(screen.getByTestId('heatmap')).toBeInTheDocument();
    const tick0Cell = DEMO_HEATMAP_TICKS[0].cells[0];
    expect(screen.getByTestId(`heatmap-cell-${tick0Cell.id}`)).toHaveTextContent(tick0Cell.valueLabel);
  });

  it('re-scales to the next demo grid after the tick interval elapses', () => {
    renderPane(1000);
    const cellId = DEMO_HEATMAP_TICKS[0].cells[0].id;
    const tick1Value = DEMO_HEATMAP_TICKS[1].cells.find((c) => c.id === cellId)!.valueLabel;

    act(() => {
      vi.advanceTimersByTime(1000);
    });

    expect(screen.getByTestId(`heatmap-cell-${cellId}`)).toHaveTextContent(tick1Value);
  });

  it('renders from the initial grid supplied by the caller - consumes the loaded mock-data layer as the source of truth, not an internal default', () => {
    renderPane(1000, DEMO_HEATMAP_TICKS[1]);
    const cell = DEMO_HEATMAP_TICKS[1].cells[0];
    expect(screen.getByTestId(`heatmap-cell-${cell.id}`)).toHaveTextContent(cell.valueLabel);
  });
});
