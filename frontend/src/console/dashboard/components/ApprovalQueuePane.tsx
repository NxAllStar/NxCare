/**
 * ApprovalQueuePane - SCR-06 "Approval queue: re-plan proposals" pane
 * (BR-22, FR-09, FR-10, FR-12). One row per `DisruptionEvent`: blast
 * radius, options, AI-labelled reason, and one-tap approve/reject.
 *
 * Approve/reject are enabled ONLY while `status === 'PENDING_APPROVAL'`
 * (TASK-027 acceptance criteria) - this is checked on every row regardless
 * of what the caller passes in, so the guard holds even if an upstream
 * list is ever supplied un-filtered. Reject always asks for confirmation
 * first (every proposal here is large-impact by definition - spec 10
 * cross-cutting UI rules "confirmation for ... reject large re-plan").
 *
 * `decide` is injectable (default = the real mock service) so this
 * component's tests can control the async outcome deterministically.
 */
import { useState } from 'react';
import { AIChip, Button, Card, ScreenState, SectionLabel } from '@/components/primitives';
import { useI18n } from '@/i18n';
import { decideProposal } from '../proposals';
import type { ApprovalActor, AuditDecision, AuditEntry, DisruptionEvent } from '../types';

export interface ApprovalQueuePaneProps {
  proposals: DisruptionEvent[];
  /** The real staff identity making the decision, derived by the caller
   * from `StaffAuthProvider` (never fabricated - see `runDecision` below).
   * `null` only in the defensive case where no session exists; SCR-06 sits
   * behind the TASK-026 role guard so a real session is always present in
   * practice, but the guard is never bypassed by writing a placeholder
   * actor here. */
  actor: ApprovalActor | null;
  /** Fired after a decision is successfully recorded, so the parent can
   * remove the proposal from its own state (the queue "dequeue"). */
  onResolved: (eventId: string, entry: AuditEntry) => void;
  decide?: (eventId: string, decision: AuditDecision, actor: ApprovalActor) => Promise<AuditEntry>;
}

// Rendered in Vietnam local time (Asia/Ho_Chi_Minh, UTC+7), not UTC - this is
// a VN hospital console (TASK-027 review fix). Tabular numbers preserved via
// the caller's `tabular-nums` class on the <time> element.
const VN_TIME_FORMATTER = new Intl.DateTimeFormat('vi-VN', {
  timeZone: 'Asia/Ho_Chi_Minh',
  hour: '2-digit',
  minute: '2-digit',
  hour12: false,
});

function formatTriggeredAt(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : VN_TIME_FORMATTER.format(d);
}

