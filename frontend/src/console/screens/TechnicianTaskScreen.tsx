import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useI18n } from '@/i18n';
import { Button, Card, StatusChip, useToast, Toast } from '@/components/primitives';
import { clinicalStore, type ClinicalTask } from '../dashboard/clinicalStore';
import {
  QrIcon,
  CheckIcon,
  GridIcon,
  SortIcon,
  MapPinIcon,
  AlertIcon,
  ClipboardListIcon,
  ClockIcon,
  UserIcon,
  CreditCardIcon,
  ChevronDownIcon,
} from '@/components/icons';

type ServiceFilter = 'ALL' | 'BLOOD' | 'IMAGING';

export function TechnicianTaskScreen() {
  const { t } = useI18n();
  const navigate = useNavigate();

  const [tasks, setTasks] = useState<ClinicalTask[]>(clinicalStore.getTasks());
  const [activeFilter, setActiveFilter] = useState<ServiceFilter>('ALL');
  const { toast, showToast } = useToast();

  useEffect(() => {
    return clinicalStore.subscribe(() => {
      setTasks([...clinicalStore.getTasks()]);
    });
  }, []);

  const handleStartTask = (task: ClinicalTask) => {
    clinicalStore.startTask(task.id);
    showToast(`Bắt đầu thực hiện ${task.serviceName} cho ${task.patientName}`);
  };

  const handleCompleteTask = (task: ClinicalTask) => {
    clinicalStore.completeTask(task.id);
    showToast(`Đã hoàn tất ${task.serviceName} cho ${task.patientName}`);
  };

  const handleUnlockTask = (task: ClinicalTask) => {
    clinicalStore.unlockTask(task.id);
    showToast(`Đã mở khóa dịch vụ ${task.serviceName}`);
  };

  const handleReportEquipmentIssue = () => {
    showToast('Máy X-quang #2 báo lỗi ngoại tuyến. Đang chuyển dữ liệu lập lịch lại.');
    // Redirect coordinator dashboard to see re-plans
    setTimeout(() => {
      navigate('/dashboard');
    }, 1500);
  };

  const isImaging = (serviceName: string) => {
    return serviceName.toLowerCase().includes('x-quang') ||
           serviceName.toLowerCase().includes('siêu âm') ||
           serviceName.toLowerCase().includes('nội soi') ||
           serviceName.toLowerCase().includes('ct');
  };

  const filteredTasks = tasks.filter((task) => {
    if (activeFilter === 'BLOOD') {
      return task.serviceName.toLowerCase().includes('máu') || task.serviceName.toLowerCase().includes('nghiệm');
    }
    if (activeFilter === 'IMAGING') {
      return isImaging(task.serviceName);
    }
    return true;
  });

  return (
    <div className="flex flex-col gap-6">
      {/* Top Section */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h1 className="flex items-center gap-3 text-2xl font-bold tracking-tight text-foreground">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <ClipboardListIcon className="h-5 w-5" />
          </span>
          {t('console.screen.tasks.title')}
        </h1>

        <div className="flex flex-wrap items-center gap-2.5">
          <button
            type="button"
            onClick={handleReportEquipmentIssue}
            className="flex items-center gap-1.5 rounded-xl border border-danger/30 bg-danger/5 px-4 py-2.5 text-sm font-semibold text-danger transition-colors hover:bg-danger/10"
          >
            <AlertIcon className="h-4 w-4" />
            Báo hỏng máy X-quang #2
          </button>

          {/* Filters (labels follow design/ki-thuat-vien-sceen.png) */}
          <button
            type="button"
            onClick={() => setActiveFilter('ALL')}
            className={`flex items-center gap-1.5 rounded-xl border px-4 py-2.5 text-sm font-semibold transition-colors ${
              activeFilter === 'ALL'
                ? 'border-primary/30 bg-primary/10 text-primary'
                : 'border-border bg-card text-foreground hover:bg-muted'
            }`}
          >
            Tất cả ({tasks.length})
            <ChevronDownIcon className="h-3.5 w-3.5" />
          </button>
          <button
            type="button"
            onClick={() => setActiveFilter('BLOOD')}
            className={`flex items-center gap-1.5 rounded-xl border px-4 py-2.5 text-sm font-semibold transition-colors ${
              activeFilter === 'BLOOD'
                ? 'border-primary/30 bg-primary/10 text-primary'
                : 'border-border bg-card text-foreground hover:bg-muted'
            }`}
          >
            <SortIcon className="h-4 w-4" />
            Xét nghiệm mới nhất
            <ChevronDownIcon className="h-3.5 w-3.5" />
          </button>
          <button
            type="button"
            onClick={() => setActiveFilter('IMAGING')}
            className={`flex items-center gap-1.5 rounded-xl border px-4 py-2.5 text-sm font-semibold transition-colors ${
              activeFilter === 'IMAGING'
                ? 'border-primary/30 bg-primary/10 text-primary'
                : 'border-border bg-card text-foreground hover:bg-muted'
            }`}
          >
            <GridIcon className="h-4 w-4" />
            Hình ảnh
          </button>
        </div>
      </div>

      {/* Task List */}
      <div className="flex flex-col gap-4">
        {filteredTasks.length === 0 ? (
          <Card className="p-12 text-center text-sm text-muted-foreground border-dashed border-2">
            {t('console.tasks.empty')}
          </Card>
        ) : (
          filteredTasks.map((task) => {
            let statusChipCode: any = task.status;
            if (task.status === 'LOCKED') statusChipCode = 'LOCKED';

            let roomName = 'Phòng xét nghiệm 2';
            if (task.serviceName.includes('Siêu âm')) roomName = 'Siêu âm 1';
            if (task.serviceName.includes('X-quang')) roomName = 'X-quang 3';

            let constraint = '—';
            if (task.serviceName.includes('Siêu âm')) constraint = 'Đã lấy máu';
            if (task.serviceName.includes('X-quang') && task.patientName === 'Nguyễn Thị Lan') constraint = 'Chuyển từ máy #2 hỏng';

            const isRerouted = constraint.includes('máy #2');

            return (
              <Card
                key={task.id}
                className="flex flex-col justify-between gap-4 rounded-2xl border-border bg-card p-5 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-md md:flex-row md:items-center"
              >
                <div className="flex min-w-0 items-center gap-4">
                  <div className="flex w-[68px] shrink-0 flex-col items-center justify-center gap-1 rounded-xl bg-primary/10 py-3">
                    <span className="font-mono text-base font-extrabold tabular-nums text-primary">
                      {task.timeSlot}
                    </span>
                    <ClockIcon className="h-3.5 w-3.5 text-primary/60" />
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-1.5 truncate text-base font-bold text-foreground">
                      <UserIcon className="h-4 w-4 shrink-0 text-primary" />
                      {task.patientName}{' '}
                      <span className="text-sm font-mono font-medium text-muted-foreground">({task.patientCode})</span>
                    </div>
                    <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
                      <span className="inline-flex items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-xs font-semibold text-foreground">
                        <MapPinIcon className="h-3 w-3 text-muted-foreground" />
                        {roomName}
                      </span>
                      {constraint !== '—' && (
                        <span
                          className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold ${
                            isRerouted ? 'bg-warning/10 text-warning' : 'bg-success/10 text-success'
                          }`}
                        >
                          {isRerouted ? <AlertIcon className="h-3 w-3" /> : <CheckIcon className="h-3 w-3" />}
                          {constraint}
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="flex flex-wrap items-center justify-between gap-x-5 gap-y-3 md:justify-end">
                  <div className="text-[15px] font-bold text-primary">{task.serviceName}</div>

                  {task.status === 'LOCKED' ? (
                    <div className="inline-flex items-center gap-1.5 rounded-full border border-success/30 bg-success/10 px-3 py-1.5 text-sm font-medium text-success">
                      <span className="h-1.5 w-1.5 rounded-full bg-success"></span>
                      {t('console.tasks.lockedText')}
                    </div>
                  ) : (
                    <StatusChip code={statusChipCode} />
                  )}

                  {task.status === 'LOCKED' && (
                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => handleUnlockTask(task)}
                      className="rounded-xl"
                    >
                      <CreditCardIcon className="h-4 w-4" />
                      Thanh toán (demo)
                    </Button>
                  )}
                  {task.status === 'PENDING' && (
                    <Button size="sm" onClick={() => handleStartTask(task)} className="rounded-xl">
                      <QrIcon className="h-4 w-4" />
                      {t('console.tasks.scanToStart')}
                    </Button>
                  )}
                  {task.status === 'IN_PROGRESS' && (
                    <Button size="sm" onClick={() => handleCompleteTask(task)} className="rounded-xl">
                      <CheckIcon className="h-4 w-4" />
                      {t('console.tasks.complete')}
                    </Button>
                  )}
                  {task.status === 'DONE' && (
                    <span className="flex items-center gap-1 text-sm font-semibold text-success">
                      <CheckIcon className="h-4 w-4" />
                      Đã xong
                    </span>
                  )}
                </div>
              </Card>
            );
          })
        )}
      </div>
      <Toast message={toast} />
    </div>
  );
}
