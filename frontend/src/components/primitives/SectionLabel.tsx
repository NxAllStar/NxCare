/**
 * SectionLabel - the small uppercase, letter-spaced group heading that
 * separates content sections on every screen (design direction). Renders
 * as an <h2> by default so the heading structure stays semantic.
 */
import type { HTMLAttributes, ElementType } from 'react';
import { cn } from '@/lib/utils';

interface SectionLabelProps extends HTMLAttributes<HTMLElement> {
  as?: ElementType;
}

export function SectionLabel({ as: Tag = 'h2', className, ...props }: SectionLabelProps) {
  return (
    <Tag
      className={cn(
        'text-xs font-bold uppercase tracking-[0.04em] text-neutral-400',
        className,
      )}
      {...props}
    />
  );
}
