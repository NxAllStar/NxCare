/**
 * LanguageToggle - proves FR-21 / NFR-USE-03: VI is the default, toggling to
 * EN changes display labels, and any English code rendered alongside it
 * (simulated here via a StatusChip-shaped code prop) never gets translated.
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';
import { I18nProvider, useI18n } from '@/i18n';
import { LanguageToggle } from './LanguageToggle';

function Probe() {
  const { t } = useI18n();
  return <p data-testid="probe">{t('login.submit')}</p>;
}

describe('LanguageToggle (FR-21 VI default, EN toggle)', () => {
  it('defaults to Vietnamese', () => {
    render(
      <I18nProvider>
        <Probe />
      </I18nProvider>,
    );
    expect(screen.getByTestId('probe')).toHaveTextContent('Đăng nhập');
  });

  it('switches every localised label from VI to EN when toggled', async () => {
    const user = userEvent.setup();
    render(
      <I18nProvider>
        <LanguageToggle />
        <Probe />
      </I18nProvider>,
    );

    expect(screen.getByTestId('probe')).toHaveTextContent('Đăng nhập');

    await user.click(screen.getByRole('button', { name: /EN/ }));

    expect(screen.getByTestId('probe')).toHaveTextContent('Log in');
  });

  it('never translates an English code even after switching locale', async () => {
    const user = userEvent.setup();
    render(
      <I18nProvider>
        <LanguageToggle />
        <span data-testid="code">PENDING</span>
      </I18nProvider>,
    );

    await user.click(screen.getByRole('button', { name: /EN/ }));

    expect(screen.getByTestId('code')).toHaveTextContent('PENDING');
  });
});
