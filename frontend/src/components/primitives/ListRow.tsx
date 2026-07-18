/**
 * ListRow - the tappable navigation row used by the records index, the
 * "more" menu, results lists, and anywhere a card links deeper. Title +
 * optional count badge / trailing detail + a chevron. Renders as a real
 * <Link> or <button> so it is keyboard-operable with a visible focus ring.
 */
import type { ReactNode } from 'react';
import { Link } from 'react-router-dom';
import { cn } from '@/lib/utils';
import { ChevronRightIcon } from '@/components/icons';

interface ListRowProps {
  title: ReactNode;
  /** A count badge (teal pill) shown next to the title. */
  badge?: ReactNode;
  /** Secondary text under the title. */
  subtitle?: ReactNode;
  /** Trailing content shown before the chevron (e.g. a StatusChip). */
  trailing?: ReactNode;
  /** Leading content (e.g. an avatar or icon tile). */
  leading?: ReactNode;
  to?: string;
  onClick?: () => void;
  className?: string;
}

const ROW_CLASS =
  'flex w-full items-center gap-3 rounded-2xl border border-border bg-card p-4 text-left ' +
  'transition-colors active:bg-muted focus-visible:outline-none focus-visible:ring-2 ' +
  'focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background';

function Inner({ title, badge, subtitle, trailing, leading }: Omit<ListRowProps, 'to' | 'onClick' | 'className'>) {
  return (
    <>
      {leading}
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <span className="truncate text-base font-bold text-foreground">{title}</span>
          {badge != null && (
            <span className="inline-flex h-[22px] min-w-[22px] shrink-0 items-center justify-center rounded-pill bg-primary px-1.5 text-xs font-bold text-primary-foreground">
              {badge}
            </span>
          )}
        </div>
        {subtitle != null && <div className="mt-0.5 truncate text-[13px] text-muted-foreground">{subtitle}</div>}
      </div>
      {trailing}
      <ChevronRightIcon className="h-3.5 w-3.5 shrink-0 text-neutral-300" />
    </>
  );
}

export function ListRow({ to, onClick, className, ...inner }: ListRowProps) {
  if (to) {
    return (
      <Link to={to} className={cn(ROW_CLASS, className)}>
        <Inner {...inner} />
      </Link>
    );
  }
  return (
    <button type="button" onClick={onClick} className={cn(ROW_CLASS, className)}>
      <Inner {...inner} />
    </button>
  );
}
