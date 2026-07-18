/**
 * Minimal i18n scaffold (FR-21, NFR-USE-03): VI default, EN toggle.
 *
 * Display labels localise through `t()`. Codes and enum values NEVER pass
 * through this module - render them literally (see StatusChip.tsx, BR-31).
 * Deliberately no external i18n library: two flat dictionaries plus a
 * context is enough for this scope and keeps the dependency surface small.
 */
import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react';
import en from './dictionaries/en';
import vi, { type DictKey } from './dictionaries/vi';

export type Locale = 'vi' | 'en';

const DICTIONARIES: Record<Locale, Record<DictKey, string>> = { vi, en };

const STORAGE_KEY = 'vaic.locale';

function readStoredLocale(): Locale {
  if (typeof window === 'undefined') return 'vi';
  const stored = window.localStorage.getItem(STORAGE_KEY);
  return stored === 'en' ? 'en' : 'vi';
}

interface I18nContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: (key: DictKey) => string;
}

const I18nContext = createContext<I18nContextValue | null>(null);

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(() => readStoredLocale());

  const setLocale = useCallback((next: Locale) => {
    setLocaleState(next);
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(STORAGE_KEY, next);
    }
  }, []);

  const t = useCallback((key: DictKey) => DICTIONARIES[locale][key], [locale]);

  const value = useMemo(() => ({ locale, setLocale, t }), [locale, setLocale, t]);

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nContextValue {
  const ctx = useContext(I18nContext);
  if (!ctx) {
    throw new Error('useI18n must be used within an I18nProvider');
  }
  return ctx;
}

export type { DictKey };
