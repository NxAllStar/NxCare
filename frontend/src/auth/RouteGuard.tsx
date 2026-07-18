/**
 * Route guard (FR-18 AC-18.1): unauthenticated access to any screen other
 * than /login redirects to /login. This is a client-side convenience only
 * - the server is the real authorization gate (NFR-SEC-05); every request
 * a real backend would enforce role/scope again regardless of this guard.
 */
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from './AuthContext';

export function RouteGuard() {
  const { session } = useAuth();
  const location = useLocation();

  if (!session) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return <Outlet />;
}
