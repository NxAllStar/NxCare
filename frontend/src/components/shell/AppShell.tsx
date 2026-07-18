/**
 * AppShell - the mobile-first, single-column app shell shared by every
 * authenticated patient screen (spec 10 cross-cutting rules; PRD-FR-12
 * 3.2 navigation structure): a context header (profile chip + notification
 * bell), the routed screen in the middle, the assistant FAB floating above,
 * and the 5-tab bar fixed at the bottom.
 *
 * The header reads the session non-throwingly so the shell still renders in
 * isolation (AppShell.test) where no AuthProvider is mounted.
 */
import { Link, Outlet } from 'react-router-dom';
import { useI18n } from '@/i18n';
import { useOptionalSession } from '@/auth/AuthContext';
import { BellIcon, ChevronDownIcon } from '@/components/icons';
import { Avatar } from '@/components/primitives';
import { AssistantFab } from './AssistantFab';
import { BottomNav } from './BottomNav';

export function AppShell() {
  const { t } = useI18n();
  const session = useOptionalSession();
  const patientName = session?.patient.fullName ?? t('app.name');

  return (
    <div
      data-testid="app-shell"
      className="mx-auto flex min-h-screen max-w-xl flex-col bg-background text-foreground"
    >
      <header className="sticky top-0 z-20 flex items-center justify-between border-b border-border bg-card px-5 pb-3 pt-safe">
        {session ? (
          <Link
            to="/family"
            aria-label={t('family.switcherLabel')}
            className="flex items-center gap-2 rounded-pill bg-muted py-1 pl-1 pr-3.5 text-sm font-semibold transition-colors active:bg-border"
          >
            <Avatar name={patientName} size="sm" />
            <span className="max-w-[10rem] truncate">{patientName}</span>
            <ChevronDownIcon className="h-2.5 w-2.5 text-muted-foreground" />
          </Link>
        ) : (
          <span className="text-base font-bold text-primary">{t('app.name')}</span>
        )}

        <Link
          to="/notifications"
          aria-label={t('nav.notifications')}
          className="relative flex h-10 w-10 items-center justify-center rounded-pill border border-border bg-card text-foreground transition-colors active:bg-muted"
        >
          <BellIcon className="h-5 w-5" />
          <span
            aria-hidden="true"
            className="absolute right-2 top-2 h-2 w-2 rounded-full border-[1.5px] border-card bg-danger"
          />
        </Link>
      </header>

      <main className="flex-1 pb-28">
        <Outlet />
      </main>

      <AssistantFab />
      <BottomNav />
    </div>
  );
}
