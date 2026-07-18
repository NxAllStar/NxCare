/**
 * Mock client-side session/auth context (FR-18, patient path - TASK-021).
 *
 * This is a DEMO session only: it lives in memory (plus a sessionStorage
 * mirror so a page refresh does not silently log the demo user out mid
 * walkthrough). It is not a security boundary - the server is the real
 * gate (NFR-SEC-05); this context only drives client-side routing and UI.
 */
import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react';
import * as sessionApi from '@/lib/api/session';
import type { Session } from '@/lib/api/session';

const STORAGE_KEY = 'vaic.session';

function readStoredSession(): Session | null {
  if (typeof window === 'undefined') return null;
  const raw = window.sessionStorage.getItem(STORAGE_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as Session;
  } catch {
    return null;
  }
}

interface AuthContextValue {
  session: Session | null;
  isAuthenticating: boolean;
  login: (patientCode: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<Session | null>(() => readStoredSession());
  const [isAuthenticating, setIsAuthenticating] = useState(false);

  const login = useCallback(async (patientCode: string, password: string) => {
    setIsAuthenticating(true);
    try {
      const nextSession = await sessionApi.login(patientCode, password);
      setSession(nextSession);
      if (typeof window !== 'undefined') {
        window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(nextSession));
      }
    } finally {
      setIsAuthenticating(false);
    }
  }, []);

  const logout = useCallback(async () => {
    await sessionApi.logout();
    setSession(null);
    if (typeof window !== 'undefined') {
      window.sessionStorage.removeItem(STORAGE_KEY);
    }
  }, []);

  const value = useMemo(
    () => ({ session, isAuthenticating, login, logout }),
    [session, isAuthenticating, login, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}

/**
 * Non-throwing session read for chrome that may render outside a provider
 * (e.g. the shell in isolation tests). Returns null when there is no
 * provider or no active session, so the caller can degrade gracefully
 * instead of crashing.
 */
export function useOptionalSession(): Session | null {
  return useContext(AuthContext)?.session ?? null;
}
