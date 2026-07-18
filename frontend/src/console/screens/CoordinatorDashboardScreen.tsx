import { useCallback, useEffect, useState } from 'react';
import { AIChip, Card, ScreenState, type ViewState } from '@/components/primitives';
import { ActivityIcon, ClockIcon, GridIcon, ShieldIcon, UsersIcon } from '@/components/icons';
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
        if (!cancelled) setViewState('error');
      });

    return () => {
      cancelled = true;
    };
  }, [loadData]);

  const handleResolved = useCallback((eventId: string) => {
    setProposals((current) => current.filter((event) => event.id !== eventId));
  }, []);

  const actor: ApprovalActor | null = session
    ? { actorId: session.role, actorRole: session.role, actorDisplayName: session.displayName }
    : null;

  const kpis = [
    { label: 'Chờ trung bình', value: '32', unit: 'phút', icon: ClockIcon, iconClass: 'bg-primary/10 text-primary' },
    { label: 'Tắc nghẽn', value: 'Trung bình', unit: '', icon: ActivityIcon, iconClass: 'bg-warning/10 text-warning' },
    { label: 'Công suất', value: '78', unit: '%', icon: GridIcon, iconClass: 'bg-primary/10 text-primary' },
    { label: 'Đang xử lý', value: '34', unit: 'ca', icon: UsersIcon, iconClass: 'bg-primary/10 text-primary' },
    {
      label: 'Chờ duyệt',
      value: String(proposals.length),
      unit: 'đề xuất',
      icon: ShieldIcon,
      iconClass: proposals.length > 0 ? 'bg-danger/10 text-danger' : 'bg-success/10 text-success',
    },
  ];

  // Model-produced forecast (FR-07); bar colour follows the sequential load
  // heatmap scale from the design tokens (green -> amber -> red).
  const forecast = [
    { hour: '10h', load: 40 },
    { hour: '11h', load: 55 },
    { hour: '12h', load: 70 },
    { hour: '13h', load: 50 },
    { hour: '14h', load: 65 },
    { hour: '15h', load: 85 },
    { hour: '16h', load: 60 },
    { hour: '17h', load: 45 },
  ];
  const peakLoad = Math.max(...forecast.map((f) => f.load));
  const heatClass = (load: number) => {
    if (load < 50) return 'bg-heat-1';
    if (load < 60) return 'bg-heat-2';
    if (load < 70) return 'bg-heat-3';
    if (load < 80) return 'bg-heat-4';
    return 'bg-heat-5';
  };

  return (
    <div className="flex flex-col gap-6">
      <h1 className="text-2xl font-bold tracking-tight text-foreground">
        {t('console.screen.dashboard.title')}
      </h1>

      <ScreenState
        state={viewState}
        loadingLabel={t('console.dashboard.loadingLabel')}
        errorMessage={
          <Card className="w-full border-danger/30 bg-danger/5 text-left p-4" data-testid="dashboard-error-banner">
            <p className="text-sm font-bold text-danger">{t('console.dashboard.error.title')}</p>
            <p className="mt-1 text-sm text-foreground/80">{t('console.dashboard.error.body')}</p>
          </Card>
        }
      >
        <div className="flex flex-col gap-6">
          {/* Top KPI Cards */}
          <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-4">
            {kpis.map((k, idx) => {
              const Icon = k.icon;
              const isTextValue = Number.isNaN(Number(k.value));
              return (
                <Card
                  key={idx}
                  className="group flex flex-col gap-3.5 border-border bg-card p-5 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-md"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                      {k.label}
                    </span>
                    <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-lg transition-transform duration-200 group-hover:scale-105 ${k.iconClass}`}>
                      <Icon className="h-[18px] w-[18px]" />
                    </span>
                  </div>
                  <div className="flex items-baseline gap-1.5">
                    <span
                      className={`font-extrabold tracking-tight text-foreground ${
                        isTextValue ? 'text-[22px]' : 'font-mono text-3xl tabular-nums'
                      }`}
                    >
                      {k.value}
                    </span>
                    {k.unit && <span className="text-sm font-semibold text-muted-foreground">{k.unit}</span>}
                  </div>
                </Card>
              );
            })}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Heatmap Section */}
            <div className="lg:col-span-2 flex flex-col gap-4">
              {heatmap && <HeatmapPane initialGrid={heatmap} />}
            </div>

            {/* Workload Forecast Section */}
            <div className="flex flex-col gap-3">
              <div className="flex items-center gap-2 px-1">
                <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                  Dự báo tải theo giờ
                </span>
                <AIChip label="AI" />
              </div>
              <Card className="flex flex-1 flex-col gap-3 border-border bg-card p-5 shadow-sm">
                <div className="flex h-48 flex-1 items-end justify-between gap-2 border-b border-border pb-1">
                  {forecast.map((f, idx) => {
                    const isPeak = f.load === peakLoad;
                    return (
                      <div key={idx} className="group flex h-full flex-1 flex-col items-center justify-end gap-1">
                        <span
                          className={`font-mono text-xs tabular-nums transition-opacity ${
                            isPeak ? 'font-bold text-danger' : 'text-muted-foreground opacity-0 group-hover:opacity-100'
                          }`}
                        >
                          {f.load}%
                        </span>
                        <div
                          style={{ height: `${f.load}%` }}
                          className={`w-full max-w-8 rounded-t-md transition-all duration-300 group-hover:opacity-100 ${heatClass(f.load)} ${
                            isPeak ? 'opacity-100 ring-2 ring-danger/30' : 'opacity-80'
                          }`}
                        />
                      </div>
                    );
                  })}
                </div>
                <div className="flex justify-between gap-2">
                  {forecast.map((f, idx) => (
                    <span
                      key={idx}
                      className={`flex-1 text-center text-xs font-mono select-none ${
                        f.load === peakLoad ? 'font-bold text-foreground' : 'text-muted-foreground'
                      }`}
                    >
                      {f.hour}
                    </span>
                  ))}
                </div>
              </Card>
            </div>
          </div>

          {/* Proposals queue & reasoning stream */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <ApprovalQueuePane proposals={proposals} actor={actor} onResolved={handleResolved} />
            </div>
            <div>
              <ReasoningStreamPane transcript={reasoningTranscript} />
            </div>
          </div>
        </div>
      </ScreenState>
    </div>
  );
}
