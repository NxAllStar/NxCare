/**
 * Live Disruption-Agent reasoning stream (SCR-06 "Stream reasoning" -
 * FR-09, FR-10). No backend/socket exists yet - the "stream" is a mock
 * word-by-word reveal of a fixed demo transcript (fixtures.ts), calm and
 * readable per spec 10's "signature surfaces" direction. Rendered only as
 * plain text (StreamingText primitive), never as HTML (frontend.md).
 */
import { useEffect, useMemo, useState } from 'react';

/** Pure: splits a transcript into small word-groups to reveal over time.
 * `wordsPerChunk` controls how "chatty" the reveal feels - kept small for a
 * calm, readable pace rather than one word at a time. */
export function chunkReasoningText(text: string, wordsPerChunk = 4): string[] {
  const words = text.trim().split(/\s+/).filter(Boolean);
  const chunks: string[] = [];
  for (let i = 0; i < words.length; i += wordsPerChunk) {
    chunks.push(words.slice(i, i + wordsPerChunk).join(' '));
  }
  return chunks;
}

export interface ReasoningStreamState {
  /** The text revealed so far - always a prefix of the full transcript. */
  text: string;
  /** True while there is more of the transcript still to reveal - drives
   * the "thinking" indicator (spec 10 SCR-06 "Waiting behaviour"). */
  isStreaming: boolean;
}

/** Reveals `transcript` a few words at a time on a fixed interval, mocking
 * a live token stream. Resets and re-streams whenever `transcript` changes. */
export function useReasoningStream(transcript: string, intervalMs = 200): ReasoningStreamState {
  const chunks = useMemo(() => chunkReasoningText(transcript), [transcript]);
  const [revealedCount, setRevealedCount] = useState(0);

  useEffect(() => {
    setRevealedCount(0);
    if (chunks.length === 0) return;

    const id = window.setInterval(() => {
      setRevealedCount((count) => {
        const next = count + 1;
        if (next >= chunks.length) {
          window.clearInterval(id);
        }
        return next;
      });
    }, intervalMs);

    return () => window.clearInterval(id);
  }, [chunks, intervalMs]);

  return {
    text: chunks.slice(0, revealedCount).join(' '),
    isStreaming: revealedCount < chunks.length,
  };
}
