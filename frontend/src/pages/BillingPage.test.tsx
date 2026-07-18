/**
 * BillingPage - /billing (PMA-M6, DISPLAY-ONLY - FR-05, AS-02, TASK-023).
 *
 * Proves cost estimate, coverage, and invoice history all render, and -
 * this is the load-bearing assertion - there is NO payment form, button,
 * or control of any kind anywhere on the screen. The app never processes
 * money.
 */
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { AuthProvider } from '@/auth/AuthContext';
import { I18nProvider } from '@/i18n';
import * as billingApi from '@/lib/api/billing';
import { BillingPage } from './BillingPage';

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
        <MemoryRouter initialEntries={['/billing']}>
          <BillingPage />
        </MemoryRouter>
      </AuthProvider>
    </I18nProvider>,
  );
}

describe('BillingPage (/billing, PMA-M6, display-only)', () => {
  it('shows a loading indicator while billing data is being fetched', () => {
    seedSession();
    renderPage();
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('shows the empty state when there is nothing to show', async () => {
    seedSession();
    vi.spyOn(billingApi, 'listBillingEstimates').mockResolvedValueOnce([]);
    vi.spyOn(billingApi, 'listInvoices').mockResolvedValueOnce([]);
    renderPage();
    expect(await screen.findByText('Chưa có hóa đơn nào')).toBeInTheDocument();
  });

  it('renders the cost estimate, insurance coverage, co-pay, and invoice history', async () => {
    seedSession();
    renderPage();

    await screen.findByText('Chup X-quang nguc');
    expect(screen.getByText('BHYT chi tra 80%')).toBeInTheDocument();
    expect(screen.getByText(/70000/)).toBeInTheDocument();
    expect(await screen.findByText('Kham lam sang + xet nghiem mau')).toBeInTheDocument();
    expect(screen.getByText('Chup X-quang')).toBeInTheDocument();
  });

  it('shows the display-only notice and NEVER renders a payment form, button, or control', async () => {
    seedSession();
    renderPage();

    await screen.findByText('Chup X-quang nguc');
    expect(screen.getByText('Chỉ hiển thị thông tin - vui lòng đi thanh toán tại quầy.')).toBeInTheDocument();

    // No payment action anywhere: no button/link whose name suggests paying,
    // no form element, no QR/card/wallet control of any kind.
    expect(screen.queryByRole('form')).not.toBeInTheDocument();
    expect(document.querySelector('form')).toBeNull();
    expect(screen.queryByRole('button', { name: /thanh toán|pay|checkout|wallet|thẻ|qr/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /thanh toán|pay|checkout|wallet|thẻ|qr/i })).not.toBeInTheDocument();
  });

  it('shows the error state when a fetch fails', async () => {
    seedSession();
    vi.spyOn(billingApi, 'listBillingEstimates').mockRejectedValueOnce(new Error('down'));
    renderPage();
    expect(await screen.findByRole('alert')).toBeInTheDocument();
  });
});
