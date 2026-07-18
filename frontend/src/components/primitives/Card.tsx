/**
 * Card + HeroCard - the two surface primitives the patient screens sit on.
 *
 * Card: a white, hairline-bordered rounded surface (the default content
 * block). HeroCard: the teal, elevated "spotlight" surface used once per
 * screen for the single most important thing (the next appointment, the
 * current step). Both are token-only (frontend.md).
 */
import type { HTMLAttributes } from 'react';
import { cn } from '@/lib/utils';

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('rounded-2xl border border-border bg-card p-4', className)}
      {...props}
    />
  );
}

/**
 * The elevated teal surface. `as` lets it be a button when the whole card
 * is the tap target (keeps it a real, keyboard-focusable control).
 */
export function HeroCard({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        'rounded-3xl bg-primary p-5 text-primary-foreground shadow-raised',
        className,
      )}
      {...props}
    />
  );
}

/** A quiet muted surface (used for grouped info blocks, "why waiting", etc.). */
export function MutedCard({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn('rounded-2xl border border-border bg-muted p-4', className)}
      {...props}
    />
  );
}
