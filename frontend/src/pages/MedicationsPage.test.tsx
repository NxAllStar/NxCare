/**
 * MedicationsPage - /medications (PMA-M5, no backing FR - TASK-023).
 *
 * Proves dose/usage/reminder render, and that an interaction/allergy
 * warning (model-produced) carries the AIChip (NFR-USE-05) while a
 * medication with no warning never renders one.
 */
import { render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { AuthProvider } from '@/auth/AuthContext';
import { I18nProvider } from '@/i18n';
import * as recordsApi from '@/lib/api/records';
import { MedicationsPage } from './MedicationsPage';

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
        <MemoryRouter initialEntries={['/medications']}>
          <MedicationsPage />
        </MemoryRouter>
      </AuthProvider>
    </I18nProvider>,
  );
}

describe('MedicationsPage (/medications, PMA-M5)', () => {
  it('shows a loading indicator while medications are being fetched', () => {
    seedSession();
    renderPage();
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('shows the empty state when there are no prescriptions', async () => {
    seedSession();
    vi.spyOn(recordsApi, 'listMedications').mockResolvedValueOnce([]);
    renderPage();
    expect(await screen.findByText('Chưa có đơn thuốc nào')).toBeInTheDocument();
  });

  it('renders dose, usage, and reminder times for each medication', async () => {
    seedSession();
    renderPage();

    await screen.findByText('Paracetamol 500mg');
    const item = screen.getByText('Paracetamol 500mg').closest('[data-testid="medication-item"]') as HTMLElement;
    expect(within(item).getByText('1 vien / lan')).toBeInTheDocument();
    expect(within(item).getByText('Uong sau an, cach nhau it nhat 6 gio')).toBeInTheDocument();
    expect(within(item).getByText('08:00, 14:00, 20:00')).toBeInTheDocument();
  });

  it('NFR-USE-05: labels an interaction warning with the AIChip; a medication with none never shows one', async () => {
    seedSession();
    renderPage();

    await screen.findByText('Amoxicillin 500mg');
    const warned = screen.getByText('Amoxicillin 500mg').closest('[data-testid="medication-item"]');
    expect(warned?.querySelector('[data-testid="ai-chip"]')).not.toBeNull();

    const unwarned = screen.getByText('Paracetamol 500mg').closest('[data-testid="medication-item"]');
    expect(unwarned?.querySelector('[data-testid="ai-chip"]')).toBeNull();
  });

  it('shows the error state when the fetch fails', async () => {
    seedSession();
    vi.spyOn(recordsApi, 'listMedications').mockRejectedValueOnce(new Error('down'));
    renderPage();
    expect(await screen.findByRole('alert')).toBeInTheDocument();
  });
});
