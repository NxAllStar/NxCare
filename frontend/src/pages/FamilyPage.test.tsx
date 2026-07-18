/**
 * FamilyPage - /family family-switcher UI SHELL (PMA-M7, TASK-023).
 *
 * DECISION (spec-guardian lock, TASK-023): spec 06 has no delegated-viewer
 * scope, so this screen is a switcher SHELL only. Proves:
 * - The self profile and any linked family profiles render as switcher
 *   options.
 * - Selecting the self profile shows the current patient's OWN data only.
 * - Selecting a non-self profile NEVER fetches or displays that other
 *   patient's data - it shows the "not implemented" notice instead. This is
 *   the load-bearing assertion: no cross-patient Own-scope leak.
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { AuthProvider } from '@/auth/AuthContext';
import { I18nProvider } from '@/i18n';
import * as familyApi from '@/lib/api/family';
import * as patientApi from '@/lib/api/patient';
import { FamilyPage } from './FamilyPage';

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
        <MemoryRouter initialEntries={['/family']}>
          <FamilyPage />
        </MemoryRouter>
      </AuthProvider>
    </I18nProvider>,
  );
}

describe('FamilyPage (/family, PMA-M7 switcher shell)', () => {
  it('shows a loading indicator while the family profile list is being fetched', () => {
    seedSession();
    renderPage();
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('renders the self profile and any linked family profiles as switcher options', async () => {
    seedSession();
    renderPage();

    await screen.findByRole('group', { name: 'Chuyển đổi hồ sơ' });
    expect(screen.getByRole('button', { name: /Ban than/ })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Me \(BN Nguyen Thi L\.\)/ })).toBeInTheDocument();
  });

  it('shows the current patient own data for the self profile by default', async () => {
    seedSession();
    renderPage();

    await screen.findByText('BN-000123');
  });

  it('never fetches or displays another profile own-scope data when a non-self profile is selected', async () => {
    const user = userEvent.setup();
    seedSession();
    const getPatientSpy = vi.spyOn(patientApi, 'getPatient');
    renderPage();

    await screen.findByText('BN-000123');
    getPatientSpy.mockClear();

    await user.click(screen.getByRole('button', { name: /Me \(BN Nguyen Thi L\.\)/ }));

    expect(await screen.findByText('Xem hồ sơ của người thân chưa được triển khai trong bản demo này - đây chỉ là giao diện mẫu.')).toBeInTheDocument();
    expect(screen.queryByText('BN-000123')).not.toBeInTheDocument();
    // The critical assertion: selecting another profile never triggers a
    // fetch of anyone's patient data at all - own-scope data access simply
    // does not run down that path.
    expect(getPatientSpy).not.toHaveBeenCalled();
  });

  it('shows the error state when the profile list fetch fails', async () => {
    seedSession();
    vi.spyOn(familyApi, 'listFamilyProfiles').mockRejectedValueOnce(new Error('down'));
    renderPage();
    expect(await screen.findByRole('alert')).toBeInTheDocument();
  });
});
