/**
 * LandingPage - public entry at /landing. Introduces the two product
 * surfaces (patient companion app + hospital console) and links into both.
 *
 * Follows the VAIC design direction (spec 10 "Visual design direction"):
 * calm clinical light palette on the shared design tokens, one humanist
 * sans, SVG icons from the shared icon set (frontend.md: no emoji as
 * iconography, no hardcoded colours), and the same NxC hexagon brand
 * lockup as the console header and staff login.
 */
import {
  AssistantIcon,
  CheckIcon,
  ChevronRightIcon,
  ClockIcon,
  GridIcon,
  HeartPulseIcon,
  RouteIcon,
  SparkleIcon,
  StethoscopeIcon,
  TrendingUpIcon,
} from '@/components/icons';

// The landing is Vietnamese-only, like the whole demo (owner decision
// 2026-07-18: no VI/EN toggle on this page).
const CONTENT = {
    badge: 'Hệ thống Y tế AI Thế hệ Mới',
    title1: 'Chuyển đổi trải nghiệm',
    title2: 'khám chữa bệnh',
    subtitle: 'Giải pháp toàn diện tối ưu hóa lộ trình khám chữa bệnh tại viện, giảm thời gian chờ đợi cho bệnh nhân và nâng cao hiệu suất hoạt động phòng khám.',
    patientAppBtn: 'Trải nghiệm ứng dụng AI',
    patientAppDesc: 'Dành cho Bệnh nhân (Giao diện Mobile)',
    consoleBtn: 'Vào website bệnh viện',
    consoleDesc: 'Dành cho Nhân viên & Điều phối viên',
    featuresTitle: 'Hệ thống Tính năng Cốt lõi',
    featuresSub: 'Kết nối bệnh nhân và bệnh viện trong thời gian thực bằng trí tuệ nhân tạo',
    feature1Title: 'Khai thác triệu chứng & Đặt lịch',
    feature1Desc: 'AI tự động phân loại triệu chứng của bệnh nhân, định tuyến chuyên khoa và đề xuất khung giờ khám tối ưu.',
    feature2Title: 'Lộ trình trong viện thời gian thực',
    feature2Desc: 'Theo dõi hàng chờ, sơ đồ chỉ dẫn đường đi và cập nhật thời gian chờ ước tính tự động cho bệnh nhân.',
    feature3Title: 'Bản đồ tải & Tự động điều phối',
    feature3Desc: 'Phát hiện sự cố tức thì, trực quan hóa tải phòng khám bằng bản đồ nhiệt và tự động lập lại kế hoạch (re-plan).',
    feature4Title: 'Trợ lý AI đồng hành 24/7',
    feature4Desc: 'Giải đáp thắc mắc lộ trình, nhắc nhở chuẩn bị trước khám và khảo sát nhật ký theo dõi hồi phục tại nhà.',
    stat1Label: 'Thời gian chờ trung bình',
    stat1Val: '~12 phút',
    stat2Label: 'Mức độ hài lòng của bệnh nhân',
    stat2Val: '96.4%',
    stat3Label: 'Hiệu suất phòng khám tối ưu',
    stat3Val: '+35%',
    statsNote: 'Số liệu mục tiêu từ kịch bản mô phỏng dòng bệnh nhân (SimPy), không phải kết quả triển khai thực tế.',
    footerText: 'NxCare & VAIC © 2026. Được thiết kế và vận hành bởi đội ngũ phát triển y tế thông minh.',
    techTitle: 'Nền tảng công nghệ tin cậy',
    techDesc: 'Hệ thống tích hợp mô phỏng dòng bệnh nhân SimPy, trợ lý AI LLM được neo chuẩn kiến thức y khoa và kiến trúc bảo mật đa lớp RBAC.',
    headerCta: 'Trải nghiệm ngay',
    demoSectionTitle: 'Trải Nghiệm Trực Quan',
    demoSectionSub: 'Chọn giao diện bạn muốn thử nghiệm bên dưới',
    patientHeading: 'Ứng dụng Đồng hành Bệnh nhân',
    patientTag: 'Bệnh nhân',
    patientFeatures: ['Khai báo triệu chứng với trợ lý AI', 'Nhận sơ đồ lộ trình và vị trí phòng khám', 'Xem đơn thuốc, nhắc nhở chuẩn bị khám'],
    staffHeading: 'Console Quản trị & Điều phối',
    staffTag: 'Bệnh viện',
    staffFeatures: ['Theo dõi bản đồ tải phòng khám trực tiếp', 'Duyệt đề xuất lập lại kế hoạch do sự cố', 'Quản lý chỉ định của bác sĩ & nhiệm vụ kỹ thuật viên'],
    launchBtn: 'Khởi chạy ứng dụng',
};

