/**
 * LanguageToggle - the VI/EN switch used on SCR-08 (login) and SCR-10
 * (settings) - FR-21, NFR-USE-03. Two explicit buttons (not a native
 * select) so both options and the active one are always visible and
 * screen-reader friendly (aria-pressed).
 */
import { useI18n, type Locale } from '@/i18n';
import { cn } from '@/lib/utils';

const OPTIONS: Array<{ locale: Locale; label: string }> = [
  { locale: 'vi', label: 'VI' },
  { locale: 'en', label: 'EN' },
];

interface LanguageToggleProps {
  className?: string;
}

export function LanguageToggle({ className }: LanguageToggleProps) {
  const { locale, setLocale, t } = useI18n();

  return (
    <div
      role="group"
      aria-label={t('login.languageToggle')}
      className={cn('inline-flex rounded-pill border border-border bg-card p-1', className)}
    >
      {OPTIONS.map((option) => {
        const isActive = option.locale === locale;
        return (
          <button
            key={option.locale}
            type="button"
            aria-pressed={isActive}
            onClick={() => setLocale(option.locale)}
            className={cn(
              'rounded-pill px-3 py-1 text-xs font-medium transition-colors',
              isActive ? 'bg-primary text-primary-foreground' : 'text-muted-foreground',
            )}
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
