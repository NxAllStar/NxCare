/**
 * JourneyPage - SCR-02 Journey timeline (FR-04, FR-05, FR-06, FR-11, FR-17).
 *
 * FR-05/AS-02: the LOCKED-task banner is DISPLAY ONLY - a reminder to go
 * pay at the counter. There is no payment control anywhere on this screen;
 * the app never processes money.
 */
import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useI18n, type DictKey } from '@/i18n';
import { useAuth } from '@/auth/AuthContext';
import * as patientApi from '@/lib/api/patient';
import * as careplanApi from '@/lib/api/careplan';
import type { Appointment, CarePlan, Notification, Payment, Task } from '@/lib/api/types';
import { cn } from '@/lib/utils';
import {
  AIChip,
  Button,
  buttonVariants,
  Card,
  PatientCodeQr,
  ScreenState,
  SectionLabel,
  StatusChip,
  Timeline,
  TimelineStep,
  type TimelineStatus,
  type ViewState,
} from '@/components/primitives';
import { SparkleIcon } from '@/components/icons';

export function JourneyPage() {
  const { t } = useI18n();
  const { session } = useAuth();
  const patientId = session?.patient.id;
  const patientCode = session?.patient.patientCode;

  const [carePlan, setCarePlan] = useState<CarePlan | null | undefined>(undefined);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [appointment, setAppointment] = useState<Appointment | null>(null);
  const [loadError, setLoadError] = useState(false);
  const [confirmingCancel, setConfirmingCancel] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!patientId || !patientCode) return;
    let cancelled = false;
    let closeStream = () => {};
    setLoadError(false);

    // The care plan comes from the real backend (TASK-038): resolve the patient's canonical UUID,
    // read the active plan, then keep it live over SSE - a doctor's order on the console pushes a
    // `careplan.updated` event and this refetches. Notifications/appointments stay on the mock layer
    // (out of this task's scope). A backend miss (404) maps to the same empty state as before.
    async function loadCarePlan(patientUuid: string) {
      const view = await careplanApi.fetchActiveCarePlan(patientUuid);
      if (cancelled) return;
      if (!view) {
        setCarePlan(null);
        setTasks([]);
        setPayments([]);
        return;
      }
      setCarePlan(view.carePlan);
      setTasks(view.tasks);
      setPayments(view.payments);
    }

    (async () => {
      try {
        const [resolved, notifs, appointments] = await Promise.all([
          careplanApi.resolvePatient(patientCode),
          patientApi.listNotifications(patientId),
          patientApi.listAppointments(patientId),
        ]);
        if (cancelled) return;
        setNotifications(notifs);
        setAppointment(appointments[0] ?? null);

        await loadCarePlan(resolved.patientId);
        if (cancelled) return;
        closeStream = careplanApi.openCarePlanStream(resolved.patientId, () => {
          void loadCarePlan(resolved.patientId);
        });
      } catch {
        if (!cancelled) setLoadError(true);
      }
    })();

    return () => {
      cancelled = true;
      closeStream();
    };
  }, [patientId, patientCode]);

  async function handleReschedule() {
    if (!appointment) return;
    const newSlotStart = new Date(Date.now() + 24 * 60 * 60_000).toISOString();
    await patientApi.rescheduleAppointment(appointment.id, newSlotStart);
    setActionMessage(t('journey.rescheduled'));
  }

  async function handleConfirmCancel() {
    if (!appointment) return;
    await patientApi.cancelAppointment(appointment.id);
    setConfirmingCancel(false);
    setActionMessage(t('journey.cancelled'));
  }

  const replanNotification = notifications.find((n) => n.aiGenerated && n.reason);
  const paymentByTaskId = new Map(payments.map((p) => [p.subjectId, p]));

  const viewState: ViewState = loadError ? 'error' : carePlan === undefined ? 'loading' : carePlan === null ? 'empty' : 'success';

  const timelineStatus = (code: Task['executionStatus']): TimelineStatus =>
    code === 'DONE' ? 'done' : code === 'IN_PROGRESS' ? 'active' : 'upcoming';

  return (
    <div className="flex flex-col gap-4 px-5 py-4 animate-fade-up">
      <h1 className="text-[22px] font-bold">{t('journey.title')}</h1>

      <ScreenState state={viewState} emptyMessage={t('journey.emptyMessage')}>
        <div className="flex flex-col gap-4">
          {session && (
            <Card className="flex flex-col items-center gap-2">
              <SectionLabel>{t('journey.patientCodeLabel')}</SectionLabel>
              <PatientCodeQr code={session.patient.patientCode} />
              <span className="text-xs text-muted-foreground">{t('journey.patientCodeHint')}</span>
            </Card>
          )}

          {replanNotification && (
            <Card className="flex items-start gap-3">
              <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-primary/10">
                <SparkleIcon className="h-4 w-4 text-primary" />
              </span>
              <div className="flex flex-col gap-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-primary">{t('journey.replanReasonLabel')}</span>
                  <AIChip />
                </div>
                <p className="text-sm leading-relaxed text-muted-foreground">{replanNotification.reason}</p>
              </div>
            </Card>
          )}

          <Timeline>
            {tasks.map((task) => {
              const payment = paymentByTaskId.get(task.id);
              const isLocked = task.executionStatus === 'LOCKED';
              return (
                <TimelineStep
                  key={task.id}
                  status={timelineStatus(task.executionStatus)}
                  statusLabel={t(`status.${task.executionStatus}` as DictKey)}
                  label={
                    <div className="flex flex-wrap items-center gap-2">
                      <span>{task.label}</span>
                      <StatusChip code={task.executionStatus} />
                    </div>
                  }
                  meta={
                    <div className="flex flex-col gap-2">
                      <div className="flex flex-wrap items-center gap-x-4 gap-y-1">
                        <span>
                          {t('journey.ownerLabel')}: <span className="font-mono">{task.ownerId}</span>
                        </span>
                        <span>
                          {t('journey.etaLabel')}: <span className="font-mono">~{task.estimatedDurationMin} phut</span>
                        </span>
                        {payment && <StatusChip code={payment.status} />}
                      </div>
                      {isLocked && (
                        <div className="flex items-start gap-2 rounded-xl border border-warning/30 bg-warning/10 p-2.5 text-[13px] font-medium text-warning">
                          <span className="font-semibold">{t('journey.payReminderTitle')}</span>
                          <span>{t('journey.payReminderBody')}</span>
                        </div>
                      )}
                    </div>
                  }
                />
              );
            })}
          </Timeline>

          {appointment && (
            <Card className="flex flex-col gap-3">
              {actionMessage && <p className="text-[15px] font-semibold text-success">{actionMessage}</p>}
              {confirmingCancel ? (
                <div className="flex flex-col gap-3">
                  <p className="text-[15px]">{t('journey.cancelConfirm')}</p>
                  <div className="flex gap-2">
                    <Button
                      variant="danger"
                      size="sm"
                      onClick={() => void handleConfirmCancel()}
                      className="border-none bg-danger text-danger-foreground active:brightness-95"
                    >
                      {t('journey.cancelConfirmYes')}
                    </Button>
                    <Button variant="secondary" size="sm" onClick={() => setConfirmingCancel(false)}>
                      {t('journey.cancelConfirmNo')}
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="flex gap-2">
                  <Button variant="secondary" size="sm" onClick={() => void handleReschedule()}>
                    {t('journey.rescheduleButton')}
                  </Button>
                  <Button variant="danger" size="sm" onClick={() => setConfirmingCancel(true)}>
                    {t('journey.cancelButton')}
                  </Button>
                </div>
              )}
            </Card>
          )}

          <Link to="/assistant" className={cn(buttonVariants({ variant: 'ghost', size: 'md' }), 'self-center')}>
            {t('journey.askAssistant')}
          </Link>
        </div>
      </ScreenState>
    </div>
  );
}
