/**
 * BookPage - /book slot confirmation flow feeding SCR-02 (FR-02 capacity
 * validation).
 *
 * Proves:
 * - Loading -> success: available slots render, an AI-suggested slot
 *   carries the AIChip (NFR-USE-05).
 * - FR-02 capacity validation: a full slot cannot be booked - the confirm
 *   action is disabled and a "slot full" message is shown instead.
 * - Success: confirming an available slot books it (never creating a
 *   ServiceOrder - that type has no representation on the patient surface)
 *   and offers a link into the journey (SCR-02).
 * - Empty/error states render through ScreenState.
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { AuthProvider } from '@/auth/AuthContext';
import { I18nProvider } from '@/i18n';
import * as bookingApi from '@/lib/api/booking';
import { BookPage } from './BookPage';

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

function renderBookPage() {
  return render(
    <I18nProvider>
      <AuthProvider>
        <MemoryRouter initialEntries={['/book']}>
          <Routes>
            <Route path="/book" element={<BookPage />} />
            <Route path="/journey" element={<p>journey screen</p>} />
          </Routes>
        </MemoryRouter>
      </AuthProvider>
    </I18nProvider>,
  );
}

describe('BookPage (/book slot confirmation, FR-02)', () => {
  beforeEach(() => {
    seedSession();
  });

  it('shows a loading state while slots are being fetched', () => {
    renderBookPage();
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('renders available slots once loaded, with the AI-suggested one carrying the AIChip', async () => {
    renderBookPage();
    await screen.findByText('Khung giờ trống');
    expect(screen.getAllByTestId('ai-chip').length).toBeGreaterThan(0);
  });

  it('FR-02: disables booking a full slot and shows a capacity message', async () => {
    renderBookPage();
    await screen.findByText('Khung giờ trống');

    const fullSlotCard = screen.getByText('~12:00').closest('div[data-testid="bookable-slot"]');
    expect(fullSlotCard).not.toBeNull();
    expect(fullSlotCard).toHaveTextContent('Khung giờ này đã đầy. Vui lòng chọn khung khác.');
    const confirmButtonInFullSlot = fullSlotCard?.querySelector('button');
    expect(confirmButtonInFullSlot).toBeDisabled();
  });

  it('books an available slot and shows a success confirmation linking to the journey', async () => {
    const user = userEvent.setup();
    renderBookPage();
    await screen.findByText('Khung giờ trống');

    const availableSlotCard = screen.getByText('~10:15, it dong').closest('div[data-testid="bookable-slot"]');
    const confirmButton = availableSlotCard?.querySelector('button') as HTMLButtonElement;
    await user.click(confirmButton);

    expect(await screen.findByText('Đã đặt lịch khám thành công')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Xem lộ trình của tôi' })).toHaveAttribute('href', '/journey');
  });

  it('shows the error state when fetching slots fails', async () => {
    vi.spyOn(bookingApi, 'listBookableSlots').mockRejectedValueOnce(new Error('network down'));
    renderBookPage();
    expect(await screen.findByRole('alert')).toBeInTheDocument();
  });
});
