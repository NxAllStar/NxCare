/**
 * Mock notifications-center stub (/notifications, SCR-09 - FR-20, TASK-023).
 *
 * `patient.ts` already exports a plain `listNotifications(patientId)` used
 * by /home and /journey; this module adds the SCR-09-specific concerns
 * (pagination, type filter, mark-read) without changing that existing
 * signature and its callers. Every result stays scoped to the requesting
 * `patientId` - a notification belonging to another patient is structurally
 * absent from the result (NFR-SEC-05), never merely hidden by the UI.
 *
 * No backend exists yet - every export is marked for replacement.
 */
import { DEMO_NOTIFICATIONS } from './fixtures';
import type { Notification, NotificationType } from './types';

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export const NOTIFICATIONS_PAGE_SIZE = 3;

export interface NotificationsPage {
  items: Notification[];
  page: number;
  pageSize: number;
  totalCount: number;
}

export interface ListNotificationsOptions {
  page?: number;
  type?: NotificationType | null;
}

/** TODO: replace with a real API call (GET /patients/:id/notifications?page=&type= - FR-20). */
export async function listNotificationsPage(
  patientId: string,
  options: ListNotificationsOptions = {},
): Promise<NotificationsPage> {
  await delay(80);

  const page = options.page ?? 1;
  const scoped = DEMO_NOTIFICATIONS.filter((n) => n.patientId === patientId);
  const filtered = options.type ? scoped.filter((n) => n.notificationType === options.type) : scoped;

  const start = (page - 1) * NOTIFICATIONS_PAGE_SIZE;
  const items = filtered.slice(start, start + NOTIFICATIONS_PAGE_SIZE);

  return { items, page, pageSize: NOTIFICATIONS_PAGE_SIZE, totalCount: filtered.length };
}

/**
 * TODO: replace with a real API call (PATCH /notifications/:id - FR-20 mark
 * as read, own scope only). Returns a new object rather than mutating the
 * shared fixture, so repeated calls in tests stay deterministic.
 */
export async function markNotificationRead(notificationId: string): Promise<Notification> {
  await delay(60);
  const existing = DEMO_NOTIFICATIONS.find((n) => n.id === notificationId);
  if (!existing) {
    throw new Error(`notification-not-found:${notificationId}`);
  }
  return { ...existing, read: true };
}
