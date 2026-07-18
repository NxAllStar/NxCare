/**
 * Mock Journey/Intake Agent assistant chat stub (/assistant FAB - FR-06,
 * TASK-022). No backend/model exists yet.
 *
 * Security (AC-01.3/AC-06.3, same rule as intake.ts): the patient's `text`
 * is data. This module never inspects it for "commands" and never lets it
 * change any status - it only echoes a scripted, clearly AI-labelled reply.
 */
import type { ChatMessage } from './types';

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

let counter = 0;
function nextId(): string {
  counter += 1;
  return `assistant-msg-${counter}`;
}

export const QUICK_QUESTIONS = [
  'Toi con phai cho bao lau?',
  'Toi doi qua co an truoc duoc khong?',
  'Vi sao lo trinh doi thu tu?',
] as const;

/** TODO: replace with a real API call (Journey Agent turn - FR-06, FR-11). */
export async function sendAssistantMessage(patientText: string): Promise<ChatMessage> {
  await delay(300);

  const trimmed = patientText.trim();
  const lower = trimmed.toLowerCase();

  let text =
    'Minh la tro ly AI, luon di kem ban trong lo trinh kham. Ban co the hoi minh ve thoi gian cho, thu tu cac buoc, hoac cac dieu kien nhu nhin an.';

  if (lower.includes('bao lau') || lower.includes('cho')) {
    text = 'Theo lo trinh hien tai, buoc tiep theo cua ban con khoang ~10-15 phut nua - so lieu la uoc tinh, khong phai con so cung.';
  } else if (lower.includes('an truoc') || lower.includes('nhin an')) {
    text = 'Mau cua ban da duoc lay roi nen an nhe truoc gio la duoc; minh se giu cho buoi sieu am tiep theo.';
  } else if (lower.includes('vi sao') || lower.includes('doi thu tu')) {
    text = 'Lo trinh vua doi thu tu vi co mot ca cap cuu duoc uu tien truoc tai phong xet nghiem, du kien them khoang 8 phut.';
  }

  return {
    id: nextId(),
    sender: 'agent',
    text,
    createdAt: new Date().toISOString(),
    aiGenerated: true,
  };
}
