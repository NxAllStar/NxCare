/**
 * IntakePage - SCR-01 Intake chat (FR-01, FR-02, BF-05).
 *
 * The chat transcript and slot suggestions are the ScreenState "success"
 * content; the greeting, the thinking/timeout indicator, and the error
 * message are the empty/loading/error states (spec 10 SCR-01 States table).
 * "No permission" is not applicable here (public to the authenticated
 * patient, per spec 10) and is not wired to any reachable path.
 *
 * Security (AC-01.3/AC-06.3): every chat bubble renders `message.text` as a
 * plain React text child - never `dangerouslySetInnerHTML` - so text that
 * looks like an instruction or embeds markup is always inert data.
 */
import { useRef, useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useI18n } from '@/i18n';
import { cn } from '@/lib/utils';
import * as intakeApi from '@/lib/api/intake';
import type { ChatMessage, RankedSlotSuggestion } from '@/lib/api/types';
import { AIChip, Button, SectionLabel } from '@/components/primitives';
import { ScreenState, type ViewState } from '@/components/primitives/ScreenState';
import { AlertIcon, SendIcon, SparkleIcon } from '@/components/icons';

// SCR-01 "Waiting behaviour": thinking indicator with a timeout, after which
// the screen offers a retry rather than spinning forever (NFR-USE-04).
const THINKING_TIMEOUT_MS = 8000;

type TurnStatus = 'idle' | 'thinking' | 'timeout' | 'error';

let messageIdCounter = 0;
function nextMessageId(): string {
  messageIdCounter += 1;
  return `intake-patient-msg-${messageIdCounter}`;
}

function ChatBubble({ message }: { message: ChatMessage }) {
  const isPatient = message.sender === 'patient';
  return (
    <div className={cn('flex items-end gap-2', isPatient ? 'justify-end' : 'justify-start')}>
      {!isPatient && (
        <span
          aria-hidden="true"
          className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-primary text-primary-foreground"
        >
          <SparkleIcon className="h-3.5 w-3.5" />
        </span>
      )}
      <p
        className={cn(
          'max-w-[80%] rounded-2xl px-4 py-2.5 text-[15px] leading-relaxed',
          isPatient ? 'bg-primary text-primary-foreground' : 'bg-muted text-foreground',
        )}
      >
        {message.text}
      </p>
    </div>
  );
}

