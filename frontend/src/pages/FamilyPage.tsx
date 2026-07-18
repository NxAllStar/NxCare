/**
 * FamilyPage - /family family-switcher UI SHELL (PMA-M7, TASK-023).
 *
 * DECISION (spec-guardian lock, this task): spec 06 (access control) has no
 * delegated-viewer scope, so this screen never fetches or renders another
 * patient's Own-scope data. Selecting the self profile shows the current
 * patient's own data (via the normal patient.ts path); selecting any other
 * profile only flips a local UI selection to the "not implemented" notice -
 * it never calls a data-fetching function for that other profile at all.
 */
import { useEffect, useState } from 'react';
import { useI18n } from '@/i18n';
import { cn } from '@/lib/utils';
import { useAuth } from '@/auth/AuthContext';
import * as familyApi from '@/lib/api/family';
import * as patientApi from '@/lib/api/patient';
import type { FamilyProfile, Patient } from '@/lib/api/types';
import { Avatar, Card, PatientCodeQr, ScreenState, type ViewState } from '@/components/primitives';

export function FamilyPage() {
  const { t } = useI18n();
  const { session } = useAuth();
  const patientId = session?.patient.id;

  const [profiles, setProfiles] = useState<FamilyProfile[] | null>(null);
  const [loadError, setLoadError] = useState(false);
  const [selectedProfileId, setSelectedProfileId] = useState<string | null>(null);
  const [ownPatient, setOwnPatient] = useState<Patient | null>(null);

  useEffect(() => {
    if (!patientId) return;
    let cancelled = false;
    setLoadError(false);

    familyApi
      .listFamilyProfiles(patientId)
      .then((result) => {
        if (cancelled) return;
        setProfiles(result);
        setSelectedProfileId((prev) => prev ?? result.find((p) => p.isSelf)?.id ?? result[0]?.id ?? null);
      })
      .catch(() => {
        if (!cancelled) setLoadError(true);
      });

    return () => {
      cancelled = true;
    };
  }, [patientId]);

  const selectedProfile = profiles?.find((p) => p.id === selectedProfileId) ?? null;

  useEffect(() => {
    if (!patientId || !selectedProfile?.isSelf) {
      setOwnPatient(null);
      return;
    }
    let cancelled = false;
    patientApi.getPatient(patientId).then((result) => {
      if (!cancelled) setOwnPatient(result);
    });
    return () => {
      cancelled = true;
    };
  }, [patientId, selectedProfile?.isSelf]);

  const viewState: ViewState = loadError
    ? 'error'
    : profiles === null
      ? 'loading'
      : profiles.length === 0
        ? 'empty'
        : 'success';

  return (
    <div className="flex flex-col gap-4 px-5 py-4 animate-fade-up">
      <h1 className="text-[22px] font-bold">{t('family.title')}</h1>

      <ScreenState state={viewState} emptyMessage={t('family.emptyMessage')}>
        <div className="flex flex-col gap-4">
          <div role="group" aria-label={t('family.switcherLabel')} className="flex flex-wrap gap-2">
            {profiles?.map((profile) => {
              const isActive = profile.id === selectedProfileId;
              return (
                <button
                  key={profile.id}
                  type="button"
                  aria-pressed={isActive}
                  onClick={() => setSelectedProfileId(profile.id)}
                  className={cn(
                    'flex items-center gap-2 rounded-pill border py-1.5 pl-1.5 pr-3.5 text-[13px] font-bold transition-colors',
                    isActive
                      ? 'border-primary bg-primary text-primary-foreground'
                      : 'border-border bg-card text-muted-foreground',
                  )}
                >
                  <Avatar name={profile.displayName} size="sm" tone={isActive ? 'neutral' : 'primary'} />
                  <span>
                    {profile.displayName}
                    {profile.isSelf && <span className="ml-1 opacity-70">({t('family.selfBadge')})</span>}
                  </span>
                </button>
              );
            })}
          </div>

          {selectedProfile?.isSelf ? (
            ownPatient && (
              <Card className="flex flex-col items-center gap-3 py-6">
                <span className="text-[15px] font-semibold">{selectedProfile.relationshipLabel}</span>
                <PatientCodeQr code={ownPatient.patientCode} />
              </Card>
            )
          ) : (
            <p className="rounded-2xl bg-warning/10 px-4 py-3 text-[15px] leading-relaxed text-warning">
              {t('family.notImplementedNotice')}
            </p>
          )}
        </div>
      </ScreenState>
    </div>
  );
}
