/**
 * TASK-026 acceptance criteria under test:
 * - "Navigating to /console with no staff session lands on the console
 *   login."
 * - "After selecting a staff role ... a role visiting a screen not
 *   permitted to it is redirected (e.g. a doctor cannot reach SCR-06; both
 *   coordinator and admin can; admin reaches SCR-06 too)."
 * - "Every stub screen renders inside the desktop shell ..."
 *
 * This exercises the full console router (login -> role select -> guarded
 * routes) rather than any one module in isolation, so a regression in how
 * the pieces are wired together (not just in access.ts's table) would fail
 * a test here. Each case gets its own `it()` (one render per test) rather
 * than several renders looped inside one test, so a failure is isolated to
 * exactly the (role, screen) pair that broke.
 *
 * Content assertions use `getByRole('heading', ...)` rather than a bare
 * text query: the sidebar's own nav label can read the same words as a
 * screen's full title (both come from spec 10's screen names), so scoping
 * to the page's <h1> is what actually distinguishes "this screen rendered"
 * from "this screen is merely listed in the sidebar".
 */
import { afterEach, describe, expect, it } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ConsoleApp } from './ConsoleApp';
import { STAFF_SESSION_STORAGE_KEY } from './auth/StaffAuthContext';
import { defaultPathForRole, screenPath, type ConsoleScreenId, type StaffRole } from './access';

const SCREEN_HEADING: Record<ConsoleScreenId, RegExp> = {
  'SCR-03': /Màn khám và chỉ định|Consult and orders/,
  'SCR-04': /Worklist bác sĩ|Doctor worklist/,
  'SCR-05': /Màn task kỹ thuật viên|Technician task view/,
  'SCR-06': /Dashboard điều phối|Coordinator dashboard/,
  'SCR-07': /Console quản trị và audit|Admin and audit console/,
};

const ROLE_BUTTON_LABEL: Record<StaffRole, RegExp> = {
  doctor: /Bác sĩ|Doctor/,
  technician: /Kỹ thuật viên|Technician/,
  coordinator: /Điều phối viên|Coordinator/,
  admin: /Quản trị viên|Admin/,
};

const CONTRACT: Array<{ role: StaffRole; permitted: ConsoleScreenId[]; forbidden: ConsoleScreenId[] }> = [
  { role: 'doctor', permitted: ['SCR-03', 'SCR-04'], forbidden: ['SCR-05', 'SCR-06', 'SCR-07'] },
  { role: 'technician', permitted: ['SCR-05'], forbidden: ['SCR-03', 'SCR-04', 'SCR-06', 'SCR-07'] },
  { role: 'coordinator', permitted: ['SCR-06', 'SCR-07'], forbidden: ['SCR-03', 'SCR-04', 'SCR-05'] },
  { role: 'admin', permitted: ['SCR-06', 'SCR-07'], forbidden: ['SCR-03', 'SCR-04', 'SCR-05'] },
];

function goTo(path: string) {
  window.history.pushState({}, '', path);
}

// ConsoleApp is rendered directly here (not through the top-level App path
// switch), so its own BrowserRouter basename ("/console") must actually be
// present in window.location.pathname or the router matches nothing.
function goToConsole(pathWithinConsole: string) {
  goTo(`/console${pathWithinConsole}`);
}

function seedSession(role: StaffRole) {
  window.sessionStorage.setItem(
    STAFF_SESSION_STORAGE_KEY,
    JSON.stringify({ role, displayName: 'Demo staff', issuedAt: new Date().toISOString() }),
  );
}

function defaultScreenFor(role: StaffRole): ConsoleScreenId {
  const path = defaultPathForRole(role);
  const match = (['SCR-03', 'SCR-04', 'SCR-05', 'SCR-06', 'SCR-07'] as ConsoleScreenId[]).find(
    (id) => screenPath(id) === path,
  );
  if (!match) throw new Error(`no screen for default path ${path}`);
  return match;
}

