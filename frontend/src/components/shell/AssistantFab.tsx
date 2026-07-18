/**
 * AssistantFab - the always-reachable floating action button into the
 * Journey Agent chat (PRD-FR-12 3.2 principle 3: "the AI assistant is a
 * reachable floating action button, an auxiliary entry point, never the
 * center of the screen"). Floats above the bottom tab bar on every screen.
 */
import { Link, useLocation } from 'react-router-dom';
import { useI18n } from '@/i18n';
import { AssistantIcon } from '@/components/icons';

const ASSISTANT_PATH = '/assistant';

export function AssistantFab() {
  const { t } = useI18n();
  const location = useLocation();

  // Do not float the FAB on top of the chat it opens.
  if (location.pathname === ASSISTANT_PATH) return null;

  return (
    <Link
      to={ASSISTANT_PATH}
      aria-label={t('nav.assistant')}
      className="fixed bottom-24 right-4 z-40 flex h-14 w-14 items-center justify-center rounded-pill bg-primary text-primary-foreground shadow-fab transition-transform active:scale-95"
    >
      <AssistantIcon className="h-6 w-6" />
    </Link>
  );
}
