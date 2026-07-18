/**
 * SegmentedProgress - the row of thin pill segments that shows progress
 * through a multi-step flow (onboarding, the booking wizard). Segments up
 * to and including `current` are teal; the rest are muted. Announced to
 * assistive tech via aria-valuenow so it is not colour-only.
 */
import { cn } from '@/lib/utils';

interface SegmentedProgressProps {
  /** Total number of steps. */
  total: number;
  /** Zero-based index of the current step. */
  current: number;
  label?: string;
  className?: string;
}

export function SegmentedProgress({ total, current, label, className }: SegmentedProgressProps) {
  return (
    <div
      role="progressbar"
      aria-label={label}
      aria-valuemin={1}
      aria-valuemax={total}
      aria-valuenow={current + 1}
      className={cn('flex gap-1.5', className)}
    >
      {Array.from({ length: total }).map((_, i) => (
        <span
          key={i}
          aria-hidden="true"
          className={cn('h-1 flex-1 rounded-pill', i <= current ? 'bg-primary' : 'bg-border')}
        />
      ))}
    </div>
  );
}
