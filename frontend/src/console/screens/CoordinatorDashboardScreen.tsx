/**
 * SCR-06 Coordinator dashboard (role_coordinator, role_admin) - the
 * flagship surface (TASK-027, FR-09, FR-10, FR-12): a real-time load
 * heatmap, a re-plan approval queue with blast radius and one-tap
 * approve/reject, and a live Disruption-Agent reasoning stream, on demo
 * mock data. Replaces the TASK-026 stub.
 *
 * States (spec 10 SCR-06): `loading` and `error` are the screen's own
 * top-level `ScreenState` (the initial async load); once loaded, the
 * screen always renders the heatmap and reasoning stream (they hold no
 * "empty" concept of their own - a calm heatmap IS the empty-queue look),
 * while the "Empty (calm heatmap, no proposals)" row from the spec's
 * states table is realised at the `ApprovalQueuePane`'s own nested
 * `ScreenState` (its "no proposals" message) - see that component's doc
 * comment. `no-permission` is already handled by the TASK-026
 * `ScreenGuard` at the route level, so it is not reproduced here.
 *
 * On a mock LLM failure the screen shows the "auto-coordination paused"
 * banner and holds the last-known screen instead of applying anything
 * (ai-governance.md; TASK-027 acceptance criteria) - `loadData` rejecting
 * is exactly that failure, and no proposal is auto-applied on this path.
 *
 * `loadData` is injected (default = the real mock loader) so tests can
 * simulate that failure deterministically without a global mutable flag.
 */
import { useCallback, useEffect, useState } from 'react';
import { Card, ScreenState, type ViewState } from '@/components/primitives';
import { useI18n } from '@/i18n';
import { useOptionalStaffSession } from '../auth/StaffAuthContext';
import { loadDashboardData, type DashboardData } from '../dashboard/data';
import { ApprovalQueuePane } from '../dashboard/components/ApprovalQueuePane';
import { HeatmapPane } from '../dashboard/components/HeatmapPane';
import { ReasoningStreamPane } from '../dashboard/components/ReasoningStreamPane';
import type { ApprovalActor, DisruptionEvent, HeatmapGrid } from '../dashboard/types';

export interface CoordinatorDashboardScreenProps {
  loadData?: () => Promise<DashboardData>;
}

export function CoordinatorDashboardScreen({ loadData = loadDashboardData }: CoordinatorDashboardScreenProps = {}) {
  const { t } = useI18n();
  const session = useOptionalStaffSession();

  const [viewState, setViewState] = useState<ViewState>('loading');
  const [reasoningTranscript, setReasoningTranscript] = useState('');
  const [proposals, setProposals] = useState<DisruptionEvent[]>([]);
  const [heatmap, setHeatmap] = useState<HeatmapGrid | null>(null);

  useEffect(() => {
    let cancelled = false;
    setViewState('loading');

    loadData()
      .then((data) => {
        if (cancelled) return;
        setHeatmap(data.heatmap);
        setProposals(data.proposals);
        setReasoningTranscript(data.reasoningTranscript);
        setViewState('success');
      })
      .catch(() => {
        // Hold the current plan; nothing is applied automatically
        // (ai-governance.md "Human in the loop").
        if (!cancelled) setViewState('error');
      });

    return () => {
      cancelled = true;
    };
  }, [loadData]);

  const handleResolved = useCallback((eventId: string) => {
    setProposals((current) => current.filter((event) => event.id !== eventId));
  }, []);

  // Derived from the real StaffAuthProvider session - never fabricated
  // (audit-actor integrity, TASK-027 review fix). StaffSession carries no
  // numeric account id, so role is the stable identity in this
  // single-account-per-role demo (matching dashboard/types.ts
  // ApprovalActor's doc comment). SCR-06 sits behind the TASK-026 role
  // guard, so `session` is always present by the time this screen is
  // reachable; `null` is handled defensively by ApprovalQueuePane (disables
  // approve/reject rather than writing a placeholder identity) and is not
  // expected to occur here.
  const actor: ApprovalActor | null = session
    ? { actorId: session.role, actorRole: session.role, actorDisplayName: session.displayName }
    : null;

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-2xl font-bold text-foreground">{t('console.screen.dashboard.title')}</h1>

      <ScreenState
        state={viewState}
        loadingLabel={t('console.dashboard.loadingLabel')}
        errorMessage={
          <Card className="w-full border-danger/30 bg-danger/5 text-left" data-testid="dashboard-error-banner">
            <p className="text-sm font-bold text-danger">{t('console.dashboard.error.title')}</p>
            <p className="mt-1 text-sm text-foreground">{t('console.dashboard.error.body')}</p>
          </Card>
        }
      >
        <div className="flex flex-col gap-4">
          {heatmap && <HeatmapPane initialGrid={heatmap} />}
          <ApprovalQueuePane proposals={proposals} actor={actor} onResolved={handleResolved} />
          <ReasoningStreamPane transcript={reasoningTranscript} />
        </div>
      </ScreenState>
    </div>
  );
}
