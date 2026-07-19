/**
 * Faithful port of the "Patient Companion App" Design Composer prototype
 * (owner-supplied Patient Companion App.html) - the state machine and demo
 * data, transcribed 1:1 from the design's `Component` class so the React
 * app reproduces the design exactly (screens, flows, Vietnamese content).
 *
 * This is a self-contained demo experience (VN-only, like the design); it
 * does not use the app's routing/auth/i18n. The design's login/OTP buttons
 * are demo affordances that only advance the onboarding state, matching the
 * prototype.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';

// ---- Static demo data (exact content from the design) ----

export interface JourneyStep {
  id: string;
  label: string;
  time: string;
  status: 'done' | 'active' | 'upcoming';
  room: string;
  directions?: string;
}

export const JOURNEY_STEPS: JourneyStep[] = [
  { id: 'reg', label: 'Đăng ký & khám ban đầu', time: '08:40', status: 'done', room: 'Quầy tiếp nhận' },
  { id: 'blood', label: 'Lấy máu xét nghiệm', time: '09:10', status: 'done', room: 'Phòng lấy máu – Tầng 1' },
  { id: 'xray', label: 'Chụp X-quang', time: '~09:35', status: 'active', room: 'Phòng X1 – Tầng 1', directions: 'Đi thẳng từ khu chờ, rẽ phải qua thang bộ, phòng X1 bên tay trái.' },
  { id: 'ultra', label: 'Siêu âm bụng', time: '~09:55', status: 'upcoming', room: 'Phòng S2 – Tầng 1', directions: 'Từ phòng X1 đi thẳng khoảng 20 bước, phòng S2 đối diện quầy nước.' },
  { id: 'return', label: 'Khám lại với BS. Minh', time: '~10:20', status: 'upcoming', room: 'Phòng khám 12 – Tầng 2', directions: 'Lên tầng 2 bằng thang máy khu A, phòng 12 ngay cạnh thang máy.' },
];

export interface Appointment {
  id: number;
  date: string;
  time: string;
  doctor: string;
  dept: string;
  status: 'upcoming' | 'done';
}

export const APPOINTMENTS: Appointment[] = [
  { id: 1, date: 'Hôm nay', time: '10:15', doctor: 'BS. Trần Văn Minh', dept: 'Ngoại tổng quát', status: 'upcoming' },
  { id: 2, date: '12/05/2026', time: '09:00', doctor: 'BS. Lê Thị Hoa', dept: 'Nội tổng quát', status: 'done' },
];

export interface ResultItem {
  id: number;
  name: string;
  date: string;
  status: 'ok' | 'review' | 'pending';
  note: string;
}

export const RESULTS: ResultItem[] = [
  { id: 1, name: 'Công thức máu', date: 'Hôm nay, 09:20', status: 'ok', note: 'Các chỉ số trong ngưỡng bình thường.' },
  { id: 2, name: 'X-quang bụng', date: 'Hôm nay, 09:45', status: 'review', note: 'Cần bác sĩ đọc kết quả chi tiết.' },
  { id: 3, name: 'Siêu âm bụng', date: 'Đang chờ thực hiện', status: 'pending', note: '' },
];

export interface Medication {
  id: number;
  name: string;
  dose: string;
  remind: string;
  warn?: string;
}

export const MEDICATIONS: Medication[] = [
  { id: 1, name: 'Paracetamol 500mg', dose: '1 viên, 3 lần/ngày sau ăn', remind: '08:00 · 13:00 · 19:00' },
  { id: 2, name: 'Men tiêu hóa', dose: '1 viên, 2 lần/ngày', remind: '08:00 · 19:00', warn: 'Không dùng cùng sữa' },
];

export interface NotificationItem {
  id: number;
  kind: 'ai' | 'ok' | 'warn';
  text: string;
  time: string;
}

export const NOTIFICATIONS: NotificationItem[] = [
  { id: 1, kind: 'ai', text: 'Lộ trình vừa cập nhật — siêu âm trước, X-quang sau, do máy X1 bận. +6 phút.', time: '2 phút trước' },
  { id: 2, kind: 'ok', text: 'Kết quả Công thức máu đã có.', time: '15 phút trước' },
  { id: 3, kind: 'warn', text: 'Nhắc: nhịn ăn từ 22:00 hôm nay cho buổi khám sáng mai.', time: 'Hôm qua' },
];

export interface FamilyMember {
  id: string;
  name: string;
  rel: string;
  avatarTone: 'primary' | 'neutral';
  status: string | null;
}

export const FAMILY: FamilyMember[] = [
  { id: 'lan', name: 'Nguyễn Thị Lan', rel: 'Mẹ', avatarTone: 'primary', status: 'Đang chờ chụp X-quang — Tầng 1' },
  { id: 'huong', name: 'Trần Thị Hương', rel: 'Bản thân', avatarTone: 'neutral', status: null },
];

export interface Specialty {
  id: string;
  name: string;
  wait: string;
  tag: string | null;
}

export const SPECIALTIES: Specialty[] = [
  { id: 'ngoai', name: 'Ngoại tổng quát', wait: '~10 phút', tag: 'Ít đông' },
  { id: 'noi', name: 'Nội tổng quát', wait: '~25 phút', tag: null },
  { id: 'nhi', name: 'Nhi khoa', wait: '~15 phút', tag: null },
  { id: 'sanphukhoa', name: 'Sản phụ khoa', wait: '~20 phút', tag: null },
];

export interface Slot {
  t: string;
  tag: string | null;
}

export const SLOTS: Slot[] = [
  { t: '09:00', tag: null },
  { t: '09:30', tag: null },
  { t: '10:15', tag: 'Ít đông' },
  { t: '11:00', tag: null },
];

export const PREP_ITEMS = [
  'Nhịn ăn từ 22:00 hôm nay',
  'Mang theo đơn thuốc / kết quả cũ nếu có',
  'Mang thẻ BHYT và CCCD',
  'Đến trước giờ hẹn 15 phút',
];

export const PATIENT_NAME = 'Nguyễn Thị Lan';
export const OTP_DIGITS = ['9', '4', '1', '2', '0', '7'];

export interface DiaryEntry {
  id: number;
  text: string;
  time: string;
}

export interface ChatMessage {
  from: 'ai' | 'user';
  text: string;
}

// ---- State shape ----

export type OnboardStep = 'login' | 'otp' | 'profile' | 'insurance';
export type Tab = 'home' | 'appointments' | 'journey' | 'records' | 'more';
export type ApptScreen = 'list' | 'book' | 'intake' | 'checkin' | 'prep';
export type JourneyScreen = 'timeline' | 'step';
export type RecordsScreen = 'list' | 'results' | 'resultDetail' | 'medications' | 'recovery' | 'visitSummary';
export type MoreScreen = 'menu' | 'billing' | 'family' | 'settings';

export interface CompanionState {
  appStage: 'onboarding' | 'main';
  onboardStep: OnboardStep;
  tab: Tab;
  apptScreen: ApptScreen;
  bookStep: number;
  bookSpecialty: string | null;
  bookSlot: string | null;
  intakeStep: number;
  checkinStage: 'idle' | 'queued';
  journeyScreen: JourneyScreen;
  journeyStepId: string;
  whyOpen: boolean;
  recordsScreen: RecordsScreen;
  selectedResult: number;
  moreScreen: MoreScreen;
  locationMode: 'inside' | 'outside';
  chatOpen: boolean;
  chatMessages: ChatMessage[];
  notifOpen: boolean;
  familyOpen: boolean;
  activeProfile: string;
  toast: string | null;
  billingPaid: boolean;
  recoveryDiary: DiaryEntry[];
  symptomText: string;
  largeText: boolean;
  highContrast: boolean;
  shareLocation: boolean;
  profileHeight: string;
  profileWeight: string;
  profileAllergy: string;
  profileCondition: string;
}

const QUICK_REPLIES: Record<string, { user: string; ai: string }> = {
  hungry: { user: 'Tôi đói quá, ăn trước được không?', ai: 'Máu của chị đã lấy rồi nên ăn nhẹ được. Em vẫn giữ chỗ siêu âm, chị cứ yên tâm.' },
  wait: { user: 'Còn chờ bao lâu nữa?', ai: 'Còn khoảng 8–10 phút, phía trước còn 2 người. Em sẽ báo ngay khi tới lượt.' },
  where: { user: 'Phòng siêu âm ở đâu?', ai: 'Phòng S2, tầng 1 — đi thẳng từ đây khoảng 30 bước, bên tay phải quầy nước.' },
};

// ---- URL hash <-> navigation sync ----
//
// The companion app keeps its whole navigation in React state, so without a
// URL anchor the browser Back button (and the iOS swipe-back gesture) leaves
// the app entirely and loses every screen. We mirror only the navigation
// slice of the state into `location.hash` - `#home`, `#appointments/book`,
// `#journey/step/xray`, `#records/result/2`, `#more/billing` - so each screen
// change pushes a history entry and Back returns to the previous screen with
// its state intact. The hash is the anchor, never the source of truth for
// content data.

const APPT_SUBS: ApptScreen[] = ['book', 'intake', 'checkin', 'prep'];
const RECORDS_SUBS: RecordsScreen[] = ['results', 'medications', 'recovery', 'visitSummary'];
const MORE_SUBS: MoreScreen[] = ['billing', 'family', 'settings'];

/** The navigation slice of the state encoded as a hash path (no leading `#`). */
export function navToHash(s: CompanionState): string {
  if (s.appStage !== 'main') return '';
  switch (s.tab) {
    case 'home':
      return 'home';
    case 'appointments':
      return s.apptScreen === 'list' ? 'appointments' : `appointments/${s.apptScreen}`;
    case 'journey':
      return s.journeyScreen === 'timeline' ? 'journey' : `journey/step/${s.journeyStepId}`;
    case 'records':
      if (s.recordsScreen === 'list') return 'records';
      if (s.recordsScreen === 'resultDetail') return `records/result/${s.selectedResult}`;
      return `records/${s.recordsScreen}`;
    case 'more':
      return s.moreScreen === 'menu' ? 'more' : `more/${s.moreScreen}`;
    default:
      return '';
  }
}

