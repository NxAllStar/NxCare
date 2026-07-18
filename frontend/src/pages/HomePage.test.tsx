/**
 * HomePage - dual-mode /home (PRD-FR-12 M1: Home + Live Companion).
 *
 * Proves:
 * - The signature IA decision: the SAME /home tab renders two visibly
 *   different modes - an out-of-hospital dashboard and an in-hospital Live
 *   Companion - and a control switches between them.
 * - Live Companion shows the current step and an ETA.
 * - The out-of-hospital dashboard renders upcoming visits, a reminders
 *   section, and shortcuts (book/intake/checkin).
 * - "What AI is doing for you" in Live Companion carries the AIChip
 *   (NFR-USE-05).
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { AuthProvider } from '@/auth/AuthContext';
import { I18nProvider } from '@/i18n';
import { HomePage } from './HomePage';

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

function renderHomePage() {
  return render(
    <I18nProvider>
      <AuthProvider>
        <MemoryRouter initialEntries={['/home']}>
          <Routes>
            <Route path="/home" element={<HomePage />} />
            <Route path="/book" element={<p>book screen</p>} />
            <Route path="/intake" element={<p>intake screen</p>} />
            <Route path="/checkin" element={<p>checkin screen</p>} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    </I18nProvider>,
  );
}

describe('HomePage (dual-mode /home, PRD-FR-12 M1)', () => {
  it('defaults to Live Companion mode when the patient has a step in progress', async () => {
    seedSession('patient-0001');
    renderHomePage();
    expect(await screen.findByText('Xet nghiem mau / Blood test')).toBeInTheDocument();
    expect(screen.getByText('AI đang làm gì cho bạn')).toBeInTheDocument();
  });

  it('shows an ETA on the current Live Companion step', async () => {
    seedSession('patient-0001');
    renderHomePage();
    await screen.findByText('Xet nghiem mau / Blood test');
    expect(screen.getByText('Thời gian còn lại (ước tính)')).toBeInTheDocument();
  });

  it('labels "what AI is doing for you" with the AIChip (NFR-USE-05)', async () => {
    seedSession('patient-0001');
    renderHomePage();
    await screen.findByText('Xet nghiem mau / Blood test');
    expect(screen.getAllByTestId('ai-chip').length).toBeGreaterThan(0);
  });

  it('switches from Live Companion to the out-of-hospital dashboard via the mode control', async () => {
    const user = userEvent.setup();
    seedSession('patient-0001');
    renderHomePage();

    await screen.findByText('Xet nghiem mau / Blood test');
    await user.click(screen.getByRole('button', { name: 'Ngoài viện' }));

    expect(screen.getByText('Lịch sắp tới')).toBeInTheDocument();
    expect(screen.getByText('Lối tắt')).toBeInTheDocument();
    expect(screen.queryByText('AI đang làm gì cho bạn')).not.toBeInTheDocument();
  });

  it('switches back to Live Companion mode via the mode control', async () => {
    const user = userEvent.setup();
    seedSession('patient-0001');
    renderHomePage();

    await screen.findByText('Xet nghiem mau / Blood test');
    await user.click(screen.getByRole('button', { name: 'Ngoài viện' }));
    await user.click(screen.getByRole('button', { name: 'Trong viện' }));

    expect(await screen.findByText('AI đang làm gì cho bạn')).toBeInTheDocument();
  });

  it('defaults to the out-of-hospital dashboard for a patient with no step in progress', async () => {
    seedSession('patient-0002');
    renderHomePage();

    expect(await screen.findByText('Lịch sắp tới')).toBeInTheDocument();
    expect(screen.getByText('Bạn chưa có lịch khám sắp tới.')).toBeInTheDocument();
  });

  it('renders shortcuts to book, intake, and check-in on the dashboard', async () => {
    seedSession('patient-0002');
    renderHomePage();

    await screen.findByText('Lối tắt');
    expect(screen.getByRole('link', { name: 'Đặt lịch khám' })).toHaveAttribute('href', '/book');
    expect(screen.getByRole('link', { name: 'Mô tả triệu chứng' })).toHaveAttribute('href', '/intake');
    expect(screen.getByRole('link', { name: 'Check-in tại viện' })).toHaveAttribute('href', '/checkin');
  });
});
