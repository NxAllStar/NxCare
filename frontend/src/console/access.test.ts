/**
 * TASK-026 acceptance criteria under test:
 * - "the sidebar and the client-side route guard MUST enforce exactly this
 *   [role -> permitted-screens contract]" (task file, locked 2026-07-18).
 * - "a role visiting a screen not permitted to it per the contract table is
 *   redirected (e.g. a doctor cannot reach SCR-06; both coordinator and
 *   admin can; admin reaches SCR-06 too)".
 * - "Role-hierarchy inheritance ... is capability-only: admin does NOT gain
 *   SCR-03/04/05."
 *
 * This file asserts the pure `access.ts` contract table itself, row by row,
 * so the shell and the route guard (tested separately) can both be trusted
 * to read from a single, already-verified source of truth.
 */
import { describe, expect, it } from 'vitest';
import {
  canAccessScreen,
  CONSOLE_SCREENS,
  defaultPathForRole,
  permittedScreens,
  screenPath,
  type ConsoleScreenId,
  type StaffRole,
} from './access';

const ALL_SCREENS: ConsoleScreenId[] = ['SCR-03', 'SCR-04', 'SCR-05', 'SCR-06', 'SCR-07'];

const CONTRACT: Array<{ role: StaffRole; permitted: ConsoleScreenId[] }> = [
  { role: 'doctor', permitted: ['SCR-03', 'SCR-04'] },
  { role: 'technician', permitted: ['SCR-05'] },
  { role: 'coordinator', permitted: ['SCR-06', 'SCR-07'] },
  { role: 'admin', permitted: ['SCR-06', 'SCR-07'] },
];

describe('console role -> screen access contract (TASK-026 locked contract table)', () => {
  for (const { role, permitted } of CONTRACT) {
    for (const screen of ALL_SCREENS) {
      const expected = permitted.includes(screen);
      it(`${role} ${expected ? 'can' : 'cannot'} access ${screen}`, () => {
        expect(canAccessScreen(role, screen)).toBe(expected);
      });
    }

    it(`permittedScreens(${role}) is exactly [${permitted.join(', ')}]`, () => {
      expect(permittedScreens(role)).toEqual(permitted);
    });
  }

  it('SCR-06 boundary is "coordinator OR admin": admin reaches the flagship dashboard', () => {
    expect(canAccessScreen('admin', 'SCR-06')).toBe(true);
    expect(canAccessScreen('coordinator', 'SCR-06')).toBe(true);
  });

  it('SCR-07 route admits both coordinator (read-only) and admin (full)', () => {
    expect(canAccessScreen('coordinator', 'SCR-07')).toBe(true);
    expect(canAccessScreen('admin', 'SCR-07')).toBe(true);
  });

  it('admin does not inherit SCR-03/04/05 (capability-only role hierarchy)', () => {
    expect(canAccessScreen('admin', 'SCR-03')).toBe(false);
    expect(canAccessScreen('admin', 'SCR-04')).toBe(false);
    expect(canAccessScreen('admin', 'SCR-05')).toBe(false);
  });

  it('every screen in CONSOLE_SCREENS is reachable by at least one role', () => {
    for (const def of CONSOLE_SCREENS) {
      const reachable = CONTRACT.some(({ permitted }) => permitted.includes(def.id));
      expect(reachable).toBe(true);
    }
  });

  it('defaultPathForRole resolves to the first permitted screen path for every role', () => {
    expect(defaultPathForRole('doctor')).toBe(screenPath('SCR-03'));
    expect(defaultPathForRole('technician')).toBe(screenPath('SCR-05'));
    expect(defaultPathForRole('coordinator')).toBe(screenPath('SCR-06'));
    expect(defaultPathForRole('admin')).toBe(screenPath('SCR-06'));
  });
});
