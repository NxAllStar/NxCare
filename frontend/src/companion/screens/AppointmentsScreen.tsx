/**
 * AppointmentsScreen - list / book / intake / checkin / prep sub-screens.
 * Transcribed 1:1 from the design's isApptList / isApptBook / isApptIntake /
 * isApptCheckin / isApptPrep blocks.
 */
import {
  APPOINTMENTS,
  PATIENT_NAME,
  PREP_ITEMS,
  SLOTS,
  SPECIALTIES,
  type ScreenProps,
} from '../state';

const TEAL = '#2563EB';
const MUTED = '#5A626B';

export function AppointmentsScreen({ s, a }: ScreenProps) {
  if (s.apptScreen === 'list') {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16, animation: 'vaicFadeUp .25s ease' }}>
        <div style={{ display: 'flex', gap: 10 }}>
          <button onClick={a.goNewBooking} style={{ flex: 1, height: 46, borderRadius: 14, border: '1px solid #E2E5E8', background: '#fff', fontSize: 14, fontWeight: 700, cursor: 'pointer' }}>Đặt lịch mới</button>
        </div>
        <div style={{ fontSize: 13, fontWeight: 700, color: '#9BA3AB', textTransform: 'uppercase', letterSpacing: '.04em' }}>Sắp tới</div>
        {APPOINTMENTS.map((appt) => (
          <div key={appt.id} style={{ border: '1px solid #E2E5E8', borderRadius: 18, padding: 16, background: '#fff', display: 'flex', flexDirection: 'column', gap: 10 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <div>
                <div style={{ fontSize: 17, fontWeight: 700 }}>{appt.time} · {appt.dept}</div>
                <div style={{ fontSize: 14, color: MUTED, marginTop: 2 }}>{appt.date} · {appt.doctor}</div>
              </div>
            </div>
            {appt.status === 'upcoming' && (
              <div style={{ display: 'flex', gap: 8 }}>
                <button onClick={a.goCheckinShortcut} style={{ flex: 1, height: 40, borderRadius: 12, border: 'none', background: TEAL, color: '#fff', fontSize: 13, fontWeight: 700, cursor: 'pointer' }}>Check-in</button>
                <button onClick={a.goPrepShortcut} style={{ flex: 1, height: 40, borderRadius: 12, border: '1px solid #E2E5E8', background: '#fff', fontSize: 13, fontWeight: 700, cursor: 'pointer' }}>Chuẩn bị</button>
              </div>
            )}
            {appt.status === 'done' && (
              <div style={{ fontSize: 12, fontWeight: 700, color: MUTED, background: '#F7F8F9', alignSelf: 'flex-start', padding: '4px 10px', borderRadius: 999 }}>Đã khám xong</div>
            )}
          </div>
        ))}
      </div>
    );
  }

  if (s.apptScreen === 'book') {
    const step2Color = s.bookStep >= 2 ? TEAL : '#E2E5E8';
    const step3Color = s.bookStep >= 3 ? TEAL : '#E2E5E8';
    const bookSpecialtyObj = SPECIALTIES.find((x) => x.id === s.bookSpecialty) ?? { name: '' };

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 18, animation: 'vaicFadeUp .25s ease' }}>
        <div style={{ display: 'flex', gap: 6 }}>
          <div style={{ height: 4, flex: 1, borderRadius: 99, background: TEAL }} />
          <div style={{ height: 4, flex: 1, borderRadius: 99, background: step2Color }} />
          <div style={{ height: 4, flex: 1, borderRadius: 99, background: step3Color }} />
        </div>

        {s.bookStep === 1 && (
          <>
            <div style={{ fontSize: 13, fontWeight: 700, color: '#9BA3AB', textTransform: 'uppercase' }}>Bước 1 · Chọn chuyên khoa</div>
            {SPECIALTIES.map((sp) => (
              <button key={sp.id} onClick={() => a.selectSpecialty(sp.id)} style={{ textAlign: 'left', border: '1px solid #E2E5E8', borderRadius: 16, padding: 16, background: '#fff', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontSize: 16, fontWeight: 700 }}>{sp.name}</div>
                  <div style={{ fontSize: 13, color: MUTED, marginTop: 2 }}>Chờ dự kiến {sp.wait}</div>
                </div>
                {sp.tag && (
                  <span style={{ fontSize: 12, fontWeight: 700, color: '#2F9D66', background: 'rgba(47,157,102,.1)', padding: '4px 10px', borderRadius: 999 }}>{sp.tag}</span>
                )}
              </button>
            ))}
          </>
        )}

        {s.bookStep === 2 && (
          <>
            <div style={{ fontSize: 13, fontWeight: 700, color: '#9BA3AB', textTransform: 'uppercase' }}>Bước 2 · Chọn giờ — {bookSpecialtyObj.name}</div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              {SLOTS.map((sl) => (
                <button key={sl.t} onClick={() => a.selectSlot(sl.t)} style={{ border: '1px solid #E2E5E8', borderRadius: 14, padding: 14, background: '#fff', cursor: 'pointer', display: 'flex', flexDirection: 'column', gap: 4, alignItems: 'center' }}>
                  <span style={{ fontSize: 18, fontWeight: 700, fontFamily: "'IBM Plex Mono', monospace" }}>{sl.t}</span>
                  {sl.tag && <span style={{ fontSize: 11, fontWeight: 700, color: '#2F9D66' }}>{sl.tag}</span>}
                </button>
              ))}
            </div>
            <button onClick={a.backBookStep} style={{ height: 44, border: 'none', background: 'none', color: MUTED, fontSize: 14, fontWeight: 600, cursor: 'pointer' }}>← Chọn lại chuyên khoa</button>
          </>
        )}

        {s.bookStep === 3 && (
          <>
            <div style={{ fontSize: 13, fontWeight: 700, color: '#9BA3AB', textTransform: 'uppercase' }}>Bước 3 · Xác nhận</div>
            <div style={{ border: '1px solid #E2E5E8', borderRadius: 18, padding: 18, background: '#F7F8F9', display: 'flex', flexDirection: 'column', gap: 10 }}>
              <div style={{ fontSize: 20, fontWeight: 800 }}>{s.bookSlot} · {bookSpecialtyObj.name}</div>
              <div style={{ fontSize: 14, color: MUTED }}>Hôm nay · BS. sẽ được xếp tự động</div>
            </div>
            <div style={{ border: '1px solid #E2E5E8', borderRadius: 18, padding: 18, display: 'flex', flexDirection: 'column', gap: 10 }}>
              <div style={{ fontSize: 13, fontWeight: 700, color: '#9BA3AB', textTransform: 'uppercase' }}>Hồ sơ bệnh nhân gửi kèm</div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14 }}><span style={{ color: MUTED }}>Họ và tên</span><span style={{ fontWeight: 600 }}>{PATIENT_NAME}</span></div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14 }}><span style={{ color: MUTED }}>Chiều cao / Cân nặng</span><span style={{ fontWeight: 600, fontFamily: "'IBM Plex Mono', monospace" }}>{s.profileHeight} cm · {s.profileWeight} kg</span></div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14 }}><span style={{ color: MUTED }}>Bệnh nền</span><span style={{ fontWeight: 600, textAlign: 'right', maxWidth: '60%' }}>{s.profileCondition}</span></div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 14 }}><span style={{ color: MUTED }}>Dị ứng</span><span style={{ fontWeight: 600, textAlign: 'right', maxWidth: '60%' }}>{s.profileAllergy}</span></div>
            </div>
            <button onClick={a.confirmBooking} style={{ height: 52, border: 'none', borderRadius: 999, background: TEAL, color: '#fff', fontSize: 16, fontWeight: 700, cursor: 'pointer' }}>Xác nhận đặt lịch</button>
            <button onClick={a.backBookStep} style={{ height: 44, border: 'none', background: 'none', color: MUTED, fontSize: 14, fontWeight: 600, cursor: 'pointer' }}>← Chọn giờ khác</button>
          </>
        )}
      </div>
    );
  }

  if (s.apptScreen === 'intake') {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 14, height: '100%', animation: 'vaicFadeUp .25s ease' }}>
        <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start', background: 'rgba(217,144,43,.08)', border: '1px solid rgba(217,144,43,.25)', borderRadius: 14, padding: 12 }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0, marginTop: 2 }}><path d="M12 9v4M12 16.5h.01" stroke="#D9902B" strokeWidth="2" strokeLinecap="round" /><circle cx="12" cy="12" r="9" stroke="#D9902B" strokeWidth="1.6" /></svg>
          <span style={{ fontSize: 13, color: '#8a6420', lineHeight: 1.4 }}>Đây là gợi ý định tuyến, <b>không phải chẩn đoán</b>. Bác sĩ sẽ khám và quyết định.</span>
        </div>

        <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
          <div style={{ width: 30, height: 30, borderRadius: 999, background: TEAL, flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><svg width="15" height="15" viewBox="0 0 24 24" fill="#fff"><path d="M12 2l1.6 5.2L19 9l-5.4 1.8L12 16l-1.6-5.2L5 9l5.4-1.8L12 2z" /></svg></div>
          <div style={{ background: '#F7F8F9', borderRadius: 16, padding: '12px 14px', fontSize: 15, lineHeight: 1.5, maxWidth: '80%' }}>Chào bạn, bạn đang thấy khó chịu ở đâu? Mô tả càng cụ thể,tôigợi ý càng đúng.</div>
        </div>

        {s.intakeStep === 0 && (
          <button onClick={a.selectSymptomChip} style={{ alignSelf: 'flex-end', maxWidth: '85%', textAlign: 'right', border: '1px solid #E2E5E8', borderRadius: 16, padding: '12px 14px', background: '#fff', fontSize: 15, cursor: 'pointer' }}>&quot;Đau bụng dưới, sốt nhẹ 2 hôm nay&quot;</button>
        )}

        {s.intakeStep === 1 && (
          <>
            <div style={{ alignSelf: 'flex-end', maxWidth: '85%', textAlign: 'right', borderRadius: 16, padding: '12px 14px', background: TEAL, color: '#fff', fontSize: 15 }}>Đau bụng dưới, sốt nhẹ 2 hôm nay</div>
            <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
              <div style={{ width: 30, height: 30, borderRadius: 999, background: TEAL, flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}><svg width="15" height="15" viewBox="0 0 24 24" fill="#fff"><path d="M12 2l1.6 5.2L19 9l-5.4 1.8L12 16l-1.6-5.2L5 9l5.4-1.8L12 2z" /></svg></div>
              <div style={{ background: '#F7F8F9', borderRadius: 16, padding: 14, fontSize: 15, lineHeight: 1.5, maxWidth: '85%', display: 'flex', flexDirection: 'column', gap: 10 }}>
                <div>Với triệu chứng này,tôigợi ý <b>chuyên khoa Ngoại tổng quát</b> — hiện đang ít đông.</div>
                <div style={{ background: '#fff', borderRadius: 12, padding: '10px 12px', fontWeight: 700 }}>10:15 hôm nay · Ngoại tổng quát</div>
                <div style={{ background: '#fff', borderRadius: 12, padding: 12, display: 'flex', flexDirection: 'column', gap: 6 }}>
                  <div style={{ fontSize: 12, fontWeight: 700, color: '#9BA3AB', textTransform: 'uppercase' }}>Hồ sơ gửi kèm bác sĩ</div>
                  <div style={{ fontSize: 13, color: MUTED }}>{PATIENT_NAME} · {s.profileHeight}cm · {s.profileWeight}kg</div>
                  <div style={{ fontSize: 13, color: MUTED }}>Bệnh nền: {s.profileCondition} · Dị ứng: {s.profileAllergy}</div>
                </div>
                <div style={{ display: 'flex', gap: 8 }}>
                  <button onClick={a.acceptIntakeSuggestion} style={{ flex: 1, height: 42, border: 'none', borderRadius: 12, background: TEAL, color: '#fff', fontSize: 14, fontWeight: 700, cursor: 'pointer' }}>Đặt lịch này</button>
                  <button onClick={a.goNewBooking} style={{ flex: 1, height: 42, border: '1px solid #E2E5E8', borderRadius: 12, background: '#fff', fontSize: 14, fontWeight: 700, cursor: 'pointer' }}>Chọn khác</button>
                </div>
              </div>
            </div>
          </>
        )}
      </div>
    );
  }

  if (s.apptScreen === 'checkin') {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 20, paddingTop: 20, animation: 'vaicFadeUp .25s ease' }}>
        {s.checkinStage === 'idle' && (
          <>
            <div style={{ width: 220, height: 220, borderRadius: 24, background: '#F7F8F9', border: '1.5px dashed #C7CDD2', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <svg width="120" height="120" viewBox="0 0 24 24" fill="none"><rect x="3" y="3" width="7" height="7" stroke="#12151A" strokeWidth="1.4" /><rect x="14" y="3" width="7" height="7" stroke="#12151A" strokeWidth="1.4" /><rect x="3" y="14" width="7" height="7" stroke="#12151A" strokeWidth="1.4" /><path d="M14 14h3v3h-3zM20 14v3M14 20h3M18 18h3v3" stroke="#12151A" strokeWidth="1.4" /></svg>
            </div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 18, fontWeight: 700 }}>Quét QR tại quầy hoặc bảng chỉ dẫn</div>
              <div style={{ fontSize: 14, color: MUTED, marginTop: 6 }}>Lịch hẹn 10:15 · Ngoại tổng quát</div>
            </div>
            <button onClick={a.scanQr} style={{ height: 52, width: '100%', border: 'none', borderRadius: 999, background: TEAL, color: '#fff', fontSize: 16, fontWeight: 700, cursor: 'pointer' }}>Quét QR (mô phỏng)</button>
          </>
        )}
        {s.checkinStage === 'queued' && (
          <>
            <div style={{ width: 96, height: 96, borderRadius: 999, background: 'rgba(47,157,102,.1)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}><svg width="44" height="44" viewBox="0 0 24 24" fill="none"><path d="M5 13l4 4 10-10" stroke="#2F9D66" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" /></svg></div>
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 18, fontWeight: 700 }}>Đã vào hàng đợi</div>
              <div style={{ fontSize: 15, color: MUTED, marginTop: 6 }}>Vị trí thứ 3 · chờ khoảng 12 phút</div>
            </div>
            <button onClick={a.enterLiveCompanion} style={{ height: 52, width: '100%', border: 'none', borderRadius: 999, background: TEAL, color: '#fff', fontSize: 16, fontWeight: 700, cursor: 'pointer' }}>Vào khu chờ — bật chế độ đồng hành</button>
          </>
        )}
      </div>
    );
  }

  if (s.apptScreen === 'prep') {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16, animation: 'vaicFadeUp .25s ease' }}>
        <div style={{ fontSize: 15, color: MUTED, lineHeight: 1.5 }}>Nhắc chuẩn bị cho lịch khám <b>10:15 · Ngoại tổng quát</b> hôm nay.</div>
        <div style={{ border: '1px solid #E2E5E8', borderRadius: 16, overflow: 'hidden' }}>
          {PREP_ITEMS.map((p, i) => (
            <div key={i} style={{ display: 'flex', gap: 12, alignItems: 'flex-start', padding: 14, borderBottom: '1px solid #E2E5E8' }}>
              <div style={{ width: 22, height: 22, borderRadius: 999, border: '1.5px solid #C7CDD2', flexShrink: 0, marginTop: 1 }} />
              <span style={{ fontSize: 15, lineHeight: 1.4 }}>{p}</span>
            </div>
          ))}
        </div>
        <button onClick={a.backAppt} style={{ height: 52, border: 'none', borderRadius: 999, background: TEAL, color: '#fff', fontSize: 16, fontWeight: 700, cursor: 'pointer' }}>Đã hiểu</button>
      </div>
    );
  }

  return null;
}
