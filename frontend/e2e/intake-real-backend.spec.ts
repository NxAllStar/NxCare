import { test, expect } from '@playwright/test';

// Golden-path e2e against the REAL FastAPI backend (TASK-024): login (mocked
// client-side session, see src/lib/api/session.ts - no auth HTTP endpoint
// exists yet) -> intake chat, which does hit the real
// vaic.api.intake_routes:/api/intake/chat over HTTP (playwright.config.ts
// boots uvicorn alongside Vite). No LLM provider is configured for this
// backend process, so triage deterministically falls back to
// RuleBasedTriageLLM - the reply text asserted below is the fixed
// _ROUTINE_REPLY_VI string, not a mocked frontend value.
test.describe('patient golden path against the real backend', () => {
  test('login -> intake chat gets a real triage reply and slot suggestions', async ({ page }) => {
    await page.goto('/login');

    // Quick-select demo account button (BN-000123) - same shape a manual
    // patient-code/password submit would produce (src/pages/LoginPage.tsx).
    await page.getByRole('button', { name: /BN-000123/ }).click();

    await expect(page).toHaveURL(/\/home$/);

    await page.goto('/intake');

    const input = page.getByLabel('Ô nhập tin nhắn');
    await input.fill('toi bi dau bung duoi va sot nhe 2 hom nay');
    await page.getByRole('button', { name: 'Gửi' }).click();

    const stream = page.getByTestId('intake-chat-stream');
    await expect(stream.getByText('toi bi dau bung duoi va sot nhe 2 hom nay')).toBeVisible();

    // Real HTTP round trip to the backend - deterministic rule-based reply
    // text (_ROUTINE_REPLY_VI, unaccented ASCII in the source), since no
    // LLM_API_KEY/LLM_API_BASE_URL is set for the e2e backend process
    // (playwright.config.ts webServer env).
    await expect(
      stream.getByText(
        'Cam on ban da mo ta trieu chung. Day la goi y dinh tuyen, khong phai chan doan - minh de xuat vai khung gio it dong ben duoi.',
      ),
    ).toBeVisible({ timeout: 10_000 });

    await expect(page.getByText('Khung giờ đề xuất')).toBeVisible();
  });
});
