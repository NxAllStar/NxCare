/**
 * Avatar - an initials circle for family profiles and the header profile
 * chip. Colour comes from a token by default; a `tone` prop lets the family
 * list vary members without hardcoding hex at the call site.
 */
import { cn } from '@/lib/utils';

interface AvatarProps {
  name: string;
  size?: 'sm' | 'md' | 'lg';
  tone?: 'primary' | 'neutral';
  className?: string;
}

const SIZE: Record<NonNullable<AvatarProps['size']>, string> = {
  sm: 'h-7 w-7 text-xs',
  md: 'h-9 w-9 text-sm',
  lg: 'h-11 w-11 text-base',
};

const TONE: Record<NonNullable<AvatarProps['tone']>, string> = {
  primary: 'bg-primary text-primary-foreground',
  neutral: 'bg-neutral-500 text-white',
};

export function Avatar({ name, size = 'md', tone = 'primary', className }: AvatarProps) {
  const initial = name.trim().charAt(0).toUpperCase() || '?';
  return (
    <span
      aria-hidden="true"
      className={cn(
        'inline-flex shrink-0 items-center justify-center rounded-full font-bold',
        SIZE[size],
        TONE[tone],
        className,
      )}
    >
      {initial}
    </span>
  );
}