/**
 * Parse a hash into a navigation patch. Returns an empty object for an
 * unrecognised hash, so the caller can tell "no anchor" from "go home".
 * Unknown sub-segments fall back to the tab's root screen rather than
 * throwing - the hash is untrusted input from the URL bar.
 */
export function hashToNav(rawHash: string): Partial<CompanionState> {
  const clean = rawHash.replace(/^#/, '').replace(/^\/+/, '');
  if (!clean) return {};
  const [tab, ...rest] = clean.split('/');
  switch (tab) {
    case 'home':
      return { tab: 'home' };
    case 'appointments': {
      const sub = rest[0] as ApptScreen | undefined;
      return { tab: 'appointments', apptScreen: sub && APPT_SUBS.includes(sub) ? sub : 'list' };
    }
    case 'journey':
      if (rest[0] === 'step' && rest[1]) {
        return { tab: 'journey', journeyScreen: 'step', journeyStepId: rest[1] };
      }
      return { tab: 'journey', journeyScreen: 'timeline' };
    case 'records': {
      if (rest[0] === 'result' && rest[1] && Number.isFinite(Number(rest[1]))) {
        return { tab: 'records', recordsScreen: 'resultDetail', selectedResult: Number(rest[1]) };
      }
      const sub = rest[0] as RecordsScreen | undefined;
      return { tab: 'records', recordsScreen: sub && RECORDS_SUBS.includes(sub) ? sub : 'list' };
    }
    case 'more': {
      const sub = rest[0] as MoreScreen | undefined;
      return { tab: 'more', moreScreen: sub && MORE_SUBS.includes(sub) ? sub : 'menu' };
    }
    default:
      return {};
  }
}

export function initialState(startAtHome = false): CompanionState {
  // A navigation hash present at load (deep link or a reload after the user
  // navigated) restores that screen and enters the main app directly, so a
  // refresh does not drop the patient back to onboarding.
  const hashNav = typeof window !== 'undefined' ? hashToNav(window.location.hash) : {};
  const hasHashNav = Object.keys(hashNav).length > 0;
  const inMain = startAtHome || hasHashNav;
  return {
    appStage: inMain ? 'main' : 'onboarding',
    onboardStep: 'login',
    tab: 'home',
    apptScreen: 'list',
    bookStep: 1,
    bookSpecialty: null,
    bookSlot: null,
    intakeStep: 0,
    checkinStage: 'idle',
    journeyScreen: 'timeline',
    journeyStepId: 'xray',
    whyOpen: false,
    recordsScreen: 'list',
    selectedResult: 2,
    moreScreen: 'menu',
    locationMode: inMain ? 'inside' : 'outside',
    ...hashNav,
    chatOpen: false,
    chatMessages: [{ from: 'ai', text: 'Chào chị, em đang theo dõi lộ trình khám hôm nay. Chị cần hỏi gì cứ nhắn em nhé.' }],
    notifOpen: false,
    familyOpen: false,
    activeProfile: 'lan',
    toast: null,
    billingPaid: false,
    recoveryDiary: [{ id: 1, text: 'Đỡ đau hơn hôm qua, còn mệt nhẹ.', time: 'Hôm nay, 08:00' }],
    symptomText: '',
    largeText: false,
    highContrast: false,
    shareLocation: true,
    profileHeight: '160',
    profileWeight: '58',
    profileAllergy: 'Không rõ',
    profileCondition: 'Tăng huyết áp',
  };
}

/** Props every screen/overlay sub-component receives. */
export interface ScreenProps {
  s: CompanionState;
  a: CompanionActions;
}

export interface CompanionActions {
  // onboarding
  goOtp: () => void;
  goProfile: () => void;
  goInsurance: () => void;
  finishOnboarding: () => void;
  obBack: () => void;
  setProfileHeight: (v: string) => void;
  setProfileWeight: (v: string) => void;
  setProfileAllergy: (v: string) => void;
  setProfileCondition: (v: string) => void;
  // tabs
  goTabHome: () => void;
  goTabAppt: () => void;
  goTabJourney: () => void;
  goTabRecords: () => void;
  goTabMore: () => void;
  // home shortcuts
  goCheckinShortcut: () => void;
  goBookShortcut: () => void;
  goPrepShortcut: () => void;
  goResultsFromHome: () => void;
  goJourneyFromHome: () => void;
  endVisitDemo: () => void;
  toggleWhy: () => void;
  // appointments
  backAppt: () => void;
  goNewBooking: () => void;
  selectSpecialty: (id: string) => void;
  selectSlot: (t: string) => void;
  backBookStep: () => void;
  confirmBooking: () => void;
  selectSymptomChip: () => void;
  acceptIntakeSuggestion: () => void;
  scanQr: () => void;
  enterLiveCompanion: () => void;
  // journey
  openStep: (id: string) => void;
  backJourney: () => void;
  // records
  goResults: () => void;
  goMedications: () => void;
  goRecovery: () => void;
  goVisitSummary: () => void;
  backRecords: () => void;
  openResult: (id: number) => void;
  viewPdf: () => void;
  setSymptomText: (v: string) => void;
  addSymptom: () => void;
  recoveryBetter: () => void;
  recoveryWorse: () => void;
  // more
  goBilling: () => void;
  goFamily: () => void;
  goSettings: () => void;
  backMore: () => void;
  payBill: () => void;
  toggleShare: () => void;
  toggleLargeText: () => void;
  toggleHighContrast: () => void;
  logout: () => void;
  // header / overlays
  toggleFamilySwitcher: () => void;
  activateProfile: (id: string) => void;
  toggleNotif: () => void;
  openChat: () => void;
  closeChat: () => void;
  sendQuickReply: (key: 'hungry' | 'wait' | 'where') => void;
}

export function useCompanionState(startAtHome = false): { s: CompanionState; a: CompanionActions } {
  const [s, setS] = useState<CompanionState>(() => initialState(startAtHome));
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const patch = useCallback((next: Partial<CompanionState> | ((prev: CompanionState) => Partial<CompanionState>)) => {
    setS((prev) => ({ ...prev, ...(typeof next === 'function' ? next(prev) : next) }));
  }, []);

  // Anchor the current screen in the URL hash so a screen change pushes a
  // history entry. navHash is the only value the write depends on, so the
  // effect fires exactly when the screen changes, never on content edits.
  const navHash = navToHash(s);
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const current = window.location.hash.replace(/^#/, '');
    if (navHash && navHash !== current) {
      window.location.hash = navHash;
    }
  }, [navHash]);

  // Follow Back/Forward: restore the navigation the hash points at. The
  // no-op guard (comparing encoded navigation) absorbs the echo of our own
  // hash writes above, so the two effects cannot loop.
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const onHashChange = () => {
      const nav = hashToNav(window.location.hash);
      if (Object.keys(nav).length === 0) return;
      setS((prev) => {
        if (prev.appStage !== 'main') return prev;
        const next = { ...prev, ...nav };
        return navToHash(next) === navToHash(prev) ? prev : next;
      });
    };
    window.addEventListener('hashchange', onHashChange);
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);

  const showToast = useCallback((msg: string) => {
    setS((prev) => ({ ...prev, toast: msg }));
    if (toastTimer.current) clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setS((prev) => ({ ...prev, toast: null })), 2600);
  }, []);

  const a = useMemo<CompanionActions>(() => ({
    goOtp: () => patch({ onboardStep: 'otp' }),
    goProfile: () => patch({ onboardStep: 'profile' }),
    goInsurance: () => patch({ onboardStep: 'insurance' }),
    finishOnboarding: () => patch({ appStage: 'main' }),
    obBack: () => patch((prev) => {
      const order: OnboardStep[] = ['login', 'otp', 'profile', 'insurance'];
      const i = order.indexOf(prev.onboardStep);
      return { onboardStep: order[Math.max(0, i - 1)] };
    }),
    setProfileHeight: (v) => patch({ profileHeight: v }),
    setProfileWeight: (v) => patch({ profileWeight: v }),
    setProfileAllergy: (v) => patch({ profileAllergy: v }),
    setProfileCondition: (v) => patch({ profileCondition: v }),

    goTabHome: () => patch({ tab: 'home' }),
    goTabAppt: () => patch({ tab: 'appointments', apptScreen: 'list' }),
    goTabJourney: () => patch({ tab: 'journey', journeyScreen: 'timeline' }),
    goTabRecords: () => patch({ tab: 'records', recordsScreen: 'list' }),
    goTabMore: () => patch({ tab: 'more', moreScreen: 'menu' }),

    goCheckinShortcut: () => patch({ tab: 'appointments', apptScreen: 'checkin', checkinStage: 'idle' }),
    goBookShortcut: () => patch({ tab: 'appointments', apptScreen: 'book', bookStep: 1 }),
    goPrepShortcut: () => patch({ tab: 'appointments', apptScreen: 'prep' }),
    goResultsFromHome: () => patch({ tab: 'records', recordsScreen: 'results' }),
    goJourneyFromHome: () => patch({ tab: 'journey', journeyScreen: 'timeline' }),
    endVisitDemo: () => patch({ locationMode: 'outside' }),
    toggleWhy: () => patch((prev) => ({ whyOpen: !prev.whyOpen })),

    backAppt: () => patch({ apptScreen: 'list' }),
    goNewBooking: () => patch({ apptScreen: 'book', bookStep: 1, bookSpecialty: null, bookSlot: null }),
    selectSpecialty: (id) => patch({ bookSpecialty: id, bookStep: 2 }),
    selectSlot: (t) => patch({ bookSlot: t, bookStep: 3 }),
    backBookStep: () => patch((prev) => ({ bookStep: Math.max(1, prev.bookStep - 1) })),
    confirmBooking: () => {
      setS((prev) => {
        const sp = SPECIALTIES.find((x) => x.id === prev.bookSpecialty);
        showToast('Đã đặt lịch ' + (prev.bookSlot || '') + ' — ' + (sp ? sp.name : ''));
        return { ...prev, apptScreen: 'list', bookStep: 1 };
      });
    },
    selectSymptomChip: () => patch({ intakeStep: 1 }),
    acceptIntakeSuggestion: () => {
      patch({ apptScreen: 'list', intakeStep: 0 });
      showToast('Đã đặt lịch 10:15 — Ngoại tổng quát');
    },
    scanQr: () => patch({ checkinStage: 'queued' }),
    enterLiveCompanion: () => patch({ tab: 'home', apptScreen: 'list', checkinStage: 'idle', locationMode: 'inside' }),

    openStep: (id) => patch({ journeyStepId: id, journeyScreen: 'step' }),
    backJourney: () => patch({ journeyScreen: 'timeline' }),

    goResults: () => patch({ recordsScreen: 'results' }),
    goMedications: () => patch({ recordsScreen: 'medications' }),
    goRecovery: () => patch({ recordsScreen: 'recovery' }),
    goVisitSummary: () => patch({ recordsScreen: 'visitSummary' }),
    backRecords: () => patch((prev) => ({ recordsScreen: prev.recordsScreen === 'resultDetail' ? 'results' : 'list' })),
    openResult: (id) => patch({ selectedResult: id, recordsScreen: 'resultDetail' }),
    viewPdf: () => showToast('Đang tải PDF…'),
    setSymptomText: (v) => patch({ symptomText: v }),
    addSymptom: () => patch((prev) => {
      if (!prev.symptomText.trim()) return {};
      return {
        recoveryDiary: [{ id: Date.now(), text: prev.symptomText, time: 'Vừa xong' }, ...prev.recoveryDiary],
        symptomText: '',
      };
    }),
    recoveryBetter: () => showToast('Đã ghi nhận: đỡ nhiều'),
    recoveryWorse: () => showToast('Đã ghi nhận — sẽ báo bác sĩ nếu cần'),

    goBilling: () => patch({ moreScreen: 'billing' }),
    goFamily: () => patch({ moreScreen: 'family' }),
    goSettings: () => patch({ moreScreen: 'settings' }),
    backMore: () => patch({ moreScreen: 'menu' }),
    payBill: () => { patch({ billingPaid: true }); showToast('Đã thanh toán qua VNPay QR'); },
    toggleShare: () => patch((prev) => ({ shareLocation: !prev.shareLocation })),
    toggleLargeText: () => patch((prev) => ({ largeText: !prev.largeText })),
    toggleHighContrast: () => patch((prev) => ({ highContrast: !prev.highContrast })),
    logout: () => showToast('Đã đăng xuất (demo)'),

    toggleFamilySwitcher: () => patch((prev) => ({ familyOpen: !prev.familyOpen })),
    activateProfile: (id) => patch({ activeProfile: id, familyOpen: false }),
    toggleNotif: () => patch((prev) => ({ notifOpen: !prev.notifOpen })),
    openChat: () => patch({ chatOpen: true }),
    closeChat: () => patch({ chatOpen: false }),
    sendQuickReply: (key) => {
      const script = QUICK_REPLIES[key];
      if (!script) return;
      patch((prev) => ({ chatMessages: [...prev.chatMessages, { from: 'user', text: script.user }, { from: 'ai', text: script.ai }] }));
    },
  }), [patch, showToast]);

  return { s, a };
}
