/**
 * ResultsPage - /results (PMA-M4, no backing FR - TASK-023).
 *
 * Proves the narrow safety guardrail (PRD-FR-12 4, PMA-M4): a result is only
 * ever labelled within/outside its reference range plus "discuss this with
 * your doctor" - never a diagnosis, and the guardrail only appears on the
 * abnormal (outside-range) result, not the normal one.
 */
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { AuthProvider } from '@/auth/AuthContext';
import { I18nProvider } from '@/i18n';
import * as recordsApi from '@/lib/api/records';
import { ResultsPage } from './ResultsPage';

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

function renderPage() {
  return render(
    <I18nProvider>
      <AuthProvider>
        <MemoryRouter initialEntries={['/results']}>
          <ResultsPage />
        </MemoryRouter>
      </AuthProvider>
    </I18nProvider>,
  );
}

describe('ResultsPage (/results, PMA-M4)', () => {
  it('shows a loading indicator while results are being fetched', () => {
    seedSession();
    renderPage();
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('shows the empty state when there are no results', async () => {
    seedSession();
    vi.spyOn(recordsApi, 'listLabResults').mockResolvedValueOnce([]);
    renderPage();
    expect(await screen.findByText('Chưa có kết quả nào')).toBeInTheDocument();
  });

  it('labels the abnormal result outside range and tells the patient to ask their doctor', async () => {
    seedSession();
    renderPage();

    await screen.findByText('Bach cau (WBC)');
    const outsideRow = screen.getByText('Bach cau (WBC)').closest('[data-testid="lab-result"]');
    expect(outsideRow).not.toBeNull();
    expect(outsideRow?.textContent).toContain('Ngoài ngưỡng tham chiếu');
    expect(outsideRow?.textContent).toContain('Hãy trao đổi với bác sĩ của bạn.');
  });

  it('labels the normal result within range and never shows the doctor guardrail for it', async () => {
    seedSession();
    renderPage();

    await screen.findByText('Duong huyet luc doi (Glucose)');
    const withinRow = screen.getByText('Duong huyet luc doi (Glucose)').closest('[data-testid="lab-result"]');
    expect(withinRow).not.toBeNull();
    expect(withinRow?.textContent).toContain('Trong ngưỡng tham chiếu');
    expect(withinRow?.textContent).not.toContain('Hãy trao đổi với bác sĩ của bạn.');
  });

  it('shows the error state when the fetch fails', async () => {
    seedSession();
    vi.spyOn(recordsApi, 'listLabResults').mockRejectedValueOnce(new Error('down'));
    renderPage();
    expect(await screen.findByRole('alert')).toBeInTheDocument();
  });
});
