/**
 * NotificationsPage - SCR-09 Notifications center (FR-20, TASK-023).
 *
 * Spec 10 SCR-09 has NO Model-assisted content row: unlike every other
 * patient screen, this one never renders an AIChip, even for a
 * notification whose underlying fixture is `aiGenerated: true` (that flag
 * only drives the AIChip on /journey's re-plan-reason banner, FR-11 - it is
 * intentionally ignored here).
 */
import { useEffect, useState } from 'react';
import { useI18n, type DictKey } from '@/i18n';
import { cn } from '@/lib/utils';
import { useAuth } from '@/auth/AuthContext';
import * as notificationsApi from '@/lib/api/notifications';
import { NotificationType } from '@/lib/api/types';
import type { Notification } from '@/lib/api/types';
import { Button, Card, ScreenState, type ViewState } from '@/components/primitives';
import { AlertIcon, BellIcon, CalendarIcon, RouteIcon } from '@/components/icons';

const TYPE_FILTERS: Array<{ value: NotificationType | null; labelKey: DictKey }> = [
  { value: null, labelKey: 'notifications.filterAll' },
  { value: NotificationType.APPOINTMENT, labelKey: 'notifType.APPOINTMENT' },
  { value: NotificationType.RESULT, labelKey: 'notifType.RESULT' },
  { value: NotificationType.BILLING, labelKey: 'notifType.BILLING' },
  { value: NotificationType.JOURNEY, labelKey: 'notifType.JOURNEY' },
];

// Purely decorative type -> icon/colour mapping (no new visible text) so
// each row carries the coloured status icon the design direction calls for.
const TYPE_ICON: Record<NotificationType, { Icon: typeof BellIcon; tone: string }> = {
  [NotificationType.APPOINTMENT]: { Icon: CalendarIcon, tone: 'bg-info/10 text-info' },
  [NotificationType.RESULT]: { Icon: BellIcon, tone: 'bg-success/10 text-success' },
  [NotificationType.BILLING]: { Icon: AlertIcon, tone: 'bg-warning/10 text-warning' },
  [NotificationType.JOURNEY]: { Icon: RouteIcon, tone: 'bg-primary/10 text-primary' },
};

export function NotificationsPage() {
  const { t } = useI18n();
  const { session } = useAuth();
  const patientId = session?.patient.id;

  const [typeFilter, setTypeFilter] = useState<NotificationType | null>(null);
  const [page, setPage] = useState(1);
  const [items, setItems] = useState<Notification[] | null>(null);
  const [totalCount, setTotalCount] = useState(0);
  const [pageSize, setPageSize] = useState(notificationsApi.NOTIFICATIONS_PAGE_SIZE);
  const [loadError, setLoadError] = useState(false);

  useEffect(() => {
    if (!patientId) return;
    let cancelled = false;
    setLoadError(false);
    setItems(null);

    notificationsApi
      .listNotificationsPage(patientId, { page, type: typeFilter })
      .then((result) => {
        if (cancelled) return;
        setItems(result.items);
        setTotalCount(result.totalCount);
        setPageSize(result.pageSize);
      })
      .catch(() => {
        if (!cancelled) setLoadError(true);
      });

    return () => {
      cancelled = true;
    };
  }, [patientId, page, typeFilter]);

  function handleSelectType(value: NotificationType | null) {
    setTypeFilter(value);
    setPage(1);
  }

  async function handleMarkRead(notification: Notification) {
    const updated = await notificationsApi.markNotificationRead(notification.id);
    setItems((prev) => prev?.map((n) => (n.id === updated.id ? updated : n)) ?? prev);
  }

  const totalPages = Math.max(1, Math.ceil(totalCount / pageSize));
  const viewState: ViewState = loadError
    ? 'error'
    : items === null
      ? 'loading'
      : items.length === 0 && totalCount === 0
        ? 'empty'
        : 'success';

  return (
    <div className="flex flex-col gap-4 px-5 py-4 animate-fade-up">
      <h1 className="text-[22px] font-bold">{t('notifications.title')}</h1>

      <div role="group" aria-label={t('notifications.filterLabel')} className="flex flex-wrap gap-2">
        {TYPE_FILTERS.map((option) => {
          const isActive = typeFilter === option.value;
          return (
            <button
              key={option.value ?? 'ALL'}
              type="button"
              aria-pressed={isActive}
              onClick={() => handleSelectType(option.value)}
              className={cn(
                'rounded-pill border px-3 py-1.5 text-[13px] font-bold',
                isActive ? 'border-primary bg-primary text-primary-foreground' : 'border-border bg-card text-muted-foreground',
              )}
            >
              {t(option.labelKey)}
            </button>
          );
        })}
      </div>

      <ScreenState state={viewState} emptyMessage={t('notifications.emptyMessage')}>
        <div className="flex flex-col gap-4">
          <ol className="flex flex-col gap-3">
            {items?.map((notification) => {
              const { Icon, tone } = TYPE_ICON[notification.notificationType];
              return (
                <li key={notification.id} data-testid="notification-item">
                  <Card className="flex flex-col gap-2.5">
                    <div className="flex items-start gap-3">
                      <span
                        aria-hidden="true"
                        className={cn('flex h-8 w-8 shrink-0 items-center justify-center rounded-full', tone)}
                      >
                        <Icon className="h-4 w-4" />
                      </span>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-start justify-between gap-2">
                          <p className="text-[15px] leading-relaxed">{notification.body}</p>
                          <span
                            className={cn(
                              'shrink-0 rounded-pill px-2 py-0.5 text-[10px] font-bold uppercase',
                              notification.read ? 'bg-muted text-muted-foreground' : 'bg-info/10 text-info',
                            )}
                          >
                            {notification.read ? t('notifications.readLabel') : t('notifications.unreadLabel')}
                          </span>
                        </div>
                      </div>
                    </div>
                    {!notification.read && (
                      <Button
                        variant="secondary"
                        size="sm"
                        className="self-start"
                        onClick={() => void handleMarkRead(notification)}
                      >
                        {t('notifications.markRead')}
                      </Button>
                    )}
                  </Card>
                </li>
              );
            })}
          </ol>

          <div className="flex items-center justify-between gap-2">
            <Button
              variant="secondary"
              size="sm"
              disabled={page <= 1}
              onClick={() => setPage((p) => Math.max(1, p - 1))}
            >
              {t('notifications.prevPage')}
            </Button>
            <span className="font-mono text-xs text-muted-foreground">
              {t('notifications.pageOf')} {page}/{totalPages}
            </span>
            <Button
              variant="secondary"
              size="sm"
              disabled={page >= totalPages}
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
            >
              {t('notifications.nextPage')}
            </Button>
          </div>
        </div>
      </ScreenState>
    </div>
  );
}
