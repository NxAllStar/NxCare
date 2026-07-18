import { test, expect } from '@playwright/test';

// Wiring smoke test (TASK-021 close-out): proves the app boots under
// Playwright and that RouteGuard (FR-18 AC-18.1) actually redirects an
// unauthenticated visit. Not the golden-path suite - that is TASK-024.
test.describe('app boot and route guard', () => {
  test('unauthenticated visit to / redirects to /login', async ({ page }) => {
    await page.goto('/');

    await expect(page).toHaveURL(/\/login$/);
    // The login screen renders the app name from the i18n dictionary
    // (VI default, see src/i18n/dictionaries/vi.ts "app.name": "VAIC"),
    // confirming the app actually booted rather than showing a blank page.
    await expect(page.getByText('VAIC', { exact: true })).toBeVisible();
  });
});