/** The NxC hexagon brand mark shared with the console header and login. */
function BrandMark({ size = 40, textClass = 'text-sm' }: { size?: number; textClass?: string }) {
  return (
    <span
      className="flex shrink-0 items-center justify-center bg-primary shadow-sm shadow-primary/25"
      style={{
        width: size,
        height: size,
        clipPath: 'polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%)',
      }}
    >
      <span className={`font-mono font-extrabold text-white ${textClass}`}>NxC</span>
    </span>
  );
}

export function LandingPage() {
  const c = CONTENT;

  const stats = [
    { value: c.stat1Val, label: c.stat1Label, icon: ClockIcon, chip: 'bg-primary/10 text-primary' },
    { value: c.stat2Val, label: c.stat2Label, icon: HeartPulseIcon, chip: 'bg-success/10 text-success' },
    { value: c.stat3Val, label: c.stat3Label, icon: TrendingUpIcon, chip: 'bg-primary/10 text-primary' },
  ];

  const features = [
    { title: c.feature1Title, desc: c.feature1Desc, icon: StethoscopeIcon },
    { title: c.feature2Title, desc: c.feature2Desc, icon: RouteIcon },
    { title: c.feature3Title, desc: c.feature3Desc, icon: GridIcon },
    { title: c.feature4Title, desc: c.feature4Desc, icon: AssistantIcon },
  ];

  return (
    // `console-surface` swaps the primary token to the NxCare console blue
    // (#2563EB) - the landing brands like the hospital website, not like the
    // teal patient app (index.css scoped token override).
    <div className="console-surface relative min-h-screen overflow-x-hidden bg-background font-sans text-foreground">
      {/* Ambient background - calm clinical: radial washes, a faint blueprint
          grid fading out of the hero, and slow-drifting glow blobs. All
          token-based; the drift is transform-only and disabled under
          prefers-reduced-motion (index.css). */}
      <div aria-hidden="true" className="pointer-events-none absolute inset-0 overflow-hidden">
        <div
          className="absolute inset-0"
          style={{
            background:
              'radial-gradient(70rem 45rem at 15% -10%, hsl(var(--primary) / 0.08), transparent 60%),' +
              'radial-gradient(55rem 40rem at 110% 25%, hsl(var(--primary) / 0.06), transparent 55%)',
          }}
        />
        <div
          className="absolute inset-x-0 top-0 h-[42rem]"
          style={{
            backgroundImage:
              'linear-gradient(hsl(var(--border) / 0.6) 1px, transparent 1px),' +
              'linear-gradient(90deg, hsl(var(--border) / 0.6) 1px, transparent 1px)',
            backgroundSize: '3.5rem 3.5rem',
            maskImage: 'radial-gradient(ellipse 80% 90% at 50% 0%, black 30%, transparent 78%)',
            WebkitMaskImage: 'radial-gradient(ellipse 80% 90% at 50% 0%, black 30%, transparent 78%)',
          }}
        />
        <div className="animate-float-a absolute -top-24 right-[-8%] h-[26rem] w-[26rem] rounded-full bg-primary/10 blur-3xl" />
        <div className="animate-float-b absolute left-[-10%] top-[38rem] h-[30rem] w-[30rem] rounded-full bg-primary/5 blur-3xl" />
        <div className="animate-float-a absolute bottom-40 right-[-6%] h-[24rem] w-[24rem] rounded-full bg-success/10 blur-3xl" />
      </div>

      {/* ------------------------------------------------------------------ */}
      {/* Header                                                              */}
      {/* ------------------------------------------------------------------ */}
      <header className="sticky top-0 z-50 border-b border-border bg-card/85 px-6 py-3.5 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <a href="/landing" className="flex items-center gap-3">
            <BrandMark size={44} />
            <span className="select-none text-2xl font-extrabold tracking-tight text-foreground">
              Nx<span className="text-primary">Care</span>
            </span>
          </a>
          <a
            href="#demo"
            className="inline-flex items-center gap-1.5 rounded-xl bg-primary px-5 py-2.5 text-sm font-bold text-primary-foreground shadow-sm shadow-primary/25 transition-all hover:-translate-y-0.5 hover:shadow-md hover:shadow-primary/30"
          >
            {c.headerCta}
            <ChevronRightIcon className="h-4 w-4" />
          </a>
        </div>
      </header>

      {/* ------------------------------------------------------------------ */}
      {/* Hero - centered copy, product screenshots side by side below         */}
      {/* ------------------------------------------------------------------ */}
      <section className="relative mx-auto max-w-6xl px-6 pb-24 pt-16 lg:pt-20">
        <div className="mx-auto flex max-w-3xl flex-col items-center gap-6 text-center">
          <div className="inline-flex animate-fade-up items-center gap-2 rounded-pill border border-primary/25 bg-primary/10 px-4 py-1.5 text-xs font-bold uppercase tracking-wide text-primary">
            <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-primary" />
            {c.badge}
          </div>

          <h1 className="animate-fade-up text-4xl font-extrabold leading-[1.12] tracking-tight md:text-6xl">
            <span className="block text-foreground">{c.title1}</span>
            <span className="block text-primary">{c.title2}</span>
          </h1>

          <p className="max-w-2xl animate-fade-up text-lg leading-relaxed text-muted-foreground md:text-xl">
            {c.subtitle}
          </p>

          <div className="mt-4 flex w-full animate-fade-up flex-col items-center gap-4 sm:w-auto sm:flex-row">
            <a
              href="/onboarding"
              className="group inline-flex w-full flex-col items-center rounded-2xl bg-primary px-8 py-4 font-bold text-primary-foreground shadow-lg shadow-primary/25 transition-all hover:-translate-y-0.5 hover:shadow-xl hover:shadow-primary/30 sm:w-auto"
            >
              <span className="flex items-center gap-2 text-base">
                {c.patientAppBtn}
                <ChevronRightIcon className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </span>
              <span className="mt-0.5 text-[11px] font-medium opacity-85">{c.patientAppDesc}</span>
            </a>

            <a
              href="/console"
              className="group inline-flex w-full flex-col items-center rounded-2xl border border-border bg-card px-8 py-4 font-bold text-foreground shadow-sm transition-all hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-md sm:w-auto"
            >
              <span className="flex items-center gap-2 text-base">
                {c.consoleBtn}
                <ChevronRightIcon className="h-4 w-4 transition-transform group-hover:translate-x-1" />
              </span>
              <span className="mt-0.5 text-[11px] font-medium text-muted-foreground">{c.consoleDesc}</span>
            </a>
          </div>
        </div>

        {/* Product screenshots side by side - real captures of /console/dashboard
            and /?home=1 (public/landing/). The phone is sized to ~21.5% of the row
            so both frames end up nearly the same height, bottoms aligned. */}
        <div className="relative mt-16 animate-fade-up">
          <div
            aria-hidden="true"
            className="pointer-events-none absolute -inset-x-8 -inset-y-6 rounded-[40px] bg-primary/5 blur-2xl"
          />
          <div className="relative flex flex-col items-center gap-8 md:flex-row md:items-end">
            <div className="w-full flex-1 overflow-hidden rounded-2xl border border-border bg-card shadow-xl shadow-black/5 transition-all duration-300 ease-out hover:-translate-y-2 hover:shadow-2xl hover:shadow-primary/15">
              <div className="flex items-center gap-1.5 border-b border-border bg-muted/60 px-4 py-2.5">
                <span className="h-3 w-3 rounded-full bg-danger/70" />
                <span className="h-3 w-3 rounded-full bg-warning/70" />
                <span className="h-3 w-3 rounded-full bg-success/70" />
                <span className="ml-2 font-mono text-xs text-muted-foreground">nxcare-console-dashboard</span>
              </div>
              <img
                src="/landing/console-dashboard.webp"
                width={1920}
                height={1080}
                loading="eager"
                fetchPriority="high"
                alt="Dashboard điều phối của console bệnh viện: KPI, bản đồ tải, dự báo tải theo giờ và hàng chờ duyệt"
                className="block h-auto w-full"
              />
            </div>
            <div className="w-[220px] shrink-0 overflow-hidden rounded-[28px] bg-card shadow-xl shadow-primary/15 ring-1 ring-border transition-all duration-300 ease-out hover:-translate-y-2 hover:scale-[1.03] hover:shadow-2xl hover:shadow-primary/25 md:w-[21.5%]">
              <img
                src="/landing/patient-app.webp"
                width={780}
                height={1688}
                loading="eager"
                alt="Màn hình Trang chủ của ứng dụng đồng hành bệnh nhân: bước hiện tại Chụp X-quang, còn khoảng 12 phút"
                className="block h-auto w-full"
              />
            </div>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* Features                                                            */}
      {/* ------------------------------------------------------------------ */}
      <section className="relative border-t border-border bg-muted/30 px-6 py-24">
        <div className="mx-auto max-w-6xl">
          <div className="mx-auto mb-14 flex max-w-3xl flex-col gap-3 text-center">
            <h2 className="text-3xl font-extrabold tracking-tight text-foreground md:text-4xl">{c.featuresTitle}</h2>
            <p className="text-base text-muted-foreground md:text-lg">{c.featuresSub}</p>
          </div>

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
            {features.map((feature, i) => {
              const Icon = feature.icon;
              return (
                <div
                  key={i}
                  className="group flex flex-col gap-4 rounded-2xl border border-border bg-card p-6 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-md"
                >
                  <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 text-primary transition-transform duration-200 group-hover:scale-105">
                    <Icon className="h-6 w-6" />
                  </span>
                  <div className="flex flex-col gap-2">
                    <h3 className="text-lg font-bold text-foreground">{feature.title}</h3>
                    <p className="text-sm leading-relaxed text-muted-foreground">{feature.desc}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* Demo portal cards                                                   */}
      {/* ------------------------------------------------------------------ */}
      <section id="demo" className="mx-auto max-w-6xl scroll-mt-24 px-6 py-24">
        <div className="mx-auto mb-14 flex max-w-3xl flex-col gap-3 text-center">
          <h2 className="text-3xl font-extrabold tracking-tight text-foreground md:text-4xl">{c.demoSectionTitle}</h2>
          <p className="text-base text-muted-foreground md:text-lg">{c.demoSectionSub}</p>
        </div>

        <div className="mx-auto grid max-w-5xl gap-8 md:grid-cols-2">
          {/* Patient app card */}
          <div className="group flex flex-col gap-6 rounded-3xl border border-primary/25 bg-primary/5 p-8 shadow-sm transition-all duration-200 hover:-translate-y-1 hover:shadow-lg hover:shadow-primary/10">
            <div className="flex items-start justify-between">
              <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                <HeartPulseIcon className="h-6 w-6" />
              </span>
              <span className="rounded-pill border border-primary/25 bg-primary/10 px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-primary">
                {c.patientTag}
              </span>
            </div>
            <div className="flex flex-col gap-2">
              <h3 className="text-2xl font-bold text-foreground">{c.patientHeading}</h3>
              <ul className="mt-2 flex flex-col gap-2.5">
                {c.patientFeatures.map((feat, idx) => (
                  <li key={idx} className="flex items-center gap-2.5 text-sm text-foreground/85">
                    <CheckIcon className="h-4 w-4 shrink-0 text-primary" />
                    {feat}
                  </li>
                ))}
              </ul>
            </div>
            <a
              href="/onboarding"
              className="mt-auto w-full rounded-xl bg-primary py-3.5 text-center font-bold text-primary-foreground shadow-sm shadow-primary/25 transition-all hover:brightness-95"
            >
              {c.launchBtn}
            </a>
          </div>

          {/* Hospital console card */}
          <div className="group flex flex-col gap-6 rounded-3xl border border-primary/25 bg-primary/5 p-8 shadow-sm transition-all duration-200 hover:-translate-y-1 hover:shadow-lg hover:shadow-primary/10">
            <div className="flex items-start justify-between">
              <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-primary/10 text-primary">
                <GridIcon className="h-6 w-6" />
              </span>
              <span className="rounded-pill border border-primary/25 bg-primary/10 px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-primary">
                {c.staffTag}
              </span>
            </div>
            <div className="flex flex-col gap-2">
              <h3 className="text-2xl font-bold text-foreground">{c.staffHeading}</h3>
              <ul className="mt-2 flex flex-col gap-2.5">
                {c.staffFeatures.map((feat, idx) => (
                  <li key={idx} className="flex items-center gap-2.5 text-sm text-foreground/85">
                    <CheckIcon className="h-4 w-4 shrink-0 text-primary" />
                    {feat}
                  </li>
                ))}
              </ul>
            </div>
            <a
              href="/console"
              className="mt-auto w-full rounded-xl bg-primary py-3.5 text-center font-bold text-primary-foreground shadow-sm shadow-primary/25 transition-all hover:brightness-95"
            >
              {c.launchBtn}
            </a>
          </div>
        </div>
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* Stats                                                               */}
      {/* ------------------------------------------------------------------ */}
      <section className="border-t border-border bg-muted/30 px-6 py-20">
        <div className="mx-auto grid max-w-6xl gap-6 md:grid-cols-3">
          {stats.map((stat, i) => {
            const Icon = stat.icon;
            return (
              <div
                key={i}
                className="flex items-center gap-4 rounded-2xl border border-border bg-card p-6 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-md"
              >
                <span className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl ${stat.chip}`}>
                  <Icon className="h-6 w-6" />
                </span>
                <div className="flex flex-col gap-0.5">
                  <span className="font-mono text-3xl font-extrabold tabular-nums text-foreground">{stat.value}</span>
                  <span className="text-sm font-semibold text-muted-foreground">{stat.label}</span>
                </div>
              </div>
            );
          })}
        </div>
        <p className="mx-auto mt-6 max-w-6xl text-center text-xs text-muted-foreground/80">{c.statsNote}</p>
      </section>

      {/* ------------------------------------------------------------------ */}
      {/* Tech note + footer                                                  */}
      {/* ------------------------------------------------------------------ */}
      <section className="mx-auto max-w-3xl px-6 py-20 text-center">
        <div className="flex flex-col items-center gap-4">
          <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-primary/10 text-primary">
            <SparkleIcon className="h-5 w-5" />
          </span>
          <h2 className="text-2xl font-bold text-foreground">{c.techTitle}</h2>
          <p className="text-sm leading-relaxed text-muted-foreground md:text-base">{c.techDesc}</p>
        </div>
      </section>

      <footer className="border-t border-border bg-card px-6 py-8 text-center text-sm text-muted-foreground">
        <div className="mx-auto flex max-w-6xl flex-col items-center gap-3">
          <div className="flex items-center gap-2">
            <BrandMark size={28} textClass="text-[9px]" />
            <span className="text-sm font-bold text-foreground">
              Nx<span className="text-primary">Care</span>
            </span>
          </div>
          {c.footerText}
        </div>
      </footer>
    </div>
  );
}
