/**
 * Proves the reasoning stream reveals text progressively with a "thinking"
 * flag while it does (TASK-027 acceptance criteria: "reasoning stream
 * renders labelled AI text" + "thinking indicator while streaming").
 */
import { act, renderHook } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { chunkReasoningText, useReasoningStream } from './reasoningStream';

describe('chunkReasoningText (pure)', () => {
  it('splits a transcript into small word groups, in order, losslessly', () => {
    const chunks = chunkReasoningText('one two three four five six', 2);
    expect(chunks).toEqual(['one two', 'three four', 'five six']);
  });

  it('returns an empty array for an empty transcript', () => {
    expect(chunkReasoningText('   ', 4)).toEqual([]);
  });
});

describe('useReasoningStream (mock token reveal)', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('starts empty and streaming, then reveals more text on each tick until done', () => {
    const { result } = renderHook(() => useReasoningStream('one two three four five six seven eight', 100));

    expect(result.current.text).toBe('');
    expect(result.current.isStreaming).toBe(true);

    act(() => {
      vi.advanceTimersByTime(100);
    });
    const afterFirstTick = result.current.text;
    expect(afterFirstTick.length).toBeGreaterThan(0);
    expect(result.current.isStreaming).toBe(true);

    act(() => {
      vi.advanceTimersByTime(1000); // plenty of ticks to reach the end
    });
    expect(result.current.text).toBe('one two three four five six seven eight');
    expect(result.current.isStreaming).toBe(false);
  });

  it('resets and re-streams when the transcript changes', () => {
    const { result, rerender } = renderHook(({ transcript }) => useReasoningStream(transcript, 100), {
      initialProps: { transcript: 'first transcript here' },
    });

    act(() => {
      vi.advanceTimersByTime(1000);
    });
    expect(result.current.text).toBe('first transcript here');
    expect(result.current.isStreaming).toBe(false);

    rerender({ transcript: 'second transcript now' });
    expect(result.current.text).toBe('');
    expect(result.current.isStreaming).toBe(true);
  });
});
