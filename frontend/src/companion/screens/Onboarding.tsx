/**
 * Onboarding - login (phone + OTP send), OTP entry, health profile, and BHYT
 * linking. Login is phone + OTP only (no Google sign-in). Primary colour is the
 * NxCare console blue so the patient app matches the hospital web console.
 */
import { PATIENT_NAME, OTP_DIGITS, type ScreenProps, type OnboardStep } from '../state';

const PRIMARY = '#2563EB';
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
            <div key={step} style={{ height: 4, flex: 1, borderRadius: 99, background: i <= currentIndex ? PRIMARY : '#E2E5E8' }} />
          ))}
        </div>
      </div>

      {s.onboardStep === 'login' && (
        <div style={{ flexShrink: 0, padding: '28px 24px 32px', display: 'flex', flexDirection: 'column', gap: 24, animation: 'vaicFadeUp .3s ease' }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 20 }}>
              <span style={{ width: 44, height: 44, background: PRIMARY, display: 'flex', alignItems: 'center', justifyContent: 'center', clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)' }} aria-hidden="true">
                <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 14, fontWeight: 800, color: '#fff' }}>NxC</span>
              </span>
              <span style={{ fontSize: 26, fontWeight: 800, letterSpacing: '-0.02em', color: '#12151A' }}>Nx<span style={{ color: PRIMARY }}>Care</span></span>
            </div>
            <div style={{ fontSize: 26, fontWeight: 700, letterSpacing: '-0.01em' }}>Sức khỏe trong tầm tay</div>
            <div style={{ fontSize: 16, color: MUTED, marginTop: 8, lineHeight: 1.5 }}>Đăng nhập để theo dõi lịch khám, kết quả và lộ trình của bạn và người thân.</div>
          </div>

          <div>
            <div style={{ fontSize: 14, fontWeight: 600, color: MUTED, marginBottom: 8 }}>Số điện thoại</div>
            <div style={{ height: 56, borderRadius: 16, background: '#F7F8F9', border: '1px solid #E2E5E8', display: 'flex', alignItems: 'center', gap: 10, padding: '0 18px' }}>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0 }}><path d="M6.6 10.8c1.4 2.8 3.8 5.2 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.2.5 2.5.8 3.9.8.6 0 1 .4 1 1V20c0 .6-.4 1-1 1C10.6 21 3 13.4 3 4c0-.6.4-1 1-1h3.2c.6 0 1 .4 1 1 0 1.4.3 2.7.8 3.9.1.4 0 .8-.2 1L6.6 10.8z" stroke={MUTED} strokeWidth="1.5" strokeLinejoin="round" /></svg>
              <span style={{ fontSize: 18, fontWeight: 600, fontFamily: "'IBM Plex Mono', monospace" }}>090 234 5678</span>
            </div>
          </div>
          <button onClick={a.goOtp} style={{ height: 56, border: 'none', borderRadius: 999, background: PRIMARY, color: '#fff', fontSize: 17, fontWeight: 700, cursor: 'pointer' }}>Gửi mã OTP</button>
          <div style={{ textAlign: 'center', fontSize: 13, color: FAINT, lineHeight: 1.5 }}>Tiếp tục đồng nghĩa bạn đồng ý với Điều khoản sử dụng &amp; Chính sách riêng tư.</div>
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
          <button onClick={a.goProfile} style={{ height: 56, border: 'none', borderRadius: 999, background: PRIMARY, color: '#fff', fontSize: 17, fontWeight: 700, cursor: 'pointer' }}>Xác nhận</button>
          <button style={{ height: 36, border: 'none', background: 'none', color: PRIMARY, fontSize: 14, fontWeight: 700, cursor: 'pointer' }}>Gửi lại mã</button>
        </div>
      )}

      {s.onboardStep === 'profile' && (
        <div style={{ flexShrink: 0, padding: '28px 24px 32px', display: 'flex', flexDirection: 'column', gap: 20, animation: 'vaicFadeUp .3s ease' }}>
          <div>
            <div style={{ fontSize: 26, fontWeight: 700 }}>Hồ sơ sức khỏe</div>
          </div>
          <Field label="Họ và tên"><div style={{ height: 52, borderRadius: 14, background: '#F7F8F9', border: '1px solid #E2E5E8', display: 'flex', alignItems: 'center', padding: '0 16px', fontSize: 16, fontWeight: 600 }}>{PATIENT_NAME}</div></Field>
          <div style={{ display: 'flex', gap: 12 }}>
            <Field label="Chiều cao (cm)" flex><input value={s.profileHeight} onChange={(e) => a.setProfileHeight(e.target.value)} style={numInput} /></Field>
            <Field label="Cân nặng (kg)" flex><input value={s.profileWeight} onChange={(e) => a.setProfileWeight(e.target.value)} style={numInput} /></Field>
          </div>
          <Field label="Dị ứng (nếu có)"><input value={s.profileAllergy} onChange={(e) => a.setProfileAllergy(e.target.value)} placeholder="VD: Penicillin, hải sản…" style={textInput} /></Field>
          <Field label="Bệnh nền (nếu có)"><input value={s.profileCondition} onChange={(e) => a.setProfileCondition(e.target.value)} placeholder="VD: Tăng huyết áp, tiểu đường…" style={textInput} /></Field>
          <button onClick={a.goInsurance} style={{ height: 56, border: 'none', borderRadius: 999, background: PRIMARY, color: '#fff', fontSize: 17, fontWeight: 700, cursor: 'pointer', marginTop: 4 }}>Tiếp tục</button>
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
            <button onClick={a.finishOnboarding} style={{ height: 56, border: 'none', borderRadius: 999, background: PRIMARY, color: '#fff', fontSize: 17, fontWeight: 700, cursor: 'pointer' }}>Liên kết &amp; hoàn tất</button>
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
