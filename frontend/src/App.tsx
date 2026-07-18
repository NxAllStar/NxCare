import { PatientCompanionApp } from '@/companion/PatientCompanionApp';

/**
 * App root. Renders the faithful 1:1 reproduction of the owner-supplied
 * "Patient Companion App" design (self-contained demo, VN-only, inside an
 * iPhone frame) - see src/companion/. The earlier routed patient app
 * (src/routes, src/pages) remains in the tree but is no longer the entry;
 * this matches the owner's request to clone the design exactly.
 */
function App() {
  // Demo shortcut: `?home=1` skips onboarding and opens the in-hospital
  // live-companion home directly (mirrors the design's startScreen prop).
  const startAtHome =
    typeof window !== 'undefined' && new URLSearchParams(window.location.search).has('home');
  return <PatientCompanionApp startAtHome={startAtHome} />;
}

export default App;
