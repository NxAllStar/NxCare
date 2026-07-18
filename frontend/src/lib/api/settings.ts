/**
 * Mock settings/preferences stub (/settings, SCR-10 - FR-15, FR-21, FR-18,
 * TASK-023).
 *
 * Spec 10 SCR-10 states table governs exactly: "Loading: -" (no such state
 * exists for this screen) - so, unlike every other mock module in this
 * directory, these functions resolve SYNCHRONOUSLY with no artificial
 * delay; the screen never has anything to show a spinner for. "Error:
 * invalid choice rejected" is modelled as `InvalidChannelError` thrown by
 * `saveNotificationChannelPreference` for a channel outside the two the
 * spec allows (in-app, SMS).
 *
 * No backend exists yet - every export is marked for replacement.
 */
import { NotificationChannel } from './types';

const ALLOWED_CHANNELS = [NotificationChannel.IN_APP, NotificationChannel.SMS] as const;
export type SettingsNotificationChannel = (typeof ALLOWED_CHANNELS)[number];

export class InvalidChannelError extends Error {
  constructor(channel: string) {
    super(`invalid-channel:${channel}`);
    this.name = 'InvalidChannelError';
  }
}

// Demo-only, in-memory per-patient preference store so a choice survives a
// remount within the same session (there is no backend to persist it to).
const channelPreferenceByPatient = new Map<string, SettingsNotificationChannel>();

/** TODO: replace with a real API call (GET /patients/:id/preferences). */
export function getNotificationChannelPreference(patientId: string): SettingsNotificationChannel {
  return channelPreferenceByPatient.get(patientId) ?? NotificationChannel.IN_APP;
}

/** TODO: replace with a real API call (PATCH /patients/:id/preferences -
 * FR-15 simulated SMS channel, FR-21). */
export function saveNotificationChannelPreference(
  patientId: string,
  channel: string,
): SettingsNotificationChannel {
  if (!(ALLOWED_CHANNELS as readonly string[]).includes(channel)) {
    throw new InvalidChannelError(channel);
  }
  const validated = channel as SettingsNotificationChannel;
  channelPreferenceByPatient.set(patientId, validated);
  return validated;
}
