/**
 * ConsoleShell - the desktop-first chrome shared by every authenticated
 * console screen (TASK-026 "Deliver" list item 3): a left sidebar nav
 * filtered by role per the locked contract (access.ts), and a top bar with
 * the signed-in user + role + a language toggle + logout. Not the patient
 * iPhone frame and not a bottom tab bar - built from the shared
 * primitives/tokens (frontend.md), desktop multi-pane (spec 10 "Visual
 * design direction" > Responsiveness).
 *
 * Reads the session non-throwingly so the shell still renders in isolation
 * (this component's own test) without crashing if a session is briefly
 * absent mid-transition.
 */
import { NavLink, Outlet } from 'react-router-dom';
import { useI18n } from '@/i18n';
import { cn } from '@/lib/utils';
import { Avatar, Button, LanguageToggle } from '@/components/primitives';
import {
  ClipboardListIcon,
  GridIcon,
  LogoutIcon,
  ShieldIcon,
  StethoscopeIcon,
  WrenchIcon,
} from '@/components/icons';
import type { ComponentType, SVGProps } from 'react';
import { CONSOLE_SCREENS, permittedScreens, ROLE_LABEL_KEY, type ConsoleScreenId } from '../access';
import { useOptionalStaffSession, useStaffAuth } from '../auth/StaffAuthContext';

const SCREEN_ICON: Record<ConsoleScreenId, ComponentType<SVGProps<SVGSVGElement>>> = {
  'SCR-03': StethoscopeIcon,
  'SCR-04': ClipboardListIcon,
  'SCR-05': WrenchIcon,
  'SCR-06': GridIcon,
  'SCR-07': ShieldIcon,
};

export function ConsoleShell() {
  const { t } = useI18n();
  const session = useOptionalStaffSession();
  const { logout } = useStaffAuth();
  const role = session?.role;
  const items = role ? CONSOLE_SCREENS.filter((s) => permittedScreens(role).includes(s.id)) : [];

  return (
    <div data-testid="console-shell" className="flex min-h-screen bg-background text-foreground">
      <aside className="flex w-64 shrink-0 flex-col border-r border-border bg-card px-3 py-5">
        <div className="mb-6 px-3 text-lg font-bold text-primary">{t('console.appName')}</div>
        <nav aria-label={t('console.sidebar.navLabel')} className="flex flex-col gap-1">
          {items.map((item) => {
            const Icon = SCREEN_ICON[item.id];
            return (
              <NavLink
                key={item.id}
                to={item.path}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold text-muted-foreground transition-colors',
                    'hover:bg-muted',
                    isActive && 'bg-primary/10 text-primary',
                  )
                }
              >
                <Icon className="h-5 w-5 shrink-0" />
                <span>{t(item.navLabelKey)}</span>
              </NavLink>
            );
          })}
        </nav>
      </aside>

      <div className="flex flex-1 flex-col">
        <header className="flex items-center justify-between border-b border-border bg-card px-6 py-3">
          <div className="flex items-center gap-3">
            <Avatar name={session?.displayName ?? '?'} />
            <div>
              <div className="text-sm font-semibold">{session?.displayName}</div>
              <div className="text-xs text-muted-foreground">
                {role ? t(ROLE_LABEL_KEY[role]) : ''}
              </div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <LanguageToggle />
            <Button variant="secondary" size="sm" onClick={() => void logout()}>
              <LogoutIcon className="h-4 w-4" />
              {t('settings.logout')}
            </Button>
          </div>
        </header>
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
