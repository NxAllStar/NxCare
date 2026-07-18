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
import { Button, Card, LanguageToggle } from '@/components/primitives';
import { canAccessScreen, defaultPathForRole, ROLE_LABEL_KEY, screenForPath, STAFF_ROLES, type StaffRole } from '../access';
import { useStaffAuth } from '../auth/StaffAuthContext';

interface ConsoleLoginLocationState {
  from?: string;
}

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
    <div className="flex min-h-screen items-center justify-center bg-background p-6">
      <Card className="w-full max-w-md">
        <div className="mb-6 flex items-center justify-between gap-4">
          <h1 className="text-xl font-bold text-foreground">{t('console.login.title')}</h1>
          <LanguageToggle />
        </div>
        <p className="mb-6 text-sm text-muted-foreground">{t('console.login.subtitle')}</p>
        <div className="flex flex-col gap-3" role="group" aria-label={t('console.login.title')}>
          {STAFF_ROLES.map((role) => (
            <Button
              key={role}
              variant="secondary"
              size="lg"
              block
              disabled={isAuthenticating}
              onClick={() => void handleSelectRole(role)}
            >
              {t(ROLE_LABEL_KEY[role])}
            </Button>
          ))}
        </div>
      </Card>
    </div>
  );
}
