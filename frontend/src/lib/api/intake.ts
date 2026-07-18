/**
 * Mock Intake Agent chat stub (SCR-01, FR-01, FR-02, BF-05 - TASK-022).
 *
 * No backend/model exists yet. This module simulates one chat turn: it
 * echoes back a scripted agent reply, ranks a couple of mock slot
 * suggestions, and flags a suspected emergency from a fixed keyword list -
 * a stand-in for the real Intake Agent's classification.
 *
 * Security (AC-01.3/AC-06.3): the patient's `text` is NEVER inspected for
 * "commands" beyond the emergency-keyword check below, and is always
 * returned unchanged for the caller to render as data. Nothing in this
 * module executes an instruction found inside chat text.
 */
import type { ChatMessage, IntakeTurnResult, RankedSlotSuggestion } from './types';

// Deliberately narrow, deterministic keyword list - a stand-in for the real
// classifier. Matches BF-05's escalation intent only; not a diagnosis.
const EMERGENCY_KEYWORDS = [
  'dau nguc du doi',
  'kho tho',
  'ngat xiu',
  'chay mau nhieu',
  'chest pain',
  'cannot breathe',
  'severe bleeding',
];

function normalize(text: string): string {
  return text
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, ''); // strip Vietnamese diacritics for a simple keyword match
}

function detectEmergency(text: string): boolean {
  const normalized = normalize(text);
  return EMERGENCY_KEYWORDS.some((kw) => normalized.includes(normalize(kw)));
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

let messageCounter = 0;
function nextId(prefix: string): string {
  messageCounter += 1;
  return `${prefix}-${messageCounter}`;
}

const MOCK_SLOT_SUGGESTIONS: RankedSlotSuggestionSeed[] = [
  { specialty: 'Noi tong quat', startOffsetMin: 45, etaLabel: '~10:15, it dong', loadLevel: 'low' },
  { specialty: 'Noi tong quat', startOffsetMin: 90, etaLabel: '~10:45-11:00', loadLevel: 'medium' },
];

interface RankedSlotSuggestionSeed {
  specialty: string;
  startOffsetMin: number;
  etaLabel: string;
  loadLevel: 'low' | 'medium' | 'high';
}

/** TODO: replace with a real API call (Intake Agent turn - FR-01, FR-02, BF-05). */
export async function sendIntakeMessage(patientText: string): Promise<IntakeTurnResult> {
  await delay(300);

  const emergencySuspected = detectEmergency(patientText);
  const now = new Date().toISOString();

  if (emergencySuspected) {
    return {
      reply: {
        id: nextId('intake-msg'),
        sender: 'agent',
        text:
          'Trieu chung ban mo ta co the la tinh huong khan cap. Vui long lien he nhan vien y te ngay hoac goi 115 - minh chua the xep lich thuong quy trong truong hop nay.',
        createdAt: now,
        aiGenerated: true,
      },
      suggestedSlots: [],
      emergencySuspected: true,
    };
  }

  const suggestedSlots: RankedSlotSuggestion[] = MOCK_SLOT_SUGGESTIONS.map((seed, index) => ({
    slotId: `intake-slot-${index}`,
    specialty: seed.specialty,
    start: new Date(Date.now() + seed.startOffsetMin * 60_000).toISOString(),
    etaLabel: seed.etaLabel,
    loadLevel: seed.loadLevel,
  }));

  const reply: ChatMessage = {
    id: nextId('intake-msg'),
    sender: 'agent',
    text: 'Cam on ban da mo ta trieu chung. Day la goi y dinh tuyen, khong phai chan doan - minh de xuat vai khung gio it dong ben duoi.',
    createdAt: now,
    aiGenerated: true,
  };

  return { reply, suggestedSlots, emergencySuspected: false };
}
