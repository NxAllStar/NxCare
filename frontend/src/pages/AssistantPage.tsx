/**
 * AssistantPage - FAB-launched Journey/Intake Agent chat (/assistant).
 *
 * PRD-FR-12 3.2 principle 3: the assistant is an auxiliary entry point, not
 * the center of the screen - this page is only reached through the FAB.
 *
 * Security (AC-01.3/AC-06.3, same rule as /intake): every chat bubble
 * renders `message.text` as a plain React text child, never
 * `dangerouslySetInnerHTML` - text that looks like an instruction or embeds
 * markup is always inert data, never executed.
 */
import { useState, type FormEvent } from 'react';
import { useI18n } from '@/i18n';
import { cn } from '@/lib/utils';
import * as assistantApi from '@/lib/api/assistant';
import type { ChatMessage } from '@/lib/api/types';
import { AIChip, Button } from '@/components/primitives';

let messageIdCounter = 0;
function nextMessageId(): string {
  messageIdCounter += 1;
  return `assistant-patient-msg-${messageIdCounter}`;
}

function initialGreeting(t: (key: 'assistant.greeting') => string): ChatMessage {
  return {
    id: 'assistant-greeting',
    sender: 'agent',
    text: t('assistant.greeting'),
    createdAt: new Date().toISOString(),
    aiGenerated: true,
  };
}

export function AssistantPage() {
  const { t } = useI18n();
  const [messages, setMessages] = useState<ChatMessage[]>([initialGreeting(t)]);
  const [isThinking, setIsThinking] = useState(false);
  const [inputValue, setInputValue] = useState('');

  async function sendText(text: string) {
    const patientMessage: ChatMessage = {
      id: nextMessageId(),
      sender: 'patient',
      text,
      createdAt: new Date().toISOString(),
      aiGenerated: false,
    };
    setMessages((prev) => [...prev, patientMessage]);
    setInputValue('');
    setIsThinking(true);
    try {
      const reply = await assistantApi.sendAssistantMessage(text);
      setMessages((prev) => [...prev, reply]);
    } finally {
      setIsThinking(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const text = inputValue.trim();
    if (!text) return;
    void sendText(text);
  }

  return (
    <div className="flex flex-col gap-4 px-5 py-4 animate-fade-up">
      <div>
        <h1 className="text-[22px] font-bold">{t('assistant.title')}</h1>
        <p className="text-[15px] text-muted-foreground">{t('assistant.subtitle')}</p>
      </div>

      <div className="flex flex-col gap-3" data-testid="assistant-chat-stream">
        {messages.map((message) => {
          const isPatient = message.sender === 'patient';
          return (
            <div key={message.id} className={cn('flex flex-col gap-1', isPatient ? 'items-end' : 'items-start')}>
              {!isPatient && (
                <div className="flex items-center gap-2">
                  <AIChip />
                </div>
              )}
              <p
                className={cn(
                  'max-w-[85%] rounded-2xl px-4 py-2.5 text-[15px] leading-relaxed',
                  isPatient ? 'bg-primary text-primary-foreground' : 'bg-muted text-foreground',
                )}
              >
                {message.text}
              </p>
            </div>
          );
        })}

        {isThinking && (
          <div role="status" aria-live="polite" className="text-sm text-muted-foreground">
            {t('assistant.thinking')}
          </div>
        )}
      </div>

      <div className="flex flex-col gap-2">
        <h2 className="text-xs font-bold uppercase tracking-[0.04em] text-neutral-400">
          {t('assistant.quickQuestionsHeading')}
        </h2>
        <div className="flex flex-wrap gap-2">
          {assistantApi.QUICK_QUESTIONS.map((question) => (
            <Button
              key={question}
              variant="secondary"
              size="sm"
              onClick={() => void sendText(question)}
            >
              {question}
            </Button>
          ))}
        </div>
      </div>

      <form onSubmit={handleSubmit} className="flex items-center gap-2">
        <label htmlFor="assistant-message-input" className="sr-only">
          {t('assistant.inputLabel')}
        </label>
        <input
          id="assistant-message-input"
          aria-label={t('assistant.inputLabel')}
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          placeholder={t('assistant.inputPlaceholder')}
          disabled={isThinking}
          className="h-12 flex-1 rounded-2xl border border-border bg-muted px-4 text-[15px] font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
        />
        <Button type="submit" size="md" disabled={isThinking || inputValue.trim().length === 0}>
          {t('assistant.send')}
        </Button>
      </form>
    </div>
  );
}
