/**
 * Mock booking stub (/book, FR-02 capacity validation - TASK-022).
 *
 * No backend exists yet. `listBookableSlots` seeds a small fixed set of
 * slots (one deliberately at zero capacity, to exercise the FR-02
 * capacity-full path); `bookSlot` validates capacity and returns a new
 * `Appointment`, in `BOOKED` status. Booking NEVER creates a `ServiceOrder`
 * - that type does not exist on the patient surface at all; only a doctor
 * path creates one (SCR-03, coding-standards.md "clinical boundary").
 */
import { AppointmentStatus, PaymentStatus } from './types';
import type { Appointment, BookableSlot } from './types';

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

const DEMO_BOOKABLE_SLOTS: BookableSlot[] = [
  {
    slotId: 'book-slot-0001',
    specialty: 'Noi tong quat',
    ownerLabel: 'BS. Le Van C',
    start: '2026-07-19T02:15:00.000Z',
    etaLabel: '~10:15, it dong',
    capacityRemaining: 3,
    aiSuggested: true,
  },
  {
    slotId: 'book-slot-0002',
    specialty: 'Noi tong quat',
    ownerLabel: 'BS. Pham Thi D',
    start: '2026-07-19T03:00:00.000Z',
    etaLabel: '~11:00-11:15',
    capacityRemaining: 1,
    aiSuggested: false,
  },
  {
    slotId: 'book-slot-0003',
    specialty: 'Noi tong quat',
    ownerLabel: 'BS. Le Van C',
    start: '2026-07-19T04:00:00.000Z',
    etaLabel: '~12:00',
    capacityRemaining: 0,
    aiSuggested: false,
  },
];

export class SlotFullError extends Error {
  constructor(slotId: string) {
    super(`slot-full:${slotId}`);
    this.name = 'SlotFullError';
  }
}

/** TODO: replace with a real API call (GET /slots?specialty=... - FR-02). */
export async function listBookableSlots(): Promise<BookableSlot[]> {
  await delay(200);
  return DEMO_BOOKABLE_SLOTS;
}

/**
 * TODO: replace with a real API call (POST /appointments - FR-02 capacity
 * validation). Read-only against the fixture list above: this mock does not
 * mutate shared state between calls, so it stays deterministic across tests.
 */
export async function bookSlot(patientId: string, slotId: string): Promise<Appointment> {
  await delay(200);

  const slot = DEMO_BOOKABLE_SLOTS.find((s) => s.slotId === slotId);
  if (!slot) {
    throw new Error(`slot-not-found:${slotId}`);
  }
  if (slot.capacityRemaining <= 0) {
    throw new SlotFullError(slotId);
  }

  return {
    id: `appt-mock-${slotId}`,
    patientId,
    specialty: slot.specialty,
    status: AppointmentStatus.BOOKED,
    paymentStatus: PaymentStatus.UNPAID,
    slotStart: slot.start,
    createdAt: new Date().toISOString(),
  };
}
