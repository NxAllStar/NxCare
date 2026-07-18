/**
 * TASK-026 locked role -> permitted-screens contract (task file "Role ->
 * permitted-screens contract", locked by spec-guardian 2026-07-18 from
 * specs 06 + 10):
 *
 * | Role         | SCR-03 | SCR-04 | SCR-05 | SCR-06 | SCR-07 |
 * |--------------|--------|--------|--------|--------|--------|
 * | doctor       | Yes    | Yes    | No     | No     | No     |
 * | technician   | No     | No     | Yes    | No     | No     |
 * | coordinator  | No     | No     | No     | Yes    | Yes    |
 * | admin        | No     | No     | No     | Yes    | Yes    |
 *
 * SCR-06 is "coordinator OR admin" (admin reaches the flagship dashboard,
 * not just non-coordinators being blocked). SCR-07 admits both coordinator
 * (read-only audit) and admin (full) at the route level - the sub-element
 * split (simulator config admin-only) is deferred to the real SCR-07 task.
 * Role-hierarchy inheritance is capability-only: admin does NOT gain
 * SCR-03/04/05.
 *
 * The sidebar (ConsoleShell) and the client-side route guard (ScreenGuard)
 * both read this single table, so they can never drift from each other.
 * This is a UX convenience gate only - the server is the real
 * authorization boundary (NFR-SEC-05); real server-side authz (FR-18
 * AC-18.3, BR-28) is explicitly out of scope for this task.
 */
import type { DictKey } from '@/i18n';

export type StaffRole = 'doctor' | 'technician' | 'coordinator' | 'admin';

export type ConsoleScreenId = 'SCR-03' | 'SCR-04' | 'SCR-05' | 'SCR-06' | 'SCR-07';

export interface ConsoleScreenDef {
  id: ConsoleScreenId;
  /** Route path, absolute within the console router's basename ("/console"). */
  path: string;
  /** Short sidebar nav label. */
  navLabelKey: DictKey;
  /** Full on-screen title (matches the spec 10 screen name). */
  titleKey: DictKey;
}

export const CONSOLE_SCREENS: ConsoleScreenDef[] = [
  {
    id: 'SCR-03',
    path: '/consult',
    navLabelKey: 'console.nav.consult',
    titleKey: 'console.screen.consult.title',
  },
  {
    id: 'SCR-04',
    path: '/worklist',
    navLabelKey: 'console.nav.worklist',
    titleKey: 'console.screen.worklist.title',
  },
  {
    id: 'SCR-05',
    path: '/tasks',
    navLabelKey: 'console.nav.tasks',
    titleKey: 'console.screen.tasks.title',
  },
  {
    id: 'SCR-06',
    path: '/dashboard',
    navLabelKey: 'console.nav.dashboard',
    titleKey: 'console.screen.dashboard.title',
  },
  {
    id: 'SCR-07',
    path: '/audit',
    navLabelKey: 'console.nav.audit',
    titleKey: 'console.screen.audit.title',
  },
];

// The locked contract table, row for row - see the doc block above.
const ROLE_SCREEN_ACCESS: Record<StaffRole, ConsoleScreenId[]> = {
  doctor: ['SCR-03', 'SCR-04'],
  technician: ['SCR-05'],
  coordinator: ['SCR-06', 'SCR-07'],
  admin: ['SCR-06', 'SCR-07'],
};

export const ROLE_LABEL_KEY: Record<StaffRole, DictKey> = {
  doctor: 'console.role.doctor',
  technician: 'console.role.technician',
  coordinator: 'console.role.coordinator',
  admin: 'console.role.admin',
};

export function permittedScreens(role: StaffRole): ConsoleScreenId[] {
  return ROLE_SCREEN_ACCESS[role];
}

export function canAccessScreen(role: StaffRole, screen: ConsoleScreenId): boolean {
  return ROLE_SCREEN_ACCESS[role].includes(screen);
}

export function screenDef(id: ConsoleScreenId): ConsoleScreenDef {
  const def = CONSOLE_SCREENS.find((s) => s.id === id);
  if (!def) {
    throw new Error(`unknown console screen: ${id}`);
  }
  return def;
}

export function screenPath(id: ConsoleScreenId): string {
  return screenDef(id).path;
}

/**
 * The first screen permitted to `role` - used as both the `/console` index
 * redirect target and the fallback a role lands on when it visits a screen
 * the contract table does not permit it to reach.
 */
export function defaultPathForRole(role: StaffRole): string {
  const [first] = permittedScreens(role);
  return first ? screenPath(first) : '/login';
}
