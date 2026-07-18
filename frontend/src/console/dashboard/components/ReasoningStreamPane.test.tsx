/**
 * Proves the reasoning stream renders labelled AI text with a thinking
 * indicator while streaming (TASK-027 acceptance criteria).
 */
import { act, render, screen } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { I18nProvider } from '@/i18n';
import { ReasoningStreamPane } from './ReasoningStreamPane';

function renderPane(transcript: string, intervalMs = 100) {
  return render(
    <I18nProvider>
      <ReasoningStreamPane transcript={transcript} intervalMs={intervalMs} />
    </I18nProvider>,
  );
}

describe('ReasoningStreamPane (SCR-06 live reasoning stream)', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('renders the AI-reasoning label and shows the thinking indicator while streaming', () => {
    renderPane('mot hai ba bon nam');
    expect(screen.getByText('Suy luận của trợ lý sự cố')).toBeInTheDocument();
    expect(screen.getByTestId('streaming-text-thinking')).toBeInTheDocument();
  });

  it('reveals more text over time and hides the thinking indicator once done', () => {
    renderPane('mot hai ba bon nam sau bay tam', 100);
    act(() => {
      vi.advanceTimersByTime(1000);
    });
    expect(screen.getByTestId('streaming-text-body')).toHaveTextContent('mot hai ba bon nam sau bay tam');
    expect(screen.queryByTestId('streaming-text-thinking')).not.toBeInTheDocument();
  });
});
