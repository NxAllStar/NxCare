/**
 * MoreScreen - menu / billing / family / settings. Transcribed 1:1 from the
 * design's isMoreMenu / isBilling / isFamily / isSettings blocks.
 */
import { FAMILY, type ScreenProps } from '../state';

export function MoreScreen({ s, a }: ScreenProps) {
  if (s.moreScreen === 'menu') {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12, animation: 'vaicFadeUp .25s ease' }}>
        <button onClick={a.goBilling} style={{ textAlign: 'left', border: '1px solid #E2E5E8', borderRadius: 16, padding: 16, background: '#fff', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: 16, fontWeight: 700 }}>Viện phí &amp; BHYT</span>
          <svg width="8" height="14" viewBox="0 0 8 14"><path d="M1 1l6 6-6 6" stroke="#C7CDD2" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" /></svg>
        </button>
        <button onClick={a.goFamily} style={{ textAlign: 'left', border: '1px solid #E2E5E8', borderRadius: 16, padding: 16, background: '#fff', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: 16, fontWeight: 700 }}>Gia đình</span>
          <svg width="8" height="14" viewBox="0 0 8 14"><path d="M1 1l6 6-6 6" stroke="#C7CDD2" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" /></svg>
        </button>
        <button onClick={a.goSettings} style={{ textAlign: 'left', border: '1px solid #E2E5E8', borderRadius: 16, padding: 16, background: '#fff', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: 16, fontWeight: 700 }}>Cài đặt</span>
          <svg width="8" height="14" viewBox="0 0 8 14"><path d="M1 1l6 6-6 6" stroke="#C7CDD2" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" /></svg>
        </button>
      </div>
    );
  }

  if (s.moreScreen === 'billing') {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16, animation: 'vaicFadeUp .25s ease' }}>
        <div style={{ border: '1px solid #E2E5E8', borderRadius: 18, padding: 18, display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14 }}><span style={{ color: '#5A626B' }}>Khám bệnh</span><span style={{ fontFamily: "'IBM Plex Mono', monospace" }}>150.000đ</span></div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14 }}><span style={{ color: '#5A626B' }}>Xét nghiệm máu</span><span style={{ fontFamily: "'IBM Plex Mono', monospace" }}>320.000đ</span></div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14 }}><span style={{ color: '#5A626B' }}>X-quang</span><span style={{ fontFamily: "'IBM Plex Mono', monospace" }}>280.000đ</span></div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14 }}><span style={{ color: '#5A626B' }}>Siêu âm</span><span style={{ fontFamily: "'IBM Plex Mono', monospace" }}>250.000đ</span></div>
          <div style={{ height: 1, background: '#E2E5E8' }} />
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 15, fontWeight: 700 }}><span>Tổng chi phí</span><span style={{ fontFamily: "'IBM Plex Mono', monospace" }}>1.000.000đ</span></div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14, color: '#2F9D66' }}><span>BHYT chi trả (80%)</span><span style={{ fontFamily: "'IBM Plex Mono', monospace" }}>-800.000đ</span></div>
        </div>
        <div style={{ background: '#F7F8F9', borderRadius: 16, padding: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: 16, fontWeight: 700 }}>Cần thanh toán</span>
          <span style={{ fontSize: 22, fontWeight: 800, fontFamily: "'IBM Plex Mono', monospace" }}>200.000đ</span>
        </div>
        {s.billingPaid && (
          <div style={{ height: 52, borderRadius: 999, background: 'rgba(47,157,102,.1)', color: '#2F9D66', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, fontSize: 16, fontWeight: 700 }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none"><path d="M5 13l4 4 10-10" stroke="#2F9D66" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" /></svg>
            Đã thanh toán
          </div>
        )}
        {!s.billingPaid && (
          <button onClick={a.payBill} style={{ height: 52, border: 'none', borderRadius: 999, background: '#0E7490', color: '#fff', fontSize: 16, fontWeight: 700, cursor: 'pointer' }}>Thanh toán 200.000đ qua QR</button>
        )}
      </div>
    );
  }

  if (s.moreScreen === 'family') {
    const shareTrackColor = s.shareLocation ? '#0E7490' : '#C7CDD2';
    const shareThumbPos = s.shareLocation ? '23px' : '3px';

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16, animation: 'vaicFadeUp .25s ease' }}>
        {FAMILY.map((f) => {
          const avatarColor = f.avatarTone === 'primary' ? '#0E7490' : '#5A626B';
          return (
            <button key={f.id} onClick={() => {}} style={{ textAlign: 'left', border: '1px solid #E2E5E8', borderRadius: 16, padding: 16, background: '#fff', cursor: 'pointer', display: 'flex', gap: 12, alignItems: 'center' }}>
              <div style={{ width: 44, height: 44, borderRadius: 999, background: avatarColor, color: '#fff', fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>{f.name.charAt(0)}</div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 16, fontWeight: 700 }}>{f.name}</div>
                <div style={{ fontSize: 13, color: '#5A626B', marginTop: 2 }}>{f.rel}</div>
                {f.status && <div style={{ fontSize: 13, color: '#0E7490', fontWeight: 600, marginTop: 4 }}>● {f.status}</div>}
              </div>
            </button>
          );
        })}
        <div style={{ border: '1px solid #E2E5E8', borderRadius: 16, padding: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontSize: 15, fontWeight: 700 }}>Chia sẻ vị trí thực tế</div>
            <div style={{ fontSize: 13, color: '#5A626B', marginTop: 2 }}>Cho phép người thân theo dõi realtime</div>
          </div>
          <button onClick={a.toggleShare} style={{ width: 48, height: 28, borderRadius: 999, border: 'none', background: shareTrackColor, position: 'relative', cursor: 'pointer', flexShrink: 0 }}>
            <div style={{ width: 22, height: 22, borderRadius: 999, background: '#fff', position: 'absolute', top: 3, left: shareThumbPos, boxShadow: '0 1px 3px rgba(0,0,0,.2)', transition: 'left .15s' }} />
          </button>
        </div>
        <button onClick={a.openChat} style={{ height: 48, border: '1px solid #E2E5E8', borderRadius: 999, background: '#fff', fontSize: 15, fontWeight: 700, cursor: 'pointer' }}>Chat hộ với Trợ lý</button>
      </div>
    );
  }

  // moreScreen === 'settings'
  const largeTextTrackColor = s.largeText ? '#0E7490' : '#C7CDD2';
  const largeTextThumbPos = s.largeText ? '23px' : '3px';
  const highContrastTrackColor = s.highContrast ? '#0E7490' : '#C7CDD2';
  const highContrastThumbPos = s.highContrast ? '23px' : '3px';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, animation: 'vaicFadeUp .25s ease' }}>
      <div style={{ border: '1px solid #E2E5E8', borderRadius: 16, overflow: 'hidden' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: 16, borderBottom: '1px solid #E2E5E8' }}>
          <span style={{ fontSize: 16, fontWeight: 600 }}>Cỡ chữ lớn</span>
          <button onClick={a.toggleLargeText} style={{ width: 48, height: 28, borderRadius: 999, border: 'none', background: largeTextTrackColor, position: 'relative', cursor: 'pointer' }}>
            <div style={{ width: 22, height: 22, borderRadius: 999, background: '#fff', position: 'absolute', top: 3, left: largeTextThumbPos, boxShadow: '0 1px 3px rgba(0,0,0,.2)' }} />
          </button>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: 16 }}>
          <span style={{ fontSize: 16, fontWeight: 600 }}>Độ tương phản cao</span>
          <button onClick={a.toggleHighContrast} style={{ width: 48, height: 28, borderRadius: 999, border: 'none', background: highContrastTrackColor, position: 'relative', cursor: 'pointer' }}>
            <div style={{ width: 22, height: 22, borderRadius: 999, background: '#fff', position: 'absolute', top: 3, left: highContrastThumbPos, boxShadow: '0 1px 3px rgba(0,0,0,.2)' }} />
          </button>
        </div>
      </div>
      <div style={{ border: '1px solid #E2E5E8', borderRadius: 16, padding: 16 }}>
        <div style={{ fontSize: 13, fontWeight: 700, color: '#9BA3AB', textTransform: 'uppercase', marginBottom: 10 }}>Nhật ký đồng ý</div>
        <div style={{ fontSize: 14, color: '#5A626B', lineHeight: 1.6 }}>
          • 12/05/2026 — Đồng ý AI gợi ý định tuyến khám<br />
          • 12/05/2026 — Đồng ý chia sẻ vị trí với gia đình
        </div>
      </div>
      <button onClick={a.logout} style={{ height: 48, border: '1px solid #E2E5E8', borderRadius: 999, background: '#fff', color: '#E5484D', fontSize: 15, fontWeight: 700, cursor: 'pointer' }}>Đăng xuất</button>
    </div>
  );
}
