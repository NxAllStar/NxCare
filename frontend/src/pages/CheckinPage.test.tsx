/**
 * CheckinPage - /checkin QR / remote check-in (FR-17).
 *
 * FR-17's actor list has the patient PRESENT the code and STAFF perform the
 * scan (doctor/technician), never the reverse. This screen therefore only
 * DISPLAYS the patient's own code; it deliberately builds no self-check-in
 * transition that flips a Task/Appointment status - that would be drift
 * against FR-17 (spec-guardian lock recorded in the TASK-022 task file).
 *
 * Proves:
 * - Loading -> success: the patient's own QR/patient-code renders.
 * - The screen explains staff performs the scan, and carries a visible
 *   demo note that no in-app status change happens.
 * - No control on this screen claims to check the patient in.
 */
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { AuthProvider } from '@/auth/AuthContext';
import { I18nProvider } from '@/i18n';
import { CheckinPage } from './CheckinPage';

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

function renderCheckinPage() {
  return render(
    <I18nProvider>
      <AuthProvider>
        <MemoryRouter initialEntries={['/checkin']}>
          <CheckinPage />
        </MemoryRouter>
      </AuthProvider>
    </I18nProvider>,
  );
}

describe('CheckinPage (/checkin, FR-17)', () => {
  it('shows a loading state before the patient record resolves', () => {
    seedSession();
    renderCheckinPage();
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('displays the patient own QR/patient-code once loaded', async () => {
    seedSession();
    renderCheckinPage();
    expect(await screen.findByRole('img', { name: /BN-000123/ })).toBeInTheDocument();
  });

  it('explains that staff scan the code and carries a demo-only note (FR-17 actor list)', async () => {
    seedSession();
    renderCheckinPage();
    await screen.findByRole('img', { name: /BN-000123/ });
    expect(
      screen.getByText(
        'Xuất trình mã này để nhân viên quét khi bạn đến nơi (không tự thao tác check-in trong ứng dụng).',
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        'Chế độ demo: đây chỉ là hiển thị mã, không có bước check-in tự động nào được thực hiện trong ứng dụng.',
      ),
    ).toBeInTheDocument();
  });

  it('never renders a self-check-in control that could flip a status (FR-17 drift guard)', async () => {
    seedSession();
    renderCheckinPage();
    await screen.findByRole('img', { name: /BN-000123/ });
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
  });
});
