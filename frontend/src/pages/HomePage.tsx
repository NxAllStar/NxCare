/**
 * HomePage - dual-mode /home (PRD-FR-12 M1 Home + Live Companion).
 *
 * The signature IA decision (PRD-FR-12 3.2): the SAME tab renders two
 * visibly different modes depending on whether the patient is currently at
 * the hospital (a task from their active care plan is IN_PROGRESS) or not.
 * A manual mode toggle is included for this demo (in place of a real
 * location signal, which this build has no source for) - once toggled, the
 * manual choice wins over the derived default until the page is remounted.
 */
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useI18n } from '@/i18n';
import { cn } from '@/lib/utils';
import { useAuth } from '@/auth/AuthContext';
import * as patientApi from '@/lib/api/patient';
import type { Appointment, Notification, Task } from '@/lib/api/types';
import { AIChip, Button, buttonVariants, Card, HeroCard, MutedCard, SectionLabel } from '@/components/primitives';
import { CalendarIcon, ChevronRightIcon, QrIcon, SparkleIcon } from '@/components/icons';

type HomeMode = 'dashboard' | 'live';

export function HomePage() {
  const { t } = useI18n();
  const { session } = useAuth();
  const patientId = session?.patient.id;

  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [manualMode, setManualMode] = useState<HomeMode | null>(null);

  useEffect(() => {
    if (!patientId) return;
    let cancelled = false;

    (async () => {
      const [appts, notifs, plan] = await Promise.all([
        patientApi.listAppointments(patientId),
        patientApi.listNotifications(patientId),
        patientApi.getActiveCarePlan(patientId),
      ]);
      if (cancelled) return;
      setAppointments(appts);
      setNotifications(notifs);

      if (plan) {
        const planTasks = await patientApi.listTasksForCarePlan(plan.id);
        if (!cancelled) setTasks(planTasks);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [patientId]);

  const currentStep = tasks.find((task) => task.executionStatus === 'IN_PROGRESS') ?? null;
  const computedDefaultMode: HomeMode = currentStep ? 'live' : 'dashboard';
  const mode = manualMode ?? computedDefaultMode;

  const upcomingVisits = appointments.filter((a) => a.status === 'BOOKED' || a.status === 'PROPOSED');
  const reminders = notifications.filter((n) => !n.reason);

  return (
    <div className="flex flex-col gap-4 px-5 py-4 animate-fade-up">
      <div
        role="group"
        aria-label={t('home.modeToggleLabel')}
        className="inline-flex self-center rounded-pill border border-border bg-muted p-1"
      >
        {(['dashboard', 'live'] as const).map((option) => {
          const isActive = mode === option;
          return (
            <button
              key={option}
              type="button"
              aria-pressed={isActive}
              onClick={() => setManualMode(option)}
              className={cn(
                'rounded-pill px-4 py-1.5 text-[13px] font-bold transition-colors',
                isActive ? 'bg-primary text-primary-foreground shadow-card' : 'text-muted-foreground',
              )}
            >
              {option === 'dashboard' ? t('home.modeDashboard') : t('home.modeLive')}
            </button>
          );
        })}
      </div>

      {mode === 'live' ? (
        <LiveCompanion currentStep={currentStep} />
      ) : (
        <Dashboard upcomingVisits={upcomingVisits} reminders={reminders} />
      )}
    </div>
  );
}

function LiveCompanion({ currentStep }: { currentStep: Task | null }) {
  const { t } = useI18n();
  const [whyOpen, setWhyOpen] = useState(false);

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-2 self-center">
        <span aria-hidden="true" className="h-2 w-2 rounded-full bg-primary animate-pulse-dot" />
        <span className="text-xs font-bold uppercase tracking-[0.04em] text-primary">
          {t('home.liveTitle')}
        </span>
      </div>

      {currentStep ? (
        <MutedCard className="flex flex-col gap-1">
          <span className="text-[13px] font-semibold text-muted-foreground">{t('home.liveCurrentStep')}</span>
          <span className="text-2xl font-extrabold">{currentStep.label}</span>
          <div className="mt-2 flex items-baseline gap-1.5">
            <span className="font-mono text-4xl font-extrabold text-primary">
              ~{currentStep.estimatedDurationMin}
            </span>
            <span className="text-base font-semibold text-muted-foreground">{t('home.liveEta')}</span>
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            <Link to={`/journey/step/${currentStep.id}`} className={buttonVariants({ variant: 'secondary', size: 'sm' })}>
              {t('home.liveWayfinding')}
            </Link>
            <Button variant="ghost" size="sm" onClick={() => setWhyOpen((v) => !v)} aria-expanded={whyOpen}>
              {t('home.liveWhyWaiting')}
            </Button>
          </div>
          {whyOpen && (
            <p className="mt-2 rounded-xl bg-card p-3 text-sm leading-relaxed text-muted-foreground">
              {t('home.liveWhyWaitingBody')}
            </p>
          )}
        </MutedCard>
      ) : (
        <p className="text-center text-sm text-muted-foreground">{t('home.liveNoActiveStep')}</p>
      )}

      <Card className="flex items-start gap-3">
        <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10">
          <SparkleIcon className="h-4 w-4 text-primary" />
        </span>
        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold">{t('home.liveAiDoing')}</span>
            <AIChip />
          </div>
          <p className="text-sm leading-relaxed text-muted-foreground">{t('home.liveAiDoingBody')}</p>
        </div>
      </Card>
    </div>
  );
}

function Dashboard({ upcomingVisits, reminders }: { upcomingVisits: Appointment[]; reminders: Notification[] }) {
  const { t } = useI18n();
  const nextVisit = upcomingVisits[0];

  return (
    <div className="flex flex-col gap-5">
      <h1 className="text-[22px] font-bold">{t('home.dashboardTitle')}</h1>

      {nextVisit && (
        <HeroCard className="flex flex-col gap-2.5">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-[0.04em] opacity-90">
            <SparkleIcon className="h-3.5 w-3.5" />
            {t('home.nextVisitLabel')}
          </div>
          <div className="text-xl font-bold">
            {nextVisit.specialty}
            {nextVisit.slotStart ? ` - ${new Date(nextVisit.slotStart).toLocaleString('vi-VN')}` : ''}
          </div>
          <Link
            to="/prep/next"
            className={cn(
              buttonVariants({ variant: 'secondary', size: 'sm' }),
              'mt-1 self-start border-none bg-white/20 text-white active:bg-white/30',
            )}
          >
            {t('prep.title')}
          </Link>
        </HeroCard>
      )}

      <section className="flex flex-col gap-2">
        <SectionLabel>{t('home.upcomingVisitsHeading')}</SectionLabel>
        {upcomingVisits.length === 0 ? (
          <p className="text-sm text-muted-foreground">{t('home.noUpcomingVisits')}</p>
        ) : (
          upcomingVisits.map((appt) => (
            <Card key={appt.id} className="text-[15px] font-medium">
              {appt.specialty} - {appt.slotStart ? new Date(appt.slotStart).toLocaleString('vi-VN') : ''}
            </Card>
          ))
        )}
      </section>

      <section className="flex flex-col gap-2">
        <SectionLabel>{t('home.prepRemindersHeading')}</SectionLabel>
        {reminders.length === 0 ? (
          <p className="text-sm text-muted-foreground">{t('state.empty')}</p>
        ) : (
          reminders.map((n) => (
            <Card key={n.id} className="text-[15px]">
              {n.body}
            </Card>
          ))
        )}
      </section>

      <section className="flex flex-col gap-2">
        <SectionLabel>{t('home.newResultsHeading')}</SectionLabel>
        <Link
          to="/results"
          className="flex items-center justify-between rounded-2xl border border-border bg-card p-4 active:bg-muted"
        >
          <span className="text-[15px] font-semibold">{t('results.title')}</span>
          <ChevronRightIcon className="h-3.5 w-3.5 text-neutral-300" />
        </Link>
      </section>

      <section className="flex flex-col gap-2">
        <SectionLabel>{t('home.shortcutsHeading')}</SectionLabel>
        <div className="grid grid-cols-2 gap-3">
          <Link
            to="/book"
            className="flex flex-col gap-2 rounded-2xl border border-border bg-card p-4 active:bg-muted"
          >
            <CalendarIcon className="h-6 w-6 text-primary" />
            <span className="text-[15px] font-bold">{t('home.shortcutBook')}</span>
          </Link>
          <Link
            to="/intake"
            className="flex flex-col gap-2 rounded-2xl border border-border bg-card p-4 active:bg-muted"
          >
            <SparkleIcon className="h-6 w-6 text-primary" />
            <span className="text-[15px] font-bold">{t('home.shortcutIntake')}</span>
          </Link>
          <Link
            to="/checkin"
            className="col-span-2 flex items-center gap-3 rounded-2xl border border-dashed border-neutral-300 p-4 text-muted-foreground active:bg-muted"
          >
            <QrIcon className="h-5 w-5" />
            <span className="text-[15px] font-semibold">{t('home.shortcutCheckin')}</span>
          </Link>
        </div>
      </section>
    </div>
  );
}
