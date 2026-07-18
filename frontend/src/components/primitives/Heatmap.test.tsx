/**
 * Heatmap - proves the accessibility contract (frontend.md, WCAG 2.1 AA):
 * colour is never the sole signal (a label AND a value accompany every
 * cell), cells are keyboard-reachable, and re-rendering with a different
 * `cells` prop re-scales the grid (SCR-06 "updates on a mock real-time
 * tick" - the ticking itself lives in console/dashboard/heatmap.ts and is
 * proven there; this only proves the presentational primitive reflects new
 * props).
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { Heatmap, type HeatmapCellData } from './Heatmap';

const ROWS = ['Cap cuu', 'Noi tong quat'];
const COLUMNS = ['08:00', '09:00'];

function cells(overrides?: Partial<Record<string, HeatmapCellData>>): HeatmapCellData[] {
  const base: HeatmapCellData[] = [
    { id: 'ED:08:00', rowLabel: 'Cap cuu', columnLabel: '08:00', level: 6, levelLabel: 'Cao', valueLabel: '94%' },
    { id: 'ED:09:00', rowLabel: 'Cap cuu', columnLabel: '09:00', level: 2, levelLabel: 'Thap', valueLabel: '38%' },
    {
      id: 'IM:08:00',
      rowLabel: 'Noi tong quat',
      columnLabel: '08:00',
      level: 3,
      levelLabel: 'Trung binh',
      valueLabel: '52%',
    },
    {
      id: 'IM:09:00',
      rowLabel: 'Noi tong quat',
      columnLabel: '09:00',
      level: 1,
      levelLabel: 'Thap',
      valueLabel: '24%',
    },
  ];
  return base.map((c) => ({ ...c, ...(overrides?.[c.id] ?? {}) }));
}

describe('Heatmap (SCR-06 load heatmap, WCAG 2.1 AA)', () => {
  it('renders a semantic table with a caption, row headers, and column headers', () => {
    render(<Heatmap rows={ROWS} columns={COLUMNS} cells={cells()} caption="Load by area" />);
    expect(screen.getByTestId('heatmap')).toBeInTheDocument();
    expect(screen.getByText('Load by area')).toBeInTheDocument();
    expect(screen.getByRole('columnheader', { name: '08:00' })).toBeInTheDocument();
    expect(screen.getByRole('rowheader', { name: 'Cap cuu' })).toBeInTheDocument();
  });

  it('pairs every cell with a text label AND a tabular value - colour is never the sole signal', () => {
    render(<Heatmap rows={ROWS} columns={COLUMNS} cells={cells()} caption="Load by area" />);
    const cell = screen.getByTestId('heatmap-cell-ED:08:00');
    expect(cell).toHaveTextContent('Cao');
    expect(cell).toHaveTextContent('94%');
    expect(cell).toHaveAccessibleName('Cap cuu, 08:00: Cao, 94%');
  });

  it('every cell is a real button, reachable and operable by keyboard', async () => {
    const user = userEvent.setup();
    render(<Heatmap rows={ROWS} columns={COLUMNS} cells={cells()} caption="Load by area" />);
    const cell = screen.getByTestId('heatmap-cell-ED:08:00');
    expect(cell.tagName).toBe('BUTTON');

    await user.tab();
    expect(cell).toHaveFocus();
  });

  it('re-scales when given a different cells prop for the same cell id (mock real-time tick)', () => {
    const { rerender } = render(<Heatmap rows={ROWS} columns={COLUMNS} cells={cells()} caption="Load by area" />);
    expect(screen.getByTestId('heatmap-cell-ED:08:00')).toHaveTextContent('94%');

    const nextTick = cells().map((c) => (c.id === 'ED:08:00' ? { ...c, level: 1 as const, levelLabel: 'Thap', valueLabel: '24%' } : c));
    rerender(<Heatmap rows={ROWS} columns={COLUMNS} cells={nextTick} caption="Load by area" />);

    expect(screen.getByTestId('heatmap-cell-ED:08:00')).toHaveTextContent('24%');
    expect(screen.getByTestId('heatmap-cell-ED:08:00')).not.toHaveTextContent('94%');
  });
});
