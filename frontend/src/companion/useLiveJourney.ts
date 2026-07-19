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
 * The step mapping (room per service, ordering, active-step marker) is the SHARED
 * `toCarePlanSteps` (lib/api/careplanDisplay), the same one the doctor console renders its care-plan
 * preview with, so the patient's journey and the doctor's view are identical for the same plan.
 *
 * Identity is fixed to the design's patient (Nguyen Thi Lan, whose demo OTP spells 941207), matching
 * `PATIENT_NAME` / `OTP_DIGITS` in `state.ts`; that same `patient_code` is what the console signs
 * orders under, so both surfaces resolve to one backend patient.
 */
import { useEffect, useState } from 'react';
import * as careplanApi from '@/lib/api/careplan';
import { toCarePlanSteps } from '@/lib/api/careplanDisplay';
import type { JourneyStep } from './state';

const COMPANION_PATIENT_CODE = 'BN-941207';

function toJourneySteps(tasks: careplanApi.PatientTaskOut[]): JourneyStep[] {
  return toCarePlanSteps(tasks).map((step) => ({
    id: step.id,
    label: step.serviceLabel,
    time: step.time,
    status: step.status,
    room: step.room,
    directions: step.directions,
    peopleWaiting: step.peopleWaiting,
    queueEtaMinutes: step.queueEtaMinutes,
  }));
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

    // Guards overlapping loads: load() runs on mount and again on every SSE event, so two responses
    // can be in flight at once - only the newest may write, or a slow older read could revert to
    // stale steps.
    let latestLoad = 0;

    (async () => {
      try {
        const { patientId } = await careplanApi.resolvePatient(COMPANION_PATIENT_CODE);

        async function load() {
          const seq = (latestLoad += 1);
          const view = await careplanApi.fetchActiveCarePlan(patientId);
          if (cancelled || seq !== latestLoad) return;
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
