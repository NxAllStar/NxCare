import { useEffect, useState } from 'react';
import { useI18n } from '@/i18n';
import { Avatar, Button, Card, StatusChip, PatientCodeQr, useToast, Toast } from '@/components/primitives';
import { clinicalStore, type ClinicalPatient } from '../dashboard/clinicalStore';
import { CheckIcon, PlusIcon, XIcon, QrIcon } from '@/components/icons';

const SERVICE_CATALOG = [
  'Xét nghiệm máu',
  'X-quang ngực',
  'CT ngực',
  'Siêu âm bụng',
  'Chụp X-quang bụng',
  'Nội soi dạ dày'
];

export function ConsultOrdersScreen() {
  const { t } = useI18n();

  const [patients, setPatients] = useState<ClinicalPatient[]>(clinicalStore.getPatients());
  const [selectedPatientId, setSelectedPatientId] = useState<string | null>(null);

  const [diagnosisInput, setDiagnosisInput] = useState('');
  const [orderedServices, setOrderedServices] = useState<string[]>([]);
  const [selectedService, setSelectedService] = useState('');

  const [showScanSimulator, setShowScanSimulator] = useState(false);
  const [scannedCode, setScannedCode] = useState('');
  const [localSigned, setLocalSigned] = useState(false);
  const { toast, showToast } = useToast();

  useEffect(() => {
    return clinicalStore.subscribe(() => {
      setPatients([...clinicalStore.getPatients()]);
    });
  }, []);

  const selectedPatient = patients.find((p) => p.id === selectedPatientId);

  useEffect(() => {
    if (selectedPatient) {
      setDiagnosisInput(selectedPatient.diagnoses.join(', ') || '');
      setOrderedServices(selectedPatient.orders || []);
      setLocalSigned(selectedPatient.status === 'completed');

      if (selectedPatient.status === 'waiting_consult') {
        clinicalStore.startConsult(selectedPatient.id);
      }
    } else {
      setDiagnosisInput('');
      setOrderedServices([]);
      setLocalSigned(false);
    }
  }, [selectedPatientId]);

  const handleAddService = () => {
    if (selectedService && !orderedServices.includes(selectedService)) {
      setOrderedServices([...orderedServices, selectedService]);
      setSelectedService('');
    }
  };

  const handleRemoveService = (service: string) => {
    setOrderedServices(orderedServices.filter((s) => s !== service));
  };

  const handleSignOrders = () => {
    if (!selectedPatientId) return;
    if (!diagnosisInput.trim()) {
      showToast('Chẩn đoán lâm sàng không được để trống');
      return;
    }

    const diagnoses = diagnosisInput.split(',').map((d) => d.trim()).filter(Boolean);
    clinicalStore.signAndFinaliseOrders(selectedPatientId, diagnoses, orderedServices);
    setLocalSigned(true);

    showToast(`Đã ký và chốt chỉ định cho ${selectedPatient?.name}`);
  };

  const handleSimulateScan = (e: React.FormEvent) => {
    e.preventDefault();
    if (!scannedCode.trim()) return;

    const patient = patients.find((p) => p.patientCode.toLowerCase() === scannedCode.trim().toLowerCase());
    if (patient) {
      clinicalStore.checkInPatient(patient.patientCode);
      showToast(`Đã tiếp nhận thành công cho ${patient.name}`);
      setSelectedPatientId(patient.id);
    } else {
      showToast('Mã bệnh nhân không tồn tại trên hệ thống');
    }

    setScannedCode('');
    setShowScanSimulator(false);
  };

  const carePlanTasks = [
    { label: 'Lấy máu — Phòng xét nghiệm 2', owner: 'KTV Bình', duration: '15 phút', done: true, color: 'bg-success' },
    { label: 'Siêu âm bụng — Phòng Siêu âm 1', owner: 'KTV Hạnh', duration: '20 phút', done: false, color: 'bg-warning' },
    { label: 'X-quang ngực — Phòng X-quang 1 (đổi từ máy #2)', owner: 'KTV Long', duration: '10 phút', done: false, color: 'bg-primary' },
    { label: 'Quay lại bác sĩ đọc kết quả — P.302', owner: 'BS. Lê Văn Minh', duration: '—', done: false, color: 'bg-muted-foreground/30' },
  ];

  return (
    <div className="flex h-full flex-col gap-5 rounded-2xl border border-border bg-card p-6 shadow-sm">
      {/* Required test header */}
      <h1 className="flex items-center gap-2.5 text-2xl font-bold tracking-tight text-foreground">
        {t('console.screen.consult.title')}
        <span aria-hidden="true" className="mt-1 h-2 w-2 rounded-full bg-primary" />
      </h1>

      <div className="flex flex-1 gap-6 overflow-hidden min-h-0">
        {/* Left Side: Waiting Patient Queue */}
        <div className="w-96 shrink-0 flex flex-col gap-4 overflow-y-auto pr-1">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold uppercase tracking-wider text-primary">
              {t('console.consult.queue')}
            </h2>
            <Button size="sm" variant="secondary" onClick={() => setShowScanSimulator(true)} className="text-sm">
              <QrIcon className="mr-1.5 h-3.5 w-3.5" />
              Tiếp nhận
            </Button>
          </div>

          {/* QR Scan Popover */}
          {showScanSimulator && (
            <Card className="border border-primary/20 bg-primary/5 p-3.5 flex flex-col gap-2 shrink-0">
              <form onSubmit={handleSimulateScan} className="flex flex-col gap-2">
                <label className="text-sm font-semibold text-primary">Nhập mã bệnh nhân cần tiếp nhận:</label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="BN-941207..."
                    value={scannedCode}
                    onChange={(e) => setScannedCode(e.target.value)}
                    className="flex-1 rounded-lg border border-input bg-card px-2.5 py-1 text-sm outline-none focus:ring-1 focus:ring-primary text-foreground"
                    autoFocus
                  />
                  <Button size="sm" type="submit">Quét</Button>
                  <Button size="sm" variant="secondary" onClick={() => setShowScanSimulator(false)}>Hủy</Button>
                </div>
                <div className="text-xs text-muted-foreground font-mono">Ví dụ: BN-941207, BN-921105</div>
              </form>
            </Card>
          )}

          {/* Patient Queue List */}
          <div className="flex flex-col gap-2">
            {patients.length === 0 ? (
              <div className="text-center text-sm text-muted-foreground py-10">
                {t('console.consult.emptyQueue')}
              </div>
            ) : (
              patients.map((p, idx) => {
                const isActive = p.id === selectedPatientId;
                let statusChipCode: any = 'PENDING';
                if (p.status === 'in_consult') statusChipCode = 'IN_CONSULT';
                if (p.status === 'completed') statusChipCode = 'DONE';

                const avatarTint = [
                  'bg-primary/15 text-primary',
                  'bg-success/15 text-success',
                  'bg-info/15 text-info',
                ][idx % 3];

                return (
                  <button
                    key={p.id}
                    onClick={() => setSelectedPatientId(p.id)}
                    className={`group flex flex-col gap-2.5 rounded-2xl border bg-card p-4 text-left shadow-sm transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary/40 ${
                      isActive
                        ? 'border-primary/50 ring-2 ring-primary/25'
                        : 'border-border hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-md'
                    }`}
                  >
                    <div className="flex w-full items-start justify-between gap-3">
                      <div className="flex min-w-0 items-center gap-3">
                        <Avatar name={p.name} className={`h-11 w-11 shrink-0 ${avatarTint}`} />
                        <div className="min-w-0 leading-tight">
                          <div className="truncate text-base font-bold text-foreground">{p.name}</div>
                          <div className="mt-0.5 truncate font-mono text-sm text-muted-foreground">{p.patientCode}</div>
                        </div>
                      </div>
                      <StatusChip code={statusChipCode} stacked className="shrink-0" />
                    </div>
                    <div className="w-full text-right text-sm text-muted-foreground">{p.suspectedSpecialty}</div>
                  </button>
                );
              })
            )}
          </div>
        </div>

        {/* Right Side: Selected Patient Workspace */}
        <div className="flex-1 overflow-y-auto pr-1">
          {selectedPatient ? (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 h-full">
              {/* Column 1: Patient Summary Info */}
              <div className="flex flex-col gap-5">
                <Card className="p-4 border-border bg-card shadow-sm flex flex-col gap-4">
                  <div className="flex justify-between items-start">
                    <div>
                      <h3 className="text-base font-bold text-foreground">{selectedPatient.name}</h3>
                      <span className="text-sm font-mono text-muted-foreground">{selectedPatient.patientCode} · 68 tuổi · Nữ</span>
                    </div>
                    <PatientCodeQr code={selectedPatient.patientCode} className="shrink-0 scale-90" />
                  </div>
                  <div className="bg-primary/5 border border-primary/20 rounded-xl p-3 text-sm leading-relaxed text-foreground">
                    <div className="font-bold text-primary mb-1">Phân loại tiếp nhận tham khảo:</div>
                    <p className="italic">“{selectedPatient.triageText}”</p>
                  </div>
                </Card>

                <div className="flex flex-col gap-3">
                  <div className="text-xs font-bold uppercase tracking-wider text-muted-foreground px-1">
                    Hồ sơ bệnh án
                  </div>
                  <Card className="p-4 border-border bg-card shadow-sm flex flex-col gap-3 text-sm">
                    <div>
                      <div className="text-muted-foreground font-medium">Tiền sử bệnh lý</div>
                      <div className="font-bold text-foreground mt-0.5">Tăng huyết áp (2019), Đái tháo đường type 2</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground font-medium">Dị ứng</div>
                      <div className="font-bold text-danger mt-0.5">Penicillin</div>
                    </div>
                    <div>
                      <div className="text-muted-foreground font-medium">Thuốc đang sử dụng</div>
                      <div className="font-bold text-foreground mt-0.5">Metformin 500mg · Losartan 50mg</div>
                    </div>
                  </Card>
                </div>
              </div>

              {/* Column 2: Diagnosis & Orders Form */}
              <div className="flex flex-col gap-5">
                <div className="flex flex-col gap-2">
                  <label className="text-xs font-bold uppercase tracking-wider text-muted-foreground px-1">
                    Chẩn đoán lâm sàng *
                  </label>
                  <input
                    type="text"
                    placeholder="Nhập chẩn đoán lâm sàng..."
                    value={diagnosisInput}
                    onChange={(e) => setDiagnosisInput(e.target.value)}
                    disabled={selectedPatient.status === 'completed' || localSigned}
                    className="w-full rounded-xl border border-input bg-card px-4 py-2.5 text-sm outline-none focus:border-primary text-foreground disabled:opacity-60"
                  />
                </div>

                <div className="flex flex-col gap-3">
                  <div className="text-xs font-bold uppercase tracking-wider text-muted-foreground px-1">
                    Chỉ định dịch vụ cận lâm sàng
                  </div>
                  <Card className="p-4 border-border bg-card shadow-sm flex flex-col gap-4">
                    {selectedPatient.status !== 'completed' && !localSigned && (
                      <div className="flex gap-2">
                        <select
                          value={selectedService}
                          onChange={(e) => setSelectedService(e.target.value)}
                          className="flex-1 bg-muted border border-border rounded-xl text-sm px-3 py-2 outline-none font-medium text-foreground"
                        >
                          <option value="">Chọn dịch vụ...</option>
                          {SERVICE_CATALOG.map((service) => (
                            <option key={service} value={service} disabled={orderedServices.includes(service)}>
                              {service}
                            </option>
                          ))}
                        </select>
                        <Button variant="secondary" size="sm" onClick={handleAddService} className="text-sm">
                          <PlusIcon className="mr-1 h-3.5 w-3.5" />
                          Thêm
                        </Button>
                      </div>
                    )}

                    <div className="flex flex-col gap-1.5">
                      {orderedServices.length === 0 ? (
                        <div className="rounded-xl border border-dashed border-border py-6 text-center text-sm text-muted-foreground">
                          Chưa có chỉ định cận lâm sàng nào được chọn.
                        </div>
                      ) : (
                        orderedServices.map((service) => (
                          <div
                            key={service}
                            className="flex items-center justify-between rounded-xl border border-border bg-muted/20 px-3.5 py-2 text-sm text-foreground font-semibold"
                          >
                            <span>{service}</span>
                            {selectedPatient.status !== 'completed' && !localSigned && (
                              <button
                                onClick={() => handleRemoveService(service)}
                                className="text-muted-foreground hover:text-danger p-0.5 transition-colors"
                              >
                                <XIcon className="h-3.5 w-3.5" />
                              </button>
                            )}
                          </div>
                        ))
                      )}
                    </div>
                  </Card>
                </div>

                {selectedPatient.status !== 'completed' && !localSigned && (
                  <Button
                    variant="primary"
                    size="lg"
                    onClick={handleSignOrders}
                    className="w-full text-sm font-bold py-2.5 shadow-md shadow-primary/20 transition-all hover:shadow-lg hover:shadow-primary/25"
                  >
                    <CheckIcon className="mr-2 h-4 w-4" />
                    Ký và chốt chỉ định y khoa
                  </Button>
                )}
              </div>

              {/* Column 3: Care Plan Timeline */}
              <div className="flex flex-col gap-3">
                <div className="text-xs font-bold uppercase tracking-wider text-muted-foreground px-1">
                  Lộ trình chăm sóc của bệnh nhân
                </div>
                {!localSigned ? (
                  <Card className="p-6 border-dashed border-2 border-border text-center text-sm text-muted-foreground flex items-center justify-center min-h-48">
                    Chưa có lộ trình — ký chỉ định để kích hoạt Trợ lý kế hoạch tự sinh chuỗi.
                  </Card>
                ) : (
                  <div className="flex flex-col gap-4">
                    <div className="flex flex-col gap-2.5 bg-card border border-border rounded-2xl shadow-sm p-4">
                      {carePlanTasks.map((t, idx) => (
                        <div key={idx} className="flex gap-3 text-sm items-start">
                          <div className="flex flex-col items-center flex-shrink-0 mt-1">
                            <span className={`w-2.5 h-2.5 rounded-full ${t.color}`}></span>
                            {idx < carePlanTasks.length - 1 && (
                              <span className="w-0.5 bg-border h-10 my-0.5"></span>
                            )}
                          </div>
                          <div>
                            <div className="font-bold text-foreground">{t.label}</div>
                            <div className="text-xs text-muted-foreground mt-0.5">
                              {t.owner} · {t.duration}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>

                    <div className="bg-primary/5 border border-primary/20 rounded-2xl p-4 text-sm leading-relaxed text-foreground">
                      <div className="font-bold text-primary mb-1">Vì sao thứ tự này?</div>
                      <p className="font-mono text-sm text-muted-foreground leading-normal">
                        Constraint checker: siêu âm cần nhịn ăn nhẹ — giữ trước lấy máu. Lấy máu → 30 phút chờ kết quả song song với di chuyển sang phòng siêu âm, tối ưu tổng thời gian chờ.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="flex h-full flex-col items-center justify-center rounded-2xl border border-border bg-card p-8 text-center">
              <svg viewBox="0 0 220 170" className="mb-6 h-44 w-56" aria-hidden="true" fill="none">
                <ellipse cx="112" cy="92" rx="86" ry="66" className="fill-primary/10" />
                <path d="M40 104c-12-15-10-33 2-44 5 13 3 30-2 44Z" className="fill-primary/30" />
                <path d="M186 100c11-13 10-29 0-39-5 12-3 27 0 39Z" className="fill-primary/30" />
                <rect x="72" y="28" width="78" height="106" rx="11" className="fill-card stroke-primary/40" strokeWidth="2.5" />
                <rect x="96" y="20" width="30" height="15" rx="5.5" className="fill-primary/70" />
                <circle cx="90" cy="56" r="6" className="fill-primary/50" />
                <rect x="102" y="52" width="34" height="7" rx="3.5" className="fill-primary/45" />
                <rect x="84" y="72" width="52" height="6" rx="3" className="fill-primary/25" />
                <rect x="84" y="86" width="44" height="6" rx="3" className="fill-primary/25" />
                <rect x="84" y="100" width="52" height="6" rx="3" className="fill-primary/15" />
                <circle cx="152" cy="120" r="17" className="fill-primary" />
                <path d="M152 113v14M145 120h14" className="stroke-white" strokeWidth="3" strokeLinecap="round" />
              </svg>
              <h3 className="text-lg font-bold text-foreground">Không có bệnh nhân được chọn</h3>
              <p className="text-sm text-muted-foreground mt-1.5 max-w-sm leading-relaxed">
                Chọn bệnh nhân từ hàng đợi bên trái để bắt đầu khám.
              </p>
            </div>
          )}
        </div>
      </div>
      <Toast message={toast} />
    </div>
  );
}
