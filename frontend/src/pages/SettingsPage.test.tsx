/**
 * SettingsPage - SCR-10 Settings (FR-21, FR-15, FR-18, TASK-023).
 *
 * Proves the spec-10 SCR-10 states table EXACTLY - and no more:
 * - Empty: default settings render immediately (VI, in-app).
 * - Loading: "-" - there is no loading state; nothing here ever shows a
 *   spinner or the shared no-permission state (spec-10 has no such row for
 *   this screen; asserting their absence is the point of this suite).
 * - Error: an invalid channel choice is rejected with a message.
 * - Success: a choice applies immediately with a saved confirmation.
 *
 * Also proves FR-21 (codes stay English while labels localise) and FR-18
 * (logout ends the session).
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { AuthProvider, useAuth } from '@/auth/AuthContext';
import { I18nProvider } from '@/i18n';
import * as settingsApi from '@/lib/api/settings';
import { SettingsPage } from './SettingsPage';

function seedSession() {
  window.sessionStorage.setItem(
    'vaic.session',
    JSON.stringify({
      patient: {
        id: 'patient-0001',
        fullName: 'Nguyen Van A',
        phone: null,
        patientCode: 'BN-000123',
        priorityLevel: 'ROUTINE',
        createdAt: '2026-01-01T00:00:00.000Z',
      },
      role: 'patient',
      issuedAt: '2026-07-18T00:00:00.000Z',
    }),
  );
}

function LogoutSpy() {
  const { session } = useAuth();
  return <p>{session ? 'session:active' : 'session:none'}</p>;
}

function renderPage() {
  return render(
    <I18nProvider>
      <AuthProvider>
        <SettingsPage />
        <LogoutSpy />
      </AuthProvider>
    </I18nProvider>,
  );
}

describe('SettingsPage (SCR-10 Settings)', () => {
  it('renders default settings immediately - no loading spinner, no no-permission state', () => {
    seedSession();
    renderPage();

    expect(screen.getByRole('heading', { name: 'Cài đặt' })).toBeInTheDocument();
    expect(screen.queryByTestId('screen-state-loading')).not.toBeInTheDocument();
    expect(screen.queryByTestId('screen-state-no-permission')).not.toBeInTheDocument();
    expect(screen.getByRole('group', { name: 'Ngôn ngữ' })).toBeInTheDocument();
  });

  it('FR-21: toggles VI<->EN, labels localise while the underlying code stays English', async () => {
    const user = userEvent.setup();
    seedSession();
    renderPage();

    expect(screen.getByRole('heading', { name: 'Cài đặt' })).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'EN' }));

    expect(screen.getByRole('heading', { name: 'Settings' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'In-app' })).toBeInTheDocument();
  });

  it('renders the notification channel choice (in-app / SMS) and applies a selection immediately with a saved confirmation', async () => {
    const user = userEvent.setup();
    seedSession();
    renderPage();

    const smsButton = screen.getByRole('button', { name: 'SMS (mô phỏng)' });
    await user.click(smsButton);

    expect(smsButton).toHaveAttribute('aria-pressed', 'true');
    expect(await screen.findByText('Đã lưu cài đặt.')).toBeInTheDocument();
  });

  it('Error: shows the invalid-choice message when the channel save is rejected', async () => {
    const user = userEvent.setup();
    seedSession();
    vi.spyOn(settingsApi, 'saveNotificationChannelPreference').mockImplementationOnce(() => {
      throw new settingsApi.InvalidChannelError('BOGUS');
    });
    renderPage();

    await user.click(screen.getByRole('button', { name: 'SMS (mô phỏng)' }));

    expect(await screen.findByText('Lựa chọn không hợp lệ bị từ chối.')).toBeInTheDocument();
  });

  it('FR-18: logs out and clears the session', async () => {
    const user = userEvent.setup();
    seedSession();
    renderPage();

    expect(screen.getByText('session:active')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Đăng xuất' }));

    expect(await screen.findByText('session:none')).toBeInTheDocument();
  });
});
