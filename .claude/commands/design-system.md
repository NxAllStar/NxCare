---
description: Surface the consolidated VAIC design system - direction, concrete tokens, and patient-app IA - in one shot before any UI work.
argument-hint: "[optional focus, e.g. palette | typography | heatmap | patient]"
---

Load and present the VAIC design system so a UI task starts from the settled sources, not a guess.
Read the authoritative files below, then give a concise synthesis. If **$1** is provided, focus the
synthesis on that aspect (palette, typography, heatmap, motion, patient surface, etc.) but still list
every source so nothing is silently dropped. Do NOT restate whole accepted tables verbatim - link to
them and summarise; the linked files remain the contract.

## The three authoritative layers

1. **Direction (the contract, spec).**
   [`docs/specs/10-ui-ux-wireframes.md` -> "Visual design direction"](../../docs/specs/10-ui-ux-wireframes.md#visual-design-direction).
   The app-wide, build-stable direction: component kit (Tailwind + shadcn/ui), palette intent (calm
   clinical neutral base + one trustworthy teal/blue primary; semantic status green/amber/red/blue;
   sequential green->amber->red load heatmap), typography (one humanist sans, tabular numerals),
   tone, AI-content treatment (NFR-USE-05 "AI" chip), signature surfaces, motion, theme, and
   responsiveness. This section deliberately does NOT pin hex/spacing - it defers them to layer 2.

2. **Concrete tokens (the build-time values, now recorded in the frontend code).**
   These fulfil the spec's deferred promise ("chosen at build time by `frontend-ui-dev` and recorded
   once in the frontend code"). All under `frontend/`:
   - [`frontend/design-tokens.json`](../../frontend/design-tokens.json) - the documented
     source-of-truth for every raw token value: neutral/primary scales, semantic status, the load
     heatmap, typography (Inter + IBM Plex Mono), spacing, radius, shadow, motion, component tokens.
   - [`frontend/src/index.css`](../../frontend/src/index.css) - the same tokens as shadcn/ui CSS
     variables (HSL triplets) for `:root` (light) and `.dark`; the app CSS entry, imported from
     `src/main.tsx`. Self-hosted fonts imported here (`@fontsource/*`, no font CDN).
   - [`frontend/tailwind.config.ts`](../../frontend/tailwind.config.ts) - the Tailwind theme reading
     those CSS variables, so `bg-primary`, `text-danger`, `bg-heat-3`, `font-mono`, etc. resolve to
     the tokens and flip with the `.dark` class.
   - [`frontend/README.md`](../../frontend/README.md) - how the three stay in sync.

   Invariant: `design-tokens.json` is the source of truth; when a value changes, `index.css` and
   `tailwind.config.ts` are updated to match it. Build a UI from these primitives, never a one-off
   style where a token exists.

3. **Patient-app screen-level detail (the IA / sitemap / golden path).**
   [`docs/requirements/PRD-FR-12-patient-mobile-app.md`](../../docs/requirements/PRD-FR-12-patient-mobile-app.md).
   The 5-tab nav, Home dual-mode (dashboard / Live Companion), module-to-screen mapping (M1-M10),
   and per-screen P0/P1/P2 priority for the patient mobile surface. Spec 10 remains the app-wide
   contract and governs where the two differ (see the PRD's section 6 and the spec-10 note).

## Guardrails to carry into the UI work

- Model-produced content always carries the "AI" chip/label and is visually distinct from confirmed
  facts (NFR-USE-05). No emoji anywhere - SVG icons only. WCAG 2.1 AA contrast in both themes
  (NFR-USE-02). Patient views mobile-first, staff/coordinator views desktop-first.
- Screen and feature build-out (SCR-01..SCR-07, FR-12) is TASK-011 / TASK-015, not this command's
  job. This command surfaces the system; it does not build screens.
