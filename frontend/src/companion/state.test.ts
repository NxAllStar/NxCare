/**
 * Hash <-> navigation anchoring for the patient companion app. The behaviour
 * under test: every screen change is mirrored into location.hash so the
 * browser Back button (and iOS swipe-back) navigates within the app instead
 * of leaving it, and a hash present at load restores that screen. Verifies
 * navToHash/hashToNav are inverse over every navigable screen, that a
 * malformed hash degrades to the tab root, and the round-trip through the hook.
 */
import { afterEach, describe, expect, it } from 'vitest';
import { act, renderHook } from '@testing-library/react';
import { hashToNav, initialState, navToHash, useCompanionState, type CompanionState } from './state';

function stateWith(patch: Partial<CompanionState>): CompanionState {
  return { ...initialState(true), ...patch };
}

afterEach(() => {
  window.history.replaceState({}, '', '/');
});

describe('navToHash', () => {
  it('encodes each tab root', () => {
    expect(navToHash(stateWith({ tab: 'home' }))).toBe('home');
    expect(navToHash(stateWith({ tab: 'appointments', apptScreen: 'list' }))).toBe('appointments');
    expect(navToHash(stateWith({ tab: 'journey', journeyScreen: 'timeline' }))).toBe('journey');
    expect(navToHash(stateWith({ tab: 'records', recordsScreen: 'list' }))).toBe('records');
    expect(navToHash(stateWith({ tab: 'more', moreScreen: 'menu' }))).toBe('more');
  });

  it('encodes sub-screens including their parameter', () => {
    expect(navToHash(stateWith({ tab: 'appointments', apptScreen: 'book' }))).toBe('appointments/book');
    expect(navToHash(stateWith({ tab: 'journey', journeyScreen: 'step', journeyStepId: 'ultra' }))).toBe('journey/step/ultra');
    expect(navToHash(stateWith({ tab: 'records', recordsScreen: 'resultDetail', selectedResult: 3 }))).toBe('records/result/3');
    expect(navToHash(stateWith({ tab: 'records', recordsScreen: 'medications' }))).toBe('records/medications');
    expect(navToHash(stateWith({ tab: 'more', moreScreen: 'billing' }))).toBe('more/billing');
  });

  it('emits no anchor while onboarding', () => {
    expect(navToHash(stateWith({ appStage: 'onboarding' }))).toBe('');
  });
});

describe('hashToNav', () => {
  it('parses tab roots and sub-screens', () => {
    expect(hashToNav('#home')).toEqual({ tab: 'home' });
    expect(hashToNav('#appointments/book')).toEqual({ tab: 'appointments', apptScreen: 'book' });
    expect(hashToNav('#journey/step/xray')).toEqual({ tab: 'journey', journeyScreen: 'step', journeyStepId: 'xray' });
    expect(hashToNav('#records/result/2')).toEqual({ tab: 'records', recordsScreen: 'resultDetail', selectedResult: 2 });
    expect(hashToNav('#more/settings')).toEqual({ tab: 'more', moreScreen: 'settings' });
  });

  it('falls back to the tab root for an unknown sub-screen (untrusted URL input)', () => {
    expect(hashToNav('#appointments/bogus')).toEqual({ tab: 'appointments', apptScreen: 'list' });
    expect(hashToNav('#records/result/notanumber')).toEqual({ tab: 'records', recordsScreen: 'list' });
    expect(hashToNav('#more/../etc')).toEqual({ tab: 'more', moreScreen: 'menu' });
  });

  it('returns an empty patch for an empty or unrecognised hash', () => {
    expect(hashToNav('')).toEqual({});
    expect(hashToNav('#')).toEqual({});
    expect(hashToNav('#nope')).toEqual({});
  });

  it('is the inverse of navToHash over every navigable screen', () => {
    const screens: Partial<CompanionState>[] = [
      { tab: 'home' },
      { tab: 'appointments', apptScreen: 'list' },
      { tab: 'appointments', apptScreen: 'checkin' },
      { tab: 'journey', journeyScreen: 'timeline' },
      { tab: 'journey', journeyScreen: 'step', journeyStepId: 'return' },
      { tab: 'records', recordsScreen: 'list' },
      { tab: 'records', recordsScreen: 'resultDetail', selectedResult: 1 },
      { tab: 'records', recordsScreen: 'visitSummary' },
      { tab: 'more', moreScreen: 'family' },
    ];
    for (const scr of screens) {
      const s = stateWith(scr);
      expect(hashToNav('#' + navToHash(s))).toMatchObject(scr);
    }
  });
});

describe('initialState reads the hash on load', () => {
  it('deep-links into the main app at the hashed screen instead of onboarding', () => {
    window.history.replaceState({}, '', '/#journey/step/ultra');
    const s = initialState(false);
    expect(s.appStage).toBe('main');
    expect(s.tab).toBe('journey');
    expect(s.journeyScreen).toBe('step');
    expect(s.journeyStepId).toBe('ultra');
  });

  it('stays in onboarding when there is no navigation hash', () => {
    window.history.replaceState({}, '', '/');
    expect(initialState(false).appStage).toBe('onboarding');
  });
});

describe('useCompanionState hash sync', () => {
  it('writes the current screen into location.hash', () => {
    window.history.replaceState({}, '', '/');
    const { result } = renderHook(() => useCompanionState(true));
    act(() => result.current.a.goTabJourney());
    expect(window.location.hash).toBe('#journey');
    act(() => result.current.a.openStep('ultra'));
    expect(window.location.hash).toBe('#journey/step/ultra');
  });

  it('restores navigation when the hash changes (Back/Forward)', () => {
    window.history.replaceState({}, '', '/');
    const { result } = renderHook(() => useCompanionState(true));
    act(() => result.current.a.goTabRecords());
    act(() => result.current.a.openResult(3));
    expect(result.current.s.recordsScreen).toBe('resultDetail');

    // Simulate the browser Back button returning to the records list.
    act(() => {
      window.history.replaceState({}, '', '/#records');
      window.dispatchEvent(new HashChangeEvent('hashchange'));
    });
    expect(result.current.s.tab).toBe('records');
    expect(result.current.s.recordsScreen).toBe('list');
  });
});
