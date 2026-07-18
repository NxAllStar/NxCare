/**
 * Staff login (TASK-026): a role selector only - synthetic demo staff,
 * never a real account or password (agent-guardrails.md). Reachable at
 * /console when there is no staff session (see ConsoleRouteGuard).
 *
 * Split layout: a brand panel in the console blue on the left (quote +
 * operating stats), the role selector on the right - the left panel hides
 * below lg so mobile still gets the compact centered form.
 *
 * ConsoleRouteGuard captures the originally requested path in
 * `location.state.from` before redirecting here. After login, that path is
 * honored - but only if the selected role is actually permitted to reach it
 * (`canAccessScreen`); a role is never redirected to a screen the locked
 * contract table (access.ts) forbids it. Any other case (no `from`, `from`
 * matches no known screen, or the role cannot reach it) falls back to the
 * role's own default screen, exactly as before.
 */
import { useState, type FormEvent } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useI18n } from '@/i18n';
import {
  ClockIcon,
  GridIcon,
  HeartPulseIcon,
  ShieldIcon,
  StethoscopeIcon,
  TrendingUpIcon,
  WrenchIcon,
} from '@/components/icons';
import type { ComponentType, SVGProps } from 'react';
import { canAccessScreen, defaultPathForRole, ROLE_LABEL_KEY, screenForPath, STAFF_ROLES, type StaffRole } from '../access';
import { useStaffAuth } from '../auth/StaffAuthContext';

interface ConsoleLoginLocationState {
  from?: string;
}

const ROLE_ICON: Record<StaffRole, ComponentType<SVGProps<SVGSVGElement>>> = {
  doctor: StethoscopeIcon,
  technician: WrenchIcon,
  coordinator: GridIcon,
  admin: ShieldIcon,
};

const ROLE_DESC: Record<StaffRole, string> = {
  doctor: 'Khám, chỉ định và ký lộ trình cho bệnh nhân',
  technician: 'Thực hiện cận lâm sàng và ghi nhận kết quả',
  coordinator: 'Điều phối tải, duyệt đề xuất của trợ lý AI',
  admin: 'Điều phối tải, duyệt đề xuất AI và kiểm toán hệ thống',
};

/**
 * The demo login hides the coordinator card: coordinator and admin share the
 * exact same permitted screens (SCR-06 + SCR-07, access.ts), so two cards led
 * to two identical consoles. Admin is the single supervisory login. The
 * `StaffRole` type keeps 'coordinator' untouched because the locked TASK-026
 * contract table and the audit fixtures still reference it.
 */
const LOGIN_ROLES: readonly StaffRole[] = STAFF_ROLES.filter((role) => role !== 'coordinator');

const BRAND_STATS = [
  { value: '~12', unit: 'phút', label: 'Chờ trung bình', icon: ClockIcon },
  { value: '96.4', unit: '%', label: 'Bệnh nhân hài lòng', icon: HeartPulseIcon },
  { value: '+35', unit: '%', label: 'Hiệu suất phòng khám', icon: TrendingUpIcon },
];

function BrandMark({ size = 44 }: { size?: number }) {
  return (
    <span
      className="flex shrink-0 items-center justify-center bg-primary shadow-sm shadow-primary/25"
      style={{
        width: size,
        height: size,
        clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)',
      }}
    >
      <span className="font-mono text-sm font-extrabold text-white">NxC</span>
    </span>
  );
}

