/**
 * ConsoleApp - the hospital-facing web console (TASK-026 foundation slice):
 * its own router (basename "/console"), its own I18n and staff-session
 * providers, a desktop-first sidebar shell, and role-gated route stubs for
 * SCR-03..SCR-07. Mounted by src/App.tsx only for paths under /console;
 * every other path keeps rendering PatientCompanionApp untouched.
 */
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { I18nProvider } from '@/i18n';
import { ConsoleIndexRedirect, ConsoleRouteGuard, ScreenGuard } from './auth/ConsoleRouteGuard';
import { StaffAuthProvider } from './auth/StaffAuthContext';
import { ConsoleShell } from './components/ConsoleShell';
import { AdminAuditScreen } from './screens/AdminAuditScreen';
import { ConsoleLoginPage } from './screens/ConsoleLoginPage';
import { ConsultOrdersScreen } from './screens/ConsultOrdersScreen';
import { CoordinatorDashboardScreen } from './screens/CoordinatorDashboardScreen';
import { DoctorWorklistScreen } from './screens/DoctorWorklistScreen';
import { TechnicianTaskScreen } from './screens/TechnicianTaskScreen';

export function ConsoleApp() {
  return (
    <I18nProvider>
      <StaffAuthProvider>
        <BrowserRouter basename="/console">
          <Routes>
            <Route path="/login" element={<ConsoleLoginPage />} />
            <Route element={<ConsoleRouteGuard />}>
              <Route element={<ConsoleShell />}>
                <Route index element={<ConsoleIndexRedirect />} />
                <Route
                  path="/consult"
                  element={
                    <ScreenGuard screen="SCR-03">
                      <ConsultOrdersScreen />
                    </ScreenGuard>
                  }
                />
                <Route
                  path="/worklist"
                  element={
                    <ScreenGuard screen="SCR-04">
                      <DoctorWorklistScreen />
                    </ScreenGuard>
                  }
                />
                <Route
                  path="/tasks"
                  element={
                    <ScreenGuard screen="SCR-05">
                      <TechnicianTaskScreen />
                    </ScreenGuard>
                  }
                />
                <Route
                  path="/dashboard"
                  element={
                    <ScreenGuard screen="SCR-06">
                      <CoordinatorDashboardScreen />
                    </ScreenGuard>
                  }
                />
                <Route
                  path="/audit"
                  element={
                    <ScreenGuard screen="SCR-07">
                      <AdminAuditScreen />
                    </ScreenGuard>
                  }
                />
                <Route path="*" element={<Navigate to="/" replace />} />
              </Route>
            </Route>
          </Routes>
        </BrowserRouter>
      </StaffAuthProvider>
    </I18nProvider>
  );
}
