/**
 * RecoveryPage - /recovery (PMA-M5, no backing FR - TASK-023).
 *
 * Proves the safety frame (collect -> flag -> refer to doctor): the agent's
 * check-in question is model-produced (AIChip); a WARNING-severity
 * check-in shows the escalation banner and "contact your doctor," a NORMAL
 * one never does. Never a treatment recommendation.
 */
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { AuthProvider } from '@/auth/AuthContext';
import { I18nProvider } from '@/i18n';
import * as recordsApi from '@/lib/api/records';
import { RecoveryPage } from './RecoveryPage';

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
        <MemoryRouter initialEntries={['/recovery']}>
          <RecoveryPage />
        </MemoryRouter>
      </AuthProvider>
    </I18nProvider>,
  );
}

describe('RecoveryPage (/recovery, PMA-M5)', () => {
  it('shows a loading indicator while the recovery diary is being fetched', () => {
    seedSession();
    renderPage();
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('shows the empty state when there is no recovery diary yet', async () => {
    seedSession();
    vi.spyOn(recordsApi, 'listRecoveryCheckIns').mockResolvedValueOnce([]);
    renderPage();
    expect(await screen.findByText('Chưa có nhật ký hồi phục')).toBeInTheDocument();
  });

  it('labels the agent check-in question with the AIChip', async () => {
    seedSession();
    renderPage();

    await screen.findByText('Hom nay ban co con dau bung khong?');
    const item = screen.getByText('Hom nay ban co con dau bung khong?').closest('[data-testid="recovery-item"]');
    expect(item?.querySelector('[data-testid="ai-chip"]')).not.toBeNull();
  });

  it('shows the escalation banner and "contact your doctor" only for a WARNING check-in', async () => {
    seedSession();
    renderPage();

    await screen.findByText('Ban co bi sot lai hay vet mo hong khong?');
    const warningItem = screen
      .getByText('Ban co bi sot lai hay vet mo hong khong?')
      .closest('[data-testid="recovery-item"]');
    expect(warningItem?.textContent).toContain('Triệu chứng của bạn cần được bác sĩ xem xét sớm.');
    expect(warningItem?.textContent).toContain('Vui lòng liên hệ bác sĩ.');

    const normalItem = screen.getByText('Hom nay ban co con dau bung khong?').closest('[data-testid="recovery-item"]');
    expect(normalItem?.textContent).not.toContain('Triệu chứng của bạn cần được bác sĩ xem xét sớm.');
  });

  it('shows the error state when the fetch fails', async () => {
    seedSession();
    vi.spyOn(recordsApi, 'listRecoveryCheckIns').mockRejectedValueOnce(new Error('down'));
    renderPage();
    expect(await screen.findByRole('alert')).toBeInTheDocument();
  });
});
