import { defineConfig, devices } from '@playwright/test';

// Playwright wiring for the patient app (TASK-021 close-out). This is
// wiring proof only - a single chromium project and one smoke spec. The
// full golden-path e2e suite is TASK-024's scope, not this file's.
//
// testDir is pinned to ./e2e so Playwright never walks the rest of the
// frontend/ tree - in particular never node_modules.orig-rootowned/ (a
// local leftover from a permission workaround during `npm install`, see
// TASK-021 session log) and never src/ (that is Vitest's job, see
// vitest.config.ts).
const PORT = 4319;
const BASE_URL = `http://127.0.0.1:${PORT}`;

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: 'list',
  use: {
    baseURL: BASE_URL,
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: {
    command: `npm run dev -- --port ${PORT} --strictPort`,
    url: BASE_URL,
    reuseExistingServer: !process.env.CI,
    timeout: 120_000,
  },
});
