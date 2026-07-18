/**
 * Switch - an accessible on/off toggle (role="switch", aria-checked) with
 * the iOS-style sliding thumb on a teal track. Used by settings (large
 * text, high contrast) and family (share location). Keyboard operable and
 * named via `label`.
 */
import { cn } from '@/lib/utils';

interface SwitchProps {
  checked: boolean;
  onChange: (next: boolean) => void;
  /** Accessible name for the control. */
  label: string;
  className?: string;
}

export function Switch({ checked, onChange, label, className }: SwitchProps) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      aria-label={label}
      onClick={() => onChange(!checked)}
      className={cn(
        'relative h-7 w-12 shrink-0 rounded-pill transition-colors focus-visible:outline-none ' +
          'focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background',
        checked ? 'bg-primary' : 'bg-neutral-300',
        className,
      )}
    >
      <span
        aria-hidden="true"
        className={cn(
          'absolute top-[3px] h-[22px] w-[22px] rounded-full bg-white shadow-card transition-[left]',
          checked ? 'left-[23px]' : 'left-[3px]',
        )}
      />
    </button>
  );
}
