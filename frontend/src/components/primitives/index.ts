/**
 * Shared primitive entry point. Screens import UI primitives from here, not
 * by reaching for raw elements and hardcoded values (frontend.md: build
 * from the shared primitives and design tokens).
 */
export { AIChip } from './AIChip';
export { StatusChip, type StatusCode } from './StatusChip';
export { LanguageToggle } from './LanguageToggle';
export { PatientCodeQr } from './PatientCodeQr';
export * from './ScreenState';

export { Button, buttonVariants, type ButtonProps } from './Button';
export { Card, HeroCard, MutedCard } from './Card';
export { SectionLabel } from './SectionLabel';
export { ListRow } from './ListRow';
export { IconButton } from './IconButton';
export { Avatar } from './Avatar';
export { Switch } from './Switch';
export { SegmentedProgress } from './SegmentedProgress';
export { Timeline, TimelineStep, type TimelineStatus } from './Timeline';
export { Sheet } from './Sheet';
export { Toast, useToast } from './Toast';
