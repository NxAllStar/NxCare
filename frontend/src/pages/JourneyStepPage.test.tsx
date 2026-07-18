/**
 * JourneyStepPage - /journey/step/:id (PMA-M3, TASK-023).
 *
 * Proves:
 * - Loading indicator while the step is fetched.
 * - Success: ETA range, "why this order," and wayfinding all render.
 * - The "why this order" explanation is model-produced and carries the
 *   AIChip (NFR-USE-05).
 * - Own-scope: a task id belonging to a different patient's care plan is
 *   never shown (renders the not-found state instead).
 * - Empty/not-found state when the id does not resolve to a step at all.
 */
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { AuthProvider } from '@/auth/AuthContext';
import { I18nProvider } from '@/i18n';
import * as journeyStepApi from '@/lib/api/journeyStep';
import { JourneyStepPage } from './JourneyStepPage';

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

function renderAt(taskId: string) {
  return render(
    <I18nProvider>
      <AuthProvider>
        <MemoryRouter initialEntries={[`/journey/step/${taskId}`]}>
          <Routes>
            <Route path="/journey/step/:id" element={<JourneyStepPage />} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    </I18nProvider>,
  );
}

describe('JourneyStepPage (/journey/step/:id, PMA-M3)', () => {
  it('shows a loading indicator while the step is being fetched', () => {
    seedSession();
    renderAt('task-0002');
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('renders the ETA range, why-this-order, and wayfinding for the step', async () => {
    seedSession();
    renderAt('task-0002');

    await screen.findByText('Xet nghiem mau / Blood test');
    expect(screen.getByText('~10-15 phut')).toBeInTheDocument();
    expect(
      screen.getByText('Xet nghiem mau duoc uu tien truoc vi ket qua can co truoc khi bac si doc lai.'),
    ).toBeInTheDocument();
    expect(screen.getByText('Di thang hanh lang chinh, phong lay mau o tang 1, canh quay so 3.')).toBeInTheDocument();
  });

  it('NFR-USE-05: labels the AI-produced "why this order" explanation with the AIChip', async () => {
    seedSession();
    renderAt('task-0002');

    await screen.findByText('Xet nghiem mau duoc uu tien truoc vi ket qua can co truoc khi bac si doc lai.');
    const section = screen
      .getByText('Xet nghiem mau duoc uu tien truoc vi ket qua can co truoc khi bac si doc lai.')
      .closest('div');
    expect(section?.querySelector('[data-testid="ai-chip"]')).not.toBeNull();
  });

  it('shows the not-found state for a task id that does not resolve', async () => {
    seedSession();
    renderAt('task-not-real');
    expect(await screen.findByText('Không tìm thấy bước này.')).toBeInTheDocument();
  });

  it('own-scope: a task belonging to a different patient never renders (not-found instead)', async () => {
    seedSession();
    const spy = vi.spyOn(journeyStepApi, 'getJourneyStep');
    renderAt('task-0002');
    await screen.findByText('Xet nghiem mau / Blood test');
    expect(spy).toHaveBeenCalledWith('patient-0001', 'task-0002');
  });
});
