/**
 * Toast - the transient dark pill confirmation ("Booked 10:15", "Paid via
 * QR"). `useToast` owns the show/auto-dismiss timer; `<Toast>` renders the
 * message. Announced politely to assistive tech (role status).
 */
import { useCallback, useEffect, useRef, useState } from 'react';

export function useToast(durationMs = 2600) {
  const [toast, setToast] = useState<string | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const showToast = useCallback(
    (message: string) => {
      setToast(message);
      if (timer.current) clearTimeout(timer.current);
      timer.current = setTimeout(() => setToast(null), durationMs);
    },
    [durationMs],
  );

  useEffect(() => () => { if (timer.current) clearTimeout(timer.current); }, []);

  return { toast, showToast };
}

export function Toast({ message }: { message: string | null }) {
  if (!message) return null;
  return (
    <div
      role="status"
      className="pointer-events-none absolute bottom-28 left-1/2 z-50 -translate-x-1/2 rounded-pill bg-neutral-900 px-[18px] py-3 text-sm font-semibold text-white shadow-raised animate-toast-in"
    >
      {message}
    </div>
  );
}
