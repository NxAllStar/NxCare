/**
 * ScreenState - the five-state wrapper repeated in every screen's "States"
 * table in spec 10: empty / loading / error / no-permission / success.
 *
 * The screen batches (TASK-022, TASK-023) feed this per-screen content
 * through `children` (success) and the message overrides; this task only
 * builds and tests the wrapper itself.
 *
 * "No permission" means own-scope-only (NFR-SEC-05): a caller reaches this
 * state when the requested data was never returned to begin with (see
 * frontend/src/lib/api/patient.ts), not because the UI chose to hide it.
 */
import type { ReactNode } from 'react';
import { useI18n } from '@/i18n';
import { cn } from '@/lib/utils';

export type ViewState = 'loading' | 'empty' | 'error' | 'no-permission' | 'success';

interface ScreenStateProps {
  state: ViewState;
  /**
   * Message overrides accept a ReactNode (not just a string) so a screen can
   * compose a short multi-part message (e.g. a greeting title plus a
   * prompt line) for its empty/loading/error/no-permission state, instead
   * of being limited to one plain sentence (TASK-022, e.g. /intake SCR-01
   * "Empty (chưa chat)" which specifies both a greeting AND a prompt).
   */
  loadingLabel?: ReactNode;
  emptyMessage?: ReactNode;
  errorMessage?: ReactNode;
  noPermissionMessage?: ReactNode;
  className?: string;
  children?: ReactNode;
}

export function ScreenState({
  state,
  loadingLabel,
  emptyMessage,
  errorMessage,
  noPermissionMessage,
  className,
  children,
}: ScreenStateProps) {
  const { t } = useI18n();

  switch (state) {
    case 'loading':
      return (
        <div
          role="status"
          aria-live="polite"
          data-testid="screen-state-loading"
          className={cn('flex items-center justify-center p-8 text-sm text-muted-foreground', className)}
        >
          {loadingLabel ?? t('state.loading')}
        </div>
      );
    case 'empty':
      return (
        <div
          data-testid="screen-state-empty"
          className={cn('flex items-center justify-center p-8 text-sm text-muted-foreground', className)}
        >
          {emptyMessage ?? t('state.empty')}
        </div>
      );
    case 'error':
      return (
        <div
          role="alert"
          data-testid="screen-state-error"
          className={cn('flex items-center justify-center p-8 text-sm text-danger', className)}
        >
          {errorMessage ?? t('state.error')}
        </div>
      );
    case 'no-permission':
      return (
        <div
          data-testid="screen-state-no-permission"
          className={cn('flex items-center justify-center p-8 text-sm text-muted-foreground', className)}
        >
          {noPermissionMessage ?? t('state.noPermission')}
        </div>
      );
    case 'success':
      return <>{children}</>;
  }
}
