/**
 * Synthetic, in-memory fixtures for the SCR-06 coordinator dashboard
 * (TASK-027). SYNTHETIC DATA ONLY - no real resource names, no real patient
 * data (agent-guardrails.md "Personal and sensitive data"). Mirrors the
 * fixtures.ts convention in `src/lib/api/` (a single seed module the mock
 * service functions read from) without importing from that patient-app
 * module tree (out of scope for this task).
 */
import type { DisruptionEvent, HeatLevel, HeatmapGrid } from './types';
import { DisruptionEventStatus } from './types';

// ---------------------------------------------------------------------------
// Load heatmap - 4 hospital areas x 4 time slots, 3 fixed demo ticks so a
// mock real-time refresh has something to cycle through (heatmap.ts).
// ---------------------------------------------------------------------------

interface DemoArea {
  id: string;
  label: string;
}

export const DEMO_AREAS: DemoArea[] = [
  { id: 'ED', label: 'Cấp cứu' },
  { id: 'IMG', label: 'Chẩn đoán hình ảnh' },
  { id: 'IM', label: 'Nội tổng quát' },
  { id: 'OR', label: 'Phòng mổ' },
];

export const DEMO_TIME_SLOTS: string[] = ['08:00', '09:00', '10:00', '11:00'];

/** Deterministic tabular value label for a load level - no randomness, so
 * ticks are reproducible in tests and the demo. */
function valueLabelForLevel(level: HeatLevel): string {
  return `${10 + level * 14}%`;
}

function buildGrid(tickId: string, generatedAt: string, levelsByArea: HeatLevel[][]): HeatmapGrid {
  const cells = DEMO_AREAS.flatMap((area, areaIndex) =>
    DEMO_TIME_SLOTS.map((timeSlot, slotIndex) => {
      const loadLevel = levelsByArea[areaIndex][slotIndex];
      return {
        id: `${area.id}:${timeSlot}`,
        areaId: area.id,
        areaLabel: area.label,
        timeSlot,
        loadLevel,
        valueLabel: valueLabelForLevel(loadLevel),
      };
    }),
  );

  return {
    tickId,
    generatedAt,
    areas: DEMO_AREAS.map((a) => a.label),
    timeSlots: DEMO_TIME_SLOTS,
    cells,
  };
}

// Rows follow DEMO_AREAS order (ED, IMG, IM, OR); columns follow
// DEMO_TIME_SLOTS order (08:00..11:00).
export const DEMO_HEATMAP_TICKS: HeatmapGrid[] = [
  buildGrid('tick-0', '2026-07-18T01:00:00.000Z', [
    [4, 6, 5, 3],
    [2, 3, 4, 3],
    [3, 3, 2, 2],
    [5, 6, 6, 4],
  ]),
  buildGrid('tick-1', '2026-07-18T01:05:00.000Z', [
    [3, 5, 4, 2],
    [2, 2, 3, 2],
    [2, 2, 2, 1],
    [4, 5, 5, 3],
  ]),
  buildGrid('tick-2', '2026-07-18T01:10:00.000Z', [
    [5, 6, 6, 4],
    [3, 4, 4, 3],
    [3, 3, 3, 2],
    [6, 6, 6, 5],
  ]),
];

// ---------------------------------------------------------------------------
// Approval queue - re-plan proposals (DisruptionEvent). Two PENDING_APPROVAL
// (in the queue) plus one AUTO_APPLIED (never surfaced here - scope lock
// item 1: fixed demo classification, not a computed N).
// ---------------------------------------------------------------------------

export const DEMO_DISRUPTION_EVENTS: DisruptionEvent[] = [
  {
    id: 'disruption-0001',
    status: DisruptionEventStatus.PENDING_APPROVAL,
    blastRadius: 14,
    areaLabel: 'Phòng mổ',
    triggeredAt: '2026-07-18T01:02:00.000Z',
    options: [
      {
        id: 'option-0001-a',
        label: 'Chuyển phòng mổ 2 sang phòng mổ 4',
        description: 'Ít ảnh hưởng nhất tới lịch của các bệnh nhân khác trong ca sáng.',
      },
      {
        id: 'option-0001-b',
        label: 'Dời khung giờ ca mổ sang 13:30',
        description: 'Giữ nguyên phòng nhưng dời lùi 90 phút, ảnh hưởng 3 ca tiếp theo.',
      },
    ],
    aiReason:
      'Phát hiện phòng mổ 2 trễ 25 phút do ca trước kéo dài. Phương án đổi phòng ảnh hưởng tới 14 ' +
      'bệnh nhân liên quan (trực tiếp và gián tiếp), vượt ngưỡng cần duyệt nên chuyển vào hàng chờ.',
  },
  {
    id: 'disruption-0002',
    status: DisruptionEventStatus.PENDING_APPROVAL,
    blastRadius: 9,
    areaLabel: 'Chẩn đoán hình ảnh',
    triggeredAt: '2026-07-18T01:04:00.000Z',
    options: [
      {
        id: 'option-0002-a',
        label: 'Chuyển 9 ca CT sang máy CT dự phòng',
        description: 'Máy CT chính bảo trì đột xuất, máy dự phòng còn chỗ trống.',
      },
    ],
    aiReason:
      'Máy CT chính báo lỗi đột xuất lúc 08:40. Chuyển toàn bộ 9 ca đang chờ sang máy dự phòng để ' +
      'tránh dồn ca dồn đợi quá 45 phút; ảnh hưởng 9 bệnh nhân nên vượt ngưỡng cần duyệt.',
  },
  {
    id: 'disruption-0003',
    status: DisruptionEventStatus.AUTO_APPLIED,
    blastRadius: 2,
    areaLabel: 'Nội tổng quát',
    triggeredAt: '2026-07-18T00:58:00.000Z',
    options: [
      {
        id: 'option-0003-a',
        label: 'Đổi 2 bệnh nhân sang bác sĩ trực cùng chuyên khoa',
        description: 'Bác sĩ phụ trách nghỉ đột xuất 30 phút.',
      },
    ],
    aiReason:
      'Ảnh hưởng 2 bệnh nhân, dưới ngưỡng cần duyệt nên áp dụng tự động; không xuất hiện trong hàng ' +
      'chờ duyệt của màn hình này.',
  },
];

/** One reasoning transcript the Disruption Agent streams while it works out
 * the proposals above (calm, readable chain-of-thought - spec 10 "signature
 * surfaces"). Rendered only as plain text, never as HTML (frontend.md). */
export const DEMO_REASONING_TRANSCRIPT =
  'Đang theo dõi tải tại các khu vực. Phát hiện phòng mổ 2 trễ lịch do ca trước kéo dài 25 phút. ' +
  'Đánh giá 2 phương án: đổi phòng hoặc dời khung giờ. Ước tính số bệnh nhân liên quan cho từng ' +
  'phương án. Phương án đổi phòng ảnh hưởng ít hơn nhưng vượt ngưỡng cần duyệt, nên đưa vào hàng ' +
  'chờ của điều phối viên thay vì tự áp dụng. Song song, máy CT chính báo lỗi; chuyển các ca đang ' +
  'chờ sang máy dự phòng cũng vượt ngưỡng nên đưa vào hàng chờ. Trường hợp đổi bác sĩ trực nội ' +
  'tổng quát chỉ ảnh hưởng 2 bệnh nhân, dưới ngưỡng nên áp dụng ngay không cần duyệt.';
