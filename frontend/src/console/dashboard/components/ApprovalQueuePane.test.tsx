/**
 * ApprovalQueuePane - proves BR-22/FR-09/FR-12 (TASK-027 acceptance
 * criteria): approve and reject are one-tap, enabled only while
 * PENDING_APPROVAL, reject asks for confirmation first, and a successful
 * decision is reported to the parent (the "dequeue") together with the
 * audit entry (NFR-USE-05: AI content is labelled; the reason is model
 * output rendered as plain text).
 */
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { I18nProvider } from '@/i18n';
import { ApprovalQueuePane } from './ApprovalQueuePane';
import type { ApprovalActor, AuditDecision, AuditEntry, DisruptionEvent } from '../types';

type DecideFn = (eventId: string, decision: AuditDecision, actor: ApprovalActor) => Promise<AuditEntry>;
type OnResolvedFn = (eventId: string, entry: AuditEntry) => void;

const ACTOR: ApprovalActor = { actorId: 'coordinator', actorRole: 'coordinator', actorDisplayName: 'DPV Demo' };

function makeEvent(overrides: Partial<DisruptionEvent> = {}): DisruptionEvent {
  return {
    id: 'disruption-test-1',
    status: 'PENDING_APPROVAL',
    blastRadius: 12,
    areaLabel: 'Phong mo',
    triggeredAt: '2026-07-18T01:02:00.000Z',
    options: [{ id: 'opt-1', label: 'Doi phong', description: 'It anh huong nhat' }],
    aiReason: 'Ly do AI de xuat cho tinh huong nay',
    ...overrides,
  };
}

function makeAuditEntry(overrides: Partial<AuditEntry> = {}): AuditEntry {
  return {
    id: 'audit-test-1',
    actorId: ACTOR.actorId,
    actorRole: ACTOR.actorRole,
    actorDisplayName: ACTOR.actorDisplayName,
    decision: 'APPROVED',
    targetEventId: 'disruption-test-1',
    timestamp: '2026-07-18T01:03:00.000Z',
    aiRationale: 'Ly do AI de xuat cho tinh huong nay',
    ...overrides,
  };
}

function renderPane(props: {
  proposals: DisruptionEvent[];
  decide: DecideFn;
  onResolved?: OnResolvedFn;
}) {
  const onResolved = props.onResolved ?? vi.fn<OnResolvedFn>();
  render(
    <I18nProvider>
      <ApprovalQueuePane proposals={props.proposals} actor={ACTOR} decide={props.decide} onResolved={onResolved} />
    </I18nProvider>,
  );
  return { onResolved };
}

