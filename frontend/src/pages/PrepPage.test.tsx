/**
 * PrepPage - /prep/:id proactive pre-visit prep reminders (PMA-M2,
 * TASK-023).
 */
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { AuthProvider } from '@/auth/AuthContext';
import { I18nProvider } from '@/i18n';
import * as prepApi from '@/lib/api/prep';
import { PrepPage } from './PrepPage';

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

function renderAt(appointmentId: string) {
  return render(
    <I18nProvider>
      <AuthProvider>
        <MemoryRouter initialEntries={[`/prep/${appointmentId}`]}>
          <Routes>
            <Route path="/prep/:id" element={<PrepPage />} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    </I18nProvider>,
  );
}

describe('PrepPage (/prep/:id, PMA-M2)', () => {
  it('shows a loading indicator while the reminder is being fetched', () => {
    seedSession();
    renderAt('appt-0001');
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('renders every prep instruction for the appointment', async () => {
    seedSession();
    renderAt('appt-0001');

    await screen.findByText('Nhin an tu 22h hom truoc buoi kham.');
    expect(screen.getByText('Mang theo don thuoc cu va ket qua xet nghiem gan nhat (neu co).')).toBeInTheDocument();
    expect(screen.getByText('Mang theo the BHYT va giay to tuy than.')).toBeInTheDocument();
  });

  it('shows the not-found state for an appointment with no prep reminder', async () => {
    seedSession();
    renderAt('appt-does-not-exist');
    expect(await screen.findByText('Không tìm thấy nhắc nhở cho buổi khám này.')).toBeInTheDocument();
  });

  it('shows the error state when the fetch fails', async () => {
    seedSession();
    vi.spyOn(prepApi, 'getPrepReminder').mockRejectedValueOnce(new Error('down'));
    renderAt('appt-0001');
    expect(await screen.findByRole('alert')).toBeInTheDocument();
  });
});
