---
paths:
  - "src/vaic/**/*.py"
  - "frontend/src/**/*.{ts,tsx}"
  - "tests/**/*.py"
  - "e2e/**/*.ts"
  - "pyproject.toml"
  - "frontend/package.json"
---
# Tech stack

Derived from `docs/specs/12-technical-feasibility.md` (technical approach). Where a choice is not yet
ratified it is marked and carries an open issue - do not silently pick one.

## Backend and agents (Python)

- **Language**: Python 3.11+. Package/deps in `pyproject.toml`.
- **Agent framework**: LangGraph OR a FastAPI tool-use loop - NOT yet ratified (spec OI-18). Decide via
  `/brainstorm` -> `/new-adr` before building the runtime. Until then, isolate framework-specific code
  behind the agent-core interface so the choice stays reversible.
- **Serving**: FastAPI for tool endpoints and the API the frontend consumes.
- **LLM access**: hosted API for the Coordinator/Disruption reasoning seats; self-hosted Qwen for
  Intake / Journey / the forecast-LLM. All model output is validated against a schema before use
  (NFR-SEC-12); all provider calls are mocked in tests.

## Forecast (LLM-as-a-tool)

- The forecast tool is an LLM-with-reasoning exposed as a tool (spec OI-20 resolved), NOT trained ML.
- It MUST implement the retrieve-reason-validate grounding contract in FR-07 (see `data-model.md` and
  `ai-governance.md`). Every number is grounded in observed data and range-validated (NFR-SEC-20).

## State and events

- **Redis** for real-time state and the event bus. No relational ORM; entities are Pydantic models
  (see `data-model.md`). A durable store is not yet chosen (spec OI-15) - keep persistence behind the
  `src/vaic/state` interface so it can be swapped without touching domain code.

## Simulator and eval

- **SimPy** is the "world" the agents run in and the evaluation environment. Deterministic by seed
  (BR-15) so demo metrics reproduce. A/B (agent-orchestrated vs FIFO) runs on the same seeded cohort.

## Frontend

- **React** (Vite + TypeScript), **one responsive role-gated web app** (FR-18): patient views
  mobile-first, staff/coordinator desktop-first, one login, role-based routing.
- **Tailwind CSS + shadcn/ui** as the component kit; the design direction (palette, type, tone,
  signature surfaces) is in `docs/specs/10-ui-ux-wireframes.md` "Visual design direction". Design
  tokens are chosen once at build time and recorded in the frontend, not pinned in the spec.
- **i18n**: VI default with an EN toggle (FR-21); labels are localised, codes/enums stay English.
- Patient surface is chat + timeline; coordinator surface is a load heatmap + approval queue with
  streamed reasoning. Supporting screens: login, notifications center, settings, patient search
  (SCR-08..11). See `frontend.md` for UI conventions.

## Commands (as actually run)

- Backend tests: `pytest`. Lint: `ruff check .`. Frontend tests: `npm test` (Vitest). E2E: Playwright.
  Frontend build: `npm run build`. Coverage target 80%.

## Hosting

- Local demo via Docker Compose (Redis + API + frontend + simulator). No cloud deployment for the
  hackathon build.
