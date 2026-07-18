/**
 * PlaceholderScreen - generic stand-in for every route the screen batches
 * (TASK-022, TASK-023) will replace. Not a product screen: it exists only
 * so the route table and shell are navigable end to end in this
 * foundation task.
 */
import { useI18n } from '@/i18n';
import { SparkleIcon } from '@/components/icons';

interface PlaceholderScreenProps {
  /** Screen id from docs/specs/10-ui-ux-wireframes.md or the PRD sitemap, e.g. "SCR-01" or "/book". */
  title: string;
  /** Priority tag from the PRD sitemap (P0/P1/P2), shown as-is (English code, BR-31). */
  priority?: 'P0' | 'P1' | 'P2';
}

export function PlaceholderScreen({ title, priority }: PlaceholderScreenProps) {
  const { t } = useI18n();

  return (
    <div className="flex flex-col items-center gap-4 px-6 py-16 text-center animate-fade-up">
      <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-primary/10 text-primary">
        <SparkleIcon className="h-6 w-6" />
      </span>
      <div className="flex items-center gap-2">
        <h1 className="text-base font-bold">{title}</h1>
        {priority && (
          <span className="rounded-pill bg-muted px-2 py-0.5 font-mono text-[10px] uppercase text-muted-foreground">
            {priority}
          </span>
        )}
      </div>
      <p className="max-w-xs text-sm leading-relaxed text-muted-foreground">{t('placeholder.buildLater')}</p>
    </div>
  );
}
