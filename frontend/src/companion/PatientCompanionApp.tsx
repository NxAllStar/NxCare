/**
 * PatientCompanionApp - faithful 1:1 reproduction of the owner-supplied
 * "Patient Companion App" design, rendered inside an iPhone frame. This
 * orchestrator owns the shared chrome (context/back header, tab bar,
 * assistant FAB, family/notification bottom sheets, chat overlay, toast)
 * and routes to the screen for the current tab/sub-screen. Markup and
 * styling are transcribed from the design's render markup verbatim.
 */
import { IOSDeviceFrame } from './frame';
import { JOURNEY_STEPS, FAMILY, NOTIFICATIONS, PATIENT_NAME, useCompanionState, type CompanionState } from './state';
import { Onboarding } from './screens/Onboarding';
import { HomeScreen } from './screens/HomeScreen';
import { AppointmentsScreen } from './screens/AppointmentsScreen';
import { JourneyScreen } from './screens/JourneyScreen';
import { RecordsScreen } from './screens/RecordsScreen';
import { MoreScreen } from './screens/MoreScreen';

const TEAL = '#2563EB';
const INK = '#12151A';
const MUTED = '#5A626B';
const FAINT = '#9BA3AB';

function isRootScreen(s: CompanionState): boolean {
  return (
    (s.tab === 'home') ||
    (s.tab === 'appointments' && s.apptScreen === 'list') ||
    (s.tab === 'journey' && s.journeyScreen === 'timeline') ||
    (s.tab === 'records' && s.recordsScreen === 'list') ||
    (s.tab === 'more' && s.moreScreen === 'menu')
  );
}

function headerTitle(s: CompanionState): string {
  if (s.tab === 'appointments') {
    return { book: 'Đặt lịch khám', intake: 'Trợ lý đặt lịch', checkin: 'Check-in', prep: 'Chuẩn bị trước khám', list: '' }[s.apptScreen];
  }
  if (s.tab === 'journey') return 'Chỉ đường';
  if (s.tab === 'records') {
    const rec = s.selectedResult;
    const recName = { 1: 'Công thức máu', 2: 'X-quang bụng', 3: 'Siêu âm bụng' }[rec] ?? 'Kết quả';
    return { list: '', results: 'Kết quả xét nghiệm', resultDetail: recName, medications: 'Đơn thuốc & nhắc uống', recovery: 'Theo dõi hồi phục', visitSummary: 'Tóm tắt lần khám' }[s.recordsScreen];
  }
  if (s.tab === 'more') {
    return { menu: '', billing: 'Viện phí & BHYT', family: 'Gia đình', settings: 'Cài đặt' }[s.moreScreen];
  }
  return '';
}

