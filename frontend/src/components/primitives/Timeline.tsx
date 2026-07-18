/**
 * Timeline - the vertical journey stepper (SCR-02). Each step shows a
 * status node (done = filled green check, active = ringed teal dot,
 * upcoming = hollow) joined by a connector, with a label + meta line and an
 * optional chevron when the step links to its detail. Status is conveyed by
 * shape AND colour (a11y: colour is never the only signal); the node also
 * carries an sr-only status word.
 */
import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { CheckIcon, ChevronRightIcon } from '@/components/icons';

export type TimelineStatus = 'done' | 'active' | 'upcoming';

interface TimelineStepProps {
  label: ReactNode;
  meta?: ReactNode;
  status: TimelineStatus;
  /** sr-only status word (localised by the caller). */
  statusLabel: string;
  isLast?: boolean;
  to?: string;
  onClick?: () => void;
}

function Node({ status, statusLabel }: { status: TimelineStatus; statusLabel: string }) {
  return (
    <div className="flex flex-col items-center self-stretch">
      <span className="sr-only">{statusLabel}</span>
      {status === 'done' && (
        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-success text-white">
          <CheckIcon className="h-3 w-3" />
        </span>
      )}
      {status === 'active' && (
        <span className="h-6 w-6 rounded-full bg-primary ring-4 ring-primary/15" />
      )}
      {status === 'upcoming' && <span className="h-6 w-6 rounded-full border-2 border-neutral-300" />}
      <span className="mt-1 w-0.5 flex-1 bg-border" />
    </div>
  );
}

function Body({ label, meta, linked }: { label: ReactNode; meta?: ReactNode; linked: boolean }) {
  return (
    <div className="flex flex-1 items-start justify-between gap-3 pb-5">
      <div className="min-w-0">
        <div className="text-base font-bold text-foreground">{label}</div>
        {meta != null && <div className="mt-0.5 text-[13px] text-muted-foreground">{meta}</div>}
      </div>
      {linked && <ChevronRightIcon className="mt-1.5 h-3.5 w-3.5 shrink-0 text-neutral-300" />}
    </div>
  );
}

export function TimelineStep({ label, meta, status, statusLabel, to, onClick }: TimelineStepProps) {
  const content = (
    <>
      <Node status={status} statusLabel={statusLabel} />
      <Body label={label} meta={meta} linked={Boolean(to || onClick)} />
    </>
  );
  const rowClass =
    'flex w-full gap-3.5 text-left rounded-xl focus-visible:outline-none focus-visible:ring-2 ' +
    'focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background';
  let row: ReactNode;
  if (to) {
    row = (
      <Link to={to} className={rowClass}>
        {content}
      </Link>
    );
  } else if (onClick) {
    row = (
      <button type="button" onClick={onClick} className={rowClass}>
        {content}
      </button>
    );
  } else {
    row = <div className={cn(rowClass, 'cursor-default')}>{content}</div>;
  }
  return <li>{row}</li>;
}

export function Timeline({ children, className }: { children: ReactNode; className?: string }) {
  return <ol className={cn('flex flex-col [&>li:last-child_span.bg-border]:hidden', className)}>{children}</ol>;
}
