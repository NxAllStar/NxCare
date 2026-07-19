/**
 * Shared fetch client for the real (non-fixture) backend endpoints (FR-18).
 *
 * `apiFetch` is the one place that knows the base URL, attaches the bearer token set by
 * `setAuthToken`, and turns a non-2xx response into a thrown `Error`. Callers such as
 * `session.ts` stay free of fetch/JSON boilerplate and of the token itself.
 *
 * The base URL comes from `VITE_API_BASE_URL` - anything Vite exposes to the client is PUBLIC by
 * definition (tech-stack.md), so only a plain HTTP base URL belongs here.
 *
 * The token is held in memory only (module-level, not persisted) - this mirrors the "DEMO
 * session only" note on `AuthContext`: a page refresh drops it and the next authenticated call
 * fails, which is acceptable for the current demo scope and not a security boundary either way.
 */

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000';

let authToken: string | null = null;

/** Set (or clear, with `null`) the bearer token attached to every subsequent `apiFetch` call. */
export function setAuthToken(token: string | null): void {
  authToken = token;
}

export interface ApiFetchOptions {
  method?: string;
  body?: unknown;
}

/** Error response shape FastAPI's `HTTPException` produces (`{"detail": "..."}`). */
interface ApiErrorBody {
  detail?: string;
}

async function readErrorMessage(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as ApiErrorBody;
    if (typeof body.detail === 'string' && body.detail.length > 0) {
      return body.detail;
    }
  } catch {
    // Response body was not JSON (or empty) - fall through to the status-based message.
  }
  return `request failed: ${response.status}`;
}

/**
 * JSON fetch against the real backend. Attaches `Authorization: Bearer <token>` when a token has
 * been set via `setAuthToken`. Resolves with the parsed JSON body, or `undefined` for a response
 * with no body (e.g. `204 No Content`) - callers that expect no payload should type the result as
 * `Promise<void>`.
 */
export async function apiFetch<T>(path: string, options: ApiFetchOptions = {}): Promise<T> {
  const headers: Record<string, string> = {};
  if (options.body !== undefined) {
    headers['Content-Type'] = 'application/json';
  }
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? 'GET',
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  });

  if (!response.ok) {
    throw new Error(await readErrorMessage(response));
  }

  const text = await response.text();
  if (!text) {
    return undefined as T;
  }
  return JSON.parse(text) as T;
}
