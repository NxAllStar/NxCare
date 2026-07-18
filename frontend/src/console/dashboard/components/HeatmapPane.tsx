/**
 * HeatmapPane - SCR-06 "Load heatmap by area (real-time)" pane. Consumes
 * the heatmap grid loaded from the mock-data layer (`DashboardData.heatmap`,
 * the caller's `initialGrid`) as the source of truth, and wires it into the
 * mock real-time ticker (heatmap.ts), which advances THAT grid forward on
 * each tick rather than running a parallel series of its own. Resolves each
 * cell's level into a localised label (NFR-USE-03: codes stay in
 * `heatmap.ts`, only the label text is translated here).
 */
import { Card, Heatmap, SectionLabel, type HeatmapCellData } from '@/components/primitives';
import { useI18n, type DictKey } from '@/i18n';
import { useHeatmapTicker } from '../heatmap';
import type { HeatmapGrid } from '../types';

export interface HeatmapPaneProps {
  /** The grid loaded from the mock-data layer (`DashboardData.heatmap`) -
   * the source of truth the ticker advances forward from. */
  initialGrid: HeatmapGrid;
  tickIntervalMs?: number;
}

export function HeatmapPane({ initialGrid, tickIntervalMs = 4000 }: HeatmapPaneProps) {
  const { t } = useI18n();
  const grid = useHeatmapTicker(initialGrid, tickIntervalMs);

  const cells: HeatmapCellData[] = grid.cells.map((cell) => ({
    id: cell.id,
    rowLabel: cell.areaLabel,
    columnLabel: cell.timeSlot,
    level: cell.loadLevel,
    levelLabel: t(`console.dashboard.heatmap.level.${cell.loadLevel}` as DictKey),
    valueLabel: cell.valueLabel,
  }));

  return (
    <Card className="flex h-full flex-col gap-3 p-5" data-testid="heatmap-pane">
      <SectionLabel>{t('console.dashboard.heatmap.title')}</SectionLabel>
      <Heatmap
        rows={grid.areas}
        columns={grid.timeSlots}
        cells={cells}
        caption={t('console.dashboard.heatmap.caption')}
      />
    </Card>
  );
}
