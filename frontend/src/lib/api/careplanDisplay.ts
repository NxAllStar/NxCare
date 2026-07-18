/**
 * Shared care-plan display mapping (TASK-038), used by BOTH the patient companion journey and the
 * doctor console's care-plan preview, so the two surfaces show the SAME journey for the same plan.
 *
 * The backend routes each task to whichever technician station is least busy, so a task's
 * `resourceId` is not a meaningful room. The room a service happens in is a property of the SERVICE,
 * so it is mapped from `serviceTypeCode` (codes match api/demo_state.py DEMO_SERVICE_CATALOG). Both
 * `/api/careplan/generate`'s `route` and `/api/careplan/patient/{id}/active`'s `tasks` feed the same
 * builder, which is what keeps the doctor's view and the patient's view identical.
 */

export interface CarePlanTaskInput {
  taskId: string;
  serviceTypeCode: string;
  serviceTypeLabel: string;
  start: string | null;
  durationMin: number;
  sequenceIndex: number;
  // `/active` supplies this; `/generate`'s route does not (a freshly proposed route has no execution
  // state yet), so it is optional and absence is treated as not-yet-started. Typed as a plain string
  // so any backend execution status (LOCKED/PENDING/IN_PROGRESS/DONE/CANCELLED) is accepted; only
  // DONE and IN_PROGRESS change the mapped step status, everything else is treated as upcoming.
  executionStatus?: string;
}

export interface CarePlanDisplayStep {
  id: string;
  serviceLabel: string;
  room: string;
  directions?: string;
  time: string;
  durationMin: number;
  status: 'done' | 'active' | 'upcoming';
}

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

export function serviceRoom(serviceTypeCode: string, fallback: string): string {
  return SERVICE_ROOMS[serviceTypeCode] ?? fallback;
}

function timeLabel(iso: string | null, upcoming: boolean, durationMin: number): string {
  if (!iso) return `~${durationMin} phút`;
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return `~${durationMin} phút`;
  const hh = String(date.getUTCHours()).padStart(2, '0');
  const mm = String(date.getUTCMinutes()).padStart(2, '0');
  return `${upcoming ? '~' : ''}${hh}:${mm}`;
}

/**
 * Map backend care-plan tasks to display steps, ordered by sequence. Backend tasks start LOCKED
 * (unpaid), so none is IN_PROGRESS - the first not-done step is marked active to give the timeline a
 * visible current node (matching the design's single active marker); both surfaces get the same.
 */
export function toCarePlanSteps(tasks: CarePlanTaskInput[]): CarePlanDisplayStep[] {
  const ordered = [...tasks].sort((a, b) => a.sequenceIndex - b.sequenceIndex);
  const steps: CarePlanDisplayStep[] = ordered.map((task) => {
    const status: CarePlanDisplayStep['status'] =
      task.executionStatus === 'DONE'
        ? 'done'
        : task.executionStatus === 'IN_PROGRESS'
          ? 'active'
          : 'upcoming';
    return {
      id: task.taskId,
      serviceLabel: task.serviceTypeLabel,
      room: serviceRoom(task.serviceTypeCode, task.serviceTypeLabel),
      directions: SERVICE_DIRECTIONS[task.serviceTypeCode],
      time: timeLabel(task.start, status !== 'done', task.durationMin),
      durationMin: task.durationMin,
      status,
    };
  });
  if (steps.length > 0 && !steps.some((step) => step.status === 'active')) {
    const firstPending = steps.find((step) => step.status !== 'done');
    if (firstPending) firstPending.status = 'active';
  }
  return steps;
}
