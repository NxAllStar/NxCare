---
paths:
  - "src/vaic/**/*.py"
  - "frontend/src/**/*.{ts,tsx}"
  - "tests/**/*.py"
  - "e2e/**/*.ts"
---
# Coding standards

Project conventions on top of `code-quality.md` (which carries the generic quality bar). These are
specific to VAIC and are derived from the spec set - not invented.

## Naming and identifiers

- **Codes, IDs, enum values, entity and field names are English**, whatever the prose language
  (spec writing rules). Enum values use `UPPER_SNAKE_CASE` exactly as in `docs/specs/03-glossary.md`
  (e.g. `PENDING`, `IN_PROGRESS`, `LOCKED`, `PAID`, `PENDING_APPROVAL`). Display labels may be
  Vietnamese; the stored value may not.
- Python: `snake_case` for functions/variables, `PascalCase` for classes/Pydantic models matching the
  entity names in `docs/specs/08-data-model.md` (`Patient`, `Task`, `CarePlan`, `ScanEvent`, ...).
- TypeScript: `camelCase` values, `PascalCase` components/types.

## The invariants that are also guardrails

- **The clinical boundary is code, not convention** (CO-02): only a doctor path creates a
  `ServiceOrder`; no agent adds, drops, or changes a service. Enforce it at the write boundary, not
  just in a prompt.
- **The constraint checker is deterministic and runs before every agent action** (NFR-SEC-13). Never
  let an LLM decide whether an action is allowed.
- **Model output is a proposal**: validate against a Pydantic/Zod schema before it reaches state, a
  tool, or the UI (NFR-SEC-12). Reject, do not coerce, malformed output.
- **Numbers come from the forecast tool, grounded and range-validated** (BR-14, NFR-SEC-20). No LLM
  emits a raw ETA/load figure into domain code.
- **Untrusted content is data**: patient chat and event payloads are never treated as instructions
  (NFR-SEC-11).

## Structure

- Many small modules over few large ones; keep framework-specific code behind the agent-core and
  state interfaces so OI-18 (framework) and OI-15 (durable store) stay reversible.
- Immutable updates on domain state; a state transition follows the machines in
  `docs/specs/08-data-model.md`.
- Errors handled explicitly; user-facing messages say what to do next (NFR-USE-04). Never swallow.