export function ApprovalQueuePane({ proposals, actor, onResolved, decide = decideProposal }: ApprovalQueuePaneProps) {
  const { t } = useI18n();
  const [confirmingRejectId, setConfirmingRejectId] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [errorId, setErrorId] = useState<string | null>(null);

  async function runDecision(event: DisruptionEvent, decision: AuditDecision) {
    // Defensive: never write a fabricated actor. SCR-06 sits behind the
    // TASK-026 role guard, so `actor` is always a real staff identity by the
    // time a user can reach this control; this guard only matters if that
    // invariant is ever violated, and in that case it holds - no decision,
    // no audit entry - rather than inventing an identity.
    if (!actor) return;
    setBusyId(event.id);
    setErrorId(null);
    try {
      const entry = await decide(event.id, decision, actor);
      setConfirmingRejectId((current) => (current === event.id ? null : current));
      onResolved(event.id, entry);
    } catch {
      // Errors handled explicitly (coding-standards.md) - never swallowed:
      // the row stays in place and shows a retry-able inline message.
      setErrorId(event.id);
    } finally {
      setBusyId((current) => (current === event.id ? null : current));
    }
  }

  return (
    <Card className="flex flex-col gap-4 p-5" data-testid="approval-queue-pane">
      <SectionLabel>{t('console.dashboard.approvalQueue.title')}</SectionLabel>

      <ScreenState state={proposals.length === 0 ? 'empty' : 'success'} emptyMessage={t('console.dashboard.approvalQueue.emptyMessage')}>
        <ul className="flex flex-col divide-y divide-border">
          {proposals.map((event) => {
            const isPending = event.status === 'PENDING_APPROVAL';
            const isBusy = busyId === event.id;
            // No actor (defensive, see runDecision above) disables every
            // control - never a fabricated identity behind an enabled button.
            const disabled = !isPending || isBusy || !actor;
            const isConfirmingReject = confirmingRejectId === event.id;

            return (
              <li key={event.id} className="py-4 first:pt-0 last:pb-0">
                <div className="flex flex-col gap-3" data-testid={`proposal-row-${event.id}`} data-status={event.status}>
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex flex-wrap items-center gap-2.5">
                      <span className="text-[15px] font-bold text-foreground">{event.areaLabel}</span>
                      <AIChip label={t('console.dashboard.approvalQueue.aiProposalChip')} />
                    </div>
                    <time
                      dateTime={event.triggeredAt}
                      className="font-mono text-sm tabular-nums text-muted-foreground"
                    >
                      {formatTriggeredAt(event.triggeredAt)}
                    </time>
                  </div>

                  {/* Thin danger hairline under the proposal header (design/dieu-phoi-vien.png) */}
                  <div aria-hidden="true" className="h-px w-full bg-danger/25" />

                  <div className="flex items-baseline gap-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                      {t('console.dashboard.approvalQueue.blastRadiusLabel')}
                    </span>
                    <span className="font-mono text-lg font-extrabold tabular-nums text-danger">
                      {event.blastRadius}
                    </span>
                  </div>

                  <div>
                    <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                      {t('console.dashboard.approvalQueue.optionsLabel')}
                    </span>
                    <ul className="mt-1.5 flex list-disc flex-col gap-1 pl-5 text-sm leading-relaxed text-foreground">
                      {event.options.map((option) => (
                        <li key={option.id}>
                          <span className="font-semibold">{option.label}</span>
                          {' - '}
                          <span className="text-muted-foreground">{option.description}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <p className="text-sm leading-relaxed text-muted-foreground" data-testid={`proposal-reason-${event.id}`}>
                    {event.aiReason}
                  </p>

                  {errorId === event.id && (
                    <p role="alert" className="text-sm font-medium text-danger">
                      {t('console.dashboard.approvalQueue.actionError')}
                    </p>
                  )}

                  {isConfirmingReject ? (
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-sm font-medium text-danger">
                        {t('console.dashboard.approvalQueue.confirmRejectPrompt')}
                      </span>
                      <Button
                        variant="danger"
                        size="sm"
                        className="rounded-xl"
                        disabled={isBusy || !actor}
                        onClick={() => void runDecision(event, 'REJECTED')}
                      >
                        {t('console.dashboard.approvalQueue.confirmRejectYes')}
                      </Button>
                      <Button variant="secondary" size="sm" className="rounded-xl" onClick={() => setConfirmingRejectId(null)}>
                        {t('console.dashboard.approvalQueue.confirmRejectNo')}
                      </Button>
                    </div>
                  ) : (
                    <div className="flex items-center gap-2.5">
                      <Button
                        variant="primary"
                        size="sm"
                        className="rounded-xl"
                        disabled={disabled}
                        onClick={() => void runDecision(event, 'APPROVED')}
                      >
                        {t('console.dashboard.approvalQueue.approve')}
                      </Button>
                      <Button
                        variant="danger"
                        size="sm"
                        className="rounded-xl"
                        disabled={disabled}
                        onClick={() => setConfirmingRejectId(event.id)}
                      >
                        {t('console.dashboard.approvalQueue.reject')}
                      </Button>
                    </div>
                  )}
                </div>
              </li>
            );
          })}
        </ul>
      </ScreenState>
    </Card>
  );
}
