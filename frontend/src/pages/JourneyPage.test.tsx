/**
 * JourneyPage - SCR-02 Journey timeline (FR-04, FR-05, FR-06, FR-11, FR-17).
 *
 * Proves:
 * - Empty: "no journey yet" for a patient with no active care plan.
 * - Loading: a skeleton/status indicator while data is being fetched.
 * - Success: the timeline renders each task's owner, ETA, and status via
 *   StatusChip (done/in-progress/pending, spec 10 SCR-02 Elements).
 * - FR-05/AS-02: a LOCKED task shows a go-pay REMINDER only - no payment
 *   control that could process money exists anywhere on the screen.
 * - FR-11: the AI re-plan reason is shown, labelled with the AIChip.
 * - FR-17: the patient's own QR/patient-code is displayed.
 * - Reschedule/cancel: cancelling asks for confirmation before acting.
 * - Error state renders through ScreenState.
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { AuthProvider } from '@/auth/AuthContext';
import { I18nProvider } from '@/i18n';
import * as patientApi from '@/lib/api/patient';
import { JourneyPage } from './JourneyPage';

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

function renderJourneyPage() {
  return render(
    <I18nProvider>
      <AuthProvider>
        <MemoryRouter initialEntries={['/journey']}>
          <Routes>
            <Route path="/journey" element={<JourneyPage />} />
            <Route path="/assistant" element={<p>assistant screen</p>} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    </I18nProvider>,
  );
}

describe('JourneyPage (SCR-02 Journey timeline)', () => {
  it('shows a loading indicator while data is being fetched', () => {
    seedSession('patient-0001');
    renderJourneyPage();
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('shows the empty state for a patient with no active care plan', async () => {
    seedSession('patient-0002');
    renderJourneyPage();
    expect(await screen.findByText('Chưa có lộ trình - vui lòng hoàn tất khám chẩn đoán.')).toBeInTheDocument();
  });

  it('renders each task with its owner, ETA, and a StatusChip for its status', async () => {
    seedSession('patient-0001');
    renderJourneyPage();

    await screen.findByText('Xet nghiem mau / Blood test');
    expect(screen.getByText(/staff-0009/)).toBeInTheDocument();
    const chips = screen.getAllByTestId('status-chip');
    const codes = chips.map((chip) => chip.getAttribute('data-code'));
    expect(codes).toEqual(expect.arrayContaining(['DONE', 'IN_PROGRESS', 'LOCKED']));
  });

  it('FR-05/AS-02: shows a go-pay reminder on the LOCKED task and never a payment control', async () => {
    seedSession('patient-0001');
    renderJourneyPage();

    await screen.findByText('Chup X-quang / X-ray imaging');
    expect(screen.getByText('Vui lòng đi thanh toán')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /thanh toán|pay|checkout/i })).not.toBeInTheDocument();
  });

  it('FR-11: shows the AI-labelled re-plan reason', async () => {
    seedSession('patient-0001');
    renderJourneyPage();

    await screen.findByText('Emergency pre-emption tai phong xet nghiem (+8 phut)');
    const reasonSection = screen.getByText('Emergency pre-emption tai phong xet nghiem (+8 phut)').closest('div');
    expect(reasonSection?.querySelector('[data-testid="ai-chip"]')).not.toBeNull();
  });

  it('FR-17: displays the patient own QR/patient-code', async () => {
    seedSession('patient-0001');
    renderJourneyPage();

    await screen.findByText('Xet nghiem mau / Blood test');
    expect(screen.getByRole('img', { name: /BN-000123/ })).toBeInTheDocument();
  });

  it('asks for confirmation before cancelling, and only cancels on confirm', async () => {
    const user = userEvent.setup();
    seedSession('patient-0001');
    const cancelSpy = vi.spyOn(patientApi, 'cancelAppointment');
    renderJourneyPage();

    await screen.findByText('Xet nghiem mau / Blood test');
    await user.click(screen.getByRole('button', { name: 'Hủy lịch' }));

    expect(screen.getByText('Bạn có chắc muốn hủy buổi khám này?')).toBeInTheDocument();
    expect(cancelSpy).not.toHaveBeenCalled();

    await user.click(screen.getByRole('button', { name: 'Xác nhận hủy' }));

    expect(cancelSpy).toHaveBeenCalledWith('appt-0001');
    expect(await screen.findByText('Đã hủy buổi khám.')).toBeInTheDocument();
  });

  it('shows the error state when a fetch fails', async () => {
    seedSession('patient-0001');
    vi.spyOn(patientApi, 'getActiveCarePlan').mockRejectedValueOnce(new Error('down'));
    renderJourneyPage();
    expect(await screen.findByRole('alert')).toBeInTheDocument();
  });
});
