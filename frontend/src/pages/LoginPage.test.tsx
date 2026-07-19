/**
 * LoginPage - SCR-08 Login (patient path), FR-18.
 *
 * Proves:
 * - Empty state: the login form renders with no prefilled patient code (spec 10 SCR-08 States > Empty).
 * - Success: authenticates a demo patient and routes to the patient home (AC "Success").
 * - Error: invalid credentials show one generic message, IDENTICAL whether
 *   the patient code does not exist or the password is wrong - no account
 *   enumeration (spec 10 SCR-08 States > Error).
 * - The VI/EN language toggle is present on this screen (FR-21).
 */
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AuthProvider } from '@/auth/AuthContext';
import { I18nProvider } from '@/i18n';
import * as sessionApi from '@/lib/api/session';
import type { Session } from '@/lib/api/session';
import { DEMO_PATIENTS } from '@/lib/api/fixtures';
import { LoginPage } from './LoginPage';

// `session.ts` now talks to the real backend (FR-18) instead of a fixture lookup - mock it so
// these tests exercise LoginPage/AuthContext wiring without a live server (TASK-038 follow-up).
vi.mock('@/lib/api/session');

function demoSession(): Session {
  return { patient: DEMO_PATIENTS[0], role: 'patient', issuedAt: '2026-07-19T00:00:00.000Z' };
}

beforeEach(() => {
  vi.mocked(sessionApi.listDemoAccounts).mockResolvedValue([
    { patientCode: DEMO_PATIENTS[0].patientCode, displayName: DEMO_PATIENTS[0].fullName },
  ]);
});

function renderLoginPage() {
  return render(
    <I18nProvider>
      <AuthProvider>
        <MemoryRouter initialEntries={['/login']}>
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/home" element={<p>patient home</p>} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    </I18nProvider>,
  );
}

describe('LoginPage (SCR-08 patient path, FR-18)', () => {
  it('renders an empty login form with no patient code prefilled', () => {
    renderLoginPage();
    expect(screen.getByLabelText('Mã bệnh nhân')).toHaveValue('');
    expect(screen.getByLabelText('Mật khẩu')).toHaveValue('');
  });

  it('renders the VI/EN language toggle on the login screen (FR-21)', () => {
    renderLoginPage();
    expect(screen.getByRole('group', { name: 'Ngôn ngữ' })).toBeInTheDocument();
  });

  it('authenticates a demo patient and routes to the patient home on success', async () => {
    vi.mocked(sessionApi.login).mockResolvedValue(demoSession());
    const user = userEvent.setup();
    renderLoginPage();

    await user.type(screen.getByLabelText('Mã bệnh nhân'), 'BN-000123');
    await user.type(screen.getByLabelText('Mật khẩu'), 'demo1234');
    await user.click(screen.getByRole('button', { name: 'Đăng nhập' }));

    await waitFor(() => expect(screen.getByText('patient home')).toBeInTheDocument());
    expect(sessionApi.login).toHaveBeenCalledWith('BN-000123', 'demo1234');
  });

  it('shows one generic error for a patient code that does not exist (no account enumeration)', async () => {
    vi.mocked(sessionApi.login).mockRejectedValue(new Error('invalid-credentials'));
    const user = userEvent.setup();
    renderLoginPage();

    await user.type(screen.getByLabelText('Mã bệnh nhân'), 'BN-999999');
    await user.type(screen.getByLabelText('Mật khẩu'), 'anything');
    await user.click(screen.getByRole('button', { name: 'Đăng nhập' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Sai thông tin đăng nhập. Vui lòng kiểm tra lại mã bệnh nhân và mật khẩu.',
    );
  });

  it('shows the SAME generic error for a wrong password on a real patient code', async () => {
    vi.mocked(sessionApi.login).mockRejectedValue(new Error('invalid-credentials'));
    const user = userEvent.setup();
    renderLoginPage();

    await user.type(screen.getByLabelText('Mã bệnh nhân'), 'BN-000123');
    await user.type(screen.getByLabelText('Mật khẩu'), 'wrong-password');
    await user.click(screen.getByRole('button', { name: 'Đăng nhập' }));

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Sai thông tin đăng nhập. Vui lòng kiểm tra lại mã bệnh nhân và mật khẩu.',
    );
  });

  it('logs in immediately when a demo account quick-select is used', async () => {
    vi.mocked(sessionApi.login).mockResolvedValue(demoSession());
    const user = userEvent.setup();
    renderLoginPage();

    await user.click(await screen.findByRole('button', { name: /Nguyen Van A/ }));

    await waitFor(() => expect(screen.getByText('patient home')).toBeInTheDocument());
    expect(sessionApi.login).toHaveBeenCalledWith('BN-000123', 'demo1234');
  });
});
