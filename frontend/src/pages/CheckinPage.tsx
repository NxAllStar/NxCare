/**
 * CheckinPage - /checkin QR / remote check-in (FR-17).
 *
 * DECISION (spec-guardian lock, TASK-022): FR-17's actor list has the
 * patient PRESENT the code and staff (doctor/technician) perform the scan -
 * never the reverse. This screen therefore only DISPLAYS the patient's own
 * code; it deliberately builds NO self-check-in control that flips a
 * Task/Appointment status. Doing so would be drift against FR-17's actor
 * list, so it is not built at all here, rather than built and merely
 * labelled - see the TASK-022 session log.
 */
import { useEffect, useState } from 'react';
import { useI18n } from '@/i18n';
import { useAuth } from '@/auth/AuthContext';
import * as patientApi from '@/lib/api/patient';
import type { Patient } from '@/lib/api/types';
import { PatientCodeQr } from '@/components/primitives/PatientCodeQr';
import { ScreenState, type ViewState } from '@/components/primitives/ScreenState';

export function CheckinPage() {
  const { t } = useI18n();
  const { session } = useAuth();
  const patientId = session?.patient.id;

  const [patient, setPatient] = useState<Patient | null | undefined>(undefined);
  const [loadError, setLoadError] = useState(false);

  useEffect(() => {
    if (!patientId) return;
    let cancelled = false;
    setLoadError(false);
    patientApi
      .getPatient(patientId)
      .then((result) => {
        if (!cancelled) setPatient(result);
      })
      .catch(() => {
        if (!cancelled) setLoadError(true);
      });
    return () => {
      cancelled = true;
    };
  }, [patientId]);

  const viewState: ViewState = loadError ? 'error' : patient === undefined ? 'loading' : patient === null ? 'empty' : 'success';

  return (
    <div className="flex flex-col gap-5 px-5 py-4 animate-fade-up">
      <h1 className="text-[22px] font-bold">{t('checkin.title')}</h1>

      <ScreenState state={viewState}>
        {patient && (
          <div className="flex flex-col items-center gap-5 pt-2">
            <div className="rounded-3xl border border-dashed border-neutral-300 bg-muted p-6">
              <PatientCodeQr code={patient.patientCode} />
            </div>
            <p className="max-w-xs text-center text-[15px] leading-relaxed text-muted-foreground">
              {t('checkin.instructions')}
            </p>
            <p className="w-full rounded-2xl bg-info/10 px-4 py-3 text-center text-xs text-info">
              {t('checkin.demoNote')}
            </p>
          </div>
        )}
      </ScreenState>
    </div>
  );
}
