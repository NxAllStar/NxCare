/**
 * Onboarding - login (Google + phone + OTP send), OTP entry, health
 * profile, and BHYT linking. Transcribed 1:1 from the design's render
 * markup (isOnboarding block).
 */
import { PATIENT_NAME, OTP_DIGITS, type ScreenProps, type OnboardStep } from '../state';

const TEAL = '#0E7490';
const MUTED = '#5A626B';
const FAINT = '#9BA3AB';

const ORDER: OnboardStep[] = ['login', 'otp', 'profile', 'insurance'];

export function Onboarding({ s, a }: ScreenProps) {
  const currentIndex = ORDER.indexOf(s.onboardStep);
  const showObBack = s.onboardStep !== 'login';

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'auto' }}>
      <div style={{ flexShrink: 0, padding: '56px 24px 0', display: 'flex', alignItems: 'center', gap: 14 }}>
        {showObBack && (
          <button onClick={a.obBack} style={{ width: 38, height: 38, borderRadius: 999, border: '1px solid #E2E5E8', background: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', flexShrink: 0 }}>
            <svg width="17" height="17" viewBox="0 0 20 20" fill="none"><path d="M12.5 4l-6 6 6 6" stroke="#12151A" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" /></svg>
          </button>
        )}
        <div style={{ display: 'flex', gap: 6, flex: 1 }}>
          {ORDER.map((step, i) => (
            <div key={step} style={{ height: 4, flex: 1, borderRadius: 99, background: i <= currentIndex ? TEAL : '#E2E5E8' }} />
          ))}
        </div>
      </div>

      {s.onboardStep === 'login' && (
        <div style={{ flexShrink: 0, padding: '28px 24px 32px', display: 'flex', flexDirection: 'column', gap: 24, animation: 'vaicFadeUp .3s ease' }}>
          <div>
            <div style={{ width: 52, height: 52, borderRadius: 16, background: TEAL, display: 'flex', alignItems: 'center', justifyContent: 'center', marginBottom: 20 }}>
              <svg width="26" height="26" viewBox="0 0 24 24" fill="none"><path d="M12 21s-7.5-4.9-10-9.6C.5 7.8 2.6 4 6.3 4c2.2 0 3.7 1.2 5.7 4 2-2.8 3.5-4 5.7-4 3.7 0 5.8 3.8 4.3 7.4C19.5 16.1 12 21 12 21z" fill="#fff" /></svg>
            </div>
            <div style={{ fontSize: 26, fontWeight: 700, letterSpacing: '-0.01em' }}>Đồng hành khám bệnh</div>
            <div style={{ fontSize: 16, color: MUTED, marginTop: 8, lineHeight: 1.5 }}>Đăng nhập để theo dõi lịch khám, kết quả và lộ trình của chị và người thân.</div>
          </div>

          <button onClick={a.googleSignIn} style={{ height: 54, borderRadius: 16, border: '1px solid #E2E5E8', background: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, fontSize: 16, fontWeight: 600, color: '#12151A', cursor: 'pointer' }}>
            <svg width="20" height="20" viewBox="0 0 20 20"><path fill="#4285F4" d="M19.6 10.23c0-.68-.06-1.33-.17-1.96H10v3.71h5.38a4.6 4.6 0 01-2 3.02v2.5h3.23c1.9-1.75 2.99-4.33 2.99-7.27z" /><path fill="#34A853" d="M10 20c2.7 0 4.96-.9 6.61-2.43l-3.23-2.5c-.9.6-2.04.96-3.38.96-2.6 0-4.8-1.76-5.59-4.12H1.06v2.59A9.99 9.99 0 0010 20z" /><path fill="#FBBC05" d="M4.41 11.9A6 6 0 014.1 10c0-.66.11-1.3.31-1.9V5.51H1.06A9.99 9.99 0 000 10c0 1.61.39 3.14 1.06 4.49l3.35-2.6z" /><path fill="#EA4335" d="M10 3.98c1.47 0 2.79.51 3.83 1.5l2.87-2.87A9.6 9.6 0 0010 0 9.99 9.99 0 001.06 5.51l3.35 2.6C5.2 5.74 7.4 3.98 10 3.98z" /></svg>
            Tiếp tục với Google
          </button>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ flex: 1, height: 1, background: '#E2E5E8' }} />
            <span style={{ fontSize: 13, color: FAINT, fontWeight: 600 }}>hoặc dùng số điện thoại</span>
            <div style={{ flex: 1, height: 1, background: '#E2E5E8' }} />
          </div>

          <div>
            <div style={{ fontSize: 14, fontWeight: 600, color: MUTED, marginBottom: 8 }}>Số điện thoại</div>
            <div style={{ height: 56, borderRadius: 16, background: '#F7F8F9', border: '1px solid #E2E5E8', display: 'flex', alignItems: 'center', gap: 10, padding: '0 18px' }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0 }}><path d="M6.6 10.8c1.4 2.8 3.8 5.2 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.2.5 2.5.8 3.9.8.6 0 1 .4 1 1V20c0 .6-.4 1-1 1C10.6 21 3 13.4 3 4c0-.6.4-1 1-1h3.2c.6 0 1 .4 1 1 0 1.4.3 2.7.8 3.9.1.4 0 .8-.2 1L6.6 10.8z" stroke={MUTED} strokeWidth="1.5" strokeLinejoin="round" /></svg>
              <span style={{ fontSize: 18, fontWeight: 600, fontFamily: "'IBM Plex Mono', monospace" }}>090 234 5678</span>
            </div>
          </div>
          <button onClick={a.goOtp} style={{ height: 56, border: 'none', borderRadius: 999, background: TEAL, color: '#fff', fontSize: 17, fontWeight: 700, cursor: 'pointer' }}>Gửi mã OTP</button>
          <div style={{ textAlign: 'center', fontSize: 13, color: FAINT, lineHeight: 1.5 }}>Tiếp tục đồng nghĩa chị đồng ý với Điều khoản sử dụng &amp; Chính sách riêng tư.</div>
        </div>
      )}

      {s.onboardStep === 'otp' && (
        <div style={{ flexShrink: 0, padding: '28px 24px 32px', display: 'flex', flexDirection: 'column', gap: 24, animation: 'vaicFadeUp .3s ease' }}>
          <div>
            <div style={{ fontSize: 26, fontWeight: 700 }}>Nhập mã xác nhận</div>
            <div style={{ fontSize: 16, color: MUTED, marginTop: 8, lineHeight: 1.5 }}>Mã 6 số vừa gửi tới 090 234 5678</div>
          </div>
          <div style={{ display: 'flex', gap: 10 }}>
            {OTP_DIGITS.map((d, i) => (
              <div key={i} style={{ flex: 1, height: 60, borderRadius: 14, background: '#F7F8F9', border: '1px solid #E2E5E8', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22, fontWeight: 700, fontFamily: "'IBM Plex Mono', monospace" }}>{d}</div>
            ))}
          </div>
          <button onClick={a.goProfile} style={{ height: 56, border: 'none', borderRadius: 999, background: TEAL, color: '#fff', fontSize: 17, fontWeight: 700, cursor: 'pointer' }}>Xác nhận</button>
          <button style={{ height: 36, border: 'none', background: 'none', color: TEAL, fontSize: 14, fontWeight: 700, cursor: 'pointer' }}>Gửi lại mã</button>
        </div>
      )}

      {s.onboardStep === 'profile' && (
        <div style={{ flexShrink: 0, padding: '28px 24px 32px', display: 'flex', flexDirection: 'column', gap: 20, animation: 'vaicFadeUp .3s ease' }}>
          <div>
            <div style={{ fontSize: 26, fontWeight: 700 }}>Hồ sơ sức khỏe</div>
            <div style={{ fontSize: 16, color: MUTED, marginTop: 8, lineHeight: 1.5 }}>Giúp AI cảnh báo đúng khi kê đơn hoặc gợi ý.</div>
          </div>
          <Field label="Họ và tên"><div style={{ height: 52, borderRadius: 14, background: '#F7F8F9', border: '1px solid #E2E5E8', display: 'flex', alignItems: 'center', padding: '0 16px', fontSize: 16, fontWeight: 600 }}>{PATIENT_NAME}</div></Field>
          <div style={{ display: 'flex', gap: 12 }}>
            <Field label="Chiều cao (cm)" flex><input value={s.profileHeight} onChange={(e) => a.setProfileHeight(e.target.value)} style={numInput} /></Field>
            <Field label="Cân nặng (kg)" flex><input value={s.profileWeight} onChange={(e) => a.setProfileWeight(e.target.value)} style={numInput} /></Field>
          </div>
          <Field label="Dị ứng (nếu có)"><input value={s.profileAllergy} onChange={(e) => a.setProfileAllergy(e.target.value)} placeholder="VD: Penicillin, hải sản…" style={textInput} /></Field>
          <Field label="Bệnh nền (nếu có)"><input value={s.profileCondition} onChange={(e) => a.setProfileCondition(e.target.value)} placeholder="VD: Tăng huyết áp, tiểu đường…" style={textInput} /></Field>
          <button onClick={a.goInsurance} style={{ height: 56, border: 'none', borderRadius: 999, background: TEAL, color: '#fff', fontSize: 17, fontWeight: 700, cursor: 'pointer', marginTop: 4 }}>Tiếp tục</button>
        </div>
      )}

      {s.onboardStep === 'insurance' && (
        <div style={{ flexShrink: 0, padding: '28px 24px 32px', display: 'flex', flexDirection: 'column', gap: 24, animation: 'vaicFadeUp .3s ease' }}>
          <div>
            <div style={{ fontSize: 26, fontWeight: 700 }}>Liên kết BHYT</div>
            <div style={{ fontSize: 16, color: MUTED, marginTop: 8, lineHeight: 1.5 }}>Để tính đúng chi phí đồng chi trả.</div>
          </div>
          <div>
            <div style={{ fontSize: 14, fontWeight: 600, color: MUTED, marginBottom: 8 }}>Mã thẻ BHYT</div>
            <div style={{ height: 56, borderRadius: 16, background: '#F7F8F9', border: '1px solid #E2E5E8', display: 'flex', alignItems: 'center', padding: '0 18px', fontSize: 16, fontWeight: 600, fontFamily: "'IBM Plex Mono', monospace" }}>GD4 01 79 2201234</div>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            <button onClick={a.finishOnboarding} style={{ height: 56, border: 'none', borderRadius: 999, background: TEAL, color: '#fff', fontSize: 17, fontWeight: 700, cursor: 'pointer' }}>Liên kết &amp; hoàn tất</button>
            <button onClick={a.finishOnboarding} style={{ height: 44, border: 'none', background: 'none', color: MUTED, fontSize: 15, fontWeight: 600, cursor: 'pointer' }}>Bỏ qua, làm sau</button>
          </div>
        </div>
      )}
    </div>
  );
}

const numInput: React.CSSProperties = { width: '100%', height: 52, borderRadius: 14, background: '#F7F8F9', border: '1px solid #E2E5E8', padding: '0 16px', fontSize: 16, fontWeight: 600, fontFamily: "'IBM Plex Mono', monospace", boxSizing: 'border-box' };
const textInput: React.CSSProperties = { width: '100%', height: 52, borderRadius: 14, background: '#F7F8F9', border: '1px solid #E2E5E8', padding: '0 16px', fontSize: 16, fontFamily: 'inherit', boxSizing: 'border-box' };

function Field({ label, children, flex }: { label: string; children: React.ReactNode; flex?: boolean }) {
  return (
    <div style={flex ? { flex: 1 } : undefined}>
      <div style={{ fontSize: 13, fontWeight: 600, color: MUTED, marginBottom: 8 }}>{label}</div>
      {children}
    </div>
  );
}
