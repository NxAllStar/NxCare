/**
 * TASK-026 acceptance criteria under test:
 * - "Extend the mock session/role model to a discriminated union covering
 *   staff roles ... WITHOUT changing the shipped patient login/typecheck
 *   path" - proven here by this store living entirely apart from
 *   src/auth/AuthContext.tsx (see StaffAuthContext.test isolation case) and
 *   in App.test.tsx (patient path byte-for-byte unaffected).
 * - "Staff login (role selector, synthetic/demo only - no real
 *   credentials)": `login` takes only a role, never a password.
 */
import { describe, expect, it } from 'vitest';
import { act, renderHook } from '@testing-library/react';
import type { ReactNode } from 'react';
import { STAFF_SESSION_STORAGE_KEY, StaffAuthProvider, useStaffAuth } from './StaffAuthContext';

function wrapper({ children }: { children: ReactNode }) {
  return <StaffAuthProvider>{children}</StaffAuthProvider>;
}

describe('StaffAuthContext (TASK-026: demo staff session store, role selector only)', () => {
  it('starts with no session', () => {
    const { result } = renderHook(() => useStaffAuth(), { wrapper });
    expect(result.current.session).toBeNull();
  });

  it.each(['doctor', 'technician', 'coordinator', 'admin'] as const)(
    'login(%s) issues a session carrying exactly that role',
    async (role) => {
      const { result } = renderHook(() => useStaffAuth(), { wrapper });
      await act(async () => {
        await result.current.login(role);
      });
      expect(result.current.session?.role).toBe(role);
    },
  );

  it('logout clears the session', async () => {
    const { result } = renderHook(() => useStaffAuth(), { wrapper });
    await act(async () => {
      await result.current.login('coordinator');
    });
    await act(async () => {
      await result.current.logout();
    });
    expect(result.current.session).toBeNull();
  });

  it('persists under its own storage key, isolated from the patient session key', async () => {
    const { result } = renderHook(() => useStaffAuth(), { wrapper });
    await act(async () => {
      await result.current.login('admin');
    });
    expect(window.sessionStorage.getItem('vaic.session')).toBeNull();
    expect(window.sessionStorage.getItem(STAFF_SESSION_STORAGE_KEY)).not.toBeNull();
  });
});