describe('ConsoleApp (TASK-026 foundation)', () => {
  afterEach(() => {
    goTo('/console');
  });

  it('with no staff session, /console/dashboard lands on the console login', () => {
    goTo('/console/dashboard');
    render(<ConsoleApp />);
    expect(screen.getByRole('heading', { name: /Đăng nhập nhân viên|Staff login/ })).toBeInTheDocument();
  });

  it("selecting a role logs in and lands on that role's default permitted screen", async () => {
    const user = userEvent.setup();
    goTo('/console');
    render(<ConsoleApp />);

    await user.click(screen.getByRole('button', { name: ROLE_BUTTON_LABEL.doctor }));

    expect(
      await screen.findByRole('heading', { name: SCREEN_HEADING[defaultScreenFor('doctor')] }),
    ).toBeInTheDocument();
  });

  describe('login honors the originally requested screen (code-reviewer Minor: dead redirect state)', () => {
    it('requesting a permitted screen while signed out, then logging in, lands back on that screen (not the role default)', async () => {
      const user = userEvent.setup();
      goToConsole(screenPath('SCR-04')); // doctor worklist: permitted for doctor, but not doctor's default (SCR-03)
      render(<ConsoleApp />);

      // No session yet -> redirected to login.
      expect(await screen.findByRole('heading', { name: /Đăng nhập nhân viên|Staff login/ })).toBeInTheDocument();

      await user.click(screen.getByRole('button', { name: ROLE_BUTTON_LABEL.doctor }));

      expect(await screen.findByRole('heading', { name: SCREEN_HEADING['SCR-04'] })).toBeInTheDocument();
      expect(screen.queryByRole('heading', { name: SCREEN_HEADING['SCR-03'] })).not.toBeInTheDocument();
    });

    it('requesting a screen not permitted to the chosen role falls back to that role\'s own default screen, never the forbidden one', async () => {
      const user = userEvent.setup();
      goToConsole(screenPath('SCR-06')); // dashboard: not permitted for doctor
      render(<ConsoleApp />);

      expect(await screen.findByRole('heading', { name: /Đăng nhập nhân viên|Staff login/ })).toBeInTheDocument();

      await user.click(screen.getByRole('button', { name: ROLE_BUTTON_LABEL.doctor }));

      expect(
        await screen.findByRole('heading', { name: SCREEN_HEADING[defaultScreenFor('doctor')] }),
      ).toBeInTheDocument();
      expect(screen.queryByRole('heading', { name: SCREEN_HEADING['SCR-06'] })).not.toBeInTheDocument();
    });
  });

  it('admin reaches SCR-06 directly (coordinator OR admin, not "non-coordinator blocked")', async () => {
    seedSession('admin');
    goToConsole(screenPath('SCR-06'));
    render(<ConsoleApp />);
    expect(await screen.findByRole('heading', { name: SCREEN_HEADING['SCR-06'] })).toBeInTheDocument();
  });

  it('the top bar shows the role label for the signed-in staff member', async () => {
    seedSession('coordinator');
    goToConsole(screenPath('SCR-06'));
    render(<ConsoleApp />);
    await screen.findByRole('heading', { name: SCREEN_HEADING['SCR-06'] });
    expect(screen.getByText(ROLE_BUTTON_LABEL.coordinator)).toBeInTheDocument();
  });

  for (const { role, permitted, forbidden } of CONTRACT) {
    for (const screenId of permitted) {
      it(`${role} reaches ${screenId} directly by path (permitted)`, async () => {
        seedSession(role);
        goToConsole(screenPath(screenId));
        render(<ConsoleApp />);
        expect(await screen.findByRole('heading', { name: SCREEN_HEADING[screenId] })).toBeInTheDocument();
      });
    }

    for (const screenId of forbidden) {
      it(`${role} is redirected away from ${screenId} (not permitted)`, async () => {
        seedSession(role);
        goToConsole(screenPath(screenId));
        render(<ConsoleApp />);
        const fallback = defaultScreenFor(role);
        expect(await screen.findByRole('heading', { name: SCREEN_HEADING[fallback] })).toBeInTheDocument();
        expect(screen.queryByRole('heading', { name: SCREEN_HEADING[screenId] })).not.toBeInTheDocument();
      });
    }
  }
});
