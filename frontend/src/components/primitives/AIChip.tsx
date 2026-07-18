/**
 * AIChip - the consistent "AI" label every model-produced value carries
 * (NFR-USE-05, spec 10 "Visual design direction" > AI-content treatment).
 *
 * Use on slot suggestions, re-plan reasons, chat replies, and any other
 * model output rendered in the UI - never present that content as a
 * confirmed fact without this label next to it.
 */
import { cn } from '@/lib/utils';
import { useI18n } from '@/i18n';

interface AIChipProps {
  /** Override the default localised "AI-suggested" label (e.g. for a more specific caption). */
  label?: string;
  className?: string;
}

export function AIChip({ label, className }: AIChipProps) {
  const { t } = useI18n();

  return (
    <span
      data-testid="ai-chip"
      className={cn(
        'inline-flex items-center gap-1 rounded-pill border border-primary/30 bg-primary/10',
        'px-3 py-1 text-xs font-medium text-primary',
        className,
      )}
    >
      <svg
        aria-hidden="true"
        viewBox="0 0 16 16"
        className="h-3 w-3 shrink-0 fill-current"
      >
        <path d="M8 0l1.6 4.8L14.4 6l-4.8 1.6L8 12.4 6.4 7.6 1.6 6l4.8-1.2L8 0z" />
      </svg>
      <span>{label ?? t('ai.badge')}</span>
    </span>
  );
}
