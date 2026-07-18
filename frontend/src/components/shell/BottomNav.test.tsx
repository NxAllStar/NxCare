/**
 * BottomNav - proves the patient IA's signature 5-tab bar (PRD-FR-12 3.2):
 * a fixed 5-item tab bar, thumb-reachable, plain Vietnamese labels.
 */
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { I18nProvider } from '@/i18n';
import { BottomNav } from './BottomNav';

function renderNav(initialPath = '/home') {
  return render(
    <I18nProvider>
      <MemoryRouter initialEntries={[initialPath]}>
        <BottomNav />
      </MemoryRouter>
    </I18nProvider>,
  );
}

describe('BottomNav (PRD-FR-12 3.2 - fixed 5-item tab bar)', () => {
  it('renders exactly 5 tabs', () => {
    renderNav();
    expect(screen.getAllByRole('link')).toHaveLength(5);
  });

  it('renders the five Vietnamese tab labels by default', () => {
    renderNav();
    expect(screen.getByRole('link', { name: /Trang chủ/ })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Lịch khám/ })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Lộ trình/ })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Hồ sơ sức khỏe/ })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Thêm/ })).toBeInTheDocument();
  });

  it('marks the tab matching the current route as the current page', () => {
    renderNav('/journey');
    expect(screen.getByRole('link', { name: /Lộ trình/ })).toHaveAttribute('aria-current', 'page');
  });
});
