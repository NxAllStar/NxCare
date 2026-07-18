/**
 * routeConfig - proves FR-18 AC-18.1 (unauthenticated access to any screen
 * other than /login redirects to /login) and that the patient-only route
 * table is navigable end to end through the shell.
 */
import { render, screen } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { AuthProvider } from '@/auth/AuthContext';
import { I18nProvider } from '@/i18n';
import { routes } from './routeConfig';

function renderAt(path: string) {
  const router = createMemoryRouter(routes, { initialEntries: [path] });
  return render(
    <I18nProvider>
      <AuthProvider>
        <RouterProvider router={router} />
      </AuthProvider>
    </I18nProvider>,
  );
}

describe('routeConfig (FR-18 AC-18.1 route guard, patient-only route table)', () => {
  it('redirects an unauthenticated visitor from a protected route to /login', () => {
    renderAt('/journey');
    expect(screen.getByRole('heading', { name: 'Đăng nhập' })).toBeInTheDocument();
  });

  it('serves /login directly for an unauthenticated visitor, without a redirect loop', () => {
    renderAt('/login');
    expect(screen.getByRole('heading', { name: 'Đăng nhập' })).toBeInTheDocument();
  });

  it('redirects the index route ("/") to /home for an unauthenticated visitor via /login', () => {
    renderAt('/');
    expect(screen.getByRole('heading', { name: 'Đăng nhập' })).toBeInTheDocument();
  });

  it('renders the real /journey P0 screen (TASK-022) inside the shell once a session exists', async () => {
    window.sessionStorage.setItem(
      'vaic.session',
      JSON.stringify({
        patient: { id: 'patient-0001', fullName: 'Nguyen Van A', phone: null, patientCode: 'BN-000123', priorityLevel: 'ROUTINE', createdAt: '2026-01-01T00:00:00.000Z' },
        role: 'patient',
        issuedAt: '2026-07-18T00:00:00.000Z',
      }),
    );

    renderAt('/journey');

    expect(await screen.findByText('Lộ trình của bạn')).toBeInTheDocument();
    expect(screen.getByTestId('app-shell')).toBeInTheDocument();
  });

  it('renders the real /notifications P1 screen (TASK-023) inside the shell once a session exists', async () => {
    window.sessionStorage.setItem(
      'vaic.session',
      JSON.stringify({
        patient: { id: 'patient-0001', fullName: 'Nguyen Van A', phone: null, patientCode: 'BN-000123', priorityLevel: 'ROUTINE', createdAt: '2026-01-01T00:00:00.000Z' },
        role: 'patient',
        issuedAt: '2026-07-18T00:00:00.000Z',
      }),
    );

    renderAt('/notifications');

    expect(await screen.findByRole('heading', { name: 'Trung tâm thông báo' })).toBeInTheDocument();
    expect(screen.getByTestId('app-shell')).toBeInTheDocument();
  });

  it('renders a P2 route as a tagged, non-functional placeholder once a session exists', async () => {
    window.sessionStorage.setItem(
      'vaic.session',
      JSON.stringify({
        patient: { id: 'patient-0001', fullName: 'Nguyen Van A', phone: null, patientCode: 'BN-000123', priorityLevel: 'ROUTINE', createdAt: '2026-01-01T00:00:00.000Z' },
        role: 'patient',
        issuedAt: '2026-07-18T00:00:00.000Z',
      }),
    );

    renderAt('/wellness');

    expect(await screen.findByText('P2')).toBeInTheDocument();
  });
});