export function PatientCompanionApp({ startAtHome = false }: { startAtHome?: boolean }) {
  const { s, a } = useCompanionState(startAtHome);

  if (s.appStage === 'onboarding') {
    return (
      <IOSDeviceFrame>
        <div style={{ height: '100%', display: 'flex', flexDirection: 'column', position: 'relative', overflow: 'hidden', background: '#FFFFFF' }}>
          <Onboarding s={s} a={a} />
        </div>
      </IOSDeviceFrame>
    );
  }

  const root = isRootScreen(s);
  const title = headerTitle(s);
  const activeProfile = FAMILY.find((f) => f.id === s.activeProfile) ?? FAMILY[0];
  const activeProfileInitial = activeProfile.name.charAt(0);
  const activeProfileLabel = activeProfile.rel === 'Mẹ' ? 'Bà ' + activeProfile.name.split(' ').pop() : activeProfile.name;

  const onBack = () => {
    if (s.tab === 'appointments') a.backAppt();
    else if (s.tab === 'journey') a.backJourney();
    else if (s.tab === 'records') a.backRecords();
    else if (s.tab === 'more') a.backMore();
  };

  const showFab = !s.chatOpen && !(s.tab === 'appointments' && s.apptScreen === 'intake');
  const showTabBar = root && !s.chatOpen;

  return (
    <IOSDeviceFrame>
      <div style={{ height: '100%', display: 'flex', flexDirection: 'column', position: 'relative', background: '#FFFFFF', color: INK, fontFamily: "'Inter', -apple-system, system-ui, sans-serif" }}>
        {/* Context header */}
        {root && (
          <div style={{ flexShrink: 0, padding: '56px 20px 12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: '#fff', position: 'relative', zIndex: 6 }}>
            <button onClick={a.toggleFamilySwitcher} style={{ display: 'flex', alignItems: 'center', gap: 8, border: 'none', background: '#F7F8F9', borderRadius: 999, padding: '6px 14px 6px 6px', cursor: 'pointer' }}>
              <div style={{ width: 28, height: 28, borderRadius: 999, background: TEAL, color: '#fff', fontSize: 12, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>{activeProfileInitial}</div>
              <span style={{ fontSize: 15, fontWeight: 600 }}>{activeProfileLabel}</span>
              <svg width="10" height="6" viewBox="0 0 10 6" fill="none"><path d="M1 1l4 4 4-4" stroke={MUTED} strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" /></svg>
            </button>
            <button onClick={a.toggleNotif} style={{ position: 'relative', width: 40, height: 40, borderRadius: 999, border: '1px solid #E2E5E8', background: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}>
              <svg width="19" height="19" viewBox="0 0 24 24" fill="none"><path d="M18 16v-5a6 6 0 10-12 0v5l-1.5 2.5h15L18 16z" stroke={INK} strokeWidth="1.6" strokeLinejoin="round" /><path d="M9.5 20a2.5 2.5 0 005 0" stroke={INK} strokeWidth="1.6" strokeLinecap="round" /></svg>
              <div style={{ position: 'absolute', top: 8, right: 9, width: 8, height: 8, borderRadius: 999, background: '#E5484D', border: '1.5px solid #fff' }} />
            </button>
          </div>
        )}

        {/* Back header */}
        {!root && (
          <div style={{ flexShrink: 0, padding: '56px 16px 12px', display: 'flex', alignItems: 'center', gap: 10, background: '#fff', position: 'relative', zIndex: 6 }}>
            <button onClick={onBack} style={{ width: 40, height: 40, borderRadius: 999, border: '1px solid #E2E5E8', background: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', flexShrink: 0 }}>
              <svg width="18" height="18" viewBox="0 0 20 20" fill="none"><path d="M12.5 4l-6 6 6 6" stroke={INK} strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" /></svg>
            </button>
            <span style={{ fontSize: 19, fontWeight: 700 }}>{title}</span>
          </div>
        )}

        {/* Content */}
        <div style={{ flex: 1, overflow: 'auto', padding: '16px 20px 120px' }}>
          {s.tab === 'home' && <HomeScreen s={s} a={a} />}
          {s.tab === 'appointments' && <AppointmentsScreen s={s} a={a} />}
          {s.tab === 'journey' && <JourneyScreen s={s} a={a} />}
          {s.tab === 'records' && <RecordsScreen s={s} a={a} />}
          {s.tab === 'more' && <MoreScreen s={s} a={a} />}
        </div>

        {/* Assistant FAB */}
        {showFab && (
          <button onClick={a.openChat} style={{ position: 'absolute', right: 18, bottom: 100, width: 58, height: 58, borderRadius: 999, background: TEAL, border: 'none', boxShadow: '0 10px 24px rgba(37,99,235,.35)', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', zIndex: 15 }}>
            <svg width="26" height="26" viewBox="0 0 24 24" fill="none"><path d="M4 5h16v11H9l-5 4V5z" stroke="#fff" strokeWidth="1.8" strokeLinejoin="round" /></svg>
          </button>
        )}

        {/* Tab bar */}
        {showTabBar && (
          <div style={{ flexShrink: 0, display: 'flex', padding: '8px 8px 26px', borderTop: '1px solid #E2E5E8', background: '#fff', position: 'relative', zIndex: 10 }}>
            <TabButton label="Trang chủ" active={s.tab === 'home'} onClick={a.goTabHome} icon={(c) => <path d="M4 11l8-7 8 7v9a1 1 0 01-1 1h-4v-6H9v6H5a1 1 0 01-1-1v-9z" stroke={c} strokeWidth="1.7" strokeLinejoin="round" />} />
            <TabButton label="Lịch khám" active={s.tab === 'appointments'} onClick={a.goTabAppt} icon={(c) => <><rect x="3.5" y="5" width="17" height="16" rx="2.5" stroke={c} strokeWidth="1.7" /><path d="M3.5 9.5h17M8 3v4M16 3v4" stroke={c} strokeWidth="1.7" strokeLinecap="round" /></>} />
            <TabButton label="Lộ trình" active={s.tab === 'journey'} onClick={a.goTabJourney} icon={(c) => <><path d="M12 21s7-6.6 7-12a7 7 0 10-14 0c0 5.4 7 12 7 12z" stroke={c} strokeWidth="1.7" /><circle cx="12" cy="9" r="2.4" stroke={c} strokeWidth="1.7" /></>} />
            <TabButton label="Hồ sơ" active={s.tab === 'records'} onClick={a.goTabRecords} icon={(c) => <><path d="M5 4h9l5 5v11a1 1 0 01-1 1H5a1 1 0 01-1-1V5a1 1 0 011-1z" stroke={c} strokeWidth="1.7" strokeLinejoin="round" /><path d="M14 4v5h5" stroke={c} strokeWidth="1.7" strokeLinejoin="round" /></>} />
            <TabButton label="Thêm" active={s.tab === 'more'} onClick={a.goTabMore} icon={(c) => <><circle cx="5" cy="12" r="1.8" fill={c} /><circle cx="12" cy="12" r="1.8" fill={c} /><circle cx="19" cy="12" r="1.8" fill={c} /></>} />
          </div>
        )}

        {/* Overlays */}
        {s.familyOpen && (
          <div onClick={a.toggleFamilySwitcher} style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,.35)', zIndex: 30, display: 'flex', alignItems: 'flex-end' }}>
            <div onClick={(e) => e.stopPropagation()} style={{ width: '100%', background: '#fff', borderRadius: '22px 22px 0 0', padding: 20, display: 'flex', flexDirection: 'column', gap: 10, animation: 'vaicSheetIn .2s ease' }}>
              <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 6 }}>Chuyển hồ sơ</div>
              {FAMILY.map((fm) => (
                <button key={fm.id} onClick={() => a.activateProfile(fm.id)} style={{ textAlign: 'left', border: '1px solid #E2E5E8', borderRadius: 14, padding: 14, background: '#fff', cursor: 'pointer', display: 'flex', gap: 10, alignItems: 'center' }}>
                  <div style={{ width: 36, height: 36, borderRadius: 999, background: fm.avatarTone === 'primary' ? TEAL : '#5A626B', color: '#fff', fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>{fm.name.charAt(0)}</div>
                  <span style={{ fontSize: 15, fontWeight: 600 }}>{fm.name}</span>
                </button>
              ))}
            </div>
          </div>
        )}

        {s.notifOpen && (
          <div onClick={a.toggleNotif} style={{ position: 'absolute', inset: 0, background: 'rgba(0,0,0,.35)', zIndex: 30, display: 'flex', alignItems: 'flex-end' }}>
            <div onClick={(e) => e.stopPropagation()} style={{ width: '100%', maxHeight: '70%', overflow: 'auto', background: '#fff', borderRadius: '22px 22px 0 0', padding: 20, display: 'flex', flexDirection: 'column', gap: 10, animation: 'vaicSheetIn .2s ease' }}>
              <div style={{ fontSize: 16, fontWeight: 700, marginBottom: 6 }}>Thông báo</div>
              {NOTIFICATIONS.map((n) => (
                <div key={n.id} style={{ display: 'flex', gap: 10, padding: '12px 0', borderBottom: '1px solid #E2E5E8' }}>
                  <NotifIcon kind={n.kind} />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 14, lineHeight: 1.4 }}>{n.text}</div>
                    <div style={{ fontSize: 12, color: FAINT, marginTop: 3 }}>{n.time}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {s.chatOpen && <ChatOverlay s={s} a={a} />}

        {s.toast && (
          <div style={{ position: 'absolute', left: '50%', bottom: 110, transform: 'translateX(-50%)', background: INK, color: '#fff', padding: '12px 18px', borderRadius: 999, fontSize: 14, fontWeight: 600, whiteSpace: 'nowrap', zIndex: 50, animation: 'vaicToastIn .2s ease', boxShadow: '0 8px 20px rgba(0,0,0,.25)' }}>{s.toast}</div>
        )}
      </div>
    </IOSDeviceFrame>
  );
}

function TabButton({ label, active, onClick, icon }: { label: string; active: boolean; onClick: () => void; icon: (color: string) => React.ReactNode }) {
  const color = active ? TEAL : FAINT;
  return (
    <button onClick={onClick} style={{ flex: 1, background: 'none', border: 'none', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 3, cursor: 'pointer', padding: '4px 0' }}>
      <svg width="23" height="23" viewBox="0 0 24 24" fill="none">{icon(color)}</svg>
      <span style={{ fontSize: 11, fontWeight: 700, color }}>{label}</span>
    </button>
  );
}

function NotifIcon({ kind }: { kind: 'ai' | 'ok' | 'warn' }) {
  if (kind === 'ai') {
    return (
      <div style={{ width: 30, height: 30, borderRadius: 999, background: 'rgba(37,99,235,.1)', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none"><path d="M12 2l1.6 5.2L19 9l-5.4 1.8L12 16l-1.6-5.2L5 9l5.4-1.8L12 2z" fill={TEAL} /></svg>
      </div>
    );
  }
  if (kind === 'ok') {
    return (
      <div style={{ width: 30, height: 30, borderRadius: 999, background: 'rgba(47,157,102,.1)', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M5 13l4 4 10-10" stroke="#2F9D66" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" /></svg>
      </div>
    );
  }
  return (
    <div style={{ width: 30, height: 30, borderRadius: 999, background: 'rgba(217,144,43,.1)', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><path d="M12 9v4M12 16.5h.01" stroke="#D9902B" strokeWidth="2" strokeLinecap="round" /><circle cx="12" cy="12" r="9" stroke="#D9902B" strokeWidth="1.6" /></svg>
    </div>
  );
}

function ChatOverlay({ s, a }: { s: CompanionState; a: { closeChat: () => void; sendQuickReply: (k: 'hungry' | 'wait' | 'where') => void } }) {
  return (
    <div style={{ position: 'absolute', inset: 0, background: '#fff', zIndex: 40, display: 'flex', flexDirection: 'column' }}>
      <div style={{ flexShrink: 0, padding: '56px 16px 14px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #E2E5E8' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ width: 34, height: 34, background: TEAL, display: 'flex', alignItems: 'center', justifyContent: 'center', clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)' }} aria-hidden="true">
            <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 11, fontWeight: 800, color: '#fff' }}>NxC</span>
          </span>
          <div>
            <div style={{ fontSize: 16, fontWeight: 700, color: INK }}>Nx<span style={{ color: TEAL }}>Care</span> AI Assistant</div>
            <div style={{ fontSize: 12, color: '#2F9D66', fontWeight: 600 }}>● Đang hoạt động</div>
          </div>
        </div>
        <button onClick={a.closeChat} style={{ width: 36, height: 36, borderRadius: 999, border: '1px solid #E2E5E8', background: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer' }}>
          <svg width="16" height="16" viewBox="0 0 20 20"><path d="M4 4l12 12M16 4L4 16" stroke={INK} strokeWidth="1.8" strokeLinecap="round" /></svg>
        </button>
      </div>
      <div style={{ flex: 1, overflow: 'auto', padding: 16, display: 'flex', flexDirection: 'column', gap: 12 }}>
        {s.chatMessages.map((c, i) =>
          c.from === 'ai' ? (
            <div key={i} style={{ alignSelf: 'flex-start', maxWidth: '80%', background: '#F7F8F9', borderRadius: 16, padding: '12px 14px', fontSize: 15, lineHeight: 1.5 }}>{c.text}</div>
          ) : (
            <div key={i} style={{ alignSelf: 'flex-end', maxWidth: '80%', background: TEAL, color: '#fff', borderRadius: 16, padding: '12px 14px', fontSize: 15, lineHeight: 1.5 }}>{c.text}</div>
          ),
        )}
      </div>
      <div style={{ flexShrink: 0, padding: '12px 16px', display: 'flex', gap: 8, overflow: 'auto', borderTop: '1px solid #E2E5E8' }}>
        <QuickReply label="Ăn trước được không?" onClick={() => a.sendQuickReply('hungry')} />
        <QuickReply label="Còn chờ bao lâu?" onClick={() => a.sendQuickReply('wait')} />
        <QuickReply label="Phòng siêu âm ở đâu?" onClick={() => a.sendQuickReply('where')} />
      </div>
    </div>
  );
}

function QuickReply({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button onClick={onClick} style={{ flexShrink: 0, height: 38, padding: '0 14px', borderRadius: 999, border: '1px solid #E2E5E8', background: '#fff', fontSize: 13, fontWeight: 600, cursor: 'pointer', whiteSpace: 'nowrap' }}>{label}</button>
  );
}

export { PATIENT_NAME, JOURNEY_STEPS };
