/**
 * Live journey data for the Patient Companion App (TASK-038).
 *
 * The companion is a faithful 1:1 clone of the owner's design and is otherwise self-contained on
 * static demo data (`JOURNEY_STEPS` in `state.ts`). This hook adds the ONE live seam the demo needs:
 * when a doctor signs orders on the staff console, the backend care plan for this patient appears
 * here immediately over SSE, and the Journey timeline switches from the static design steps to the
 * real backend tasks. With no active plan yet (the initial state), it returns null and the screen
 * keeps rendering the design's static steps exactly as before - so the clone is untouched until a
 * real order exists.
 *
 * Identity is fixed to the design's patient (Nguyen Thi Lan, whose demo OTP spells 941207), matching
 * `PATIENT_NAME` / `OTP_DIGITS` in `state.ts`; that same `patient_code` is what the console signs
 * orders under, so both surfaces resolve to one backend patient.
 */
import { useEffect, useState } from 'react';
import * as careplanApi from '@/lib/api/careplan';
import type { JourneyStep } from './state';

const COMPANION_PATIENT_CODE = 'BN-941207';

// The room a service happens in is a property of the SERVICE, not of the queue-assigned technician
// station (the backend routes by load, so `resourceId` is just whichever station was least busy).
// Mapping by `serviceTypeCode` is what gives each step its real location - "Lấy máu -> Phòng lấy
// máu", "Siêu âm -> Phòng siêu âm" - instead of a generic station label. Codes match the seeded
// catalog (api/demo_state.py DEMO_SERVICE_CATALOG).
const SERVICE_ROOMS: Record<string, string> = {
  BLOOD_TEST: 'Phòng lấy máu – Tầng 1',
  XRAY_CHEST: 'Phòng X-quang – Tầng 1',
  XRAY_ABDOMEN: 'Phòng X-quang – Tầng 1',
  CT_CHEST: 'Phòng CT – Tầng 2',
  ULTRASOUND_ABDOMEN: 'Phòng siêu âm – Tầng 1',
  ENDOSCOPY_GASTRIC: 'Phòng nội soi – Tầng 2',
};

const SERVICE_DIRECTIONS: Record<string, string> = {
  BLOOD_TEST: 'Khu lấy máu ở tầng 1, ngay cạnh quầy tiếp nhận.',
  XRAY_CHEST: 'Phòng X-quang tầng 1, đi thẳng từ khu chờ rồi rẽ phải.',
  XRAY_ABDOMEN: 'Phòng X-quang tầng 1, đi thẳng từ khu chờ rồi rẽ phải.',
  CT_CHEST: 'Phòng CT tầng 2, lên thang máy khu A.',
  ULTRASOUND_ABDOMEN: 'Phòng siêu âm tầng 1, đối diện quầy nước.',
  ENDOSCOPY_GASTRIC: 'Phòng nội soi tầng 2, cạnh thang máy khu A.',
};

function timeLabel(iso: string | null, upcoming: boolean): string {
  if (!iso) return '';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '';
  const hh = String(date.getUTCHours()).padStart(2, '0');
  const mm = String(date.getUTCMinutes()).padStart(2, '0');
  return `${upcoming ? '~' : ''}${hh}:${mm}`;
}

function toJourneySteps(tasks: careplanApi.PatientTaskOut[]): JourneyStep[] {
  const ordered = [...tasks].sort((a, b) => a.sequenceIndex - b.sequenceIndex);
  const steps: JourneyStep[] = ordered.map((task) => {
    const status: JourneyStep['status'] =
      task.executionStatus === 'DONE'
        ? 'done'
        : task.executionStatus === 'IN_PROGRESS'
          ? 'active'
          : 'upcoming';
    return {
      id: task.taskId,
      label: task.serviceTypeLabel,
      time: task.start ? timeLabel(task.start, status !== 'done') : `~${task.durationMin} phút`,
      status,
      room: SERVICE_ROOMS[task.serviceTypeCode] ?? task.serviceTypeLabel,
      directions: SERVICE_DIRECTIONS[task.serviceTypeCode],
    };
  });
  // Backend tasks start LOCKED (unpaid) so none is IN_PROGRESS - give the timeline a visible current
  // step by marking the first not-yet-done step active, mirroring the design's single active node.
  if (steps.length > 0 && !steps.some((step) => step.status === 'active')) {
    const firstPending = steps.find((step) => step.status !== 'done');
    if (firstPending) firstPending.status = 'active';
  }
  return steps;
}

/**
 * Returns the patient's live journey steps, or null when there is no active backend plan (the caller
 * then falls back to the design's static steps). Subscribes to SSE and refetches on every
 * `careplan.updated` push, so a console order shows up here without a manual refresh.
 */
export function useLiveJourney(): { steps: JourneyStep[] | null } {
  const [steps, setSteps] = useState<JourneyStep[] | null>(null);

  useEffect(() => {
    let cancelled = false;
    let closeStream = () => {};

    (async () => {
      try {
        const { patientId } = await careplanApi.resolvePatient(COMPANION_PATIENT_CODE);

        async function load() {
          const view = await careplanApi.fetchActiveCarePlan(patientId);
          if (cancelled) return;
          const rawTasks = view?.rawTasks ?? [];
          setSteps(rawTasks.length > 0 ? toJourneySteps(rawTasks) : null);
        }

        await load();
        if (cancelled) return;
        closeStream = careplanApi.openCarePlanStream(patientId, () => {
          void load();
        });
      } catch {
        // Backend unreachable: keep null so the static design steps render (the clone still works
        // as a standalone demo, exactly as before this seam).
        if (!cancelled) setSteps(null);
      }
    })();

    return () => {
      cancelled = true;
      closeStream();
    };
  }, []);

  return { steps };
}