export function ConsoleLoginPage() {
  const { t } = useI18n();
  const { login, isAuthenticating } = useStaffAuth();
  const navigate = useNavigate();
  const location = useLocation();

  // Demo credential form: a role is picked, then any non-empty
  // username/password signs in. No demo account is hardcoded on purpose -
  // agent-guardrails.md forbids hardcoded credentials, and this login is
  // synthetic (StaffAuthContext stores only the role, never a password).
  const [selectedRole, setSelectedRole] = useState<StaffRole | null>(null);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    if (!selectedRole) {
      setFormError('Vui lòng chọn vai trò đăng nhập.');
      return;
    }
    if (!username.trim() || !password.trim()) {
      setFormError('Vui lòng nhập tên đăng nhập và mật khẩu.');
      return;
    }
    setFormError(null);
    await login(selectedRole);
    const from = (location.state as ConsoleLoginLocationState | null)?.from;
    const requestedScreen = from ? screenForPath(from) : undefined;
    const target =
      requestedScreen && canAccessScreen(selectedRole, requestedScreen)
        ? (from as string)
        : defaultPathForRole(selectedRole);
    navigate(target, { replace: true });
  };

  return (
    <div className="console-surface flex min-h-screen bg-background font-sans text-foreground">
      {/* ---------------------------------------------------------------- */}
      {/* Left: brand panel in the console blue                             */}
      {/* ---------------------------------------------------------------- */}
      <aside className="relative hidden w-[46%] shrink-0 flex-col justify-between overflow-hidden border-r border-border bg-primary/[0.06] p-12 lg:flex">
        {/* Soft blue washes - a tinted panel, not a solid blue block */}
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0"
          style={{
            background:
              'radial-gradient(48rem 34rem at -10% -10%, hsl(var(--primary) / 0.14), transparent 60%),' +
              'radial-gradient(40rem 30rem at 115% 115%, hsl(var(--primary) / 0.10), transparent 55%)',
          }}
        />

        {/* Brand lockup - links back to the public landing page */}
        <a
          href="/landing"
          aria-label="Về trang giới thiệu NxCare"
          className="relative flex w-fit items-center gap-3 transition-opacity hover:opacity-80"
        >
          <BrandMark />
          <span className="select-none text-2xl font-extrabold tracking-tight text-foreground">
            Nx<span className="text-primary">Care</span>
          </span>
        </a>

        {/* Quote */}
        <div className="relative flex max-w-md flex-col gap-6">
          <span aria-hidden="true" className="font-serif text-7xl font-bold leading-none text-primary/30">
            &ldquo;
          </span>
          <blockquote className="-mt-8 text-[28px] font-bold leading-snug tracking-tight text-foreground">
            Mỗi phút bệnh nhân bớt chờ đợi là một phút bác sĩ dành thêm cho việc chữa lành.
          </blockquote>
          <p className="text-[15px] leading-relaxed text-muted-foreground">
            Toàn bộ lộ trình chăm sóc được AI điều phối và tối ưu theo thời gian thực.
          </p>
          <div className="mt-2 grid grid-cols-3 gap-3">
            {BRAND_STATS.map((stat) => {
              const Icon = stat.icon;
              return (
                <div
                  key={stat.label}
                  className="flex flex-col gap-2.5 rounded-2xl border border-primary/15 bg-card/90 p-4 shadow-sm backdrop-blur-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-primary/35 hover:shadow-md"
                >
                  <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                    <Icon className="h-[18px] w-[18px]" />
                  </span>
                  <span className="flex items-baseline gap-1">
                    <span className="font-mono text-xl font-extrabold tabular-nums text-foreground">{stat.value}</span>
                    <span className="text-xs font-bold text-muted-foreground">{stat.unit}</span>
                  </span>
                  <span className="text-xs font-semibold leading-tight text-muted-foreground">{stat.label}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer */}
        <div className="relative text-sm text-muted-foreground">
          © 2026 NxCare
        </div>
      </aside>

      {/* ---------------------------------------------------------------- */}
      {/* Right: role selector                                              */}
      {/* ---------------------------------------------------------------- */}
      <main className="flex flex-1 items-center justify-center p-6">
        <div className="w-full max-w-md">
          {/* Compact brand for small screens (left panel hidden) */}
          <a
            href="/landing"
            aria-label="Về trang giới thiệu NxCare"
            className="mb-8 flex items-center justify-center gap-3 transition-opacity hover:opacity-80 lg:hidden"
          >
            <BrandMark />
            <span className="select-none text-2xl font-extrabold tracking-tight text-foreground">
              Nx<span className="text-primary">Care</span>
            </span>
          </a>

          <div className="mb-7">
            <h1 className="text-[28px] font-extrabold tracking-tight text-foreground">
              {t('console.login.title')}
            </h1>
            <p className="mt-2 text-[15px] leading-relaxed text-muted-foreground">
              {t('console.login.subtitle')}
            </p>
          </div>

          <form onSubmit={(e) => void handleSubmit(e)} className="flex flex-col gap-5">
            {/* Role picker */}
            <div className="flex flex-col gap-2.5" role="group" aria-label="Chọn vai trò">
              {LOGIN_ROLES.map((role) => {
                const Icon = ROLE_ICON[role];
                const isSelected = selectedRole === role;
                return (
                  <button
                    key={role}
                    type="button"
                    disabled={isAuthenticating}
                    aria-pressed={isSelected}
                    onClick={() => {
                      setSelectedRole(role);
                      setFormError(null);
                    }}
                    className={`group flex items-center gap-4 rounded-2xl border px-5 py-3.5 text-left shadow-sm transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 disabled:pointer-events-none disabled:opacity-60 ${
                      isSelected
                        ? 'border-primary/50 bg-primary/5 ring-2 ring-primary/25'
                        : 'border-border bg-card hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-md hover:shadow-primary/5'
                    }`}
                  >
                    <span
                      className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-xl transition-colors ${
                        isSelected
                          ? 'bg-primary text-primary-foreground shadow-sm shadow-primary/30'
                          : 'bg-primary/10 text-primary group-hover:bg-primary group-hover:text-primary-foreground'
                      }`}
                    >
                      <Icon className="h-[22px] w-[22px]" />
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block text-base font-bold text-foreground">{t(ROLE_LABEL_KEY[role])}</span>
                      <span className="block truncate text-sm text-muted-foreground">{ROLE_DESC[role]}</span>
                    </span>
                    <span
                      aria-hidden="true"
                      className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full border-2 transition-colors ${
                        isSelected ? 'border-primary bg-primary' : 'border-border bg-card'
                      }`}
                    >
                      {isSelected && <span className="h-2 w-2 rounded-full bg-primary-foreground" />}
                    </span>
                  </button>
                );
              })}
            </div>

            {/* Credentials */}
            <div className="flex flex-col gap-3.5">
              <div className="flex flex-col gap-1.5">
                <label htmlFor="console-login-username" className="text-sm font-semibold text-foreground">
                  Tên đăng nhập
                </label>
                <input
                  id="console-login-username"
                  type="text"
                  autoComplete="username"
                  placeholder="vd: bs.levanminh"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  disabled={isAuthenticating}
                  className="w-full rounded-xl border border-border bg-card px-4 py-2.5 text-[15px] text-foreground outline-none transition-all placeholder:text-muted-foreground hover:border-primary/30 focus:border-primary/50 focus:ring-2 focus:ring-primary/20 disabled:opacity-60"
                />
              </div>
              <div className="flex flex-col gap-1.5">
                <label htmlFor="console-login-password" className="text-sm font-semibold text-foreground">
                  Mật khẩu
                </label>
                <input
                  id="console-login-password"
                  type="password"
                  autoComplete="current-password"
                  placeholder="Nhập mật khẩu"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={isAuthenticating}
                  className="w-full rounded-xl border border-border bg-card px-4 py-2.5 text-[15px] text-foreground outline-none transition-all placeholder:text-muted-foreground hover:border-primary/30 focus:border-primary/50 focus:ring-2 focus:ring-primary/20 disabled:opacity-60"
                />
              </div>
            </div>

            {formError && (
              <p role="alert" className="rounded-xl border border-danger/30 bg-danger/5 px-4 py-2.5 text-sm font-medium text-danger">
                {formError}
              </p>
            )}

            <button
              type="submit"
              disabled={isAuthenticating}
              className="w-full rounded-xl bg-primary py-3.5 text-base font-bold text-primary-foreground shadow-md shadow-primary/25 transition-all hover:brightness-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-60"
            >
              {isAuthenticating ? 'Đang đăng nhập...' : 'Đăng nhập vào hệ thống'}
            </button>
          </form>
        </div>
      </main>
    </div>
  );
}
