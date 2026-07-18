/**
 * ReasoningStreamPane - SCR-06 "Live reasoning stream (Disruption Agent)"
 * pane. Wires the mock token reveal (reasoningStream.ts) to the shared
 * `StreamingText` primitive - read-only, always AI-labelled.
 */
import { StreamingText } from '@/components/primitives';
import { useI18n } from '@/i18n';
import { useReasoningStream } from '../reasoningStream';

export interface ReasoningStreamPaneProps {
  transcript: string;
  intervalMs?: number;
}

export function ReasoningStreamPane({ transcript, intervalMs = 200 }: ReasoningStreamPaneProps) {
  const { t } = useI18n();
  const { text, isStreaming } = useReasoningStream(transcript, intervalMs);

  return <StreamingText text={text} isStreaming={isStreaming} label={t('console.dashboard.reasoning.title')} />;
}
