/**
 * Staff login (TASK-026): a role selector only - synthetic demo staff,
 * never a real account or password (agent-guardrails.md). Reachable at
 * /console when there is no staff session (see ConsoleRouteGuard).
 *
 * ConsoleRouteGuard captures the originally requested path in
 * `location.state.from` before redirecting here. After login, that path is
 * honored - but only if the selected role is actually permitted to reach it
 * (`canAccessScreen`); a role is never redirected to a screen the locked
 * contract table (access.ts) forbids it. Any other case (no `from`, `from`
 * matches no known screen, or the role cannot reach it) falls back to the
 * role's own default screen, exactly as before.
 */
import { useLocation, useNavigate } from 'react-router-dom';
import { useI18n } from '@/i18n';
import {
  GridIcon,
  ShieldIcon,
  StethoscopeIcon,
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
  admin: 'Quản trị hệ thống và theo dõi vết kiểm toán',
};

export function ConsoleLoginPage() {
  const { t } = useI18n();
  const { login, isAuthenticating } = useStaffAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleSelectRole = async (role: StaffRole) => {
    await login(role);
    const from = (location.state as ConsoleLoginLocationState | null)?.from;
    const requestedScreen = from ? screenForPath(from) : undefined;
    const target =
      requestedScreen && canAccessScreen(role, requestedScreen) ? (from as string) : defaultPathForRole(role);
    navigate(target, { replace: true });
  };

  return (
    <div className="console-surface relative flex min-h-screen items-center justify-center overflow-hidden bg-background p-6">
      {/* Ambient background wash - calm clinical, no imagery */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            'radial-gradient(60rem 40rem at 15% -10%, hsl(var(--primary) / 0.10), transparent 60%),' +
            'radial-gradient(50rem 40rem at 110% 110%, hsl(var(--primary) / 0.08), transparent 55%)',
        }}
      />

      <div className="relative z-10 w-full max-w-md">
        {/* Brand */}
        <div className="mb-6 flex items-center justify-center gap-2.5">
          <span
            className="flex h-9 w-9 items-center justify-center bg-primary shadow-md shadow-primary/25"
            style={{ clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)' }}
          >
            <span className="font-mono text-[13px] font-extrabold text-white">Nx</span>
          </span>
          <span className="select-none text-2xl font-extrabold tracking-tight text-foreground">NxCare</span>
        </div>

        {/* Card */}
        <div className="rounded-3xl border border-border bg-card p-7 shadow-xl shadow-black/5">
          <div className="mb-5">
            <h1 className="text-xl font-bold text-foreground">{t('console.login.title')}</h1>
            <p className="mt-1.5 text-sm text-muted-foreground">{t('console.login.subtitle')}</p>
          </div>

          <div className="flex flex-col gap-2.5" role="group" aria-label={t('console.login.title')}>
            {STAFF_ROLES.map((role) => {
              const Icon = ROLE_ICON[role];
              return (
                <button
                  key={role}
                  type="button"
                  disabled={isAuthenticating}
                  onClick={() => void handleSelectRole(role)}
                  className="group flex items-center gap-3.5 rounded-2xl border border-border bg-secondary px-4 py-3.5 text-left transition-all hover:border-primary/40 hover:bg-card hover:shadow-md hover:shadow-primary/5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 disabled:pointer-events-none disabled:opacity-60"
                >
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
                    <Icon className="h-[20px] w-[20px]" />
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block text-[15px] font-bold text-foreground">{t(ROLE_LABEL_KEY[role])}</span>
                    <span className="block truncate text-sm text-muted-foreground">{ROLE_DESC[role]}</span>
                  </span>
                  <svg
                    className="h-4 w-4 shrink-0 text-muted-foreground transition-transform group-hover:translate-x-0.5 group-hover:text-primary"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth="2"
                    aria-hidden="true"
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              );
            })}
          </div>
        </div>

        <p className="mt-5 text-center text-sm text-muted-foreground">
          NxCare - Trợ lý điều phối lộ trình chăm sóc - Chế độ demo
        </p>
      </div>
    </div>
  );
}
