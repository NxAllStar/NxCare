/**
 * StatusChip - proves the cross-cutting rules in spec 10:
 * - semantic colour mapping (green=done, amber=waiting, red=blocked, blue=in-progress)
 * - BR-31 / NFR-USE-03: the enum code stays English in the DOM even when the
 *   display label is localised.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { I18nProvider } from '@/i18n';
import { StatusChip } from './StatusChip';

function renderWithLocale(code: Parameters<typeof StatusChip>[0]['code']) {
  return render(
    <I18nProvider>
      <StatusChip code={code} />
    </I18nProvider>,
  );
}

describe('StatusChip (cross-cutting UI rules + BR-31)', () => {
  it('renders the English code in the DOM (never translated)', () => {
    renderWithLocale('PENDING');
    expect(screen.getByTestId('status-chip')).toHaveAttribute('data-code', 'PENDING');
    expect(screen.getByText('PENDING')).toBeInTheDocument();
  });

  it('renders the localised Vietnamese label alongside the code, by default', () => {
    renderWithLocale('PENDING');
    expect(screen.getByText('Đang chờ')).toBeInTheDocument();
  });

  it('maps DONE to the success (green) variant', () => {
    renderWithLocale('DONE');
    expect(screen.getByTestId('status-chip')).toHaveAttribute('data-variant', 'done');
  });

  it('maps LOCKED to the blocked (red) variant', () => {
    renderWithLocale('LOCKED');
    expect(screen.getByTestId('status-chip')).toHaveAttribute('data-variant', 'blocked');
  });

  it('maps IN_PROGRESS to the in-progress (blue) variant', () => {
    renderWithLocale('IN_PROGRESS');
    expect(screen.getByTestId('status-chip')).toHaveAttribute('data-variant', 'in-progress');
  });

  it('maps PENDING to the waiting (amber) variant', () => {
    renderWithLocale('PENDING');
    expect(screen.getByTestId('status-chip')).toHaveAttribute('data-variant', 'waiting');
  });
});
