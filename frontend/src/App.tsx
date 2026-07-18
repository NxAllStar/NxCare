import { PatientCompanionApp } from '@/companion/PatientCompanionApp';
import { ConsoleApp } from '@/console/ConsoleApp';

/**
 * App root. Path-based entry switch (TASK-026): any path starting with
 * `/console` mounts the hospital-facing web console (its own router,
 * providers, and staff session) instead. Every other path renders the
 * faithful 1:1 reproduction of the owner-supplied "Patient Companion App"
 * design (self-contained demo, VN-only, inside an iPhone frame) - see
 * src/companion/ - exactly as before this task. The earlier routed patient
 * app (src/routes, src/pages) remains in the tree but is no longer the
 * entry; this matches the owner's request to clone the design exactly.
 */
function App() {
  const isConsole =
    typeof window !== 'undefined' && window.location.pathname.startsWith('/console');
  if (isConsole) {
    return <ConsoleApp />;
  }

  // Demo shortcut: `?home=1` skips onboarding and opens the in-hospital
  // live-companion home directly (mirrors the design's startScreen prop).
  const startAtHome =
    typeof window !== 'undefined' && new URLSearchParams(window.location.search).has('home');
  return <PatientCompanionApp startAtHome={startAtHome} />;
}

export default App;
