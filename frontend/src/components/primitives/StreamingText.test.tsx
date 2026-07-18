/**
 * StreamingText - proves NFR-USE-05 (clearly labelled AI reasoning), the
 * "thinking" indicator, and that model output is rendered as plain text
 * only (never as HTML - agent-guardrails.md "Model output is a proposal").
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { I18nProvider } from '@/i18n';
import { StreamingText } from './StreamingText';

function renderWithI18n(ui: React.ReactElement) {
  return render(<I18nProvider>{ui}</I18nProvider>);
}

describe('StreamingText (SCR-06 live reasoning stream)', () => {
  it('renders the localised "AI reasoning" label', () => {
    renderWithI18n(<StreamingText text="dang danh gia phuong an" isStreaming={false} />);
    expect(screen.getByText('Suy luận AI')).toBeInTheDocument();
  });

  it('shows a "thinking" indicator while streaming', () => {
    renderWithI18n(<StreamingText text="dang danh gia" isStreaming />);
    expect(screen.getByTestId('streaming-text-thinking')).toHaveTextContent('Đang suy luận...');
  });

  it('hides the "thinking" indicator once streaming stops', () => {
    renderWithI18n(<StreamingText text="da xong" isStreaming={false} />);
    expect(screen.queryByTestId('streaming-text-thinking')).not.toBeInTheDocument();
  });

  it('renders the streamed text as plain text, never as HTML (a "<b>" tag in the text stays literal)', () => {
    renderWithI18n(<StreamingText text="<b>khong phai in dam</b>" isStreaming={false} />);
    expect(screen.getByTestId('streaming-text-body')).toHaveTextContent('<b>khong phai in dam</b>');
    expect(document.querySelector('b')).not.toBeInTheDocument();
  });

  it('is read-only - no input or button controls inside the transcript body', () => {
    renderWithI18n(<StreamingText text="chi doc" isStreaming={false} />);
    expect(screen.queryByRole('button')).not.toBeInTheDocument();
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
  });
});
