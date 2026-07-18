/**
 * TASK-026 acceptance criterion under test: "After selecting a staff role,
 * the sidebar shows exactly that role's permitted screens per the contract
 * table" - and, from the "Deliver" list: "top bar (user + role + language
 * toggle + logout)".
 */
import { describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { I18nProvider } from '@/i18n';
import { STAFF_SESSION_STORAGE_KEY, StaffAuthProvider } from '../auth/StaffAuthContext';
import type { StaffRole } from '../access';
import { ConsoleShell } from './ConsoleShell';

const NAV_LABEL: Record<string, RegExp> = {
  'SCR-03': /Khám và chỉ định|Consult and orders/,
  'SCR-04': /Worklist bác sĩ|Doctor worklist/,
  'SCR-05': /Task kỹ thuật viên|Technician tasks/,
  'SCR-06': /Dashboard điều phối|Coordinator dashboard/,
  'SCR-07': /Quản trị và audit|Admin and audit/,
};

function seedSession(role: StaffRole) {
  window.sessionStorage.setItem(
    STAFF_SESSION_STORAGE_KEY,
    JSON.stringify({ role, displayName: 'Demo staff', issuedAt: new Date().toISOString() }),
  );
}

function renderShellAs(role: StaffRole) {
  seedSession(role);
  return render(
    <I18nProvider>
      <StaffAuthProvider>
        <MemoryRouter initialEntries={['/']}>
          <Routes>
            <Route element={<ConsoleShell />}>
              <Route index element={<div>screen content</div>} />
            </Route>
          </Routes>
        </MemoryRouter>
      </StaffAuthProvider>
    </I18nProvider>,
  );
}

describe('ConsoleShell sidebar (TASK-026: sidebar filtered by role per the locked contract)', () => {
  it('doctor sees exactly SCR-03 and SCR-04', () => {
    renderShellAs('doctor');
    expect(screen.getByRole('link', { name: NAV_LABEL['SCR-03'] })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: NAV_LABEL['SCR-04'] })).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: NAV_LABEL['SCR-05'] })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: NAV_LABEL['SCR-06'] })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: NAV_LABEL['SCR-07'] })).not.toBeInTheDocument();
  });

  it('technician sees exactly SCR-05', () => {
    renderShellAs('technician');
    expect(screen.getByRole('link', { name: NAV_LABEL['SCR-05'] })).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: NAV_LABEL['SCR-03'] })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: NAV_LABEL['SCR-04'] })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: NAV_LABEL['SCR-06'] })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: NAV_LABEL['SCR-07'] })).not.toBeInTheDocument();
  });

  it('coordinator sees exactly SCR-06 and SCR-07', () => {
    renderShellAs('coordinator');
    expect(screen.getByRole('link', { name: NAV_LABEL['SCR-06'] })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: NAV_LABEL['SCR-07'] })).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: NAV_LABEL['SCR-03'] })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: NAV_LABEL['SCR-04'] })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: NAV_LABEL['SCR-05'] })).not.toBeInTheDocument();
  });

  it('admin sees exactly SCR-06 and SCR-07 (admin reaches the coordinator dashboard too)', () => {
    renderShellAs('admin');
    expect(screen.getByRole('link', { name: NAV_LABEL['SCR-06'] })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: NAV_LABEL['SCR-07'] })).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: NAV_LABEL['SCR-03'] })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: NAV_LABEL['SCR-04'] })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: NAV_LABEL['SCR-05'] })).not.toBeInTheDocument();
  });

  it('top bar shows the signed-in user, a logout control, and a language toggle', () => {
    renderShellAs('coordinator');
    expect(screen.getByText('Demo staff')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Đăng xuất|Log out/ })).toBeInTheDocument();
    expect(screen.getByRole('group', { name: /Ngôn ngữ|Language/ })).toBeInTheDocument();
  });
});
