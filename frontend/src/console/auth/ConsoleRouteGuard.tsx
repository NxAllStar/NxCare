/**
 * Client-side route guards for the console (TASK-026). UX convenience only
 * - the server is the real authorization gate (NFR-SEC-05); server-side
 * authz (FR-18 AC-18.3, BR-28) is explicitly out of scope for this task
 * (owned by agent-core-dev, src/vaic/auth/).
 */
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import type { ReactNode } from 'react';
import { canAccessScreen, defaultPathForRole, type ConsoleScreenId } from '../access';
import { useStaffAuth } from './StaffAuthContext';

/** No staff session -> /console/login (mirrors the patient RouteGuard). */
export function ConsoleRouteGuard() {
  const { session } = useStaffAuth();
  const location = useLocation();

  if (!session) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return <Outlet />;
}

/**
 * A staff session exists but its role is not permitted to `screen` (the
 * locked contract table in access.ts) -> redirected to that role's own
 * default screen. A role is never left rendering a route it cannot reach.
 */
export function ScreenGuard({ screen, children }: { screen: ConsoleScreenId; children: ReactNode }) {
  const { session } = useStaffAuth();

  if (!session) {
    return <Navigate to="/login" replace />;
  }

  if (!canAccessScreen(session.role, screen)) {
    return <Navigate to={defaultPathForRole(session.role)} replace />;
  }

  return <>{children}</>;
}

/** /console index route: send the signed-in role straight to its own
 * default screen (the first entry of its permitted set). */
export function ConsoleIndexRedirect() {
  const { session } = useStaffAuth();
  if (!session) {
    return <Navigate to="/login" replace />;
  }
  return <Navigate to={defaultPathForRole(session.role)} replace />;
}
