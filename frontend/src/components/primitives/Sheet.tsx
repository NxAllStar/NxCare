/**
 * Sheet - a bottom sheet (the family switcher, the notifications panel). A
 * dimmed scrim plus a rounded panel that slides up. Accessible: role
 * dialog, aria-modal, a labelled title, Escape to dismiss, and a scrim
 * click that closes without swallowing panel clicks. Renders nothing when
 * closed.
 */
import { useEffect, type ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface SheetProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  className?: string;
}

export function Sheet({ open, onClose, title, children, className }: SheetProps) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label={title}
      className="absolute inset-0 z-40 flex items-end bg-neutral-900/35"
      onClick={onClose}
    >
      <div
        className={cn(
          'max-h-[75%] w-full overflow-auto rounded-t-3xl bg-card p-5 shadow-sheet animate-sheet-in',
          className,
        )}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mx-auto mb-3 h-1 w-10 rounded-pill bg-border" aria-hidden="true" />
        <h2 className="mb-3 text-base font-bold">{title}</h2>
        {children}
      </div>
    </div>
  );
}
