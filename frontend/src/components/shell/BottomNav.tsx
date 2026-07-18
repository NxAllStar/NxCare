/**
 * BottomNav - the fixed 5-tab bar (PRD-FR-12 3.1/3.2): Trang chu / Lich kham
 * / Lo trinh / Ho so suc khoe / Them, thumb-reachable at the bottom of the
 * screen. No hidden deep menus - this is the entire patient navigation
 * surface besides the assistant FAB.
 *
 * Judgment call (TASK-021, recorded in the task session log): the sitemap
 * (PRD-FR-12 3.1) does not name a single landing route for "Lich kham",
 * "Ho so suc khoe", or "Them" - each fans out to several P0/P1/P2 screens
 * and the source ASCII layout shows "Them" as its own sub-menu with no
 * dedicated route in this task's route list. This foundation picks the
 * first P0/P1 screen already planned for each tab's group as its landing
 * route (book/results/settings); a later batch may promote a dedicated
 * index screen without changing this component's shape.
 */
import { NavLink } from 'react-router-dom';
import { useI18n, type DictKey } from '@/i18n';
import { cn } from '@/lib/utils';
import { CalendarIcon, HeartPulseIcon, HomeIcon, MoreIcon, RouteIcon } from '@/components/icons';
import type { ComponentType, SVGProps } from 'react';

interface TabDef {
  to: string;
  labelKey: DictKey;
  Icon: ComponentType<SVGProps<SVGSVGElement>>;
}

const TABS: TabDef[] = [
  { to: '/home', labelKey: 'nav.home', Icon: HomeIcon },
  { to: '/book', labelKey: 'nav.book', Icon: CalendarIcon },
  { to: '/journey', labelKey: 'nav.journey', Icon: RouteIcon },
  { to: '/results', labelKey: 'nav.records', Icon: HeartPulseIcon },
  { to: '/settings', labelKey: 'nav.more', Icon: MoreIcon },
];

export function BottomNav() {
  const { t } = useI18n();

  return (
    <nav
      aria-label={t('nav.home')}
      className="fixed inset-x-0 bottom-0 z-40 border-t border-border bg-card/95 backdrop-blur"
    >
      <ul className="mx-auto flex max-w-xl items-stretch justify-between px-2 pb-safe pt-2">
        {TABS.map(({ to, labelKey, Icon }) => (
          <li key={to} className="flex-1">
            <NavLink
              to={to}
              className={({ isActive }) =>
                cn(
                  'flex flex-col items-center gap-1 rounded-2xl py-1.5 text-[11px] font-bold ' +
                    'text-neutral-400 transition-colors',
                  isActive && 'text-primary',
                )
              }
            >
              {({ isActive }) => (
                <>
                  <Icon className={cn('h-[22px] w-[22px]', isActive && 'stroke-[2]')} />
                  <span>{t(labelKey)}</span>
                </>
              )}
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}
