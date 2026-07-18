/**
 * AIChip - proves NFR-USE-05 (spec 10 "Visual design direction" > AI-content
 * treatment): model-produced content always carries a visible AI label and
 * is never presented as a confirmed fact.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { I18nProvider } from '@/i18n';
import { AIChip } from './AIChip';

function renderWithI18n(ui: React.ReactElement) {
  return render(<I18nProvider>{ui}</I18nProvider>);
}

describe('AIChip (NFR-USE-05 - AI content labelling)', () => {
  it('renders the Vietnamese AI-suggested label by default', () => {
    renderWithI18n(<AIChip />);
    expect(screen.getByText('Đề xuất bởi AI')).toBeInTheDocument();
  });

  it('exposes a stable test id so any screen can assert the label is present', () => {
    renderWithI18n(<AIChip />);
    expect(screen.getByTestId('ai-chip')).toBeInTheDocument();
  });

  it('accepts an override label while keeping the AI-chip role visible', () => {
    renderWithI18n(<AIChip label="De xuat khung gio it dong" />);
    expect(screen.getByTestId('ai-chip')).toHaveTextContent('De xuat khung gio it dong');
  });
});
