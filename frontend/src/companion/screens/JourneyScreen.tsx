/**
 * JourneyScreen - patient journey timeline and per-step detail. Transcribed
 * 1:1 from the design's isJourneyTimeline / isJourneyStep blocks.
 */
import { JOURNEY_STEPS, type JourneyStep, type ScreenProps } from '../state';
import { useLiveJourney } from '../useLiveJourney';

// Live queue wait when the backend supplied it (`peopleWaiting`/`queueEtaMinutes`, from
// service_queue_overview); the static design steps have neither field, so this falls back to
// the design's original copy rather than showing a wrong or missing number.
function waitText(step: JourneyStep): string {
  if (step.peopleWaiting === undefined || step.queueEtaMinutes === undefined) {
    return 'Phía trước còn 2 người · chờ khoảng 8–10 phút.';
  }
  if (step.peopleWaiting === 0) {
    return 'Không có ai phía trước, sắp đến lượt bạn.';
  }
  return `Phía trước còn ${step.peopleWaiting} người · chờ khoảng ${step.queueEtaMinutes} phút.`;
}

export function JourneyScreen({ s, a }: ScreenProps) {
  // Live backend plan (TASK-038) when a doctor has signed orders for this patient; otherwise the
  // design's static steps, so the clone renders unchanged until a real order exists.
  const { steps: liveSteps } = useLiveJourney();
  const steps = liveSteps ?? JOURNEY_STEPS;
  const activeStep = steps.find((j) => j.status === 'active') ?? steps[0];

  if (s.journeyScreen === 'timeline') {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 18, animation: 'vaicFadeUp .25s ease' }}>
        <div style={{ background: '#F7F8F9', borderRadius: 20, padding: 18 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: '#2563EB', textTransform: 'uppercase' }}>Đang diễn ra</div>
          <div style={{ fontSize: 20, fontWeight: 800, marginTop: 4 }}>{activeStep.label}</div>
          <div style={{ fontSize: 14, color: '#5A626B', marginTop: 2 }}>{activeStep.room} · dự kiến {activeStep.time}</div>
          <div style={{ fontSize: 13, color: '#5A626B', marginTop: 6 }}>{waitText(activeStep)}</div>
        </div>

        <button onClick={a.toggleWhy} style={{ alignSelf: 'flex-start', height: 38, padding: '0 14px', borderRadius: 999, border: '1px solid #E2E5E8', background: '#fff', fontSize: 13, fontWeight: 700, cursor: 'pointer' }}>Vì sao thứ tự này?</button>
        {s.whyOpen && (
          <div style={{ fontSize: 14, color: '#5A626B', lineHeight: 1.5, background: 'rgba(37,99,235,.06)', borderRadius: 14, padding: 14 }}>X-quang và siêu âm đều ở tầng 1, gần khu chờ hiện tại nên làm trước để bạn đỡ di chuyển. Khám lại với bác sĩ để cuối vì cần đủ hai kết quả này.</div>
        )}

        <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
          {steps.map((js) => (
            <button key={js.id} onClick={() => a.openStep(js.id)} style={{ textAlign: 'left', border: 'none', background: 'none', cursor: 'pointer', display: 'flex', gap: 14, padding: '10px 0' }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0 }}>
                {js.status === 'done' && (
                  <div style={{ width: 26, height: 26, borderRadius: 999, background: '#2F9D66', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    <svg width="13" height="13" viewBox="0 0 24 24" fill="none"><path d="M5 13l4 4 10-10" stroke="#fff" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" /></svg>
                  </div>
                )}
                {js.status === 'active' && (
                  <div style={{ width: 26, height: 26, borderRadius: 999, background: '#2563EB', boxShadow: '0 0 0 4px rgba(37,99,235,.15)' }} />
                )}
                {js.status === 'upcoming' && (
                  <div style={{ width: 26, height: 26, borderRadius: 999, border: '2px solid #C7CDD2' }} />
                )}
                <div style={{ width: 2, flex: 1, background: '#E2E5E8', marginTop: 4 }} />
              </div>
              <div style={{ flex: 1, paddingBottom: 18 }}>
                <div style={{ fontSize: 16, fontWeight: 700 }}>{js.label}</div>
                <div style={{ fontSize: 13, color: '#5A626B', marginTop: 2 }}>{js.room} · {js.time}</div>
              </div>
              <svg width="8" height="14" viewBox="0 0 8 14" style={{ marginTop: 6 }}><path d="M1 1l6 6-6 6" stroke="#C7CDD2" strokeWidth="2" fill="none" strokeLinecap="round" strokeLinejoin="round" /></svg>
            </button>
          ))}
        </div>
      </div>
    );
  }

  // journeyScreen === 'step'
  const currentStepDetail = steps.find((j) => j.id === s.journeyStepId) ?? activeStep;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16, animation: 'vaicFadeUp .25s ease' }}>
      <div style={{ height: 160, borderRadius: 18, background: '#F7F8F9', border: '1px solid #E2E5E8', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <svg width="90" height="90" viewBox="0 0 24 24" fill="none"><path d="M12 21s7-6.6 7-12a7 7 0 10-14 0c0 5.4 7 12 7 12z" stroke="#2563EB" strokeWidth="1.5" /><circle cx="12" cy="9" r="2.6" stroke="#2563EB" strokeWidth="1.5" /></svg>
      </div>
      <div>
        <div style={{ fontSize: 20, fontWeight: 800 }}>{currentStepDetail.label}</div>
        <div style={{ fontSize: 15, color: '#5A626B', marginTop: 4 }}>{currentStepDetail.room} · dự kiến {currentStepDetail.time}</div>
      </div>
      {currentStepDetail.directions && (
        <div style={{ border: '1px solid #E2E5E8', borderRadius: 16, padding: 16 }}>
          <div style={{ fontSize: 13, fontWeight: 700, color: '#9BA3AB', textTransform: 'uppercase', marginBottom: 8 }}>Chỉ đường</div>
          <div style={{ fontSize: 15, lineHeight: 1.6 }}>{currentStepDetail.directions}</div>
        </div>
      )}
      <div style={{ fontSize: 14, color: '#5A626B', background: 'rgba(37,99,235,.06)', borderRadius: 14, padding: 14, lineHeight: 1.5 }}>{waitText(currentStepDetail)}</div>
    </div>
  );
}
