/**
 * ResultsPage - /results lab/imaging results (PMA-M4, no backing FR yet -
 * TASK-023, PRD-FR-12 section 7 open item).
 *
 * Safety guardrail (never loosen): a result is only ever labelled
 * within/outside its reference range - never a diagnosis, prognosis, or
 * treatment recommendation. Every OUTSIDE_RANGE result carries "discuss
 * this with your doctor"; a WITHIN_RANGE result never does.
 */
import { useEffect, useState } from 'react';
import { useI18n } from '@/i18n';
import { cn } from '@/lib/utils';
import { useAuth } from '@/auth/AuthContext';
import * as recordsApi from '@/lib/api/records';
import { ReferenceRangeStatus } from '@/lib/api/types';
import type { LabResult } from '@/lib/api/types';
import { Card } from '@/components/primitives/Card';
import { ScreenState, type ViewState } from '@/components/primitives/ScreenState';

export function ResultsPage() {
  const { t } = useI18n();
  const { session } = useAuth();
  const patientId = session?.patient.id;

  const [results, setResults] = useState<LabResult[] | null>(null);
  const [loadError, setLoadError] = useState(false);

  useEffect(() => {
    if (!patientId) return;
    let cancelled = false;
    setLoadError(false);
    recordsApi
      .listLabResults(patientId)
      .then((result) => {
        if (!cancelled) setResults(result);
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
    : results === null
      ? 'loading'
      : results.length === 0
        ? 'empty'
        : 'success';

  return (
    <div className="flex flex-col gap-4 px-5 py-4 animate-fade-up">
      <h1 className="text-[22px] font-bold">{t('results.title')}</h1>

      <ScreenState state={viewState} emptyMessage={t('results.emptyMessage')}>
        <ol className="flex flex-col gap-3">
          {results?.map((result) => {
            const isOutsideRange = result.status === ReferenceRangeStatus.OUTSIDE_RANGE;
            return (
              <li key={result.id} data-testid="lab-result">
                <Card className="flex flex-col gap-2.5">
                  <div className="flex items-start justify-between gap-3">
                    <span className="text-[15px] font-bold">{result.label}</span>
                    <span className="font-mono text-[15px] font-semibold">
                      {result.value}{' '}
                      <span className="text-xs font-medium text-muted-foreground">{result.unit}</span>
                    </span>
                  </div>
                  <span className="text-[13px] text-muted-foreground">
                    {t('results.referenceRangeLabel')}:{' '}
                    <span className="font-mono">{result.referenceRangeLabel}</span>
                  </span>
                  <span
                    className={cn(
                      'inline-flex w-fit items-center gap-1.5 rounded-pill border px-3 py-1 text-xs font-bold',
                      isOutsideRange
                        ? 'border-warning/30 bg-warning/10 text-warning'
                        : 'border-success/30 bg-success/10 text-success',
                    )}
                  >
                    <span aria-hidden="true" className="h-1.5 w-1.5 rounded-full bg-current" />
                    {isOutsideRange ? t('results.outsideRange') : t('results.withinRange')}
                  </span>
                  {isOutsideRange && (
                    <p className="rounded-xl bg-danger/10 px-3 py-2 text-[13px] font-medium text-danger">
                      {t('results.discussWithDoctor')}
                    </p>
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
