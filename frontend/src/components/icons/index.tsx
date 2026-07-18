/**
 * Hand-authored SVG icon set for the patient app shell (bottom nav + FAB).
 *
 * No emoji anywhere in the UI (frontend.md, spec 10 "Iconography"). These
 * are deliberately minimal, licence-free, hand-drawn strokes rather than an
 * added icon-font dependency - see the TASK-021 session log for the
 * reasoning (avoids an unreviewed dependency/licence decision mid-task).
 */
import type { SVGProps } from 'react';

type IconProps = SVGProps<SVGSVGElement>;

function base(props: IconProps) {
  return {
    xmlns: 'http://www.w3.org/2000/svg',
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 1.75,
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
    'aria-hidden': true,
    ...props,
  };
}

export function HomeIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M3 11.5 12 4l9 7.5" />
      <path d="M5.5 10v9a1 1 0 0 0 1 1H9a1 1 0 0 0 1-1v-4h4v4a1 1 0 0 0 1 1h2.5a1 1 0 0 0 1-1v-9" />
    </svg>
  );
}

export function CalendarIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <rect x="3.5" y="5" width="17" height="15" rx="1.5" />
      <path d="M3.5 9.5h17" />
      <path d="M8 3v3.5M16 3v3.5" />
      <path d="M8 13h2M14 13h2M8 16.5h2M14 16.5h2" />
    </svg>
  );
}

export function RouteIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <circle cx="6" cy="6" r="2" />
      <circle cx="18" cy="18" r="2" />
      <path d="M6 8v3a3 3 0 0 0 3 3h6a3 3 0 0 1 3 3v1" />
    </svg>
  );
}

export function HeartPulseIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M12 20.5s-7.5-4.6-9.7-9.4C1 8 2.4 4.9 5.4 4.1c2-.5 3.9.4 5 2 .3-1.6 2-2.5 5-2 3 .8 4.4 3.9 3.1 6.9C16.5 15.9 12 20.5 12 20.5Z" />
      <path d="M4 12h2.5l1.5-3 2 6 1.5-3H16" />
    </svg>
  );
}

export function MoreIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <circle cx="5" cy="12" r="1.4" fill="currentColor" stroke="none" />
      <circle cx="12" cy="12" r="1.4" fill="currentColor" stroke="none" />
      <circle cx="19" cy="12" r="1.4" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function AssistantIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M4 5.5h16v10H9l-3.5 3v-3H4z" />
      <path d="M8.5 9.5h7M8.5 12h4.5" />
    </svg>
  );
}

export function GlobeIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M3.5 12h17M12 3.5c2.4 2.3 3.6 5.3 3.6 8.5s-1.2 6.2-3.6 8.5c-2.4-2.3-3.6-5.3-3.6-8.5S9.6 5.8 12 3.5Z" />
    </svg>
  );
}

export function BellIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M6 9a6 6 0 1 1 12 0c0 4 1.5 5.5 1.5 5.5H4.5S6 13 6 9Z" />
      <path d="M10 18a2 2 0 0 0 4 0" />
    </svg>
  );
}

export function LogoutIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M9 4H6a1.5 1.5 0 0 0-1.5 1.5v13A1.5 1.5 0 0 0 6 20h3" />
      <path d="M15 16l4-4-4-4" />
      <path d="M19 12H9" />
    </svg>
  );
}

export function SendIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M4 12 20 4l-6.5 16-2.5-7-7-1Z" />
    </svg>
  );
}

export function AlertIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M12 3.5 21 19.5H3L12 3.5Z" />
      <path d="M12 10v4" />
      <circle cx="12" cy="17" r="0.2" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function MapPinIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M12 21s7-6.2 7-11.5A7 7 0 0 0 5 9.5C5 14.8 12 21 12 21Z" />
      <circle cx="12" cy="9.5" r="2.2" />
    </svg>
  );
}

export function ClockIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M12 7.5V12l3 2" />
    </svg>
  );
}

export function ChevronRightIcon(props: IconProps) {
  return (
    <svg {...base(props)} strokeWidth={2.2}>
      <path d="M9 5l7 7-7 7" />
    </svg>
  );
}

