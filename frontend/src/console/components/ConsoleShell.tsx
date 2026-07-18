import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { useI18n } from '@/i18n';
import { cn } from '@/lib/utils';
import { Avatar } from '@/components/primitives';
import {
  ActivityIcon,
  BellIcon,
  CalendarIcon,
  CheckIcon,
  ChevronRightIcon,
  ClipboardListIcon,
  ClockIcon,
  GridIcon,
  HelpIcon,
  LogoutIcon,
  SearchIcon,
  ShieldIcon,
  SparkleIcon,
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

const AGENT_FEED = [
  { agent: 'Trợ lý điều phối', text: 'Dàn tải: Khoa Ngoại đang 82% công suất, đề xuất chuyển 2 ca sang khung 14h.', time: '2 phút', tier: 'Tự động', color: 'success', icon: GridIcon, iconBg: 'bg-success' },
  { agent: 'Trợ lý kế hoạch', text: 'BN-2041 (Nguyễn Thị Lan): sinh lộ trình 3 bước sau khi bác sĩ ký chỉ định.', time: '5 phút', tier: 'Tự động', color: 'success', icon: CalendarIcon, iconBg: 'bg-success' },
  { agent: 'Trợ lý sự cố', text: 'Máy X-quang #2 báo lỗi. Phạm vi ảnh hưởng 12 ca. Đang tính phương án lập lại kế hoạch.', time: '6 phút', tier: 'Chờ duyệt', color: 'warning', icon: ShieldIcon, iconBg: 'bg-warning' },
  { agent: 'Trợ lý hành trình', text: 'BN-2041 hỏi có được ăn không - đã lấy máu, cho phép ăn nhẹ, giữ chỗ siêu âm.', time: '8 phút', tier: 'Tự động', color: 'success', icon: CheckIcon, iconBg: 'bg-success' },
  { agent: 'Trợ lý dự báo', text: 'Dự báo tải 4h tới tăng 15% do đợt khám định kỳ chiều.', time: '12 phút', tier: 'Tự động', color: 'success', icon: BellIcon, iconBg: 'bg-primary' },
];

export function ConsoleShell() {
  const { t } = useI18n();
  const navigate = useNavigate();
  const session = useOptionalStaffSession();
  const { logout } = useStaffAuth();
  const role = session?.role;
  const items = role ? CONSOLE_SCREENS.filter((s) => permittedScreens(role).includes(s.id)) : [];

  // Theme state
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    if (typeof document !== 'undefined') {
      return document.documentElement.classList.contains('dark') ? 'dark' : 'light';
    }
    return 'light';
  });

  const toggleTheme = () => {
    setTheme((current) => {
      const next = current === 'light' ? 'dark' : 'light';
      if (typeof document !== 'undefined') {
        document.documentElement.classList.toggle('dark', next === 'dark');
      }
      return next;
    });
  };

  // Clock state
  const [clock, setClock] = useState('');
  useEffect(() => {
    const updateClock = () => {
      setClock(
        new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit', second: '2-digit' }),
      );
    };
    updateClock();
    const interval = setInterval(updateClock, 1000);
    return () => clearInterval(interval);
  }, []);

  // Panel state - the assist rail is open by default (design/*.png)
  const [railOpen, setRailOpen] = useState(true);
  const [alertsOpen, setAlertsOpen] = useState(false);

  return (
    <div
      data-testid="console-shell"
      className="console-surface flex h-screen w-full flex-col overflow-hidden bg-background font-sans text-foreground transition-colors duration-200"
    >
      {/* ---------------------------------------------------------------- */}
      {/* Top header bar                                                    */}
      {/* ---------------------------------------------------------------- */}
      <header className="z-20 flex h-[76px] shrink-0 items-center justify-between gap-8 border-b border-border bg-card pr-8">
        {/* Left: brand + search. The brand block is exactly as wide as the
            left nav sidebar (264px) and the search box carries the same
            24px inset as the content canvas (p-6), so both edges line up
            with the workspace below (design/ki-thuat-vien-sceen.png). */}
        <div className="flex min-w-0 flex-1 items-center">
          <div className="flex w-[264px] shrink-0 items-center justify-center">
            <button
              type="button"
              className="group flex shrink-0 items-center gap-3"
              onClick={() => navigate('/')}
            >
              <span
                className="flex h-11 w-11 items-center justify-center bg-primary shadow-sm shadow-primary/25 transition-transform group-hover:scale-105"
                style={{ clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)' }}
              >
                <span className="font-mono text-sm font-extrabold text-white">NxC</span>
              </span>
              <span className="select-none text-[26px] font-extrabold tracking-tight text-foreground">
                Nx<span className="text-primary">Care</span>
              </span>
            </button>
          </div>

          <label className="relative ml-6 hidden w-[380px] shrink-0 md:block lg:w-[440px]">
            <SearchIcon className="pointer-events-none absolute left-3.5 top-1/2 h-[18px] w-[18px] -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              placeholder="Tìm bệnh nhân / mã / phòng..."
              className="w-full rounded-xl border border-border bg-muted/60 py-2.5 pl-11 pr-14 text-[15px] text-foreground outline-none transition-all placeholder:text-muted-foreground hover:border-primary/30 hover:bg-muted focus:border-primary/50 focus:bg-card focus:ring-2 focus:ring-primary/20"
            />
          </label>
        </div>

        {/* Right: status + actions */}
        <div className="flex shrink-0 items-center gap-14">
          {/* Clock */}
          <div className="hidden items-center gap-2 text-muted-foreground lg:flex">
            <ClockIcon className="h-[22px] w-[22px]" />
            <span className="font-sans text-lg font-semibold tabular-nums">{clock}</span>
          </div>

          {/* Alerts */}
          <div className="relative">
            <button
              type="button"
              onClick={() => setAlertsOpen((v) => !v)}
              className="relative flex h-10 w-10 items-center justify-center rounded-xl text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
              aria-label="Cảnh báo"
            >
              <span className="relative flex h-[22px] w-[22px] items-center justify-center">
                <BellIcon className="h-[22px] w-[22px]" />
                <span className="absolute -right-2 -top-2 flex h-[16px] min-w-[16px] items-center justify-center rounded-full bg-danger px-1 font-mono text-[10px] font-bold leading-none text-danger-foreground ring-2 ring-card">
                  3
                </span>
              </span>
            </button>

            {alertsOpen && (
              <div className="absolute right-0 top-11 z-30 flex w-80 flex-col gap-2 rounded-2xl border border-border bg-card p-3 shadow-xl">
                <div className="mb-1 text-xs font-bold uppercase tracking-wider text-muted-foreground">
                  Thông báo hệ thống
                </div>
                <div className="rounded-xl bg-destructive/10 p-2.5 text-sm text-destructive">
                  Máy X-quang #2 báo lỗi - 12 ca bị ảnh hưởng.
                </div>
                <div className="rounded-xl bg-primary/10 p-2.5 text-sm text-primary">
                  Trợ lý kế hoạch đã sinh lộ trình cho BN-2041.
                </div>
              </div>
            )}
          </div>

          {/* User */}
          <div className="flex items-center gap-3">
            <Avatar name={session?.displayName ?? '?'} className="h-11 w-11 text-lg" />
            <div className="hidden text-left leading-tight lg:block">
              <div className="text-[17px] font-bold text-foreground">{session?.displayName}</div>
              <div className="text-[13px] uppercase tracking-wider text-muted-foreground">
                {role ? t(ROLE_LABEL_KEY[role]) : ''}
              </div>
            </div>
          </div>

          {/* Theme */}
          <button
            type="button"
            onClick={toggleTheme}
            className="flex h-10 w-10 items-center justify-center rounded-xl text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            aria-label="Đổi giao diện sáng/tối"
          >
            {theme === 'light' ? (
              <svg className="h-[21px] w-[21px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.75" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            ) : (
              <svg className="h-[21px] w-[21px]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.75" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364-6.364l-.707.707M6.343 17.657l-.707.707m12.728 0l-.707-.707M6.343 6.343l-.707-.707M12 8a4 4 0 100 8 4 4 0 000-8z" />
              </svg>
            )}
          </button>

          <button
            type="button"
            onClick={() => void logout()}
            aria-label={t('settings.logout')}
            className="flex h-10 w-10 items-center justify-center rounded-xl text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
          >
            <LogoutIcon className="h-[21px] w-[21px]" />
          </button>
        </div>
      </header>

      {/* ---------------------------------------------------------------- */}
      {/* Workspace body                                                    */}
      {/* ---------------------------------------------------------------- */}
      <div className="relative flex flex-1 overflow-hidden">
        {/* Left nav sidebar */}
        <aside className="flex w-[264px] shrink-0 select-none flex-col border-r border-border bg-card">
          <nav className="flex flex-1 flex-col gap-2 overflow-y-auto px-4 py-5">
            {items.map((item) => {
              const Icon = SCREEN_ICON[item.id];
              return (
                <NavLink
                  key={item.id}
                  to={item.path}
                  className={({ isActive }) =>
                    cn(
                      'group relative flex h-[60px] items-center gap-3.5 rounded-2xl px-3.5 text-base font-medium transition-all duration-200',
                      isActive
                        ? 'bg-primary/10 font-semibold text-primary shadow-sm shadow-primary/10'
                        : 'text-muted-foreground hover:translate-x-0.5 hover:bg-muted hover:text-foreground',
                    )
                  }
                >
                  {({ isActive }) => (
                    <>
                      {/* Active tab indicator - soft pill on the item's left edge */}
                      <span
                        aria-hidden="true"
                        className={cn(
                          'absolute left-0 top-1/2 h-7 w-1 -translate-y-1/2 rounded-full bg-primary transition-opacity duration-200',
                          isActive ? 'opacity-100' : 'opacity-0',
                        )}
                      />
                      <span
                        className={cn(
                          'flex h-11 w-11 shrink-0 items-center justify-center rounded-xl transition-colors duration-200',
                          isActive
                            ? 'bg-primary text-primary-foreground shadow-sm shadow-primary/30'
                            : 'bg-muted text-muted-foreground group-hover:bg-card group-hover:text-foreground',
                        )}
                      >
                        <Icon className="h-6 w-6" />
                      </span>
                      <span className="truncate">{t(item.navLabelKey)}</span>
                    </>
                  )}
                </NavLink>
              );
            })}
          </nav>

          {/* Sidebar footer */}
          <div className="flex flex-col gap-3 p-4">
            <button
              type="button"
              className="flex items-center gap-3 rounded-2xl border border-border bg-muted/40 px-4 py-3.5 text-sm font-semibold text-foreground transition-colors hover:bg-muted"
            >
              <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-card text-muted-foreground">
                <HelpIcon className="h-[18px] w-[18px]" />
              </span>
              Trợ giúp & Hỗ trợ
            </button>
            <div className="px-1 text-xs leading-relaxed text-muted-foreground">
              <div>© 2026 NxCare</div>
              <div>v1.0.0</div>
            </div>
          </div>
        </aside>

        {/* Content canvas */}
        <main className="relative flex-1 overflow-y-auto bg-muted/25 p-6">
          <div className="mx-auto h-full max-w-[1280px]">
            <Outlet />
          </div>
        </main>

        {/* Right assist rail - omitted for the technician role (design/ki-thuat-vien-sceen.png
            has no assist rail; the technician screen is execution-only, not supervisory). */}
        {role !== 'technician' && (
        <aside
          className={cn(
            'flex shrink-0 select-none flex-col border-l border-border bg-muted/25 transition-[width] duration-300 ease-in-out',
            railOpen ? 'w-[320px]' : 'w-12',
          )}
        >
          <div className="flex h-[56px] shrink-0 items-center justify-between px-4">
            {railOpen && (
              <span className="flex items-center gap-2 text-sm font-bold uppercase tracking-[0.1em] text-foreground">
                <ActivityIcon className="h-4 w-4 text-primary" />
                Hoạt động trợ lý
              </span>
            )}
            <button
              type="button"
              onClick={() => setRailOpen((v) => !v)}
              className={cn(
                'ml-auto flex h-8 w-8 items-center justify-center rounded-lg transition-colors hover:bg-muted hover:text-foreground',
                railOpen ? 'text-muted-foreground' : 'bg-primary/10 text-primary hover:bg-primary/15 hover:text-primary',
              )}
              aria-label={railOpen ? 'Thu gọn bảng trợ lý' : 'Mở bảng trợ lý'}
            >
              {railOpen ? (
                <ChevronRightIcon className="h-4 w-4" />
              ) : (
                <SparkleIcon className="h-[18px] w-[18px]" />
              )}
            </button>
          </div>

          {railOpen && (
            <>
              <div className="flex flex-1 flex-col gap-3 overflow-y-auto px-4 pb-3">
                {AGENT_FEED.map((feed, idx) => {
                  const FeedIcon = feed.icon;
                  return (
                    <div
                      key={idx}
                      className="flex flex-col gap-2 rounded-xl border border-border bg-card p-3.5 text-sm leading-relaxed shadow-sm transition-all duration-200 hover:border-primary/30 hover:shadow-md"
                    >
                      <div className="flex items-center gap-2.5">
                        <span
                          className={cn(
                            'flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-white',
                            feed.iconBg,
                          )}
                        >
                          <FeedIcon className="h-4 w-4" />
                        </span>
                        <span className="min-w-0 flex-1 truncate text-sm font-bold text-foreground">{feed.agent}</span>
                        <span className="shrink-0 font-mono text-xs tabular-nums text-muted-foreground">{feed.time}</span>
                      </div>
                      <p className="text-sm leading-relaxed text-muted-foreground">{feed.text}</p>
                      <span
                        className={cn(
                          'w-fit rounded-md px-2 py-0.5 text-xs font-bold uppercase tracking-wide',
                          feed.color === 'success' ? 'bg-success/10 text-success' : 'bg-warning/10 text-warning',
                        )}
                      >
                        {feed.tier}
                      </span>
                    </div>
                  );
                })}
              </div>
              <div className="shrink-0 px-4 pb-4">
                <button
                  type="button"
                  className="flex w-full items-center justify-center gap-1.5 rounded-xl border border-border bg-card py-2.5 text-sm font-semibold text-primary transition-colors hover:bg-primary/5"
                >
                  Xem tất cả hoạt động
                  <ChevronRightIcon className="h-3.5 w-3.5" />
                </button>
              </div>
            </>
          )}
        </aside>
        )}
      </div>
    </div>
  );
}
