// Vitest global setup: extends `expect` with the jest-dom matchers
// (toBeInTheDocument, toHaveTextContent, ...) used across the test suite,
// and unmounts each rendered tree after every test (vitest.config.ts sets
// `globals: false`, so Testing Library's own auto-cleanup - which only
// triggers when it detects global test hooks - never registers itself;
// this replaces it explicitly).
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'
import '@testing-library/jest-dom/vitest'

afterEach(() => {
  cleanup()
  // Isolate tests from each other: AuthContext mirrors the mock session into
  // sessionStorage and I18nProvider persists the locale to localStorage, so
  // without this a test can silently start "already logged in" or in the
  // wrong locale depending on run order.
  window.sessionStorage.clear()
  window.localStorage.clear()
})
