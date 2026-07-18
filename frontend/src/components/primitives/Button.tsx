/**
 * Button - the shared action primitive for the patient app (design
 * direction: iOS-native pill buttons on the teal token palette). One
 * component, four intents, three sizes, built only from design tokens so
 * the look stays consistent and themable (frontend.md: build from tokens,
 * no hardcoded colours in screens).
 *
 * `buttonVariants` is exported so react-router `<Link>`s can wear the exact
 * same classes without duplicating them (e.g. a shortcut that navigates).
 */
import type { ButtonHTMLAttributes } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '@/lib/utils';

export const buttonVariants = cva(
  'inline-flex items-center justify-center gap-2 rounded-pill font-semibold transition-colors ' +
    'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 ' +
    'focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-60',
  {
    variants: {
      variant: {
        // Solid teal - the single primary call to action on a screen.
        primary: 'bg-primary text-primary-foreground active:brightness-95',
        // White pill with a hairline border - secondary actions.
        secondary: 'border border-border bg-card text-foreground active:bg-muted',
        // Text-only - tertiary / dismissive actions.
        ghost: 'bg-transparent text-primary active:bg-primary/5',
        // Muted fill - low-emphasis chips and quiet actions.
        subtle: 'bg-muted text-foreground active:bg-border',
        // Danger outline - destructive confirmations.
        danger: 'border border-danger bg-card text-danger active:bg-danger/5',
      },
      size: {
        lg: 'h-14 px-6 text-[17px]',
        md: 'h-12 px-5 text-[15px]',
        sm: 'h-10 px-4 text-[13px]',
      },
      block: { true: 'w-full', false: '' },
    },
    defaultVariants: { variant: 'primary', size: 'lg', block: false },
  },
);

export interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {}

export function Button({ variant, size, block, className, type, ...props }: ButtonProps) {
  return (
    <button
      type={type ?? 'button'}
      className={cn(buttonVariants({ variant, size, block }), className)}
      {...props}
    />
  );
}
