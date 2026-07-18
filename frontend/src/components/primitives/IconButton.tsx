/**
 * IconButton - the round, hairline-bordered icon control used in headers
 * (back, close, notifications bell). Always requires an accessible name via
 * `aria-label` (a11y: every control has a name). `badge` shows the small
 * notification dot.
 */
import type { ButtonHTMLAttributes, ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface IconButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  /** Show a small danger dot (unread notifications). */
  badge?: boolean;
}

export function IconButton({ children, badge, className, type, ...props }: IconButtonProps) {
  return (
    <button
      type={type ?? 'button'}
      className={cn(
        'relative flex h-10 w-10 shrink-0 items-center justify-center rounded-pill border border-border ' +
          'bg-card text-foreground transition-colors active:bg-muted focus-visible:outline-none ' +
          'focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background',
        className,
      )}
      {...props}
    >
      {children}
      {badge && (
        <span
          aria-hidden="true"
          className="absolute right-2 top-2 h-2 w-2 rounded-full border-[1.5px] border-card bg-danger"
        />
      )}
    </button>
  );
}