describe('ApprovalQueuePane (BR-22 approve/reject is one-tap and audited)', () => {
  it('shows the calm empty message when there are no proposals (spec 10 SCR-06 "Empty")', () => {
    renderPane({ proposals: [], decide: vi.fn<DecideFn>() });
    expect(screen.getByText('Hiện không có đề xuất re-plan nào chờ duyệt.')).toBeInTheDocument();
  });

  it('renders blast radius, options, and an AIChip-labelled reason for a PENDING_APPROVAL proposal', () => {
    const event = makeEvent();
    renderPane({ proposals: [event], decide: vi.fn<DecideFn>() });

    const row = screen.getByTestId(`proposal-row-${event.id}`);
    expect(within(row).getByText('12')).toBeInTheDocument();
    expect(within(row).getByText('Doi phong', { exact: false })).toBeInTheDocument();
    expect(within(row).getByTestId('ai-chip')).toBeInTheDocument();
    expect(screen.getByTestId(`proposal-reason-${event.id}`)).toHaveTextContent(event.aiReason);
  });

  it('renders triggeredAt in Vietnam local time (UTC+7), not UTC (VN hospital console)', () => {
    // 2026-07-18T01:02:00.000Z UTC is 08:02 in Asia/Ho_Chi_Minh (UTC+7).
    const event = makeEvent({ triggeredAt: '2026-07-18T01:02:00.000Z' });
    renderPane({ proposals: [event], decide: vi.fn<DecideFn>() });

    const row = screen.getByTestId(`proposal-row-${event.id}`);
    const time = within(row).getByText('08:02');
    expect(time.tagName).toBe('TIME');
    expect(time).toHaveClass('tabular-nums');
  });

  it('approve is a single tap: calls decide, then reports the resolution (dequeue) with the audit entry', async () => {
    const user = userEvent.setup();
    const event = makeEvent();
    const entry = makeAuditEntry({ decision: 'APPROVED' });
    const decide = vi.fn<DecideFn>().mockResolvedValue(entry);
    const { onResolved } = renderPane({ proposals: [event], decide });

    await user.click(screen.getByRole('button', { name: 'Duyệt' }));

    await waitFor(() => expect(decide).toHaveBeenCalledWith(event.id, 'APPROVED', ACTOR));
    await waitFor(() => expect(onResolved).toHaveBeenCalledWith(event.id, entry));
  });

  it('reject shows a confirmation step before calling decide', async () => {
    const user = userEvent.setup();
    const event = makeEvent();
    const decide = vi.fn<DecideFn>().mockResolvedValue(makeAuditEntry({ decision: 'REJECTED' }));
    renderPane({ proposals: [event], decide });

    await user.click(screen.getByRole('button', { name: 'Từ chối' }));
    expect(decide).not.toHaveBeenCalled();
    expect(screen.getByText('Từ chối đề xuất ảnh hưởng lớn này?')).toBeInTheDocument();
  });

  it('confirming the reject calls decide and reports the resolution (dequeue) with the audit entry', async () => {
    const user = userEvent.setup();
    const event = makeEvent();
    const entry = makeAuditEntry({ decision: 'REJECTED' });
    const decide = vi.fn<DecideFn>().mockResolvedValue(entry);
    const { onResolved } = renderPane({ proposals: [event], decide });

    await user.click(screen.getByRole('button', { name: 'Từ chối' }));
    await user.click(screen.getByRole('button', { name: 'Xác nhận từ chối' }));

    await waitFor(() => expect(decide).toHaveBeenCalledWith(event.id, 'REJECTED', ACTOR));
    await waitFor(() => expect(onResolved).toHaveBeenCalledWith(event.id, entry));
  });

  it('cancelling the reject confirmation returns to the normal actions without calling decide', async () => {
    const user = userEvent.setup();
    const event = makeEvent();
    const decide = vi.fn<DecideFn>();
    renderPane({ proposals: [event], decide });

    await user.click(screen.getByRole('button', { name: 'Từ chối' }));
    await user.click(screen.getByRole('button', { name: 'Hủy' }));

    expect(decide).not.toHaveBeenCalled();
    expect(screen.getByRole('button', { name: 'Duyệt' })).toBeInTheDocument();
  });

  it('approve and reject are disabled when the proposal status is not PENDING_APPROVAL', async () => {
    const user = userEvent.setup();
    const event = makeEvent({ status: 'APPROVED' });
    const decide = vi.fn<DecideFn>();
    renderPane({ proposals: [event], decide });

    const approveButton = screen.getByRole('button', { name: 'Duyệt' });
    const rejectButton = screen.getByRole('button', { name: 'Từ chối' });
    expect(approveButton).toBeDisabled();
    expect(rejectButton).toBeDisabled();

    await user.click(approveButton);
    await user.click(rejectButton);
    expect(decide).not.toHaveBeenCalled();
  });

  it('shows an inline retry-able error and keeps the row when decide rejects, without swallowing the failure', async () => {
    const user = userEvent.setup();
    const event = makeEvent();
    const decide = vi.fn<DecideFn>().mockRejectedValue(new Error('network down'));
    const { onResolved } = renderPane({ proposals: [event], decide });

    await user.click(screen.getByRole('button', { name: 'Duyệt' }));

    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Không ghi được quyết định'));
    expect(onResolved).not.toHaveBeenCalled();
    expect(screen.getByTestId(`proposal-row-${event.id}`)).toBeInTheDocument();
  });

  it('does not fabricate an actor: approve/reject stay disabled and decide is never called when actor is null (defensive - SCR-06 sits behind the role guard, so this should never occur in practice)', async () => {
    const user = userEvent.setup();
    const event = makeEvent();
    const decide = vi.fn<DecideFn>();
    render(
      <I18nProvider>
        <ApprovalQueuePane proposals={[event]} actor={null} decide={decide} onResolved={vi.fn<OnResolvedFn>()} />
      </I18nProvider>,
    );

    const approveButton = screen.getByRole('button', { name: 'Duyệt' });
    const rejectButton = screen.getByRole('button', { name: 'Từ chối' });
    expect(approveButton).toBeDisabled();
    expect(rejectButton).toBeDisabled();

    await user.click(approveButton);
    await user.click(rejectButton);
    expect(decide).not.toHaveBeenCalled();
  });
});
