/**
 * Staff login (TASK-026): a role selector only - synthetic demo staff,
 * never a real account or password (agent-guardrails.md). Reachable at
 * /console when there is no staff session (see ConsoleRouteGuard).
 */
import { useNavigate } from 'react-router-dom';
import { useI18n } from '@/i18n';
import { Button, Card, LanguageToggle } from '@/components/primitives';
import { defaultPathForRole, ROLE_LABEL_KEY, type StaffRole } from '../access';
import { useStaffAuth } from '../auth/StaffAuthContext';

const ROLES: StaffRole[] = ['doctor', 'technician', 'coordinator', 'admin'];

export function ConsoleLoginPage() {
  const { t } = useI18n();
  const { login, isAuthenticating } = useStaffAuth();
  const navigate = useNavigate();

  const handleSelectRole = async (role: StaffRole) => {
    await login(role);
    navigate(defaultPathForRole(role), { replace: true });
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
          {ROLES.map((role) => (
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
