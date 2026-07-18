/**
 * NotificationsPage - SCR-09 Notifications center (FR-20, TASK-023).
 *
 * Proves:
 * - Loading: a status indicator while the first page is fetched.
 * - Empty: "no notifications yet" when the patient has none.
 * - Success: read/unread render distinguishably, own-scope only (another
 *   patient's notification never appears).
 * - Filter by type: selecting a type narrows the list to that type.
 * - Mark-read: clicking the control flips that item to read.
 * - Pagination: a second page is reachable and shows different items.
 * - Spec-10 SCR-09 has NO Model-assisted content row: no AIChip anywhere,
 *   even though the underlying fixture has an `aiGenerated: true` entry.
 * - Error state renders through ScreenState.
 */
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { AuthProvider } from '@/auth/AuthContext';
import { I18nProvider } from '@/i18n';
import * as notificationsApi from '@/lib/api/notifications';
import { NotificationsPage } from './NotificationsPage';

function seedSession(patientId: 'patient-0001' | 'patient-0002' = 'patient-0001') {
  const patients = {
    'patient-0001': {
      id: 'patient-0001',
      fullName: 'Nguyen Van A',
      phone: null,
      patientCode: 'BN-000123',
      priorityLevel: 'ROUTINE',
      createdAt: '2026-01-01T00:00:00.000Z',
    },
    'patient-0002': {
      id: 'patient-0002',
      fullName: 'Tran Thi B',
      phone: null,
      patientCode: 'BN-000456',
      priorityLevel: 'ROUTINE',
      createdAt: '2026-01-01T00:00:00.000Z',
    },
  };
  window.sessionStorage.setItem(
    'vaic.session',
    JSON.stringify({ patient: patients[patientId], role: 'patient', issuedAt: '2026-07-18T00:00:00.000Z' }),
  );
}

function renderPage() {
  return render(
    <I18nProvider>
      <AuthProvider>
        <MemoryRouter initialEntries={['/notifications']}>
          <NotificationsPage />
        </MemoryRouter>
      </AuthProvider>
    </I18nProvider>,
  );
}

describe('NotificationsPage (SCR-09 Notifications center)', () => {
  it('shows a loading indicator while the first page is being fetched', () => {
    seedSession('patient-0001');
    renderPage();
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('shows the empty state when the patient has no notifications', async () => {
    seedSession('patient-0001');
    vi.spyOn(notificationsApi, 'listNotificationsPage').mockResolvedValueOnce({
      items: [],
      page: 1,
      pageSize: 3,
      totalCount: 0,
    });
    renderPage();
    expect(await screen.findByText('Chưa có thông báo')).toBeInTheDocument();
  });

  it('renders own-scope notifications only, distinguishing read from unread', async () => {
    seedSession('patient-0001');
    renderPage();

    await screen.findByText('Buoi kham cua ban da duoc xac nhan luc 08:30 ngay mai.');
    // Own-scope only: patient-0002's notification never appears.
    expect(screen.queryByText('Lich kham cua ban da duoc ghi nhan.')).not.toBeInTheDocument();

    const items = screen.getAllByTestId('notification-item');
    expect(items.length).toBeGreaterThan(0);
    const readItem = items.find((el) => within(el).queryByText('Đã đọc'));
    const unreadItem = items.find((el) => within(el).queryByText('Chưa đọc'));
    expect(readItem).toBeTruthy();
    expect(unreadItem).toBeTruthy();
  });

  it('never renders an AI-content chip, even though an entry is AI-generated', async () => {
    seedSession('patient-0001');
    renderPage();

    await screen.findByText('Buoi kham cua ban da duoc xac nhan luc 08:30 ngay mai.');
    expect(screen.queryByTestId('ai-chip')).not.toBeInTheDocument();
  });

  it('filters the list by notification type', async () => {
    const user = userEvent.setup();
    seedSession('patient-0001');
    renderPage();

    await screen.findByText('Buoi kham cua ban da duoc xac nhan luc 08:30 ngay mai.');
    await user.click(screen.getByRole('button', { name: 'Viện phí' }));

    await screen.findByText('Hoa don cua ban da san sang, vui long xem trong muc Vien phi.');
    expect(screen.queryByText('Buoi kham cua ban da duoc xac nhan luc 08:30 ngay mai.')).not.toBeInTheDocument();
  });

  it('marks a notification as read', async () => {
    const user = userEvent.setup();
    seedSession('patient-0001');
    renderPage();

    await screen.findByText('Ket qua xet nghiem mau cua ban da co.');
    const item = screen.getByText('Ket qua xet nghiem mau cua ban da co.').closest('[data-testid="notification-item"]');
    expect(item).not.toBeNull();
    await user.click(within(item as HTMLElement).getByRole('button', { name: 'Đánh dấu đã đọc' }));

    expect(await within(item as HTMLElement).findByText('Đã đọc')).toBeInTheDocument();
  });

  it('paginates to a second page of notifications', async () => {
    const user = userEvent.setup();
    seedSession('patient-0001');
    renderPage();

    await screen.findByText('Buoi kham cua ban da duoc xac nhan luc 08:30 ngay mai.');
    await user.click(screen.getByRole('button', { name: 'Trang sau' }));

    await screen.findByText('Hoa don cua ban da san sang, vui long xem trong muc Vien phi.');
    expect(screen.queryByText('Buoi kham cua ban da duoc xac nhan luc 08:30 ngay mai.')).not.toBeInTheDocument();
  });

  it('shows the error state when the fetch fails', async () => {
    seedSession('patient-0001');
    vi.spyOn(notificationsApi, 'listNotificationsPage').mockRejectedValueOnce(new Error('down'));
    renderPage();
    expect(await screen.findByRole('alert')).toBeInTheDocument();
  });
});
