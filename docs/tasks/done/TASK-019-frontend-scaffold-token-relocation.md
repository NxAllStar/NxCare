---
title: "TASK-019: Scaffold frontend/ (Vite+React+TS+Tailwind+shadcn) and relocate design tokens"
status: Done
fr: FR-12
owner: frontend-ui-dev
deps: "-"
priority: P2
phase: 2
created: 2026-07-18
tags: [task]
---

<!-- Task files are written 100% in English (see .claude/rules/task-tracking.md). -->

# TASK-019: Scaffold frontend/ and relocate design tokens

A status change is written in BOTH places at once: the `status:` field above, and this task's row
in `docs/tasks/master-plan.md`. They must never disagree.

## Goal

Create the FIRST `frontend/` scaffold - Vite + React + TypeScript + Tailwind + shadcn/ui WIRING ONLY,
no screens or features - and relocate the three stray token files from the repo root into it so the
spec's deferred promise (tokens "recorded once in the frontend code") is fulfilled and actually takes
effect.

## Inputs and context

- Related FR: [FR-12](../../specs/05-functional-requirements.md#fr-12) and spec 10 "Visual design
  direction" (tokens deferred to frontend-ui-dev at build time).
- Tech stack: `docs/context` / tech-stack - React (Vite + TypeScript), Tailwind CSS + shadcn/ui, one
  responsive role-gated app (patient mobile-first, staff/coordinator desktop-first), i18n VI+EN.
- Source files (repo root, untracked, to be relocated):
  - `design-tokens.json` - concrete tokens (neutral/primary/semantic/heatmap scales, Inter + IBM
    Plex Mono, spacing, radius, shadow, motion, component tokens). Keep as documented source-of-truth.
  - `globals.css` - the same tokens as shadcn/ui CSS variables (HSL triplets), light + `.dark`,
    Tailwind directives, tabular-nums utility.
  - `tailwind.config.ts` - Tailwind theme reading those CSS variables.
- Rules: `.claude/rules/frontend.md`, `.claude/rules/agent-guardrails.md`.

## To do

- [x] Scaffold a minimal `frontend/` per the tech stack: Vite + React + TS, Tailwind configured,
      shadcn/ui wiring (components.json, utils `cn`, path alias). NO screens, NO feature components,
      NO routing/i18n build-out - plumbing only.
- [x] Relocate the three files using PLAIN `mv` (they are untracked; `git mv` errors). Do NOT run
      `git add`, `git commit`, or `git mv`. Target locations:
      - `globals.css` -> the app CSS entry (e.g. `frontend/src/styles/globals.css` or
        `frontend/src/index.css` per shadcn/ui + Vite convention), imported from `main.tsx`.
      - `tailwind.config.ts` -> `frontend/tailwind.config.ts`.
      - `design-tokens.json` -> a documented location inside `frontend/` (e.g.
        `frontend/design-tokens.json` or `frontend/src/styles/`) referenced as the token
        source-of-truth by both the CSS and a short README note.
- [x] IMPORTANT ADAPTATION: `tailwind.config.ts` as authored assumes Next.js (`darkMode: ["class"]`
      is fine, but `content` globs `./app/**`, `./components/**`, `./pages/**` and the header comment
      reference `app/globals.css`). Our stack is Vite, not Next.js. Update `content` to the Vite
      layout (`./index.html`, `./src/**/*.{ts,tsx}`) and the comment to point at the real CSS path.
      Keep the theme extension (colors, radius, fonts, spacing, shadows) intact.
- [x] Ensure `tailwindcss-animate` (referenced in the config plugins) is added as a dependency, or
      swap it for an equivalent already available. The config must not reference a missing plugin.
- [x] Wire it so the tokens TAKE EFFECT: globals.css imported, Tailwind picking up the CSS variables,
      Inter + IBM Plex Mono fonts loadable, `.dark` class switching. A dev build/typecheck runs clean.

## Acceptance criteria

- [x] `design-tokens.json`, `globals.css`, `tailwind.config.ts` no longer exist at the repo root;
      they live in their correct locations inside `frontend/`.
- [x] `frontend/` builds/typechecks with no screen or feature code (plumbing only).
- [x] `tailwind.config.ts` `content` globs match the Vite layout and reference no missing plugin;
      globals.css is imported from the app entry so the CSS variables are live.
- [x] The three color systems (semantic status, load heatmap, neutral/primary scales), the two fonts,
      and light/`.dark` switching are wired and reachable from Tailwind classes.
- [x] No screens/features/routes/i18n build-out added (that is TASK-011/TASK-015, out of scope here).
- [x] No secrets, no real personal data; no `git add`/commit performed.

## Decisions and blockers

- CSS entry path: `frontend/src/index.css` (Vite's default CSS entry name, imported from
  `src/main.tsx`; matches `components.json` -> `tailwind.css`). `design-tokens.json` lives at
  `frontend/design-tokens.json` (package root), documented as source-of-truth in `frontend/README.md`.
- This scaffold is the design-system PLUMBING prerequisite for the broader FR-12 screen build-out
  (TASK-011) and the app-shell/nav/i18n task (TASK-015); it does not implement either.
- Toolchain note: the sandbox's default `node` on PATH is v12.22.9 (too old for Vite). Used a
  pre-existing Node 20.16.0 + npm 10.9.2 toolchain at `/data_hdd_16t/duydang/tools/node20/bin`
  (shared machine tool, not installed by this task) to scaffold, install, and build. Pinned
  `vite@^6.4.0` and `@vitejs/plugin-react@^4.7.0` (not the create-vite default `vite@8`/`oxlint`,
  which require Node >=20.19 and would fail under this sandbox's available Node 20.16.0); dropped
  `oxlint` entirely rather than ship a linter with an unmet engine requirement - no lint tooling was
  requested in scope. Fonts are self-hosted via `@fontsource/inter` and `@fontsource/ibm-plex-mono`,
  scoped to the `latin` + `vietnamese` subsets only (NFR-USE-03: VI default, EN toggle) rather than
  every unicode-range subset the packages ship by default, to keep the bundle lean.
- `App.tsx` was replaced with a minimal, clearly-commented token-wiring smoke test (status colors,
  heat-1..6 swatches, light/dark toggle, tabular-nums) - not a product screen. It exists only to make
  the "wired and reachable from Tailwind classes" acceptance criterion demonstrable; TASK-011 replaces
  it when the real screens land.

## Session log

| Date | Who | What was done | Result |
|------|-----|---------------|--------|
| 2026-07-18 | orchestrator | Registered task; dispatched frontend-ui-dev for Phase 2 scaffold | Planned -> Active |
| 2026-07-18 | frontend-ui-dev | Read task file + the 3 root source files (design-tokens.json, globals.css, tailwind.config.ts) and frontend.md | Confirmed scope; no frontend/ existed yet (first scaffold) |
| 2026-07-18 | frontend-ui-dev | Located a working Node 20.16.0 + npm 10.9.2 toolchain on the shared machine (default `node` on PATH is v12.22.9); ran `npm create vite@latest frontend -- --template react-ts` | frontend/ scaffolded (Vite 8 + React 19 + TS by default) |
| 2026-07-18 | frontend-ui-dev | Downgraded `vite` to ^6.4.0 and `@vitejs/plugin-react` to ^4.7.0 (Vite 8/oxlint require Node >=20.19, unavailable here); removed oxlint and demo assets (App.css, react/vite logos, hero.png, icons.svg) | Scaffold trimmed to plumbing-only |
| 2026-07-18 | frontend-ui-dev | Added Tailwind v3 + shadcn/ui wiring: `postcss.config.js`, `components.json`, `src/lib/utils.ts` (`cn`), `@` path alias in `vite.config.ts` + both tsconfig files; added `tailwindcss-animate`, `class-variance-authority`, `clsx`, `tailwind-merge`, `@fontsource/inter`, `@fontsource/ibm-plex-mono` as dependencies | Plumbing complete |
| 2026-07-18 | frontend-ui-dev | `mv` (plain, not `git mv` - files are untracked) globals.css -> frontend/src/index.css, tailwind.config.ts -> frontend/tailwind.config.ts, design-tokens.json -> frontend/design-tokens.json | Verified via `ls` at repo root: none of the three remain there |
| 2026-07-18 | frontend-ui-dev | Edited tailwind.config.ts: `content` globs `./app/**` `./components/**` `./pages/**` -> `./index.html` `./src/**/*.{ts,tsx}`; header comment `app/globals.css` -> `src/index.css`; theme extension (colors, radius, fonts, spacing, shadows) left intact | Vite adaptation done |
| 2026-07-18 | frontend-ui-dev | Updated src/index.css header comment to reference the real path and design-tokens.json as source-of-truth; scoped @fontsource imports to latin+vietnamese subsets only; wrote frontend/README.md documenting design-tokens.json as source-of-truth | Tokens documented once, in frontend code |
| 2026-07-18 | frontend-ui-dev | Replaced the create-vite demo App.tsx with a minimal, commented token-wiring smoke test (status colors, heat-1..6, dark toggle, tabular-nums font-mono) | No screens/features added, per scope |
| 2026-07-18 | frontend-ui-dev | Ran `npm install` in frontend/ (using the Node 20 toolchain) | 142 packages installed, 0 vulnerabilities, no EBADENGINE warnings |
| 2026-07-18 | frontend-ui-dev | Ran `npm run typecheck` (`tsc -b --noEmit`) | Clean, no errors |
| 2026-07-18 | frontend-ui-dev | Ran `npm run build` (`tsc -b && vite build`) | Clean build; verified CSS variables, semantic colors, heatmap classes, and both fonts (latin+vietnamese subsets) are emitted into dist/assets |
| 2026-07-18 | frontend-ui-dev | Ran `npm run dev -- --port 5199` in the background, curled `http://localhost:5199/` and `/src/index.css` | HTTP 200; served CSS confirmed to be the relocated globals.css content; dev server stopped afterward |
| 2026-07-18 | frontend-ui-dev | Removed the build's `dist/` output and confirmed `git status` shows `frontend/` only as an untracked directory (no `git add`/`git commit` run) | Guardrails self-check passed; task file and master-plan updated to Done in this same change |

## Result

`frontend/` scaffolded as Vite + React 19 + TypeScript + Tailwind CSS v3 + shadcn/ui wiring
(plumbing only, no screens/routes/i18n). The three root token files were relocated with plain `mv`
into `frontend/design-tokens.json`, `frontend/src/index.css` (the app CSS entry, imported from
`src/main.tsx`), and `frontend/tailwind.config.ts` (content globs and header comment adapted from
the authored Next.js assumption to the real Vite layout; `tailwindcss-animate` added as a
dependency so no plugin reference is missing). None of the three remain at the repo root.
`npm run typecheck` and `npm run build` both run clean; a background `npm run dev` smoke test served
HTTP 200 with the relocated CSS. No screen/feature/route/i18n code was added - that is TASK-011 and
TASK-015. No `git add`/commit was performed.
