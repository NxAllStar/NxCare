/**
 * MedicationsPage - /medications prescriptions and reminders (PMA-M5, no
 * backing FR yet - TASK-023). An `interactionWarning` is always
 * model-produced when present and must carry the AIChip (NFR-USE-05); this
 * screen never advises treatment beyond that warning text.
 */
import { useEffect, useState } from 'react';
import { useI18n } from '@/i18n';
import { useAuth } from '@/auth/AuthContext';
import * as recordsApi from '@/lib/api/records';
import type { Medication } from '@/lib/api/types';
import { AIChip } from '@/components/primitives/AIChip';
import { Card } from '@/components/primitives/Card';
import { ScreenState, type ViewState } from '@/components/primitives/ScreenState';
import { AlertIcon, ClockIcon, PillIcon } from '@/components/icons';

export function MedicationsPage() {
  const { t } = useI18n();
  const { session } = useAuth();
  const patientId = session?.patient.id;

  const [medications, setMedications] = useState<Medication[] | null>(null);
  const [loadError, setLoadError] = useState(false);

  useEffect(() => {
    if (!patientId) return;
    let cancelled = false;
    setLoadError(false);
    recordsApi
      .listMedications(patientId)
      .then((result) => {
        if (!cancelled) setMedications(result);
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
    : medications === null
      ? 'loading'
      : medications.length === 0
        ? 'empty'
        : 'success';

  return (
    <div className="flex flex-col gap-4 px-5 py-4 animate-fade-up">
      <h1 className="text-[22px] font-bold">{t('medications.title')}</h1>

      <ScreenState state={viewState} emptyMessage={t('medications.emptyMessage')}>
        <ol className="flex flex-col gap-3">
          {medications?.map((medication) => (
            <li key={medication.id} data-testid="medication-item">
              <Card className="flex flex-col gap-3">
                <div className="flex items-center gap-2.5">
                  <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-primary/10">
                    <PillIcon className="h-4 w-4 text-primary" />
                  </span>
                  <span className="text-[16px] font-bold">{medication.drugName}</span>
                </div>
                <div className="flex flex-col gap-1.5 text-[13px] text-muted-foreground">
                  <span>
                    {t('medications.doseLabel')}:{' '}
                    <span className="font-mono font-semibold text-foreground">{medication.dose}</span>
                  </span>
                  <span>
                    {t('medications.usageLabel')}:{' '}
                    <span className="text-foreground">{medication.usageInstructions}</span>
                  </span>
                  <span className="flex items-center gap-1.5">
                    {t('medications.reminderLabel')}:
                    <span className="inline-flex items-center gap-1 font-mono font-semibold text-primary">
                      <ClockIcon className="h-3.5 w-3.5" />
                      {medication.reminderTimes.join(', ')}
                    </span>
                  </span>
                </div>
                {medication.interactionWarning && (
                  <div className="flex flex-col gap-2 rounded-xl border border-danger/30 bg-danger/10 p-3">
                    <div className="flex items-center justify-between gap-2">
                      <span className="flex items-center gap-1.5 text-xs font-bold text-danger">
                        <AlertIcon className="h-3.5 w-3.5" />
                        {t('medications.interactionWarningLabel')}
                      </span>
                      <AIChip />
                    </div>
                    <p className="text-[13px] text-danger">{medication.interactionWarning}</p>
                  </div>
                )}
              </Card>
            </li>
          ))}
        </ol>
      </ScreenState>
    </div>
  );
}
