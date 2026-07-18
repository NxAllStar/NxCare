/**
 * CoordinatorDashboardScreen (SCR-06, TASK-027) - proves the acceptance
 * criteria: loading -> success renders the heatmap + approval queue +
 * reasoning stream; a mock LLM failure holds the plan and shows the
 * "auto-coordination paused" banner instead of applying anything; and
 * coordinator/admin reach the real dashboard (not the old stub) at the
 * SCR-06 route.
 */
import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';
import { I18nProvider } from '@/i18n';
import { StaffAuthProvider, STAFF_SESSION_STORAGE_KEY } from '../auth/StaffAuthContext';
import { ConsoleApp } from '../ConsoleApp';
import type { StaffRole } from '../access';
import { screenPath } from '../access';
import { listAuditEntries, resetAuditStoreForTest } from '../dashboard/auditStore';
import { loadDashboardData, type DashboardData } from '../dashboard/data';
import { resetProposalsForTest } from '../dashboard/proposals';
import { CoordinatorDashboardScreen } from './CoordinatorDashboardScreen';

function makeDashboardData(overrides: Partial<DashboardData> = {}): DashboardData {
  return {
    heatmap: {
      tickId: 'tick-test',
      generatedAt: '2026-07-18T01:00:00.000Z',
      areas: ['Cap cuu'],
      timeSlots: ['08:00'],
      cells: [
        { id: 'ED:08:00', areaId: 'ED', areaLabel: 'Cap cuu', timeSlot: '08:00', loadLevel: 6, valueLabel: '94%' },
      ],
    },
    proposals: [
      {
        id: 'disruption-test-1',
        status: 'PENDING_APPROVAL',
        blastRadius: 12,
        areaLabel: 'Phong mo',
        triggeredAt: '2026-07-18T01:02:00.000Z',
        options: [{ id: 'opt-1', label: 'Doi phong', description: 'It anh huong nhat' }],
        aiReason: 'Ly do AI',
      },
    ],
    reasoningTranscript: 'mot hai ba bon',
    ...overrides,
  };
}

function renderScreen(loadData: () => Promise<DashboardData>) {
  return render(
    <I18nProvider>
      <StaffAuthProvider>
        <CoordinatorDashboardScreen loadData={loadData} />
      </StaffAuthProvider>
    </I18nProvider>,
  );
}

