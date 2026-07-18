/**
 * SettingsPage - SCR-10 Settings (FR-21, FR-15, FR-18, TASK-023).
 *
 * DECISION (spec-guardian scope, this task): spec 10 SCR-10's own States
 * table replaces the generic 5-state ScreenState wrapper used elsewhere -
 * "Loading: -" means no loading state exists here at all (preferences
 * resolve synchronously, see lib/api/settings.ts), and there is no
 * no-permission row for this screen. Do not wrap this screen in
 * <ScreenState>; that would invent both.
 */
import { useState } from 'react';
import { useI18n } from '@/i18n';
import { cn } from '@/lib/utils';
import { useAuth } from '@/auth/AuthContext';
import * as settingsApi from '@/lib/api/settings';
import { NotificationChannel } from '@/lib/api/types';
import { Button, Card, LanguageToggle, SectionLabel } from '@/components/primitives';
import { LogoutIcon } from '@/components/icons';

const CHANNEL_OPTIONS = [
  { value: NotificationChannel.IN_APP, labelKey: 'settings.channelInApp' as const },
  { value: NotificationChannel.SMS, labelKey: 'settings.channelSms' as const },
];

export function SettingsPage() {
  const { t } = useI18n();
  const { session, logout } = useAuth();
  const patientId = session?.patient.id ?? '';

  const [channel, setChannel] = useState(() => settingsApi.getNotificationChannelPreference(patientId));
  const [savedMessage, setSavedMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  function handleSelectChannel(value: string) {
    setSavedMessage(null);
    setErrorMessage(null);
    try {
      const saved = settingsApi.saveNotificationChannelPreference(patientId, value);
      setChannel(saved);
      setSavedMessage(t('settings.savedConfirmation'));
    } catch {
      setErrorMessage(t('settings.invalidChoice'));
    }
  }

  return (
    <div className="flex flex-col gap-6 px-5 py-4 animate-fade-up">
      <h1 className="text-[22px] font-bold">{t('settings.title')}</h1>

      <section className="flex flex-col gap-2">
        <SectionLabel>{t('settings.language')}</SectionLabel>
        <Card className="flex items-center justify-between">
          <span className="text-[15px] font-semibold">{t('settings.language')}</span>
          <LanguageToggle />
        </Card>
      </section>

      <section className="flex flex-col gap-2">
        <SectionLabel>{t('settings.notificationChannelLabel')}</SectionLabel>
        <Card className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <span className="text-[15px] font-semibold">{t('settings.notificationChannelLabel')}</span>
            <div
              role="group"
              aria-label={t('settings.notificationChannelLabel')}
              className="inline-flex rounded-pill border border-border bg-muted p-1"
            >
              {CHANNEL_OPTIONS.map((option) => {
                const isActive = channel === option.value;
                return (
                  <button
                    key={option.value}
                    type="button"
                    aria-pressed={isActive}
                    onClick={() => handleSelectChannel(option.value)}
                    className={cn(
                      'rounded-pill px-3 py-1.5 text-[13px] font-bold transition-colors',
                      isActive ? 'bg-primary text-primary-foreground shadow-card' : 'text-muted-foreground',
                    )}
                  >
                    {t(option.labelKey)}
                  </button>
                );
              })}
            </div>
          </div>

          {errorMessage && (
            <p role="alert" className="rounded-xl bg-danger/10 px-3 py-2.5 text-sm text-danger">
              {errorMessage}
            </p>
          )}
          {savedMessage && !errorMessage && (
            <p className="rounded-xl bg-success/10 px-3 py-2.5 text-sm text-success">{savedMessage}</p>
          )}
        </Card>
      </section>

      <section className="flex flex-col gap-2">
        <Button variant="danger" size="md" onClick={() => void logout()} className="self-start">
          <LogoutIcon className="h-4 w-4" />
          {t('settings.logout')}
        </Button>
      </section>
    </div>
  );
}
