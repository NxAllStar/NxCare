import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { defineConfig, devices } from '@playwright/test';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Playwright wiring for the patient app (TASK-021 close-out, extended for
// TASK-024). Boots the real Vite dev server AND the real FastAPI backend
// (vaic.api.app) so the golden-path spec exercises an actual HTTP round
// trip against /api/intake/chat - not a frontend mock. Screens that still
// have no wired backend (billing, booking, family, ...) keep using their
// frontend fixtures; nothing here changes those.
//
// testDir is pinned to ./e2e so Playwright never walks the rest of the
// frontend/ tree - in particular never node_modules.orig-rootowned/ (a
// local leftover from a permission workaround during `npm install`, see
// TASK-021 session log) and never src/ (that is Vitest's job, see
// vitest.config.ts).
const FRONTEND_PORT = 4319;
const BASE_URL = `http://127.0.0.1:${FRONTEND_PORT}`;

// Dedicated e2e-only port, distinct from the API_PORT a developer may already
// have running locally (see .env / scripts/run_backend.sh) so this suite
// never collides with, or reuses, someone's manual dev session.
const BACKEND_PORT = 8010;
const BACKEND_URL = `http://127.0.0.1:${BACKEND_PORT}`;
const REPO_ROOT = path.resolve(__dirname, '..');

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
  webServer: [
    {
      // Real FastAPI backend (src/vaic/api/app.py). In-memory repository
      // (no Redis/Postgres dependency for e2e) and no LLM provider
      // configured, so triage deterministically falls back to
      // RuleBasedTriageLLM (src/vaic/api/intake_routes.py) - a real network
      // call to our own app, never to a real third-party model provider.
      command:
        `uv run uvicorn vaic.api.app:app --host 127.0.0.1 --port ${BACKEND_PORT}`,
      cwd: REPO_ROOT,
      url: `${BACKEND_URL}/health`,
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
      env: {
        // `vaic` has no [build-system] in pyproject.toml, so `uv run` does
        // not install it into the venv as a package - PYTHONPATH is how
        // pytest already resolves it too (see [tool.pytest.ini_options]).
        PYTHONPATH: path.join(REPO_ROOT, 'src'),
        VAIC_STATE_BACKEND: 'memory',
        VAIC_CORS_ORIGINS: BASE_URL,
        API_PORT: String(BACKEND_PORT),
        LLM_API_KEY: '',
        LLM_API_BASE_URL: '',
        POSTGRES_PASSWORD: '',
      },
    },
    {
      // --host 127.0.0.1 forces IPv4: Vite's default `localhost` binding
      // resolves to `::1` only on this host, which left BASE_URL (127.0.0.1)
      // unreachable and the webServer readiness check timing out.
      command: `npm run dev -- --port ${FRONTEND_PORT} --strictPort --host 127.0.0.1`,
      url: BASE_URL,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        VITE_API_BASE_URL: BACKEND_URL,
      },
    },
  ],
});
