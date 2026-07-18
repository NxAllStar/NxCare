# VAIC frontend

Vite + React + TypeScript + Tailwind CSS + shadcn/ui. This is the design-system scaffold
(TASK-019): plumbing only, no screens yet. The screen build-out (SCR-01..SCR-07, FR-12) lands
in a later task on top of this base.

## Design tokens

`design-tokens.json` (repo root of this package) is the documented source-of-truth for every raw
token value - color scales, semantic status colors, the load heatmap, typography, spacing, radius,
shadow, motion, and component tokens. See `docs/specs/10-ui-ux-wireframes.md` -> "Visual design
direction" for the rationale.

The tokens are wired into the app in two places, and both must stay in sync with
`design-tokens.json` when a value changes:

- `src/index.css` - the same tokens expressed as shadcn/ui CSS variables (HSL triplets), for
  `:root` (light) and `.dark`. This file is the app's CSS entry, imported from `src/main.tsx`.
- `tailwind.config.ts` - the Tailwind theme extension that reads those CSS variables, so classes
  like `bg-primary`, `text-danger`, or `bg-heat-3` resolve to the tokens above and flip
  automatically with the `.dark` class.

Fonts (Inter, IBM Plex Mono) are self-hosted via `@fontsource/*` packages, imported at the top of
`src/index.css` - no runtime call to a font CDN.

## Commands

- `npm install`
- `npm run dev` - Vite dev server
- `npm run build` - `tsc -b` then `vite build`
- `npm run typecheck` - type-check only, no emit
- `npm run preview` - preview the production build