export function ChevronLeftIcon(props: IconProps) {
  return (
    <svg {...base(props)} strokeWidth={2.2}>
      <path d="M15 5l-7 7 7 7" />
    </svg>
  );
}

export function ChevronDownIcon(props: IconProps) {
  return (
    <svg {...base(props)} strokeWidth={2.2}>
      <path d="M5 9l7 7 7-7" />
    </svg>
  );
}

export function CheckIcon(props: IconProps) {
  return (
    <svg {...base(props)} strokeWidth={2.6}>
      <path d="M4.5 12.5l5 5 10-11" />
    </svg>
  );
}

export function XIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M5 5l14 14M19 5L5 19" />
    </svg>
  );
}

export function PlusIcon(props: IconProps) {
  return (
    <svg {...base(props)} strokeWidth={2.2}>
      <path d="M12 5v14M5 12h14" />
    </svg>
  );
}

export function SparkleIcon(props: IconProps) {
  return (
    <svg {...base(props)} fill="currentColor" stroke="none">
      <path d="M12 2l1.7 5.5L19.5 9l-5.8 1.5L12 16l-1.7-5.5L4.5 9l5.8-1.5L12 2z" />
    </svg>
  );
}

export function QrIcon(props: IconProps) {
  return (
    <svg {...base(props)} strokeWidth={1.5}>
      <rect x="3" y="3" width="7" height="7" rx="1" />
      <rect x="14" y="3" width="7" height="7" rx="1" />
      <rect x="3" y="14" width="7" height="7" rx="1" />
      <path d="M14 14h3v3h-3zM20 14v3M14 20h3M18 18h3v3" />
    </svg>
  );
}

export function PhoneIcon(props: IconProps) {
  return (
    <svg {...base(props)} strokeWidth={1.6}>
      <path d="M6.6 10.8c1.4 2.8 3.8 5.2 6.6 6.6l2.2-2.2c.3-.3.7-.4 1-.2 1.2.5 2.5.8 3.9.8.6 0 1 .4 1 1V20c0 .6-.4 1-1 1C10.6 21 3 13.4 3 4c0-.6.4-1 1-1h3.2c.6 0 1 .4 1 1 0 1.4.3 2.7.8 3.9.1.4 0 .8-.2 1L6.6 10.8z" />
    </svg>
  );
}

export function PillIcon(props: IconProps) {
  return (
    <svg {...base(props)} strokeWidth={1.7}>
      <rect x="3" y="8" width="18" height="8" rx="4" />
      <path d="M12 8v8" />
    </svg>
  );
}

/* --- Hospital console sidebar icons (TASK-026) --- */

export function StethoscopeIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M7 4v6a4 4 0 0 0 8 0V4" />
      <path d="M11 14v2a5 5 0 0 0 10 0v-2" />
      <circle cx="21" cy="12" r="1.4" fill="currentColor" stroke="none" />
    </svg>
  );
}

export function ClipboardListIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <rect x="5" y="4" width="14" height="17" rx="1.5" />
      <path d="M9 3.5h6a1 1 0 0 1 1 1V6H8V4.5a1 1 0 0 1 1-1Z" />
      <path d="M8.5 11h7M8.5 14.5h7M8.5 18h4" />
    </svg>
  );
}

export function WrenchIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M14.5 6.5a4 4 0 0 0-5.4 4.9L4 16.5V19h2.5l5.1-5.1a4 4 0 0 0 4.9-5.4l-2.6 2.6-2-2 2.6-2.6Z" />
    </svg>
  );
}

export function GridIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <rect x="3.5" y="3.5" width="7" height="7" rx="1" />
      <rect x="13.5" y="3.5" width="7" height="7" rx="1" />
      <rect x="3.5" y="13.5" width="7" height="7" rx="1" />
      <rect x="13.5" y="13.5" width="7" height="7" rx="1" />
    </svg>
  );
}

export function ShieldIcon(props: IconProps) {
  return (
    <svg {...base(props)}>
      <path d="M12 3.5 19 6v5.5c0 5-3 8.3-7 9.5-4-1.2-7-4.5-7-9.5V6l7-2.5Z" />
      <path d="M9 12l2 2 4-4" />
    </svg>
  );
}
