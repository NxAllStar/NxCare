/**
 * The patient-only route table (TASK-021 foundation, TASK-022 P0 screens,
 * TASK-023 P1 screens).
 *
 * The P0 golden-path routes and the P1 routes below all render their real
 * screen component; every remaining (P2) route still renders
 * PlaceholderScreen - those stay non-functional stubs, out of scope per
 * PRD-FR-12 3, "Out of scope".
 *
 * /login is unguarded; every other route sits behind RouteGuard (FR-18
 * AC-18.1: unauthenticated access to a non-login route redirects to
 * /login), and is rendered inside AppShell (5-tab nav + FAB).
 */
import type { ComponentType } from 'react';
import { Navigate, type RouteObject } from 'react-router-dom';
import { AppShell } from '@/components/shell/AppShell';
import { RouteGuard } from '@/auth/RouteGuard';
import { LoginPage } from '@/pages/LoginPage';
import { PlaceholderScreen } from '@/pages/PlaceholderScreen';
import { HomePage } from '@/pages/HomePage';
import { IntakePage } from '@/pages/IntakePage';
import { BookPage } from '@/pages/BookPage';
import { CheckinPage } from '@/pages/CheckinPage';
import { JourneyPage } from '@/pages/JourneyPage';
import { AssistantPage } from '@/pages/AssistantPage';
import { NotificationsPage } from '@/pages/NotificationsPage';
import { SettingsPage } from '@/pages/SettingsPage';
import { JourneyStepPage } from '@/pages/JourneyStepPage';
import { ResultsPage } from '@/pages/ResultsPage';
import { MedicationsPage } from '@/pages/MedicationsPage';
import { RecoveryPage } from '@/pages/RecoveryPage';
import { BillingPage } from '@/pages/BillingPage';
import { FamilyPage } from '@/pages/FamilyPage';
import { PrepPage } from '@/pages/PrepPage';

// TASK-022 (P0) and TASK-023 (P1) real screens: path -> component,
// replacing PlaceholderScreen for exactly these routes. Every other route
// in ALL_SCREEN_ROUTES (the P2 set) still falls through to PlaceholderScreen.
const SCREEN_COMPONENTS: Record<string, ComponentType> = {
  '/home': HomePage,
  '/intake': IntakePage,
  '/book': BookPage,
  '/checkin': CheckinPage,
  '/journey': JourneyPage,
  '/journey/step/:id': JourneyStepPage,
  '/assistant': AssistantPage,
  '/notifications': NotificationsPage,
  '/settings': SettingsPage,
  '/results': ResultsPage,
  '/medications': MedicationsPage,
  '/recovery': RecoveryPage,
  '/billing': BillingPage,
  '/family': FamilyPage,
  '/prep/:id': PrepPage,
};

interface ScreenRouteDef {
  path: string;
  title: string;
  priority: 'P0' | 'P1' | 'P2';
}

// P0 - the golden path (TASK-022).
const P0_ROUTES: ScreenRouteDef[] = [
  { path: '/home', title: '/home - SCR home (dual-mode)', priority: 'P0' },
  { path: '/intake', title: '/intake - SCR-01 Intake chat', priority: 'P0' },
  { path: '/book', title: '/book - booking wizard', priority: 'P0' },
  { path: '/checkin', title: '/checkin - QR / remote check-in', priority: 'P0' },
  { path: '/journey', title: '/journey - SCR-02 Journey timeline', priority: 'P0' },
  { path: '/journey/step/:id', title: '/journey/step/:id - step detail / wayfinding', priority: 'P1' },
  { path: '/assistant', title: '/assistant - Journey Agent chat (FAB)', priority: 'P0' },
];

// P1 - differentiator screens (TASK-023).
const P1_ROUTES: ScreenRouteDef[] = [
  { path: '/notifications', title: '/notifications - SCR-09 Notifications center', priority: 'P1' },
  { path: '/settings', title: '/settings - SCR-10 Settings', priority: 'P1' },
  { path: '/results', title: '/results - lab/imaging results', priority: 'P1' },
  { path: '/medications', title: '/medications - prescriptions and reminders', priority: 'P1' },
  { path: '/recovery', title: '/recovery - recovery tracking', priority: 'P1' },
  { path: '/billing', title: '/billing - viện phí & BHYT (display-only)', priority: 'P1' },
  { path: '/family', title: '/family - family care', priority: 'P1' },
  { path: '/prep/:id', title: '/prep/:id - proactive prep', priority: 'P1' },
];

// P2 - vision-only, non-functional stubs (out of scope, PRD-FR-12 3 "Out of scope").
const P2_ROUTES: ScreenRouteDef[] = [
  { path: '/welcome', title: '/welcome - onboarding intro (vision only)', priority: 'P2' },
  { path: '/telehealth', title: '/telehealth - video consult (vision only)', priority: 'P2' },
  { path: '/emergency', title: '/emergency - narrow-scope emergency (vision only)', priority: 'P2' },
  { path: '/wellness', title: '/wellness - preventive care (out of scope)', priority: 'P2' },
  { path: '/journey/updates', title: '/journey/updates - re-plan history (vision only)', priority: 'P2' },
];

export const ALL_SCREEN_ROUTES = [...P0_ROUTES, ...P1_ROUTES, ...P2_ROUTES];

export const routes: RouteObject[] = [
  { path: '/login', element: <LoginPage /> },
  {
    element: <RouteGuard />,
    children: [
      {
        element: <AppShell />,
        children: [
          { index: true, element: <Navigate to="/home" replace /> },
          ...ALL_SCREEN_ROUTES.map((route) => {
            const ScreenComponent = SCREEN_COMPONENTS[route.path];
            return {
              path: route.path,
              element: ScreenComponent ? (
                <ScreenComponent />
              ) : (
                <PlaceholderScreen title={route.title} priority={route.priority} />
              ),
            };
          }),
        ],
      },
    ],
  },
];
