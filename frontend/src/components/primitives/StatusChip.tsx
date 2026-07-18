/**
 * StatusChip - semantic status display used everywhere a Task/Appointment/
 * CarePlan/Payment status is shown (spec 10 "Visual design direction":
 * green=done/available, amber=waiting/pending, red=disruption/blocked,
 * blue=in-progress).
 *
 * BR-31 / NFR-USE-03: the enum CODE is English and is rendered as-is,
 * never translated - only the accompanying label localises. Do not
 * refactor this to show only the localised label; the code must stay
 * visible in the DOM for any of ExecutionStatus/PaymentStatus/
 * AppointmentStatus/CarePlanStatus values.
 */
import { cn } from '@/lib/utils';
import { useI18n, type DictKey } from '@/i18n';

export type StatusCode =
  | 'LOCKED'
  | 'PENDING'
  | 'IN_PROGRESS'
  | 'DONE'
  | 'CANCELLED'
  | 'UNPAID'
  | 'PAID'
  | 'PROPOSED'
  | 'BOOKED'
  | 'CHECKED_IN'
  | 'IN_CONSULT'
  | 'NO_SHOW'
  | 'DRAFT'
  | 'ACTIVE'
  | 'COMPLETED';

export type StatusVariant = 'done' | 'waiting' | 'blocked' | 'in-progress';

// Every StatusCode maps to exactly one of the four semantic variants
// (cross-cutting UI rules). Judgment calls are noted where the mapping is
// not a literal reading of the code name:
// - CANCELLED / NO_SHOW -> blocked (red): terminal negative outcomes, no
//   better bucket among the four semantic colours.
// - BOOKED / PROPOSED / DRAFT / UNPAID -> waiting (amber): the patient or
//   system is waiting on the next step.
// - CHECKED_IN / IN_CONSULT / ACTIVE -> in-progress (blue).
const VARIANT_BY_CODE: Record<StatusCode, StatusVariant> = {
  LOCKED: 'blocked',
  PENDING: 'waiting',
  IN_PROGRESS: 'in-progress',
  DONE: 'done',
  CANCELLED: 'blocked',
  UNPAID: 'waiting',
  PAID: 'done',
  PROPOSED: 'waiting',
  BOOKED: 'waiting',
  CHECKED_IN: 'in-progress',
  IN_CONSULT: 'in-progress',
  NO_SHOW: 'blocked',
  DRAFT: 'waiting',
  ACTIVE: 'in-progress',
  COMPLETED: 'done',
};

const VARIANT_CLASSES: Record<StatusVariant, string> = {
  done: 'bg-success/10 text-success border-success/30',
  waiting: 'bg-warning/10 text-warning border-warning/30',
  blocked: 'bg-danger/10 text-danger border-danger/30',
  'in-progress': 'bg-info/10 text-info border-info/30',
};

interface StatusChipProps {
  code: StatusCode;
  className?: string;
}

export function StatusChip({ code, className }: StatusChipProps) {
  const { t } = useI18n();
  const variant = VARIANT_BY_CODE[code];
  const labelKey = `status.${code}` as DictKey;

  return (
    <span
      data-testid="status-chip"
      data-code={code}
      data-variant={variant}
      className={cn(
        'inline-flex items-center gap-2 rounded-pill border px-3 py-1 text-xs font-medium',
        VARIANT_CLASSES[variant],
        className,
      )}
    >
      <span aria-hidden="true" className="h-1.5 w-1.5 shrink-0 rounded-full bg-current" />
      <span>{t(labelKey)}</span>
      <span className="font-mono text-[10px] uppercase tracking-wide opacity-70">{code}</span>
    </span>
  );
}
