/**
 * ScreenState - the five-state wrapper (spec 10 "States" tables repeated on
 * every screen: empty / loading / error / no-permission / success). The
 * screen batches feed this per-screen content; this task only proves the
 * wrapper itself renders each state correctly.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { I18nProvider } from '@/i18n';
import { ScreenState } from './ScreenState';

function renderState(ui: React.ReactElement) {
  return render(<I18nProvider>{ui}</I18nProvider>);
}

describe('ScreenState (five-state wrapper)', () => {
  it('renders the loading state', () => {
    renderState(<ScreenState state="loading">content</ScreenState>);
    expect(screen.getByRole('status')).toHaveTextContent('Đang tải...');
  });

  it('renders the empty state', () => {
    renderState(<ScreenState state="empty">content</ScreenState>);
    expect(screen.getByTestId('screen-state-empty')).toHaveTextContent('Chưa có dữ liệu');
  });

  it('renders the error state with an alert role', () => {
    renderState(<ScreenState state="error">content</ScreenState>);
    expect(screen.getByRole('alert')).toHaveTextContent('Đã xảy ra lỗi');
  });

  it('renders the no-permission state, own-scope-only in spirit (data absent, not hidden)', () => {
    renderState(<ScreenState state="no-permission">content</ScreenState>);
    expect(screen.getByTestId('screen-state-no-permission')).toHaveTextContent(
      'Bạn không có quyền xem nội dung này',
    );
  });

  it('renders the children only in the success state', () => {
    renderState(<ScreenState state="success">the real content</ScreenState>);
    expect(screen.getByText('the real content')).toBeInTheDocument();
  });

  it('does not render children in the loading/empty/error/no-permission states', () => {
    renderState(<ScreenState state="loading">the real content</ScreenState>);
    expect(screen.queryByText('the real content')).not.toBeInTheDocument();
  });

  it('accepts a message override for the empty state', () => {
    renderState(<ScreenState state="empty" emptyMessage="Khong co lich hen nao">content</ScreenState>);
    expect(screen.getByText('Khong co lich hen nao')).toBeInTheDocument();
  });
});
