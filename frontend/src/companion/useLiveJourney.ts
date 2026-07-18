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

// Friendly room labels for the seeded demo stations (api/demo_state.py DEMO_CAREPLAN_STATIONS), so
// live steps read like the design's static ones instead of showing a raw UUID.
const STATION_ROOMS: Record<string, string> = {
  '00000000-0000-0000-0000-000000000011': 'Trạm 1 – Tầng 1',
  '00000000-0000-0000-0000-000000000012': 'Trạm 2 – Tầng 1',
  '00000000-0000-0000-0000-000000000013': 'Trạm 3 – Tầng 1',
};

function timeLabel(iso: string, upcoming: boolean): string {
  if (!iso) return '';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return '';
  const hh = String(date.getUTCHours()).padStart(2, '0');
  const mm = String(date.getUTCMinutes()).padStart(2, '0');
  return `${upcoming ? '~' : ''}${hh}:${mm}`;
}

function toJourneySteps(view: careplanApi.CarePlanView): JourneyStep[] {
  return view.tasks.map((task) => {
    const status: JourneyStep['status'] =
      task.executionStatus === 'DONE'
        ? 'done'
        : task.executionStatus === 'IN_PROGRESS'
          ? 'active'
          : 'upcoming';
    return {
      id: task.id,
      label: task.label,
      time: task.createdAt
        ? timeLabel(task.createdAt, status === 'upcoming')
        : `~${task.estimatedDurationMin} phút`,
      status,
      room: STATION_ROOMS[task.ownerId] ?? 'Phòng xét nghiệm',
    };
  });
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
          setSteps(view && view.tasks.length > 0 ? toJourneySteps(view) : null);
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
