import { useEffect, useState } from 'react';
import { useI18n } from '@/i18n';
import { Button, Card, useToast, Toast } from '@/components/primitives';
import { useOptionalStaffSession } from '../auth/StaffAuthContext';
import { listAuditEntries, appendAuditEntry } from '../dashboard/auditStore';
import { clinicalStore } from '../dashboard/clinicalStore';
import { ShieldIcon, ClockIcon, SearchIcon, CheckIcon, XIcon } from '@/components/icons';

export function AdminAuditScreen() {
  const { t } = useI18n();
  const { toast, showToast } = useToast();
  const session = useOptionalStaffSession();
  const isAdmin = session?.role === 'admin';

  const [auditLogs, setAuditLogs] = useState(listAuditEntries());
  const [searchQuery, setSearchQuery] = useState('');
  const [showConfirmModal, setShowConfirmModal] = useState(false);
  const [selectedSeedLevel, setSelectedSeedLevel] = useState<'default' | 'high_load'>('default');

  useEffect(() => {
    setAuditLogs(listAuditEntries());
  }, []);

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(e.target.value);
  };

  const handleOpenSeedConfirm = (level: 'default' | 'high_load') => {
    setSelectedSeedLevel(level);
    setShowConfirmModal(true);
  };

  const handleConfirmSeed = () => {
    clinicalStore.resetSimulator(selectedSeedLevel);
    
    appendAuditEntry({
      actorId: session?.role || 'admin',
      actorRole: session?.role || 'admin',
      actorDisplayName: session?.displayName || 'Quản trị viên hệ thống',
      decision: 'APPROVED',
      targetEventId: 'simulator-reset',
      aiRationale: `Khởi tạo lại cấu hình dữ liệu mô phỏng y khoa cấp độ: ${selectedSeedLevel === 'high_load' ? 'Tải cao' : 'Tiêu chuẩn'}.`
    });

    setAuditLogs(listAuditEntries());
    setShowConfirmModal(false);

    showToast(`Đặt lại bộ mô phỏng thành công (${selectedSeedLevel === 'high_load' ? 'Tải cao' : 'Tiêu chuẩn'})`);
  };

  const filteredLogs = auditLogs.filter((log) => {
    const query = searchQuery.toLowerCase().trim();
    if (!query) return true;

    return (
      log.actorDisplayName.toLowerCase().includes(query) ||
      log.actorRole.toLowerCase().includes(query) ||
      log.decision.toLowerCase().includes(query) ||
      log.targetEventId.toLowerCase().includes(query) ||
      log.aiRationale.toLowerCase().includes(query)
    );
  });

  return (
    <div className="flex flex-col gap-6">
      <h1 className="border-b border-border pb-4 text-2xl font-bold tracking-tight text-foreground">
        {t('console.screen.audit.title')}
      </h1>

      {/* Admin Simulator Control Section */}
      {isAdmin && (
        <Card className="border border-warning/25 bg-warning/5 flex flex-col gap-4 p-5 rounded-2xl">
          <div className="flex items-center gap-2">
            <ShieldIcon className="h-5 w-5 text-warning" />
            <h2 className="text-sm font-bold uppercase tracking-wider text-warning">{t('console.admin.simulatorTitle')}</h2>
          </div>
          <div className="flex flex-wrap gap-3 mt-1">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => handleOpenSeedConfirm('default')}
              className="text-sm font-semibold py-1.5 px-4"
            >
              Khởi tạo mức tiêu chuẩn
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => handleOpenSeedConfirm('high_load')}
              className="text-sm font-semibold py-1.5 px-4"
            >
              Khởi tạo mức tải cao
            </Button>
          </div>
        </Card>
      )}

      {/* Audit Logs list */}
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <h2 className="text-sm font-bold uppercase tracking-wider text-muted-foreground">
            Nhật ký vết kiểm toán
          </h2>
          <label className="relative w-80">
            <SearchIcon className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              placeholder="Tìm kiếm hành động, vai trò, lập luận..."
              value={searchQuery}
              onChange={handleSearchChange}
              className="w-full bg-card border border-border rounded-xl text-sm pl-11 pr-4 py-2 outline-none text-foreground transition-all placeholder:text-muted-foreground hover:border-primary/30 focus:border-primary/50 focus:ring-2 focus:ring-primary/20"
            />
          </label>
        </div>

        <div className="flex flex-col gap-3">
          {filteredLogs.length === 0 ? (
            <Card className="p-8 text-center text-sm text-muted-foreground border-dashed border-2">
              Không tìm thấy nhật ký kiểm toán phù hợp.
            </Card>
          ) : (
            filteredLogs.map((log, idx) => {
              const isApproved = log.decision === 'APPROVED';
              return (
                <Card
                  key={idx}
                  className={`relative overflow-hidden p-4 pl-5 border-border bg-card shadow-sm flex flex-col gap-3 transition-all duration-200 hover:border-primary/40 hover:shadow-md before:absolute before:inset-y-0 before:left-0 before:w-1 ${
                    isApproved ? 'before:bg-success' : 'before:bg-danger'
                  }`}
                >
                  <div className="flex justify-between items-center flex-wrap gap-2 text-sm">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-foreground">{log.actorDisplayName}</span>
                      <span className="text-xs bg-primary/10 text-primary font-bold px-2 py-0.5 rounded-full uppercase">
                        {log.actorRole}
                      </span>
                      <span
                        className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-bold uppercase ${
                          isApproved ? 'bg-success/10 text-success' : 'bg-danger/10 text-danger'
                        }`}
                      >
                        {isApproved ? <CheckIcon className="h-3 w-3" /> : <XIcon className="h-3 w-3" />}
                        {log.decision}
                      </span>
                    </div>
                    <div className="flex items-center gap-1 text-xs text-muted-foreground font-mono tabular-nums">
                      <ClockIcon className="h-3 w-3" />
                      <span>{new Date(log.timestamp).toLocaleTimeString('vi-VN')}</span>
                    </div>
                  </div>

                  <div className="text-sm text-muted-foreground font-mono leading-relaxed bg-muted/40 p-3 rounded-xl border border-border">
                    <div className="text-xs font-bold text-primary mb-1 uppercase tracking-wider">
                      Đối tượng: {log.targetEventId}
                    </div>
                    {log.aiRationale}
                  </div>
                </Card>
              );
            })
          )}
        </div>
      </div>

      {/* Confirmation Modal */}
      {showConfirmModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-sm p-6 flex flex-col gap-4 border border-border shadow-2xl bg-card">
            <h3 className="text-base font-bold text-foreground">Xác nhận khởi tạo lại dữ liệu?</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              Bạn có chắc chắn muốn khởi tạo lại mô phỏng y khoa với cấu hình{' '}
              <b className="text-foreground">
                {selectedSeedLevel === 'high_load' ? 'Tải cao' : 'Tiêu chuẩn'}
              </b>
              ? Hành động này sẽ thay đổi trạng thái các bệnh nhân và lịch hẹn hiện tại.
            </p>
            <div className="flex justify-end gap-3 mt-2">
              <Button variant="secondary" size="sm" onClick={() => setShowConfirmModal(false)} className="text-sm px-4 py-2">
                Hủy
              </Button>
              <Button variant="primary" size="sm" onClick={handleConfirmSeed} className="text-sm px-4 py-2">
                Xác nhận
              </Button>
            </div>
          </Card>
        </div>
      )}
      <Toast message={toast} />
    </div>
  );
}
