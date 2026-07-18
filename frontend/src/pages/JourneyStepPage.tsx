/**
 * JourneyStepPage - /journey/step/:id STEP DETAIL / wayfinding (PMA-M3,
 * TASK-023). ETA range, "why this order" (always model-produced - AIChip,
 * NFR-USE-05), and in-hospital wayfinding.
 */
import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useI18n } from '@/i18n';
import { useAuth } from '@/auth/AuthContext';
import * as journeyStepApi from '@/lib/api/journeyStep';
import type { JourneyStep } from '@/lib/api/journeyStep';
import { cn } from '@/lib/utils';
import {
  AIChip,
  buttonVariants,
  Card,
  MutedCard,
  ScreenState,
  SectionLabel,
  type ViewState,
} from '@/components/primitives';
import { MapPinIcon, SparkleIcon } from '@/components/icons';

export function JourneyStepPage() {
  const { t } = useI18n();
  const { session } = useAuth();
  const { id } = useParams<{ id: string }>();
  const patientId = session?.patient.id;

  const [step, setStep] = useState<JourneyStep | null | undefined>(undefined);
  const [loadError, setLoadError] = useState(false);

  useEffect(() => {
    if (!patientId || !id) return;
    let cancelled = false;
    setLoadError(false);
    setStep(undefined);

    journeyStepApi
      .getJourneyStep(patientId, id)
      .then((result) => {
        if (!cancelled) setStep(result);
      })
      .catch(() => {
        if (!cancelled) setLoadError(true);
      });

    return () => {
      cancelled = true;
    };
  }, [patientId, id]);

  const viewState: ViewState = loadError ? 'error' : step === undefined ? 'loading' : step === null ? 'empty' : 'success';

  return (
    <div className="flex flex-col gap-4 px-5 py-4 animate-fade-up">
      <h1 className="text-[22px] font-bold">{t('journeyStep.title')}</h1>

      <ScreenState state={viewState} emptyMessage={t('journeyStep.notFound')}>
        {step && (
          <div className="flex flex-col gap-4">
            <Card>
              <span className="text-xl font-bold">{step.task.label}</span>
            </Card>

            <MutedCard className="flex flex-col gap-1">
              <SectionLabel>{t('journeyStep.etaRangeLabel')}</SectionLabel>
              <span className="font-mono text-2xl font-extrabold text-primary">{step.detail?.etaRangeLabel}</span>
            </MutedCard>

            {step.detail?.queuePositionLabel && (
              <Card className="flex flex-col gap-1">
                <SectionLabel>{t('journeyStep.queuePositionLabel')}</SectionLabel>
                <span className="text-[15px] font-medium">{step.detail.queuePositionLabel}</span>
              </Card>
            )}

            {step.detail?.whyThisOrder && (
              <Card className="flex items-start gap-3">
                <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10">
                  <SparkleIcon className="h-4 w-4 text-primary" />
                </span>
                <div className="flex flex-col gap-2">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-primary">{t('journeyStep.whyThisOrderLabel')}</span>
                    <AIChip />
                  </div>
                  <p className="text-sm leading-relaxed text-muted-foreground">{step.detail.whyThisOrder}</p>
                </div>
              </Card>
            )}

            {step.detail?.wayfindingInstructions && (
              <Card className="flex flex-col gap-2">
                <div className="flex items-center gap-2">
                  <MapPinIcon className="h-4 w-4 text-primary" />
                  <SectionLabel as="span">{t('journeyStep.wayfindingLabel')}</SectionLabel>
                </div>
                <p className="text-[15px] leading-relaxed">{step.detail.wayfindingInstructions}</p>
              </Card>
            )}

            <Link to="/journey" className={cn(buttonVariants({ variant: 'ghost', size: 'md' }), 'self-center')}>
              {t('journeyStep.backToJourney')}
            </Link>
          </div>
        )}
      </ScreenState>
    </div>
  );
}
