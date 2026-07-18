/**
 * Barrel export for the mock data layer (TASK-021).
 *
 * Everything under frontend/src/lib/api/ is mock/stub data - there is no
 * backend yet. Every stub function is marked `// TODO: replace with real
 * API call` at its definition. No real network calls are made anywhere in
 * this module tree.
 */

export * from './types';
export * from './fixtures';
export * from './session';
export * from './patient';
export * from './intake';
export * from './booking';
export * from './assistant';
export * from './notifications';
export * from './settings';
export * from './records';
export * from './billing';
export * from './family';
export * from './prep';
export * from './journeyStep';
