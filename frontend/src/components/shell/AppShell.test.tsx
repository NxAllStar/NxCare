/**
 * AppShell - proves the mobile-first single-column shell renders the
 * signature 5-tab nav plus the assistant FAB on every authenticated screen
 * (spec 10 cross-cutting rules: patient surface is mobile-first, single
 * column, thumb-reachable actions).
 */
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, expect, it } from 'vitest';
import { I18nProvider } from '@/i18n';
import { AppShell } from './AppShell';

function renderShell() {
  return render(
    <I18nProvider>
      <MemoryRouter initialEntries={['/home']}>
        <Routes>
          <Route element={<AppShell />}>
            <Route path="/home" element={<p>home screen content</p>} />
          </Route>
        </Routes>
      </MemoryRouter>
    </I18nProvider>,
  );
}

describe('AppShell (mobile-first shell: 5-tab nav + FAB)', () => {
  it('renders the routed screen content through the outlet', () => {
    renderShell();
    expect(screen.getByText('home screen content')).toBeInTheDocument();
  });

  it('renders the 5-tab bottom nav', () => {
    renderShell();
    expect(screen.getAllByRole('link', { name: /Trang chủ|Lịch khám|Lộ trình|Hồ sơ sức khỏe|Thêm/ })).toHaveLength(5);
  });

  it('renders the assistant FAB reachable from every screen', () => {
    renderShell();
    expect(screen.getByRole('link', { name: 'Trợ lý' })).toBeInTheDocument();
  });

  it('constrains the layout to a single mobile-first column', () => {
    renderShell();
    expect(screen.getByTestId('app-shell')).toHaveClass('max-w-xl');
  });
});
