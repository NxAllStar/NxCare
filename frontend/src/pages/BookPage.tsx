/**
 * BookPage - /book slot confirmation flow feeding SCR-02 (FR-02 capacity
 * validation). Booking creates only an `Appointment` (BOOKED); it never
 * creates a `ServiceOrder` - that type has no representation on the
 * patient surface at all (coding-standards.md, the clinical boundary is a
 * doctor-only write, SCR-03).
 */
import { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useI18n } from '@/i18n';
import { cn } from '@/lib/utils';
import { useAuth } from '@/auth/AuthContext';
import * as bookingApi from '@/lib/api/booking';
import type { Appointment, BookableSlot } from '@/lib/api/types';
import { AIChip, Button, buttonVariants, SectionLabel } from '@/components/primitives';
import { ScreenState, type ViewState } from '@/components/primitives/ScreenState';
import { CheckIcon } from '@/components/icons';

type BookingLocationState = { slotId?: string; specialty?: string } | null;

export function BookPage() {
  const { t } = useI18n();
  const { session } = useAuth();
  const location = useLocation() as { state: BookingLocationState };

  const [slots, setSlots] = useState<BookableSlot[] | null>(null);
  const [loadError, setLoadError] = useState(false);
  const [confirmingSlotId, setConfirmingSlotId] = useState<string | null>(null);
  const [bookedAppointment, setBookedAppointment] = useState<Appointment | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoadError(false);
    bookingApi
      .listBookableSlots()
      .then((result) => {
        if (!cancelled) setSlots(result);
      })
      .catch(() => {
        if (!cancelled) setLoadError(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleConfirm(slot: BookableSlot) {
    if (!session) return;
    setConfirmingSlotId(slot.slotId);
    try {
      const appointment = await bookingApi.bookSlot(session.patient.id, slot.slotId);
      setBookedAppointment(appointment);
    } finally {
      setConfirmingSlotId(null);
    }
  }

  const preselectedSlotId = location.state?.slotId;

  const viewState: ViewState = loadError
    ? 'error'
    : slots === null
      ? 'loading'
      : bookedAppointment
        ? 'success'
        : slots.length === 0
          ? 'empty'
          : 'success';

  return (
    <div className="flex flex-col gap-4 px-5 py-4 animate-fade-up">
      <div>
        <h1 className="text-[22px] font-bold">{t('book.title')}</h1>
        <p className="mt-1 text-[15px] text-muted-foreground">{t('book.subtitle')}</p>
      </div>

      <ScreenState state={viewState} emptyMessage={t('book.emptyMessage')}>
        {bookedAppointment ? (
          <div className="flex flex-col items-center gap-3 rounded-3xl border border-success/30 bg-success/10 p-6 text-center">
            <span className="flex h-14 w-14 items-center justify-center rounded-full bg-success/15">
              <CheckIcon className="h-7 w-7 text-success" />
            </span>
            <p className="text-[17px] font-bold text-success">{t('book.successTitle')}</p>
            <Link to="/journey" className={buttonVariants({ variant: 'primary', size: 'md' })}>
              {t('book.goToJourney')}
            </Link>
          </div>
        ) : (
          <div className="flex flex-col gap-3">
            <SectionLabel>{t('book.slotsHeading')}</SectionLabel>
            {slots?.map((slot) => {
              const isFull = slot.capacityRemaining <= 0;
              const isPreselected = slot.slotId === preselectedSlotId;
              return (
                <div
                  key={slot.slotId}
                  data-testid="bookable-slot"
                  className={cn(
                    'flex flex-col gap-3 rounded-2xl border bg-card p-4',
                    isPreselected ? 'border-primary' : 'border-border',
                  )}
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-[15px] font-semibold">
                      {slot.specialty} - {slot.ownerLabel}
                    </span>
                    {slot.aiSuggested && <AIChip />}
                  </div>
                  <span className="font-mono text-sm text-muted-foreground">{slot.etaLabel}</span>
                  {isFull && <p className="text-xs font-medium text-danger">{t('book.capacityFull')}</p>}
                  <Button
                    variant={isFull ? 'subtle' : 'primary'}
                    size="sm"
                    disabled={isFull || confirmingSlotId === slot.slotId}
                    onClick={() => void handleConfirm(slot)}
                  >
                    {confirmingSlotId === slot.slotId ? t('book.confirming') : t('book.confirmButton')}
                  </Button>
                </div>
              );
            })}
          </div>
        )}
      </ScreenState>
    </div>
  );
}
