/**
 * RecordsScreen - records list / results / result detail / medications /
 * recovery / visit summary. Transcribed 1:1 from the design's records
 * blocks (isRecordsList, isResults, isResultDetail, isMedications,
 * isRecovery, isVisitSummary).
 */
import { MEDICATIONS, RESULTS, type ScreenProps } from '../state';

const TEAL = '#2563EB';
const MUTED = '#5A626B';
const BORDER = '#E2E5E8';

function ChevronRight() {
  return (
    <svg width="8" height="14" viewBox="0 0 8 14">
      <path d="M1 1l6 6-6 6" stroke="#C7CDD2" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

export function RecordsScreen({ s, a }: ScreenProps) {
  if (s.recordsScreen === 'list') {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12, animation: 'vaicFadeUp .25s ease' }}>
        <button onClick={a.goResults} style={{ textAlign: 'left', border: `1px solid ${BORDER}`, borderRadius: 16, padding: 16, background: '#fff', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 16, fontWeight: 700 }}>Kết quả xét nghiệm &amp; CĐHA</span>
            <span style={{ flexShrink: 0, minWidth: 22, height: 22, padding: '0 6px', borderRadius: 999, background: TEAL, color: '#fff', fontSize: 12, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>3</span>
          </div>
          <ChevronRight />
        </button>
        <button onClick={a.goMedications} style={{ textAlign: 'left', border: `1px solid ${BORDER}`, borderRadius: 16, padding: 16, background: '#fff', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 16, fontWeight: 700 }}>Đơn thuốc &amp; nhắc uống</span>
            <span style={{ flexShrink: 0, minWidth: 22, height: 22, padding: '0 6px', borderRadius: 999, background: TEAL, color: '#fff', fontSize: 12, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>2</span>
          </div>
          <ChevronRight />
        </button>
        <button onClick={a.goRecovery} style={{ textAlign: 'left', border: `1px solid ${BORDER}`, borderRadius: 16, padding: 16, background: '#fff', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 16, fontWeight: 700 }}>Theo dõi hồi phục</span>
            <span style={{ flexShrink: 0, minWidth: 22, height: 22, padding: '0 6px', borderRadius: 999, background: TEAL, color: '#fff', fontSize: 12, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>1</span>
          </div>
          <ChevronRight />
        </button>
        <button onClick={a.goVisitSummary} style={{ textAlign: 'left', border: `1px solid ${BORDER}`, borderRadius: 16, padding: 16, background: '#fff', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontSize: 16, fontWeight: 700 }}>Tóm tắt lần khám gần nhất</div>
          </div>
          <ChevronRight />
        </button>
      </div>
    );
  }

  if (s.recordsScreen === 'results') {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12, animation: 'vaicFadeUp .25s ease' }}>
        {RESULTS.map((r) => (
          <button key={r.id} onClick={() => a.openResult(r.id)} style={{ textAlign: 'left', border: `1px solid ${BORDER}`, borderRadius: 16, padding: 16, background: '#fff', cursor: 'pointer', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <div style={{ fontSize: 16, fontWeight: 700 }}>{r.name}</div>
              <div style={{ fontSize: 13, color: MUTED }}>{r.date}</div>
            </div>
            {r.status === 'ok' && (
              <span style={{ fontSize: 12, fontWeight: 700, color: '#2F9D66', background: 'rgba(47,157,102,.1)', padding: '4px 10px', borderRadius: 999 }}>Trong ngưỡng</span>
            )}
            {r.status === 'review' && (
              <span style={{ fontSize: 12, fontWeight: 700, color: '#D9902B', background: 'rgba(217,144,43,.1)', padding: '4px 10px', borderRadius: 999 }}>Cần bác sĩ đọc</span>
            )}
            {r.status === 'pending' && (
              <span style={{ fontSize: 12, fontWeight: 700, color: '#9BA3AB', background: '#F7F8F9', padding: '4px 10px', borderRadius: 999 }}>Đang chờ</span>
            )}
          </button>
        ))}
      </div>
    );
  }

  if (s.recordsScreen === 'resultDetail') {
    const currentResult = RESULTS.find((r) => r.id === s.selectedResult) ?? RESULTS[0];
    const showAiReasoning = true;
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16, animation: 'vaicFadeUp .25s ease' }}>
        <div>
          <div style={{ fontSize: 22, fontWeight: 800 }}>{currentResult.name}</div>
          <div style={{ fontSize: 14, color: MUTED, marginTop: 4 }}>{currentResult.date}</div>
        </div>
        {showAiReasoning && (
          <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start', background: 'rgba(37,99,235,.06)', borderRadius: 14, padding: 14 }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0, marginTop: 2 }}><path d="M12 2l1.6 5.2L19 9l-5.4 1.8L12 16l-1.6-5.2L5 9l5.4-1.8L12 2z" fill={TEAL} /></svg>
            <span style={{ fontSize: 14, color: '#12151A', lineHeight: 1.5 }}>{currentResult.note} Đây là diễn giải chung, hãy hỏi bác sĩ để biết chi tiết.</span>
          </div>
        )}
        <div style={{ border: `1px solid ${BORDER}`, borderRadius: 16, padding: 16, fontSize: 14, color: MUTED, lineHeight: 1.6 }}>Chỉ số chi tiết sẽ hiển thị đầy đủ tại đây kèm tham chiếu, đồng nhất với hồ sơ bác sĩ xem.</div>
      </div>
    );
  }

  if (s.recordsScreen === 'medications') {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12, animation: 'vaicFadeUp .25s ease' }}>
        {MEDICATIONS.map((m) => (
          <div key={m.id} style={{ border: `1px solid ${BORDER}`, borderRadius: 16, padding: 16, background: '#fff', display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div style={{ fontSize: 17, fontWeight: 700 }}>{m.name}</div>
            <div style={{ fontSize: 14, color: MUTED }}>{m.dose}</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: TEAL, fontWeight: 700, fontFamily: "'IBM Plex Mono', monospace" }}>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="9" stroke={TEAL} strokeWidth="1.6" /><path d="M12 7v5l3 2" stroke={TEAL} strokeWidth="1.6" strokeLinecap="round" /></svg>
              {m.remind}
            </div>
            {m.warn && (
              <div style={{ fontSize: 13, color: '#E5484D', fontWeight: 600, background: 'rgba(229,72,77,.08)', padding: '6px 10px', borderRadius: 10 }}>⚠ {m.warn}</div>
            )}
          </div>
        ))}
      </div>
    );
  }

  if (s.recordsScreen === 'recovery') {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16, animation: 'vaicFadeUp .25s ease' }}>
        <div style={{ border: `1px solid ${BORDER}`, borderRadius: 16, padding: 16, background: '#F7F8F9', display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ fontSize: 14, fontWeight: 700, color: TEAL }}>Trợ lý hỏi thăm</div>
          <div style={{ fontSize: 16, fontWeight: 600 }}>Chị có thấy đỡ đau hơn không?</div>
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={a.recoveryBetter} style={{ flex: 1, height: 42, border: 'none', borderRadius: 12, background: '#2F9D66', color: '#fff', fontSize: 14, fontWeight: 700, cursor: 'pointer' }}>Đỡ nhiều</button>
            <button onClick={a.recoveryWorse} style={{ flex: 1, height: 42, border: '1px solid #E5484D', borderRadius: 12, background: '#fff', color: '#E5484D', fontSize: 14, fontWeight: 700, cursor: 'pointer' }}>Vẫn đau</button>
          </div>
        </div>
        <div>
          <div style={{ fontSize: 13, fontWeight: 700, color: '#9BA3AB', textTransform: 'uppercase', marginBottom: 8 }}>Nhật ký triệu chứng</div>
          <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
            <input
              value={s.symptomText}
              onChange={(e) => a.setSymptomText(e.target.value)}
              placeholder="Ghi lại cảm giác hôm nay…"
              style={{ flex: 1, height: 46, borderRadius: 12, border: `1px solid ${BORDER}`, padding: '0 14px', fontSize: 15, fontFamily: 'inherit' }}
            />
            <button onClick={a.addSymptom} style={{ width: 46, height: 46, borderRadius: 12, border: 'none', background: TEAL, color: '#fff', fontSize: 22, cursor: 'pointer' }}>+</button>
          </div>
          {s.recoveryDiary.map((d) => (
            <div key={d.id} style={{ borderBottom: `1px solid ${BORDER}`, padding: '10px 0' }}>
              <div style={{ fontSize: 15 }}>{d.text}</div>
              <div style={{ fontSize: 12, color: '#9BA3AB', marginTop: 2 }}>{d.time}</div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (s.recordsScreen === 'visitSummary') {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16, animation: 'vaicFadeUp .25s ease' }}>
        <div style={{ border: `1px solid ${BORDER}`, borderRadius: 18, padding: 18, display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: MUTED, fontSize: 14 }}>Ngày khám</span><span style={{ fontWeight: 700, fontSize: 14 }}>12/05/2026</span></div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: MUTED, fontSize: 14 }}>Bác sĩ</span><span style={{ fontWeight: 700, fontSize: 14 }}>BS. Lê Thị Hoa</span></div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}><span style={{ color: MUTED, fontSize: 14 }}>Kết luận</span><span style={{ fontWeight: 700, fontSize: 14, textAlign: 'right', maxWidth: '60%' }}>Viêm dạ dày nhẹ</span></div>
        </div>
        <div style={{ border: `1px solid ${BORDER}`, borderRadius: 18, padding: 18 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: '#9BA3AB', textTransform: 'uppercase', marginBottom: 8 }}>Chỉ định đã thực hiện</div>
          <div style={{ fontSize: 15, lineHeight: 1.6, color: '#12151A' }}>Công thức máu · Nội soi dạ dày · Đơn thuốc kháng viêm 5 ngày</div>
        </div>
        <button onClick={a.viewPdf} style={{ height: 52, border: `1px solid ${BORDER}`, borderRadius: 999, background: '#fff', fontSize: 16, fontWeight: 700, cursor: 'pointer' }}>Xem PDF</button>
      </div>
    );
  }

  return null;
}
