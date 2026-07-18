/**
 * Shared "not yet built" stub renderer for SCR-03..SCR-07 (TASK-026 scope:
 * on-brand placeholders only - the real worklists, live heatmap, approval
 * queue, reasoning stream, audit search, and simulator config are follow-on
 * tasks). Renders the screen's full title plus the shared ScreenState
 * primitive in its `empty` state, built from shared tokens (frontend.md).
 */
import { useI18n, type DictKey } from '@/i18n';
import { Card, ScreenState } from '@/components/primitives';

export function StubScreen({ titleKey }: { titleKey: DictKey }) {
  const { t } = useI18n();
  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-bold text-foreground">{t(titleKey)}</h1>
      <Card>
        <ScreenState state="empty" emptyMessage={t('placeholder.buildLater')} />
      </Card>
    </div>
  );
}
