/**
 * PatientCodeQr - proves the shared patient-code display used by /checkin
 * and /journey (FR-17: the patient PRESENTS the code for staff to scan).
 *
 * This is a visual placeholder, not a real scannable QR encoder - adding a
 * QR-generation dependency is a licensing decision this task does not make
 * (ip-compliance.md); the human-readable code itself is what the demo
 * actually functions on.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { I18nProvider } from '@/i18n';
import { PatientCodeQr } from './PatientCodeQr';

function renderCode(code: string) {
  return render(
    <I18nProvider>
      <PatientCodeQr code={code} />
    </I18nProvider>,
  );
}

describe('PatientCodeQr (FR-17 patient-code display)', () => {
  it('renders the human-readable patient code in the DOM', () => {
    renderCode('BN-000123');
    expect(screen.getByText('BN-000123')).toBeInTheDocument();
  });

  it('exposes an accessible name that includes the code (screen-reader users can still act on it)', () => {
    renderCode('BN-000123');
    expect(screen.getByRole('img', { name: /BN-000123/ })).toBeInTheDocument();
  });

  it('renders a different visual pattern for a different code (deterministic, not decorative-only)', () => {
    const { container: containerA } = renderCode('BN-000123');
    const patternA = containerA.querySelector('[data-testid="patient-code-qr-pattern"]')?.innerHTML;
    const { container: containerB } = renderCode('BN-000456');
    const patternB = containerB.querySelector('[data-testid="patient-code-qr-pattern"]')?.innerHTML;
    expect(patternA).not.toEqual(patternB);
  });
});
