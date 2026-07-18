/**
 * Heatmap - a generic rows x columns sequential load grid (spec 10 "Visual
 * design direction": load heatmap uses a sequential green -> amber -> red
 * scale; a signature surface of the coordinator dashboard, SCR-06).
 *
 * Accessibility (frontend.md, WCAG 2.1 AA): every cell pairs its colour with
 * a text label AND a tabular-number value, so colour is never the sole
 * carrier of meaning; each cell is a real `<button>` inside a semantic
 * `<table>`, so it is reachable and operable by keyboard with a visible
 * focus ring and has its own accessible name (area, time slot, level,
 * value) for a screen-reader user who cannot see the colour at all.
 *
 * Token-only: cell fill/dot colours come from the `heat-1`..`heat-6` design
 * tokens (tailwind.config.ts), never a hardcoded hex (frontend.md).
 */
import { cn } from '@/lib/utils';

export type HeatLevel = 1 | 2 | 3 | 4 | 5 | 6;

export interface HeatmapCellData {
  id: string;
  rowLabel: string;
  columnLabel: string;
  level: HeatLevel;
  /** Localised textual label for the level (e.g. "Cao" / "High") - resolved
   * by the caller so this primitive stays free of i18n-key coupling to any
   * one screen's vocabulary. */
  levelLabel: string;
  /** Tabular-number display value, e.g. "82%". */
  valueLabel: string;
}

export interface HeatmapProps {
  rows: string[];
  columns: string[];
  cells: HeatmapCellData[];
  /** Accessible table caption - required, not optional, so the grid is
   * never announced without context. */
  caption: string;
  className?: string;
}

const DOT_CLASS: Record<HeatLevel, string> = {
  1: 'bg-heat-1',
  2: 'bg-heat-2',
  3: 'bg-heat-3',
  4: 'bg-heat-4',
  5: 'bg-heat-5',
  6: 'bg-heat-6',
};

const TINT_CLASS: Record<HeatLevel, string> = {
  1: 'bg-heat-1/10',
  2: 'bg-heat-2/10',
  3: 'bg-heat-3/10',
  4: 'bg-heat-4/10',
  5: 'bg-heat-5/10',
  6: 'bg-heat-6/10',
};

export function Heatmap({ rows, columns, cells, caption, className }: HeatmapProps) {
  const cellByKey = new Map(cells.map((cell) => [`${cell.rowLabel} ${cell.columnLabel}`, cell]));

  return (
    <table data-testid="heatmap" className={cn('w-full border-separate border-spacing-1.5', className)}>
      <caption className="mb-2.5 text-left text-sm font-bold uppercase tracking-[0.04em] text-neutral-400">
        {caption}
      </caption>
      <thead>
        <tr>
          <th scope="col" className="w-0" />
          {columns.map((column) => (
            <th
              key={column}
              scope="col"
              className="whitespace-nowrap px-1 pb-1.5 text-left text-sm font-semibold text-muted-foreground"
            >
              {column}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row}>
            <th scope="row" className="whitespace-nowrap pr-3 text-left text-sm font-semibold text-foreground">
              {row}
            </th>
            {columns.map((column) => {
              const cell = cellByKey.get(`${row} ${column}`);
              if (!cell) return <td key={column} />;
              return (
                <td key={column} className="p-0">
                  <button
                    type="button"
                    data-testid={`heatmap-cell-${cell.id}`}
                    aria-label={`${row}, ${column}: ${cell.levelLabel}, ${cell.valueLabel}`}
                    className={cn(
                      'flex w-full min-w-[92px] flex-col items-start gap-1.5 rounded-xl p-3 text-left',
                      'transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
                      'focus-visible:ring-offset-2 focus-visible:ring-offset-background',
                      TINT_CLASS[cell.level],
                    )}
                  >
                    <span className="flex items-center gap-1.5">
                      <span aria-hidden="true" className={cn('h-2.5 w-2.5 shrink-0 rounded-full', DOT_CLASS[cell.level])} />
                      <span className="whitespace-nowrap text-sm font-semibold text-foreground">{cell.levelLabel}</span>
                    </span>
                    <span className="font-mono text-sm font-bold tabular-nums text-foreground">
                      {cell.valueLabel}
                    </span>
                  </button>
                </td>
              );
            })}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
