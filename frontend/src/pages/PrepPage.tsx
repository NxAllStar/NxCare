/**
 * PrepPage - /prep/:id PROACTIVE PREP (PMA-M2, TASK-023). Pre-visit
 * reminders (fasting, bring old prescriptions/results) ahead of an
 * appointment.
 */
import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { useI18n } from '@/i18n';
import { cn } from '@/lib/utils';
import * as prepApi from '@/lib/api/prep';
import type { PrepReminder } from '@/lib/api/types';
import { ScreenState, type ViewState } from '@/components/primitives/ScreenState';

export function PrepPage() {
  const { t } = useI18n();
  const { id } = useParams<{ id: string }>();

  const [reminder, setReminder] = useState<PrepReminder | null | undefined>(undefined);
  const [loadError, setLoadError] = useState(false);

  useEffect(() => {
    if (!id) return;
    let cancelled = false;
    setLoadError(false);
    setReminder(undefined);

    prepApi
      .getPrepReminder(id)
      .then((result) => {
        if (!cancelled) setReminder(result);
      })
      .catch(() => {
        if (!cancelled) setLoadError(true);
      });

    return () => {
      cancelled = true;
    };
  }, [id]);

  const viewState: ViewState = loadError ? 'error' : reminder === undefined ? 'loading' : reminder === null ? 'empty' : 'success';

  return (
    <div className="flex flex-col gap-4 px-5 py-4 animate-fade-up">
      <h1 className="text-[22px] font-bold">{t('prep.title')}</h1>

      <ScreenState state={viewState} emptyMessage={t('prep.notFound')}>
        {reminder && (
          <ol className="flex flex-col overflow-hidden rounded-2xl border border-border bg-card">
            {reminder.instructions.map((instruction, index) => (
              <li
                key={index}
                className={cn(
                  'flex items-start gap-3 p-4 text-[15px] leading-relaxed',
                  index !== reminder.instructions.length - 1 && 'border-b border-border',
                )}
              >
                <span
                  aria-hidden="true"
                  className="mt-0.5 h-[22px] w-[22px] shrink-0 rounded-full border-[1.5px] border-neutral-300"
                />
                <span>{instruction}</span>
              </li>
            ))}
          </ol>
        )}
      </ScreenState>
    </div>
  );
}
