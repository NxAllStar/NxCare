/**
 * HomeScreen - dual-mode home: out-of-hospital dashboard vs in-hospital
 * live companion. Transcribed 1:1 from the design's isTabHome block.
 */
import { JOURNEY_STEPS, PATIENT_NAME, type ScreenProps } from '../state';

const TEAL = '#2563EB';
const MUTED = '#5A626B';

export function HomeScreen({ s, a }: ScreenProps) {
  const activeStep = JOURNEY_STEPS.find((j) => j.status === 'active') ?? JOURNEY_STEPS[0];

  if (s.locationMode === 'outside') {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16, animation: 'vaicFadeUp .25s ease' }}>
        <div style={{ fontSize: 22, fontWeight: 700 }}>Xin chào {PATIENT_NAME}</div>

        <div style={{ background: TEAL, borderRadius: 22, padding: 20, color: '#fff', display: 'flex', flexDirection: 'column', gap: 10, boxShadow: '0 8px 24px rgba(37,99,235,.25)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, fontWeight: 600, opacity: 0.9, textTransform: 'uppercase', letterSpacing: '.04em' }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="#fff"><path d="M12 2l1.6 5.2L19 9l-5.4 1.8L12 16l-1.6-5.2L5 9l5.4-1.8L12 2z" /></svg>
            Lịch khám sắp tới
          </div>
          <div style={{ fontSize: 20, fontWeight: 700 }}>10:15 · Ngoại tổng quát</div>
          <div style={{ fontSize: 15, opacity: 0.9 }}>Hôm nay · BS. Trần Văn Minh · Phòng khám 4</div>
          <button onClick={a.goPrepShortcut} style={{ alignSelf: 'flex-start', marginTop: 4, height: 38, padding: '0 16px', borderRadius: 999, border: 'none', background: 'rgba(255,255,255,.2)', color: '#fff', fontSize: 14, fontWeight: 700, cursor: 'pointer' }}>Xem chuẩn bị trước khám</button>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          <button onClick={a.goBookShortcut} style={{ textAlign: 'left', border: '1px solid #E2E5E8', borderRadius: 18, padding: 16, background: '#fff', cursor: 'pointer', display: 'flex', flexDirection: 'column', gap: 8 }}>
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none"><rect x="4" y="5" width="16" height="15" rx="2" stroke="#12151A" strokeWidth="1.6" /><path d="M4 9h16M8 3v4M16 3v4" stroke="#12151A" strokeWidth="1.6" strokeLinecap="round" /></svg>
            <div style={{ fontSize: 15, fontWeight: 700 }}>Đặt lịch mới</div>
          </button>
        </div>

        <div style={{ border: '1px solid #E2E5E8', borderRadius: 18, padding: 16, background: '#fff' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
            <span style={{ fontSize: 15, fontWeight: 700 }}>Kết quả mới</span>
            <span style={{ fontSize: 12, fontWeight: 700, color: '#2F9D66', background: 'rgba(47,157,102,.1)', padding: '3px 8px', borderRadius: 999 }}>1 mới</span>
          </div>
          <button onClick={a.goResultsFromHome} style={{ width: '100%', textAlign: 'left', border: 'none', background: 'none', padding: 0, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ fontSize: 15, fontWeight: 600 }}>Công thức máu</div>
            <svg width="8" height="14" viewBox="0 0 8 14"><path d="M1 1l6 6-6 6" stroke="#9BA3AB" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" /></svg>
          </button>
        </div>

        <button onClick={a.goCheckinShortcut} style={{ height: 52, border: '1.5px dashed #C7CDD2', borderRadius: 16, background: 'none', color: MUTED, fontSize: 15, fontWeight: 600, cursor: 'pointer' }}>Đã tới viện? Check-in tại đây →</button>
      </div>
    );
  }

  // inside mode
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, animation: 'vaicFadeUp .25s ease' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <div style={{ width: 8, height: 8, borderRadius: 999, background: TEAL, animation: 'vaicPulseDot 1.6s infinite' }} />
        <span style={{ fontSize: 13, fontWeight: 700, color: TEAL, textTransform: 'uppercase', letterSpacing: '.04em' }}>Đang đồng hành cùng chị</span>
      </div>

      <div style={{ background: '#F7F8F9', border: '1px solid #E2E5E8', borderRadius: 24, padding: 22, display: 'flex', flexDirection: 'column', gap: 6 }}>
        <div style={{ fontSize: 14, color: MUTED, fontWeight: 600 }}>Bước hiện tại</div>
        <div style={{ fontSize: 24, fontWeight: 800 }}>{activeStep.label}</div>
        <div style={{ fontSize: 15, color: MUTED }}>{activeStep.room}</div>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, marginTop: 10 }}>
          <span style={{ fontSize: 40, fontWeight: 800, fontFamily: "'IBM Plex Mono', monospace", color: TEAL }}>~12</span>
          <span style={{ fontSize: 16, color: MUTED, fontWeight: 600 }}>phút nữa</span>
        </div>
        <button onClick={a.toggleWhy} style={{ alignSelf: 'flex-start', marginTop: 10, height: 36, padding: '0 14px', borderRadius: 999, border: '1px solid #E2E5E8', background: '#fff', fontSize: 13, fontWeight: 700, color: '#12151A', cursor: 'pointer' }}>Vì sao chờ?</button>
        {s.whyOpen && (
          <div style={{ marginTop: 8, fontSize: 14, color: MUTED, lineHeight: 1.5, background: '#fff', borderRadius: 12, padding: 12 }}>Phía trước còn 2 người và 1 ca cấp cứu vừa ưu tiên. Em sẽ báo ngay khi tới lượt chị.</div>
        )}
      </div>

      <div style={{ display: 'flex', gap: 10 }}>
        <button onClick={a.goJourneyFromHome} style={{ flex: 1, height: 48, borderRadius: 14, border: '1px solid #E2E5E8', background: '#fff', fontSize: 14, fontWeight: 700, cursor: 'pointer' }}>Xem lộ trình đầy đủ</button>
        <button onClick={a.openChat} style={{ flex: 1, height: 48, borderRadius: 14, border: 'none', background: TEAL, color: '#fff', fontSize: 14, fontWeight: 700, cursor: 'pointer' }}>Hỏi trợ lý</button>
      </div>

      <div style={{ border: '1px solid #E2E5E8', borderRadius: 16, padding: 14, display: 'flex', gap: 10, alignItems: 'flex-start' }}>
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0, marginTop: 2 }}><path d="M12 2l1.6 5.2L19 9l-5.4 1.8L12 16l-1.6-5.2L5 9l5.4-1.8L12 2z" fill={TEAL} /></svg>
        <div style={{ fontSize: 14, color: MUTED, lineHeight: 1.5 }}><span style={{ color: '#12151A', fontWeight: 600 }}>AI đang làm gì cho chị: </span>theo dõi máy X-quang, giữ chỗ siêu âm và sẽ báo ngay nếu lộ trình thay đổi.</div>
      </div>

      <button onClick={a.endVisitDemo} style={{ height: 40, border: 'none', background: 'none', color: '#9BA3AB', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}>Kết thúc buổi khám (demo)</button>
    </div>
  );
}