describe('CoordinatorDashboardScreen (TASK-027 acceptance criteria)', () => {
  it('shows the loading state first', () => {
    renderScreen(() => new Promise(() => {})); // never resolves
    expect(screen.getByTestId('screen-state-loading')).toBeInTheDocument();
  });

  it('on success, renders the heatmap, approval queue, and reasoning stream', async () => {
    renderScreen(() => Promise.resolve(makeDashboardData()));

    expect(await screen.findByTestId('heatmap-pane')).toBeInTheDocument();
    expect(screen.getByTestId('approval-queue-pane')).toBeInTheDocument();
    expect(screen.getByTestId('streaming-text')).toBeInTheDocument();
    expect(screen.getByTestId('proposal-row-disruption-test-1')).toBeInTheDocument();
  });

  it('the heatmap pane renders the grid loaded from the mock-data layer, not an internal default (HeatmapPane consumes data.heatmap as source of truth)', async () => {
    renderScreen(() => Promise.resolve(makeDashboardData()));

    expect(await screen.findByTestId('heatmap-cell-ED:08:00')).toHaveTextContent('94%');
  });

  it('shows the calm heatmap with no proposals when the queue is empty (spec 10 SCR-06 "Empty")', async () => {
    renderScreen(() => Promise.resolve(makeDashboardData({ proposals: [] })));

    expect(await screen.findByTestId('heatmap-pane')).toBeInTheDocument();
    expect(screen.getByText('Hiện không có đề xuất re-plan nào chờ duyệt.')).toBeInTheDocument();
  });

  it('on a mock LLM failure, holds the current plan and shows the "auto-coordination paused" banner instead of applying anything', async () => {
    const loadData = vi.fn().mockRejectedValue(new Error('llm-down'));
    renderScreen(loadData);

    const banner = await screen.findByTestId('dashboard-error-banner');
    expect(banner).toHaveTextContent('Điều phối tự động tạm dừng');
    expect(banner).toHaveTextContent('Lộ trình hiện tại được giữ nguyên');
    // Nothing was applied: no queue, no heatmap, no reasoning stream mounted.
    expect(screen.queryByTestId('approval-queue-pane')).not.toBeInTheDocument();
    expect(screen.queryByTestId('heatmap-pane')).not.toBeInTheDocument();
  });

  it('dequeues a proposal once ApprovalQueuePane reports it resolved, without a full reload', async () => {
    // Uses the real default loader + real mock proposals service end to end
    // (reset first for isolation), so the clicked row's id genuinely matches
    // the service the ApprovalQueuePane calls under the hood. A real staff
    // session is seeded because SCR-06 sits behind the role guard in
    // practice, and approve/reject are disabled without one (audit-actor
    // integrity - see the dedicated tests below).
    resetProposalsForTest();
    resetAuditStoreForTest();
    seedSession('coordinator');
    const user = userEvent.setup();
    renderScreen(loadDashboardData);

    const firstRow = (await screen.findAllByTestId(/^proposal-row-/))[0];
    const rowId = firstRow.getAttribute('data-testid')!.replace('proposal-row-', '');

    await user.click(screen.getAllByRole('button', { name: 'Duyệt' })[0]);

    await waitFor(() => expect(screen.queryByTestId(`proposal-row-${rowId}`)).not.toBeInTheDocument());
  });

  it('derives the audit actor from the real staff session on approve, never a fabricated identity (audit-actor integrity)', async () => {
    resetProposalsForTest();
    resetAuditStoreForTest();
    seedSession('coordinator');
    const user = userEvent.setup();
    renderScreen(loadDashboardData);

    await screen.findAllByTestId(/^proposal-row-/);
    await user.click(screen.getAllByRole('button', { name: 'Duyệt' })[0]);

    await waitFor(() => expect(listAuditEntries()).toHaveLength(1));
    const [entry] = listAuditEntries();
    expect(entry.actorRole).toBe('coordinator');
    expect(entry.actorDisplayName).toBe('Demo staff');
    expect(entry.actorId).not.toBe('unknown');
  });

  it('without a staff session (defensive - the route guard normally prevents this), does not fabricate an audit actor: approve/reject stay disabled', async () => {
    // Deliberately renders CoordinatorDashboardScreen without seeding a
    // session, bypassing the route guard the way a defensive unit test must
    // to exercise the null-session path directly.
    renderScreen(() => Promise.resolve(makeDashboardData()));

    const row = await screen.findByTestId('proposal-row-disruption-test-1');
    expect(within(row).getByRole('button', { name: 'Duyệt' })).toBeDisabled();
    expect(within(row).getByRole('button', { name: 'Từ chối' })).toBeDisabled();
  });
});

function seedSession(role: StaffRole) {
  window.sessionStorage.setItem(
    STAFF_SESSION_STORAGE_KEY,
    JSON.stringify({ role, displayName: 'Demo staff', issuedAt: new Date().toISOString() }),
  );
}

function goToConsoleDashboard() {
  window.history.pushState({}, '', `/console${screenPath('SCR-06')}`);
}

describe('CoordinatorDashboardScreen reachability (TASK-027: coordinator and admin see the real dashboard at SCR-06)', () => {
  it('coordinator reaches the real dashboard (heatmap + approval queue + reasoning stream), not the old stub', async () => {
    seedSession('coordinator');
    goToConsoleDashboard();
    render(<ConsoleApp />);

    expect(await screen.findByTestId('heatmap-pane')).toBeInTheDocument();
    expect(screen.getByTestId('approval-queue-pane')).toBeInTheDocument();
    expect(screen.getByTestId('streaming-text')).toBeInTheDocument();
    expect(screen.queryByText('Màn hình này sẽ được xây dựng ở bước sau')).not.toBeInTheDocument();
  });

  it('admin reaches the real dashboard too (coordinator OR admin)', async () => {
    seedSession('admin');
    goToConsoleDashboard();
    render(<ConsoleApp />);

    expect(await screen.findByTestId('heatmap-pane')).toBeInTheDocument();
    expect(screen.getByTestId('approval-queue-pane')).toBeInTheDocument();
    expect(screen.getByTestId('streaming-text')).toBeInTheDocument();
  });
});
