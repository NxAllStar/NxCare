/**
 * RecoveryPage - /recovery recovery tracking (PMA-M5, no backing FR yet -
 * TASK-023). Safety frame only: collect -> flag -> refer to doctor. The
 * agent's check-in `question` is always model-produced (AIChip,
 * NFR-USE-05); a WARNING-severity check-in shows an escalation banner and
 * never a treatment recommendation.
 */
import { useEffect, useState } from 'react';
import { useI18n } from '@/i18n';
import { useAuth } from '@/auth/AuthContext';
import * as recordsApi from '@/lib/api/records';
import { RecoverySeverity } from '@/lib/api/types';
import type { RecoveryCheckIn } from '@/lib/api/types';
import { AIChip } from '@/components/primitives/AIChip';
import { Card } from '@/components/primitives/Card';
import { AlertIcon } from '@/components/icons';
import { ScreenState, type ViewState } from '@/components/primitives/ScreenState';

export function RecoveryPage() {
  const { t } = useI18n();
  const { session } = useAuth();
  const patientId = session?.patient.id;

  const [checkIns, setCheckIns] = useState<RecoveryCheckIn[] | null>(null);
  const [loadError, setLoadError] = useState(false);

  useEffect(() => {
    if (!patientId) return;
    let cancelled = false;
    setLoadError(false);
    recordsApi
      .listRecoveryCheckIns(patientId)
      .then((result) => {
        if (!cancelled) setCheckIns(result);
      })
      .catch(() => {
        if (!cancelled) setLoadError(true);
      });
    return () => {
      cancelled = true;
    };
  }, [patientId]);

  const viewState: ViewState = loadError
    ? 'error'
    : checkIns === null
      ? 'loading'
      : checkIns.length === 0
        ? 'empty'
        : 'success';

  return (
    <div className="flex flex-col gap-4 px-5 py-4 animate-fade-up">
      <h1 className="text-[22px] font-bold">{t('recovery.title')}</h1>

      <ScreenState state={viewState} emptyMessage={t('recovery.emptyMessage')}>
        <ol className="flex flex-col gap-3">
          {checkIns?.map((checkIn) => {
            const isWarning = checkIn.severity === RecoverySeverity.WARNING;
            return (
              <li key={checkIn.id} data-testid="recovery-item">
                <Card className="flex flex-col gap-2.5">
                  <div className="flex items-start justify-between gap-3">
                    <span className="text-[15px] font-bold leading-snug">{checkIn.question}</span>
                    <AIChip />
                  </div>
                  {checkIn.patientResponse && (
                    <span className="text-[13px] text-muted-foreground">
                      {t('recovery.responseLabel')}:{' '}
                      <span className="font-medium text-foreground">{checkIn.patientResponse}</span>
                    </span>
                  )}
                  {isWarning && (
                    <div
                      role="alert"
                      className="flex items-start gap-2.5 rounded-xl border border-danger/30 bg-danger/10 p-3"
                    >
                      <AlertIcon className="h-4 w-4 shrink-0 text-danger" />
                      <div className="flex flex-col gap-0.5 text-[13px] text-danger">
                        <span>{t('recovery.warningBanner')}</span>
                        <span className="font-bold">{t('recovery.contactDoctor')}</span>
                      </div>
                    </div>
                  )}
                </Card>
              </li>
            );
          })}
        </ol>
      </ScreenState>
    </div>
  );
}
