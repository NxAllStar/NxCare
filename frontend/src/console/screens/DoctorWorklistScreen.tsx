import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useI18n } from '@/i18n';
import { Avatar, Button, Card, AIChip, StatusChip, useToast, Toast } from '@/components/primitives';
import { clinicalStore, type ClinicalAppointment } from '../dashboard/clinicalStore';
import { useOptionalStaffSession } from '../auth/StaffAuthContext';
import { SendIcon, SparkleIcon } from '@/components/icons';
import { appendAuditEntry } from '../dashboard/auditStore';

interface ChatMessage {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  isStreaming?: boolean;
  proposal?: {
    id: string;
    originalAppointments: ClinicalAppointment[];
    proposedAppointments: ClinicalAppointment[];
  };
}

export function DoctorWorklistScreen() {
  const { t } = useI18n();
  const { toast, showToast } = useToast();
  const navigate = useNavigate();
  const session = useOptionalStaffSession();
  const doctorName = session?.displayName || 'BS. Lê Văn Minh';

  const [appointments, setAppointments] = useState<ClinicalAppointment[]>(clinicalStore.getAppointments());
  const [inputMessage, setInputMessage] = useState('');
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    {
      id: 'welcome',
      sender: 'assistant',
      text: 'Chào bác sĩ, tôi là trợ lý lập lịch y khoa AI. Bác sĩ có thể yêu cầu tôi sắp xếp lại lịch hẹn, dồn lịch hoặc giải phóng khung giờ nghỉ trưa.',
    },
  ]);
  const [isThinking, setIsThinking] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    return clinicalStore.subscribe(() => {
      setAppointments([...clinicalStore.getAppointments()]);
    });
  }, []);

  const doctorAppointments = appointments.filter((a) => a.doctorName === doctorName);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView?.({ behavior: 'smooth' });
  }, [chatMessages, isThinking]);

  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputMessage.trim() || isThinking) return;

    const userMsg = inputMessage.trim();
    const newUserMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: 'user',
      text: userMsg,
    };

    setChatMessages((prev) => [...prev, newUserMessage]);
    setInputMessage('');
    setIsThinking(true);

    setTimeout(() => {
      setIsThinking(false);

      const currentList = [...clinicalStore.getAppointments()];
      const shifted = currentList.map((a) => {
        if (a.doctorName === doctorName) {
          if (a.patientName === 'Trần Minh Quân' && a.timeSlot === '10:15') {
            return { ...a, timeSlot: '08:30' };
          }
          if (a.patientName === 'Nguyễn Thị Lan' && a.timeSlot === '08:00') {
            return { ...a, timeSlot: '09:30' };
          }
        }
        return a;
      });

      const responseText =
        `Đã phân tích tải của phòng khám. Tôi đề xuất hoán đổi lịch khám để tối ưu thời gian chờ:\n` +
        `- Chuyển bệnh nhân **Trần Minh Quân** từ 10:15 lên **08:30** (khung giờ ít đông).\n` +
        `- Dời bệnh nhân **Nguyễn Thị Lan** từ 08:00 sang **09:30**.\n` +
        `Điều này giúp giảm thời gian chờ của Trần Minh Quân đi 20 phút và tối ưu tải ca sáng. Bác sĩ có muốn áp dụng thay đổi này không?`;

      const aiResponse: ChatMessage = {
        id: `ai-${Date.now()}`,
        sender: 'assistant',
        text: responseText,
        proposal: {
          id: `proposal-${Date.now()}`,
          originalAppointments: currentList.filter(a => a.doctorName === doctorName),
          proposedAppointments: shifted.filter(a => a.doctorName === doctorName),
        }
      };

      setChatMessages((prev) => [...prev, aiResponse]);
    }, 1500);
  };

  const handleApplyProposal = (proposal: ChatMessage['proposal']) => {
    if (!proposal) return;

    proposal.proposedAppointments.forEach((p) => {
      const appt = clinicalStore.getAppointments().find((a) => a.id === p.id);
      if (appt) {
        appt.timeSlot = p.timeSlot;
      }
    });

    appendAuditEntry({
      actorId: 'doctor',
      actorRole: 'doctor',
      actorDisplayName: doctorName,
      decision: 'APPROVED',
      targetEventId: proposal.id,
      aiRationale: `Bác sĩ duyệt đề xuất xếp lại lịch từ trợ lý AI để dồn lịch khám ca sáng.`
    });

    clinicalStore.resetSimulator('default');
    setAppointments([...clinicalStore.getAppointments()]);

    showToast('Đã cập nhật lịch khám thành công');

    setChatMessages((prev) =>
      prev.map((msg) => (msg.proposal?.id === proposal.id ? { ...msg, proposal: undefined } : msg))
    );
  };

  const handleRejectProposal = (proposalId: string) => {
    showToast('Đã hủy đề xuất xếp lịch');
    setChatMessages((prev) =>
      prev.map((msg) => (msg.proposal?.id === proposalId ? { ...msg, proposal: undefined } : msg))
    );
  };

  return (
    <div className="flex flex-col gap-6 h-full">
      {/* Required test header */}
      <h1 className="text-2xl font-bold tracking-tight text-foreground">
        {t('console.screen.worklist.title')}
      </h1>

      <div className="flex flex-1 gap-6 overflow-hidden min-h-0">
        {/* Left Side: Today Worklist */}
        <div className="flex-1 flex flex-col gap-4 overflow-y-auto pr-1">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold uppercase tracking-wider text-muted-foreground">
              {t('console.worklist.todaySchedule')}
            </h2>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-primary/10 px-2.5 py-1 text-sm font-bold text-primary">
              <span className="h-1.5 w-1.5 rounded-full bg-primary" />
              {doctorAppointments.length} bệnh nhân
            </span>
          </div>

          <div className="flex flex-col gap-3">
            {doctorAppointments.length === 0 ? (
              <Card className="p-8 text-center text-muted-foreground border-dashed border-2">
                {t('console.worklist.empty')}
              </Card>
            ) : (
              doctorAppointments
                .sort((a, b) => a.timeSlot.localeCompare(b.timeSlot))
                .map((appt) => {
                  let statusChipCode: any = 'PENDING';
                  if (appt.status === 'in_consult') statusChipCode = 'IN_CONSULT';
                  if (appt.status === 'checked_in') statusChipCode = 'CHECKED_IN';
                  if (appt.status === 'done') statusChipCode = 'DONE';

                  return (
                    <Card
                      key={appt.id}
                      className="group p-4 border-border bg-card shadow-sm flex items-center justify-between gap-4 transition-all duration-200 hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-md"
                    >
                      <div className="flex min-w-0 items-center gap-4">
                        <div className="flex w-16 shrink-0 items-center justify-center rounded-xl border border-primary/15 bg-primary/5 px-2 py-3">
                          <span className="text-base font-extrabold text-primary font-mono tabular-nums">
                            {appt.timeSlot}
                          </span>
                        </div>
                        <Avatar name={appt.patientName} className="h-10 w-10 shrink-0" />
                        <div className="min-w-0 truncate text-base font-bold text-foreground">{appt.patientName}</div>
                      </div>

                      <div className="flex shrink-0 items-center gap-3">
                        <StatusChip code={statusChipCode} />
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => navigate('/consult')}
                          className="text-sm font-semibold py-1.5 px-3 rounded-lg border border-border transition-colors group-hover:border-primary/40 group-hover:text-primary"
                        >
                          Khám
                        </Button>
                      </div>
                    </Card>
                  );
                })
            )}
          </div>
        </div>

        {/* Right Side: Chat Assistant */}
        <div className="w-96 shrink-0 flex flex-col gap-4 border-l border-border pl-6 overflow-hidden h-full">
          <div className="flex items-center gap-2.5 border-b border-border pb-3 shrink-0">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <SparkleIcon className="h-[18px] w-[18px]" />
            </span>
            <h2 className="min-w-0 truncate text-sm font-bold uppercase tracking-wider text-foreground">
              {t('console.worklist.rearrangeTitle')}
            </h2>
          </div>

          {/* Chat conversations */}
          <div className="flex-1 overflow-y-auto space-y-4 pr-1">
            {chatMessages.map((msg) => {
              const isAI = msg.sender === 'assistant';
              return (
                <div key={msg.id} className={`flex flex-col ${isAI ? 'items-start' : 'items-end'} gap-1.5`}>
                  <div className={`flex items-center gap-1.5 text-xs text-muted-foreground ${isAI ? 'flex-row' : 'flex-row-reverse'}`}>
                    <span className="font-bold">{isAI ? 'Trợ lý AI' : 'Bác sĩ'}</span>
                    {isAI && <AIChip label="AI" />}
                  </div>
                  <div
                    className={`px-3.5 py-2.5 text-sm leading-relaxed max-w-[90%] whitespace-pre-line ${
                      isAI
                        ? 'rounded-2xl rounded-tl-md bg-card text-foreground border border-border shadow-sm'
                        : 'rounded-2xl rounded-tr-md bg-primary text-primary-foreground shadow-sm shadow-primary/20'
                    }`}
                  >
                    {msg.text}

                    {msg.proposal && (
                      <div className="mt-3 border-t border-border pt-3 flex flex-col gap-2 shrink-0">
                        <div className="text-xs font-bold uppercase tracking-wider text-primary">Đề xuất thay đổi:</div>
                        <div className="flex flex-col gap-1.5 text-sm text-muted-foreground">
                          {msg.proposal.proposedAppointments.map((p, idx) => {
                            const orig = msg.proposal?.originalAppointments.find(o => o.id === p.id);
                            return (
                              <div key={idx} className="flex justify-between items-center bg-card border border-border rounded-lg p-2">
                                <span className="font-bold text-foreground">{p.patientName}</span>
                                <span className="font-mono">
                                  {orig?.timeSlot} → <b className="text-primary font-extrabold">{p.timeSlot}</b>
                                </span>
                              </div>
                            );
                          })}
                        </div>
                        <div className="flex gap-2 mt-1">
                          <Button
                            variant="primary"
                            size="sm"
                            onClick={() => handleApplyProposal(msg.proposal)}
                            className="text-xs py-1 px-3"
                          >
                            Đồng ý
                          </Button>
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => handleRejectProposal(msg.proposal!.id)}
                            className="text-xs py-1 px-3"
                          >
                            Hủy
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
            {isThinking && (
              <div className="flex flex-col items-start gap-1.5">
                <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                  <span className="font-bold">Trợ lý AI</span>
                  <AIChip label="AI" />
                </div>
                <div className="bg-muted text-muted-foreground text-sm rounded-2xl px-3.5 py-2.5 flex items-center gap-1.5 select-none">
                  <span className="w-1.5 h-1.5 rounded-full bg-primary animate-ping"></span>
                  Đang suy luận...
                </div>
              </div>
            )}
            <div ref={chatEndRef} />
          </div>

          {/* Chat input form */}
          <form onSubmit={handleSendMessage} className="flex items-center gap-2 border-t border-border pt-3 shrink-0">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Nhập yêu cầu sắp xếp..."
              disabled={isThinking}
              className="flex-1 bg-muted/60 border border-border rounded-xl text-sm px-3.5 py-2.5 outline-none text-foreground transition-all placeholder:text-muted-foreground hover:bg-muted focus:border-primary/50 focus:bg-card focus:ring-2 focus:ring-primary/20 disabled:opacity-60"
            />
            <Button
              type="submit"
              variant="primary"
              size="sm"
              disabled={isThinking || !inputMessage.trim()}
              className="p-2.5 h-9 rounded-xl flex items-center justify-center shrink-0"
            >
              <SendIcon className="h-4 w-4" />
            </Button>
          </form>
        </div>
      </div>
      <Toast message={toast} />
    </div>
  );
}
