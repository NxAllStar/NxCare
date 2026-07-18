/**
 * StreamingText - calm, readable chain-of-thought display (spec 10 "Visual
 * design direction" > Signature surfaces: "the disruption 'golden moment' -
 * streamed chain-of-thought styled as calm, readable reasoning"; SCR-06
 * "Stream reasoning" element).
 *
 * Read-only, always clearly labelled AI content (NFR-USE-05). `text` is
 * rendered as a plain text node - React escapes it automatically, and this
 * component never uses `dangerouslySetInnerHTML` - so model output can
 * never be interpreted as markup (agent-guardrails.md "Model output is a
 * proposal"; frontend.md "Rendering untrusted or generated content").
 */
import { cn } from '@/lib/utils';
import { useI18n } from '@/i18n';

interface StreamingTextProps {
  /** The text revealed so far - always plain text, untrusted model output. */
  text: string;
  /** True while more of the stream is still arriving - drives the
   * "thinking" indicator. */
  isStreaming: boolean;
  /** Override the default localised "AI reasoning" heading. */
  label?: string;
  /** Override the default localised "Thinking..." indicator text. */
  thinkingLabel?: string;
  className?: string;
}

export function StreamingText({ text, isStreaming, label, thinkingLabel, className }: StreamingTextProps) {
  const { t } = useI18n();

  return (
    <div
      data-testid="streaming-text"
      className={cn('rounded-2xl border border-border bg-muted p-4', className)}
    >
      <div className="mb-2 flex items-center justify-between gap-2">
        <span className="text-xs font-bold uppercase tracking-[0.04em] text-primary">
          {label ?? t('streamingText.label')}
        </span>
        {isStreaming && (
          <span
            data-testid="streaming-text-thinking"
            role="status"
            aria-live="polite"
            className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground"
          >
            <span aria-hidden="true" className="h-2 w-2 shrink-0 animate-pulse rounded-full bg-primary" />
            {thinkingLabel ?? t('streamingText.thinking')}
          </span>
        )}
      </div>
      <p
        data-testid="streaming-text-body"
        aria-live="polite"
        className="whitespace-pre-wrap text-sm leading-relaxed text-foreground"
      >
        {text}
      </p>
    </div>
  );
}