export function IntakePage() {
  const { t } = useI18n();
  const navigate = useNavigate();

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [status, setStatus] = useState<TurnStatus>('idle');
  const [suggestedSlots, setSuggestedSlots] = useState<RankedSlotSuggestion[]>([]);
  const [emergencySuspected, setEmergencySuspected] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const [lastPatientText, setLastPatientText] = useState('');
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  function clearThinkingTimeout() {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }

  async function runTurn(text: string) {
    setStatus('thinking');
    setLastPatientText(text);
    clearThinkingTimeout();
    timeoutRef.current = setTimeout(() => setStatus('timeout'), THINKING_TIMEOUT_MS);

    try {
      const result = await intakeApi.sendIntakeMessage(text);
      clearThinkingTimeout();
      setMessages((prev) => [...prev, result.reply]);
      setSuggestedSlots(result.suggestedSlots);
      setEmergencySuspected(result.emergencySuspected);
      setStatus('idle');
    } catch {
      clearThinkingTimeout();
      setStatus('error');
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = inputValue.trim();
    if (!text) return;

    const patientMessage: ChatMessage = {
      id: nextMessageId(),
      sender: 'patient',
      text,
      createdAt: new Date().toISOString(),
      aiGenerated: false,
    };
    setMessages((prev) => [...prev, patientMessage]);
    setInputValue('');
    void runTurn(text);
  }

  function handleRetry() {
    void runTurn(lastPatientText);
  }

  function handleBookSlot(slot: RankedSlotSuggestion) {
    // Books toward /book; this never creates a ServiceOrder - that type
    // does not exist on the patient surface (coding-standards.md, the
    // clinical boundary is a doctor-only write, SCR-03).
    navigate('/book', { state: { slotId: slot.slotId, specialty: slot.specialty } });
  }

  const viewState: ViewState =
    messages.length === 0
      ? 'empty'
      : status === 'thinking' || status === 'timeout'
        ? 'loading'
        : status === 'error'
          ? 'error'
          : 'success';

  return (
    <div className="flex flex-col gap-4 px-5 py-4 animate-fade-up">
      <div className="flex items-start gap-2 rounded-2xl border border-warning/25 bg-warning/10 px-3.5 py-2.5">
        <AlertIcon className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
        <p className="text-[13px] leading-relaxed text-warning">{t('intake.notDiagnosisBanner')}</p>
      </div>

      <ScreenState
        state={viewState}
        emptyMessage={
          <div className="flex flex-col items-center gap-1 text-center">
            <p className="text-base font-semibold text-foreground">{t('intake.greetingTitle')}</p>
            <p className="text-[15px]">{t('intake.greetingPrompt')}</p>
          </div>
        }
        loadingLabel={
          status === 'timeout' ? (
            <div className="flex flex-col items-center gap-3">
              <p className="text-[15px] text-muted-foreground">{t('intake.timeoutMessage')}</p>
              <Button variant="secondary" size="sm" onClick={handleRetry}>
                {t('intake.retry')}
              </Button>
            </div>
          ) : (
            <span className="text-[15px] text-muted-foreground">{t('intake.thinking')}</span>
          )
        }
        errorMessage={
          <div className="flex flex-col items-center gap-3">
            <p className="text-[15px] text-muted-foreground">{t('intake.errorMessage')}</p>
            <Button variant="secondary" size="sm" onClick={handleRetry}>
              {t('intake.retry')}
            </Button>
          </div>
        }
      >
        <div className="flex flex-col gap-3" data-testid="intake-chat-stream">
          {messages.map((message) => (
            <ChatBubble key={message.id} message={message} />
          ))}

          {emergencySuspected && (
            <div
              role="alert"
              className="flex items-start gap-2 rounded-2xl border border-danger/40 bg-danger/10 p-3.5 text-sm text-danger"
            >
              <AlertIcon className="h-5 w-5 shrink-0" />
              <span>{t('intake.emergencyBanner')}</span>
            </div>
          )}

          {!emergencySuspected && suggestedSlots.length > 0 && (
            <div className="flex flex-col gap-2">
              <SectionLabel>{t('intake.slotsHeading')}</SectionLabel>
              {suggestedSlots.map((slot) => (
                <div
                  key={slot.slotId}
                  className="flex flex-col gap-3 rounded-2xl border border-border bg-card p-4 shadow-card"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[15px] font-semibold">{slot.specialty}</span>
                    <AIChip />
                  </div>
                  <span className="font-mono text-sm text-muted-foreground">{slot.etaLabel}</span>
                  <Button size="sm" onClick={() => handleBookSlot(slot)}>
                    {t('intake.bookButton')}
                  </Button>
                </div>
              ))}
            </div>
          )}
        </div>
      </ScreenState>

      <form onSubmit={handleSubmit} className="flex items-center gap-2">
        <label htmlFor="intake-message-input" className="sr-only">
          {t('intake.inputLabel')}
        </label>
        <input
          id="intake-message-input"
          aria-label={t('intake.inputLabel')}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder={t('intake.inputPlaceholder')}
          disabled={status === 'thinking'}
          className={cn(
            'h-12 flex-1 rounded-2xl border border-border bg-muted px-4 text-[15px] font-medium',
            'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2',
            'focus-visible:ring-offset-background',
          )}
        />
        <Button
          type="submit"
          size="md"
          disabled={status === 'thinking' || inputValue.trim().length === 0}
          className="shrink-0 gap-1.5"
        >
          <SendIcon className="h-4 w-4" />
          {t('intake.send')}
        </Button>
      </form>
    </div>
  );
}
