/**
 * LoginPage - SCR-08 Login, patient path (FR-18).
 *
 * Demo auth only (see src/lib/api/session.ts): a patient code + password
 * form, plus a quick-select of demo accounts. A failed login always shows
 * the SAME generic message, whether the patient code does not exist or the
 * password is wrong - no account enumeration (spec 10 SCR-08 States > Error).
 */
import { useState, type FormEvent } from 'react';
import { Navigate, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '@/auth/AuthContext';
import { listDemoAccounts } from '@/lib/api/session';
import { LanguageToggle } from '@/components/primitives/LanguageToggle';
import { Button } from '@/components/primitives';
import { HeartPulseIcon } from '@/components/icons';
import { useI18n } from '@/i18n';

const DEMO_ACCOUNTS = listDemoAccounts();
// Demo-only convenience: the quick-select buttons need a password to submit
// with, mirroring src/lib/api/session.ts DEMO_CREDENTIALS. Not a real
// credential - there is no production auth in this build (FR-18 demo scope).
const DEMO_PASSWORD = 'demo1234';

export function LoginPage() {
  const { t } = useI18n();
  const { session, isAuthenticating, login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation() as { state?: { from?: string } };

  const [patientCode, setPatientCode] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);

  if (session) {
    const redirectTo = location.state?.from && location.state.from !== '/login' ? location.state.from : '/home';
    return <Navigate to={redirectTo} replace />;
  }

  async function attemptLogin(code: string, pass: string) {
    setError(null);
    try {
      await login(code, pass);
      navigate('/home', { replace: true });
    } catch {
      // Generic message regardless of failure reason - no account enumeration.
      setError(t('login.errorInvalid'));
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void attemptLogin(patientCode, password);
  }

  const inputClass =
    'h-14 rounded-2xl border border-border bg-muted px-4 text-[15px] font-medium ' +
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ' +
    'focus-visible:ring-offset-background';

  return (
    <div className="mx-auto flex min-h-screen max-w-sm flex-col justify-center gap-8 px-6 py-10 animate-fade-up">
      <header className="flex flex-col gap-4">
        <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary text-primary-foreground">
          <HeartPulseIcon className="h-7 w-7" />
        </span>
        <div>
          <span className="block text-2xl font-bold text-primary">{t('app.name')}</span>
          <p className="mt-1 text-[15px] leading-relaxed text-muted-foreground">{t('app.tagline')}</p>
        </div>
      </header>

      <form onSubmit={handleSubmit} className="flex flex-col gap-4" noValidate>
        <div>
          <h1 className="text-[22px] font-bold">{t('login.title')}</h1>
          <p className="mt-1 text-[15px] text-muted-foreground">{t('login.subtitle')}</p>
        </div>

        <div className="flex flex-col gap-1.5">
          <label htmlFor="patient-code" className="text-sm font-semibold text-muted-foreground">
            {t('login.patientCodeLabel')}
          </label>
          <input
            id="patient-code"
            name="patientCode"
            type="text"
            autoComplete="username"
            className={inputClass}
            value={patientCode}
            onChange={(e) => setPatientCode(e.target.value)}
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <label htmlFor="password" className="text-sm font-semibold text-muted-foreground">
            {t('login.passwordLabel')}
          </label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            className={inputClass}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        {error && (
          <p role="alert" className="rounded-2xl bg-danger/10 px-4 py-3 text-sm text-danger">
            {error}
          </p>
        )}

        <Button type="submit" block disabled={isAuthenticating} className="mt-1">
          {isAuthenticating ? t('login.submitting') : t('login.submit')}
        </Button>
      </form>

      <div className="flex flex-col gap-3">
        <div className="flex items-center gap-2.5">
          <span className="h-px flex-1 bg-border" />
          <span className="text-xs font-semibold uppercase tracking-wide text-neutral-400">
            {t('login.demoAccountsLabel')}
          </span>
          <span className="h-px flex-1 bg-border" />
        </div>
        <div className="flex flex-col gap-2">
          {DEMO_ACCOUNTS.map((account) => (
            <button
              key={account.patientCode}
              type="button"
              onClick={() => void attemptLogin(account.patientCode, DEMO_PASSWORD)}
              className="flex h-12 items-center justify-center rounded-2xl border border-border bg-card px-4 text-[13px] font-semibold text-foreground active:bg-muted"
            >
              {account.displayName} ({account.patientCode})
            </button>
          ))}
        </div>
      </div>

      <div className="flex justify-center">
        <LanguageToggle />
      </div>
    </div>
  );
}
