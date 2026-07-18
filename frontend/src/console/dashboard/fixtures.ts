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
  { id: 'ED', label: 'Cap cuu' },
  { id: 'IMG', label: 'Chan doan hinh anh' },
  { id: 'IM', label: 'Noi tong quat' },
  { id: 'OR', label: 'Phong mo' },
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
    areaLabel: 'Phong mo',
    triggeredAt: '2026-07-18T01:02:00.000Z',
    options: [
      {
        id: 'option-0001-a',
        label: 'Chuyen phong mo 2 sang phong mo 4',
        description: 'It anh huong nhat toi lich cua cac benh nhan khac trong ca sang.',
      },
      {
        id: 'option-0001-b',
        label: 'Doi khung gio ca mo sang 13:30',
        description: 'Giu nguyen phong nhung day lui 90 phut, anh huong 3 ca tiep theo.',
      },
    ],
    aiReason:
      'Phat hien phong mo 2 tre 25 phut do ca truoc keo dai. Phuong an doi phong anh huong toi 14 ' +
      'benh nhan lien quan (truc tiep va gian tiep), vuot nguong can duyet nen chuyen vao hang cho.',
  },
  {
    id: 'disruption-0002',
    status: DisruptionEventStatus.PENDING_APPROVAL,
    blastRadius: 9,
    areaLabel: 'Chan doan hinh anh',
    triggeredAt: '2026-07-18T01:04:00.000Z',
    options: [
      {
        id: 'option-0002-a',
        label: 'Chuyen 9 ca CT sang may CT du phong',
        description: 'May CT chinh bao tri dot xuat, may du phong con cho trong.',
      },
    ],
    aiReason:
      'May CT chinh bao loi dot xuat luc 08:40. Chuyen toan bo 9 ca dang cho sang may du phong de ' +
      'tranh don ca don doi qua 45 phut; anh huong 9 benh nhan nen vuot nguong can duyet.',
  },
  {
    id: 'disruption-0003',
    status: DisruptionEventStatus.AUTO_APPLIED,
    blastRadius: 2,
    areaLabel: 'Noi tong quat',
    triggeredAt: '2026-07-18T00:58:00.000Z',
    options: [
      {
        id: 'option-0003-a',
        label: 'Doi 2 benh nhan sang bac si truc cung chuyen khoa',
        description: 'Bac si phu trach nghi dot xuat 30 phut.',
      },
    ],
    aiReason:
      'Anh huong 2 benh nhan, duoi nguong can duyet nen ap dung tu dong; khong xuat hien trong hang ' +
      'cho duyet cua man hinh nay.',
  },
];

/** One reasoning transcript the Disruption Agent streams while it works out
 * the proposals above (calm, readable chain-of-thought - spec 10 "signature
 * surfaces"). Rendered only as plain text, never as HTML (frontend.md). */
export const DEMO_REASONING_TRANSCRIPT =
  'Dang theo doi tai cac khu vuc. Phat hien phong mo 2 tre lich do ca truoc keo dai 25 phut. ' +
  'Danh gia 2 phuong an: doi phong hoac doi khung gio. Uoc tinh so benh nhan lien quan cho tung ' +
  'phuong an. Phuong an doi phong anh huong it hon nhung vuot nguong can duyet, nen dua vao hang ' +
  'cho cua dieu phoi vien thay vi tu ap dung. Song song, may CT chinh bao loi; chuyen cac ca dang ' +
  'cho sang may du phong cung vuot nguong nen dua vao hang cho. Truong hop doi bac si truc noi ' +
  'tong quat chi anh huong 2 benh nhan, duoi nguong nen ap dung ngay khong can duyet.';
