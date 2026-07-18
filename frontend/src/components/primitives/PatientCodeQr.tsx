/**
 * PatientCodeQr - the patient's own code, displayed for STAFF to scan
 * (FR-17: the patient presents the code; the doctor/technician performs the
 * scan - never the reverse). Shared by /checkin and /journey (SCR-02).
 *
 * This renders a deterministic, code-derived visual grid, not a real
 * scannable QR encoding: adding a QR-generation library is a dependency /
 * licensing decision this task does not make on its own (ip-compliance.md
 * "Dependency licences"). The functional identifier for this demo is the
 * human-readable `code` text underneath the pattern.
 */
import { useI18n } from '@/i18n';
import { cn } from '@/lib/utils';

interface PatientCodeQrProps {
  code: string;
  className?: string;
}

const GRID_SIZE = 6;

// A tiny deterministic hash so the same code always renders the same
// pattern, and different codes visibly differ (no crypto claim intended).
function cellIsFilled(code: string, index: number): boolean {
  let hash = 0;
  for (let i = 0; i < code.length; i += 1) {
    hash = (hash * 31 + code.charCodeAt(i) + index) % 997;
  }
  return hash % 2 === 0;
}

export function PatientCodeQr({ code, className }: PatientCodeQrProps) {
  const { t } = useI18n();
  const cells = Array.from({ length: GRID_SIZE * GRID_SIZE }, (_, index) => cellIsFilled(code, index));

  return (
    <div
      role="img"
      aria-label={`${t('patientCode.ariaLabel')}: ${code}`}
      className={cn('flex flex-col items-center gap-3', className)}
    >
      <div
        data-testid="patient-code-qr-pattern"
        className="grid gap-0.5 rounded-md border border-border bg-card p-3"
        style={{ gridTemplateColumns: `repeat(${GRID_SIZE}, minmax(0, 1fr))` }}
        aria-hidden="true"
      >
        {cells.map((filled, index) => (
          <span
            key={index}
            className={cn('h-3 w-3 rounded-[2px]', filled ? 'bg-foreground' : 'bg-transparent')}
          />
        ))}
      </div>
      <span className="font-mono text-sm font-semibold tracking-wide">{code}</span>
    </div>
  );
}
