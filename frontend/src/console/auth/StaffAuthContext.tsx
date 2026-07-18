/**
 * Demo staff session/auth for the hospital console (TASK-026, FR-18
 * foundation slice). Deliberately kept apart from the patient
 * `AuthContext`/`Session` (src/auth/AuthContext.tsx, src/lib/api/session.ts)
 * rather than widening the shared `Session['role']` union: this is the
 * "cleanest approach" named in the task, and it makes the hard constraint
 * ("patient Session.role: 'patient' must still typecheck and behave exactly
 * as today") true by construction - the shared file is never touched.
 *
 * Like the patient context, this is a client-side convenience only - the
 * server is the real authorization gate (NFR-SEC-05); a real deployment
 * enforces role/scope again per request regardless of this store (see the
 * task's "Out of scope": server-side authz is owned by agent-core-dev).
 *
 * Demo login is a role selector: no password, no account, no real
 * credential of any kind (agent-guardrails.md "Secrets" and "Personal and
 * sensitive data") - selecting a role is enough to "log in" as a synthetic
 * demo staff member of that role.
 */
import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react';
import type { StaffRole } from '../access';

export const STAFF_SESSION_STORAGE_KEY = 'vaic.console.session';

export interface StaffSession {
  role: StaffRole;
  displayName: string;
  issuedAt: string;
}

// Synthetic demo display names, one per role - never a real person, never a
// credential (agent-guardrails.md).
const DEMO_STAFF_NAME: Record<StaffRole, string> = {
  doctor: 'BS. Lê Văn Minh (demo)',
  technician: 'KTV Trần Thị Hoa (demo)',
  coordinator: 'ĐPV Phạm Thu Hà (demo)',
  admin: 'QT Ngô Đức Anh (demo)',
};

function readStoredSession(): StaffSession | null {
  if (typeof window === 'undefined') return null;
  const raw = window.sessionStorage.getItem(STAFF_SESSION_STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as StaffSession;
  } catch {
    return null;
  }
}

interface StaffAuthContextValue {
  session: StaffSession | null;
  isAuthenticating: boolean;
  login: (role: StaffRole) => Promise<void>;
  logout: () => Promise<void>;
}

const StaffAuthContext = createContext<StaffAuthContextValue | null>(null);

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export function StaffAuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<StaffSession | null>(() => readStoredSession());
  const [isAuthenticating, setIsAuthenticating] = useState(false);

  const login = useCallback(async (role: StaffRole) => {
    setIsAuthenticating(true);
    try {
      await delay(50);
      const next: StaffSession = {
        role,
        displayName: DEMO_STAFF_NAME[role],
        issuedAt: new Date().toISOString(),
      };
      setSession(next);
      if (typeof window !== 'undefined') {
        window.sessionStorage.setItem(STAFF_SESSION_STORAGE_KEY, JSON.stringify(next));
      }
    } finally {
      setIsAuthenticating(false);
    }
  }, []);

  const logout = useCallback(async () => {
    await delay(20);
    setSession(null);
    if (typeof window !== 'undefined') {
      window.sessionStorage.removeItem(STAFF_SESSION_STORAGE_KEY);
    }
  }, []);

  const value = useMemo(
    () => ({ session, isAuthenticating, login, logout }),
    [session, isAuthenticating, login, logout],
  );

  return <StaffAuthContext.Provider value={value}>{children}</StaffAuthContext.Provider>;
}

export function useStaffAuth(): StaffAuthContextValue {
  const ctx = useContext(StaffAuthContext);
  if (!ctx) {
    throw new Error('useStaffAuth must be used within a StaffAuthProvider');
  }
  return ctx;
}

/** Non-throwing session read, mirroring `useOptionalSession` for the patient
 * context, for chrome that may render outside a provider in isolation. */
export function useOptionalStaffSession(): StaffSession | null {
  return useContext(StaffAuthContext)?.session ?? null;
}
