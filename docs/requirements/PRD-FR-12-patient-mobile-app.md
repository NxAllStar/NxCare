---
title: "PRD: Patient mobile app - golden path, IA, and feature architecture"
sidebar_label: "PRD-FR-12"
description: "Product requirements document for the patient-facing mobile companion app: golden path, information architecture, sitemap, and feature-module detail behind SCR-01/SCR-02."
status: Draft
tags: [prd, requirements, patient-app]
---

# PRD: Patient mobile app - golden path, IA, and feature architecture (FR-12)

> Source requirement: [FR-12](../specs/05-functional-requirements.md#fr-12) (coordinator dashboard +
> all UI screens - the routing table in `AGENTS.md` places all UI/screen work, including the patient
> surface, under this FR umbrella).
>
> This PRD elaborates the patient mobile app surface behind the two accepted screens
> [SCR-01 Intake chat](../specs/10-ui-ux-wireframes.md#scr-01-intake-chat) and
> [SCR-02 Journey timeline](../specs/10-ui-ux-wireframes.md#scr-02-journey-timeline) in
> [spec 10](../specs/10-ui-ux-wireframes.md), and touches the following existing FRs directly:
> [FR-01](../specs/05-functional-requirements.md#fr-01),
> [FR-02](../specs/05-functional-requirements.md#fr-02),
> [FR-04](../specs/05-functional-requirements.md#fr-04),
> [FR-05](../specs/05-functional-requirements.md#fr-05),
> [FR-06](../specs/05-functional-requirements.md#fr-06),
> [FR-07](../specs/05-functional-requirements.md#fr-07),
> [FR-09](../specs/05-functional-requirements.md#fr-09),
> [FR-11](../specs/05-functional-requirements.md#fr-11),
> [FR-17](../specs/05-functional-requirements.md#fr-17),
> [FR-18](../specs/05-functional-requirements.md#fr-18),
> [FR-19](../specs/05-functional-requirements.md#fr-19),
> [FR-20](../specs/05-functional-requirements.md#fr-20),
> [FR-21](../specs/05-functional-requirements.md#fr-21). Where a described capability has no matching
> FR today, it is called out in [Open questions](#7-open-questions) rather than silently mapped.

<!-- Relocation note: this document is assembled from two untracked, root-level design-brief files
     that predated docs governance - `Patient_GoldenPath_IA_Sitemap.md` (golden path, IA, sitemap) and
     `Patient_Mobile_App_Feature_Architecture.md` (v2, modules M1-M10). The Vietnamese content is
     preserved verbatim from those sources; only the framing headings, table-of-contents shape, and
     this note are new, added to fit docs/templates/PRD.md. Emoji appearing inside preserved source
     blocks (tab-bar icons, priority markers such as star/P0) are original source content kept as-is
     for fidelity to the design brief being relocated, not new additions - see docs-workflow.md. -->

## 1. Context and problem

VI: Xây dựng **AI-first Hospital Companion** cho bệnh nhân và người nhà, trong đó **AI Smart
Scheduling** và **AI Care Journey** là hai năng lực cốt lõi giúp giảm thời gian chờ, tối ưu luồng khám
và biến trải nghiệm bệnh viện từ *hỗn loạn, mù mờ* thành *được đồng hành, minh bạch*.

EN: Build an AI-first Hospital Companion for patients and family members, where AI Smart Scheduling
and AI Care Journey are the two core capabilities that cut wait time, optimise the visit flow, and
turn the hospital experience from confusing and opaque into accompanied and transparent.

**Ba nguyên tắc thiết kế xuyên suốt / three design principles throughout:**

1. **AI cân bằng - "assist, don't take over".** AI luôn *đề xuất*, con người *quyết*. Không chẩn đoán,
   không thay bác sĩ. / AI always suggests, a human always decides; no diagnosis, no replacing the
   doctor.
2. **Một sự thật, nhiều góc nhìn.** Bệnh nhân thấy cùng dữ liệu (ETA, lộ trình, kết quả) mà bác sĩ
   thấy - chỉ khác giao diện. / One truth, many views: the patient sees the same ETA, pathway, and
   result data the doctor sees, only the presentation differs.
3. **Chủ động thay vì phản ứng.** App nhắc trước, chuẩn bị trước, giải thích trước - không đợi bệnh
   nhân hỏi. / Proactive, not reactive: the app reminds, prepares, and explains ahead of time.

**Persona dùng xuyên suốt tài liệu nguồn / persona used throughout the source brief:** bà Nguyễn Thị
Lan, 68 tuổi, đau bụng dưới + sốt nhẹ, con gái (chị Hương) theo dõi từ xa - dùng để giữ mọi màn hình
bám sát trải nghiệm thật của một bệnh nhân lớn tuổi và người thân ở xa. This persona is a synthetic
demo persona, not a real patient record.

**Nền tảng / platform:** Mobile-first (iOS/Android); web companion là bản mở rộng / a web companion
is the extended form. Tiếng Việt, tối ưu cho cả người lớn tuổi / Vietnamese-first, tuned for older
users too. This aligns with the "one responsive, role-gated web app" decision already recorded in
[01 App concept and platform](../specs/01-overview.md) and [AS-06](../specs/11-assumptions-constraints.md)
(no self-registration this release) - the mobile-first *presentation* described here is the patient
role's rendering of that one app, not a second, separate application.

The source IA document states it is "cặp đôi với `Clinician_GoldenPath_IA_Sitemap.md`" (paired with a
clinician-side golden-path/IA/sitemap document, so the two apps show "the same truth, different
interfaces"). That sibling file was not found in this repository at relocation time - see
[Open questions](#7-open-questions).

## 2. Goals and success metrics

VI: Nguồn không nêu số liệu mục tiêu cụ thể (baseline/target) cho các mục tiêu bên dưới; chỉ nêu định
hướng định tính. Không suy diễn số liệu ở đây - xem mục 7. / The source material states no quantified
baseline or target for the goals below, only qualitative direction. No number is invented here - see
section 7.

Qualitative goals stated or clearly implied by the source brief:

- Reduce perceived and actual wait time / congestion through least-crowded-slot suggestions and a
  transparent queue ("why am I waiting").
- Reduce no-show through proactive, pre-visit reminders (fasting, bring old prescriptions/results).
- Replace a reactive, opaque hospital visit with a proactively-guided, explained one (the three design
  principles above).
- Give remote family members ("Bring-someone") real-time visibility into a relative's visit without
  requiring the relative to operate the app themselves.

| Metric | Baseline | Target |
|--------|----------|--------|
| Patient-perceived wait time / congestion | Not specified in source; see [OI-08](../specs/11-assumptions-constraints.md#oi-08) (existing open baseline question) | Not specified in source |
| No-show rate | Not specified in source | Not specified in source |
| Adoption of "Bring-someone" among family accounts | Not specified in source | Not specified in source |

## 3. Scope

### In scope

- The patient mobile app's information architecture: a fixed 5-tab bar (Trang chủ / Lịch khám / Lộ
  trình / Hồ sơ sức khỏe / Thêm) plus an always-reachable assistant FAB, described in full in
  [3.2 Information architecture](#32-information-architecture).
- The full screen sitemap (`/home`, `/book`, `/intake`, `/checkin`, `/journey`, `/assistant`, etc.),
  tagged P0/P1/P2, in [3.1 Screen sitemap](#31-screen-sitemap).
- Ten feature modules (M1-M10) covering scheduling, care journey, medical records, medication and
  recovery, payments display, family care, communications, and settings/accessibility - detailed in
  [section 4](#4-detailed-requirements).
- The golden-path walkthrough (13 steps) and the five moments the source brief calls out as must-demo
  - see [section 5](#5-user-flow).
- Visual/design direction specific to the patient surface (light, calm, large-type, one-handed,
  register distinct from the clinician/coordinator surface) - see [section 6](#6-technical-constraints).

### Out of scope (explicit, per source)

- **Module 9 - Preventive Care & Wellness (P2):** the source brief itself marks this "tầm nhìn, không
  làm ở hackathon" (vision only, not built for the hackathon), including wearable integration and
  gamified health insights.
- **Telehealth video consults (part of Module 8, P2):** listed as vision, not committed for this
  release.
- **Full emergency coordination:** Module 8's Emergency screen is explicitly scoped narrow in the
  source - "chỉ gọi 115 + hiển thị cơ sở gần nhất... KHÔNG hứa điều phối cấp cứu" (only call 115 and
  show the nearest facility, no promise of emergency coordination) - consistent with the existing
  escalation mechanism in [BF-05](../specs/04-business-flows.md) and
  [FR-01](../specs/05-functional-requirements.md#fr-01), which also only flags a candidate emergency
  and hands off to staff.
- **Patient self-registration / onboarding as a full flow:** the source sitemap lists `/welcome` and
  `/profile-setup` as P2/P0 onboarding screens, but [AS-06](../specs/11-assumptions-constraints.md)
  already records that this release has no patient self-registration (patients are created via seed
  or intake). This PRD does not change that assumption; onboarding screens in the sitemap are noted as
  P2/vision pending that decision.
- **Learning loop / self-improving forecasts:** out of scope per
  [FR-16](../specs/05-functional-requirements.md#fr-16) (Won't, this release); nothing in this PRD
  reopens that.
- **Real in-app payment processing:** see the payment-scope conflict flagged in
  [Open questions](#7-open-questions) - the existing accepted constraint
  ([AS-02](../specs/11-assumptions-constraints.md), [FR-05](../specs/05-functional-requirements.md#fr-05))
  is that the app never processes money, only a proceed/paid flag; this PRD does not override that,
  it surfaces the conflict for a human decision.

### 3.1 Screen sitemap

Tag: `P0` phải có để demo · `P1` khác biệt · `P2` tầm nhìn / must-have for the demo, differentiator,
and vision-only respectively.

```
PATIENT MOBILE APP
│
├── ONBOARDING (lần đầu)
│   ├── /welcome                    Giới thiệu 3 slide                    [P2]
│   ├── /login                      SĐT + OTP                             [P0]
│   ├── /profile-setup              Hồ sơ: dị ứng, bệnh nền, thuốc        [P0]
│   └── /link-insurance             Liên kết BHYT / mã BN                 [P1]
│
├── GLOBAL (mọi màn hình)
│   ├── Family switcher (header)    Đổi hồ sơ bản thân/mẹ/con             [P1]
│   ├── /notifications              Trung tâm thông báo hợp nhất          [P1]
│   └── FAB → /assistant            Journey Agent chat (nổi mọi nơi)      [P0]
│
├── TAB 1 — TRANG CHỦ
│   ├── /home                       HOME (đổi chế độ theo vị trí)   ★     [P0]
│   │   │  Layout: đổi hẳn theo ngữ cảnh
│   │   ├── [ngoài viện] Dashboard:
│   │   │     lịch sắp tới · nhắc prep · kết quả mới · shortcut
│   │   └── [trong viện] LIVE COMPANION:
│   │         bước hiện tại full · ETA đếm ngược · chỉ đường ·
│   │         "AI đang làm gì" · "vì sao chờ"
│   └── (Family switcher ở đầu màn)
│
├── TAB 2 — LỊCH KHÁM
│   ├── /appointments               Lịch sắp tới + lịch sử                [P0]
│   ├── /book                       ĐẶT LỊCH                              [P0]
│   │   │  Layout: bước wizard (chuyên khoa → bác sĩ → giờ)
│   │   ├── Chọn chuyên khoa / bác sĩ
│   │   ├── AI gợi giờ ít đông (badge "chờ ~X phút")
│   │   └── Xác nhận
│   ├── /intake                     AI INTAKE (hội thoại)          ★     [P0]
│   │   │  Layout: chat tiếng Việt full màn
│   │   ├── Mô tả triệu chứng
│   │   ├── Banner "gợi ý định tuyến, không phải chẩn đoán"
│   │   └── Kết quả: chuyên khoa đề xuất + slot
│   ├── /checkin                    QR / REMOTE CHECK-IN                  [P0]
│   │   └── Quét QR → vào hàng đợi → chuyển Live Companion
│   └── /prep/:id                   PROACTIVE PREP  (mới)                 [P1]
│         Nhắc nhịn ăn / mang giấy tờ trước buổi khám
│
├── TAB 3 — LỘ TRÌNH CỦA TÔI
│   ├── /journey                    CARE PATHWAY TIMELINE          ★     [P0]
│   │   │  Layout: current-step hero card trên · timeline dọc dưới
│   │   ├── Bước hiện tại (hero card lớn)
│   │   ├── Timeline dọc (done/đang/sắp) + dự kiến xong
│   │   ├── "Vì sao thứ tự này?" (giải thích đời thường)
│   │   └── Số thứ tự + queue realtime
│   ├── /journey/step/:id           STEP DETAIL / WAYFINDING              [P1]
│   │   │  Layout: mini map trên · hướng dẫn + QR dưới
│   │   ├── Bản đồ "bạn → phòng đích" + chỉ đường lời
│   │   ├── QR check-in tại phòng
│   │   └── "Vì sao chờ" + queue position
│   └── /journey/updates            LỊCH SỬ CẬP NHẬT LỘ TRÌNH             [P2]
│         Các lần AI đổi lịch + lý do
│
├── TAB 4 — HỒ SƠ SỨC KHỎE
│   ├── /records                    HỒ SƠ SỨC KHỎE                       [P1]
│   │   ├── Dị ứng, bệnh nền, thuốc đang dùng
│   │   └── Lịch sử khám
│   ├── /results                    KẾT QUẢ XÉT NGHIỆM / CĐHA            [P1]
│   │   │  Layout: list kết quả → detail
│   │   ├── Danh sách kết quả
│   │   └── AI giải thích HẸP: "trong/ngoài ngưỡng" +
│   │         "hãy hỏi bác sĩ" (KHÔNG chẩn đoán)
│   ├── /medications                ĐƠN THUỐC & NHẮC UỐNG                [P1]
│   │   ├── Đơn thuốc điện tử (liều, cách dùng)
│   │   ├── Nhắc uống thuốc
│   │   └── Cảnh báo tương tác / dị ứng
│   ├── /recovery                   THEO DÕI HỒI PHỤC                     [P1]
│   │   │  (khung an toàn: thu thập → cảnh báo → đẩy bác sĩ)
│   │   ├── Symptom diary
│   │   ├── Recovery check-in (agent hỏi thăm)
│   │   └── Ngưỡng cảnh báo → giục liên hệ bác sĩ
│   └── /visit-summary/:id          TÓM TẮT LẦN KHÁM + PDF               [P1]
│
├── TRỢ LÝ (FAB — mọi nơi)
│   └── /assistant                  JOURNEY AGENT CHAT             ★     [P0]
│       │  Layout: chat tiếng Việt + gợi ý câu hỏi nhanh
│       ├── Chat ngữ cảnh (biết lộ trình hiện tại)
│       ├── Suy luận ràng buộc (nhịn ăn, chờ kết quả)
│       ├── Chip "Đã cập nhật" khi đổi được lộ trình
│       └── Gợi ý câu hỏi nhanh (tap được)
│
└── TAB 5 — THÊM
    ├── /billing                    VIỆN PHÍ & BHYT                      [P1]
    │   ├── Ước tính chi phí trước
    │   ├── BHYT: mức chi trả + đồng chi trả
    │   ├── Thanh toán QR / thẻ / ví
    │   └── Hóa đơn + lịch sử
    ├── /family                     GIA ĐÌNH (FAMILY CARE)               [P1]
    │   │  Layout: danh sách hồ sơ + chi tiết
    │   ├── Quản lý nhiều hồ sơ (mẹ/con)
    │   ├── BRING-SOMEONE: theo dõi realtime người thân
    │   │     trong viện + thông báo theo bước
    │   ├── Chat hộ với Journey Agent
    │   └── Phân quyền chia sẻ
    ├── /telehealth                 KHÁM TỪ XA (video)                   [P2]
    ├── /emergency                  KHẨN CẤP (phạm vi hẹp)               [P2]
    │     chỉ gọi 115 + cơ sở gần nhất (KHÔNG hứa điều phối)
    ├── /settings                   CÀI ĐẶT                              [P1]
    │   ├── Contextual consent log (đạo đức AI)
    │   ├── Quyền riêng tư, thiết bị đăng nhập
    │   ├── Đa ngôn ngữ
    │   └── Accessibility: cỡ chữ lớn, tương phản cao
    └── /wellness                    PHÒNG NGỪA & SỨC KHỎE               [P2]
          Health trends · nhắc khám định kỳ (tầm nhìn, không làm)
```

Note: `/billing`'s "Thanh toán QR / thẻ / ví" (online payment) line is carried unchanged from source
for fidelity, but see the payment-scope conflict in [Open questions](#7-open-questions) before this
is built.

### 3.2 Information architecture

VI nguyên tắc IA (khác Clinician - đây là mobile cho người lo lắng) / IA principles (unlike the
clinician surface - this is mobile, for an anxious user):

1. **Tab bar 5 mục cố định**, ngón cái với tới, nhãn tiếng Việt rõ. Không menu ẩn nhiều tầng - người
   lớn tuổi không đào sâu. / A fixed 5-item tab bar, thumb-reachable, plain Vietnamese labels; no deep
   hidden menus - older users will not dig.
2. **Home đổi chế độ theo NGỮ CẢNH VỊ TRÍ** (signature): ngoài viện = dashboard; trong viện = Live
   Companion 1-mục-đích. Đây là quyết định IA quan trọng nhất. / Home switches mode by location
   context - the single most important IA decision, and the app's signature.
3. **Trợ lý AI cân bằng - nút nổi (FAB) luôn với tới, nhưng không chiếm màn hình.** Chat là *lối vào
   phụ trợ*, không phải trung tâm. / The AI assistant is a reachable floating action button, an
   auxiliary entry point, never the center of the screen ("AI does not dominate").
4. **Một sự thật:** ETA, lộ trình, kết quả bệnh nhân thấy = đúng dữ liệu bác sĩ thấy. / One truth: the
   patient's ETA, pathway, and results are the same data the doctor sees.
5. **Family switcher ở đầu Home:** một tài khoản, chuyển nhanh giữa các hồ sơ (bản thân / mẹ / con). /
   A family switcher at the top of Home: one account, fast switching between profiles.

Navigation structure (source ASCII layout, preserved):

```
+- STATUS BAR + CONTEXT HEADER --------------------+
|  [Family switcher: Ba Lan]           Notifications |  <- doi ho so + bao
+---------------------------------------------------+
|                                                    |
|              WORKSPACE (1 man hinh)                |
|         (Home doi che do theo vi tri)              |
|                                                    |
|                                    +----------+    |
|                                    | Assistant |    |  <- FAB chat,
|                                    |  (FAB)   |    |     luon voi toi
|                                    +----------+    |
+---------------------------------------------------+
|  Trang chu   Lich kham   Lo trinh   Ho so   Them   |  <- TAB BAR 5 muc
+---------------------------------------------------+
```

Năm tab -> nội dung / five tabs to content:

| Tab | Chứa gì / contains | Module |
|---|---|---|
| Trang chủ | Home 2 chế độ (dashboard / Live Companion) / Home, two modes | M1 |
| Lịch khám | Đặt lịch, Intake, check-in, lịch sắp tới / booking, intake, check-in, upcoming | M2 |
| Lộ trình | Care Journey timeline, wayfinding, why-waiting | M3 |
| Hồ sơ sức khỏe | EMR, kết quả, đơn thuốc, recovery / records, results, prescriptions, recovery | M4, M5 |
| Thêm | Viện phí, Gia đình, Thông báo, Cài đặt / billing, family, notifications, settings | M6, M7, M8, M10 |

FAB "Trợ lý" (Journey Agent) nổi trên mọi tab - M3 / the assistant FAB floats on every tab.

Home mode-switch logic (signature IA decision):

```
        Benh nhan o dau?
              |
   +----------+-----------+
   v                       v
NGOAI VIEN              TRONG VIEN (da check-in / dinh vi)
= Dashboard             = LIVE COMPANION MODE
- lich sap toi          - buoc hien tai chiem full man hinh
- nhac prep             - ETA dem nguoc + nut chi duong
- ket qua moi           - "AI dang lam gi cho ban"
- shortcut              - "vi sao cho"
```

Đây là điểm nhận diện - thiết kế phải cho thấy rõ **hai trạng thái khác hẳn nhau** của cùng tab Trang
chủ. / This is the signature moment - design must make the two states of the same Home tab visibly,
unmistakably different.

## 4. Detailed requirements

Ưu tiên nguồn / source priority scale: `P0` = lõi hackathon, phải chạy thật (core, must run for
real) · `P1` = tạo khác biệt (differentiator) · `P2` = tầm nhìn, làm sau (vision, later). This scale
is preserved as-is from the source brief; it is informational context for build sequencing and is
not a substitute for the project's Must/Should/Could/Won't priority vocabulary used in
[05-functional-requirements.md](../specs/05-functional-requirements.md).

| ID | Module | Priority (source) | Requirement (summary) | Serves (existing FR) or status |
|----|--------|--------------------|------------------------|----------------------------------|
| PMA-M1 | Home & Live Companion | P0 | Home has two context-switched modes: an out-of-hospital dashboard (upcoming visits, prep reminders, new results, shortcuts) and an in-hospital "Live Companion" full-screen single-purpose view (current step, counting-down ETA, wayfinding button, "what AI is doing for you"). Auto-activates on check-in/location. | Elaborates [FR-04](../specs/05-functional-requirements.md#fr-04), [FR-06](../specs/05-functional-requirements.md#fr-06); the Home-mode-switch UX is new, not yet a named FR - see [Open questions](#7-open-questions) |
| PMA-M2 | AI Smart Scheduling (incl. Intake) | P0 | Specialty/doctor/time-slot booking; AI suggests least-crowded slots and predicted wait as a range; multi-service scheduling into one pathway; remote/QR check-in; smart reschedule. AI Intake Agent routes (never diagnoses) from natural-language Vietnamese symptoms, with the mandatory guardrail banner "this is a routing suggestion, not a diagnosis," staff confirming at the desk. Proactive Prep messages sent ahead of the visit (fasting, bring old prescriptions/results). | [FR-01](../specs/05-functional-requirements.md#fr-01), [FR-02](../specs/05-functional-requirements.md#fr-02), [FR-07](../specs/05-functional-requirements.md#fr-07), [FR-19](../specs/05-functional-requirements.md#fr-19); Proactive Prep is new, not yet a named FR |
| PMA-M3 | AI Care Journey | P0 | Full-visit timeline (current -> next -> expected finish), per-step ETA as a range, realtime queue, plain-language "why this order," in-hospital wayfinding, self-updating journey with a gentle notification and a reason on change. "Why am I waiting?" shows the reason behind a wait (e.g. "3 people ahead, one emergency just pre-empted -> +8 min"), not just a number. Journey Agent chat reasons over real constraints (fasting, pending results) and can reorder steps within permitted limits. | [FR-04](../specs/05-functional-requirements.md#fr-04), [FR-06](../specs/05-functional-requirements.md#fr-06), [FR-09](../specs/05-functional-requirements.md#fr-09), [FR-11](../specs/05-functional-requirements.md#fr-11); "Why am I waiting?" overlaps the queue-transparency concept already open at [OI-22](../specs/11-assumptions-constraints.md#oi-22) / [TASK-017](../tasks/active/TASK-017-queue-transparency-brainstorm.md) - reconcile before building |
| PMA-M4 | Medical Records & Health Intelligence | P1 | Personal health record: allergies, conditions, current medications (feeding AI safety checks); visit/diagnosis/doctor history; lab/imaging results when available; visit summary; PDF export/share. Narrow guardrail: AI only labels a result "within/outside reference range" plus term explanation, never infers disease, prognosis, or treatment; every abnormal result carries "discuss this with your doctor." | No matching FR today - candidate new FR, see [Open questions](#7-open-questions) |
| PMA-M5 | Medication & Recovery | P1 | Electronic prescription (drug, dose, usage), medication reminders, AI interaction/allergy warnings cross-checked against M4 data. Recovery tracking in a safety frame (collect -> flag -> refer to doctor): symptom diary, agent check-ins ("feeling better today?"), the agent never advises treatment, only escalates past a warning threshold; automatic follow-up reminders and one-tap follow-up booking. | No matching FR today - candidate new FR, see [Open questions](#7-open-questions) |
| PMA-M6 | Payments & Insurance | P1 | Pre-service cost estimate, insurance (BHYT) coverage and co-pay lookup, online payment (wallet/card/QR), detailed invoice and transaction history. | Conflicts with [FR-05](../specs/05-functional-requirements.md#fr-05) / [AS-02](../specs/11-assumptions-constraints.md) (app processes no money, proceed-flag only) - see [Open questions](#7-open-questions); display of billing/coverage information does not conflict |
| PMA-M7 | Family Care Platform | P1 | One account manages multiple patient profiles (elderly parent, child); progress tracking, record sharing, permissioning. "Bring-someone": a remote family member sees realtime pathway progress and step-by-step notifications for a relative in the hospital, and can chat with the Journey Agent on the relative's behalf. | No matching FR today - candidate new FR, see [Open questions](#7-open-questions) |
| PMA-M8 | Communication & Telehealth | P2 | Unified notification center (schedule, results, billing, medication, follow-up); simple-case video follow-up; secure messaging with the clinic; narrow-scope Emergency screen (call 115 + show nearest facility only, no coordination promise); hotline. | Notification center elaborates [FR-20](../specs/05-functional-requirements.md#fr-20); Emergency aligns with [BF-05](../specs/04-business-flows.md) / [FR-01](../specs/05-functional-requirements.md#fr-01) guardrail scope; telehealth video and secure messaging are new, vision-tier (P2) |
| PMA-M9 | Preventive Care & Wellness | P2 | Health trends, AI reminders for periodic checkups, wearable integration, light gamification. | Out of scope this release per source itself - see [Scope](#3-scope) |
| PMA-M10 | Settings, Privacy & Accessibility | P1 | Contextual consent: consent requested in-context each time AI is about to use data (routing, cross-department record sharing), one tap, not buried in Settings. Plus privacy management, device/session management, multi-language, accessibility (large type, high contrast, one-handed, screen reader). | Multi-language/settings elaborates [FR-21](../specs/05-functional-requirements.md#fr-21); device/session touches [FR-18](../specs/05-functional-requirements.md#fr-18); Contextual Consent is new, not yet a named FR - see [Open questions](#7-open-questions) |

### 4.1 AI agents present in the patient app

The patient app surfaces (directly or ambiently) the same six agents already specified elsewhere in
the spec set - this table is a cross-reference, not a new agent inventory:

| Agent | Appears in | Existing FR |
|---|---|---|
| Intake | M2 (symptom chat, routing) | [FR-01](../specs/05-functional-requirements.md#fr-01) |
| Care Plan | M3 (generates the pathway from signed doctor orders) | [FR-04](../specs/05-functional-requirements.md#fr-04) |
| Journey | M1, M3 (Live Companion, chat, escort) | [FR-06](../specs/05-functional-requirements.md#fr-06) |
| Forecast | M2 (least-crowded time), M3 (ETA, why-waiting) | [FR-07](../specs/05-functional-requirements.md#fr-07) |
| Disruption | M3 (reschedule notification with a reason) | [FR-09](../specs/05-functional-requirements.md#fr-09) |
| Coordinator | Ambient - the patient does not see it directly | [FR-10](../specs/05-functional-requirements.md#fr-10) |

### 4.2 Priority roll-up (source)

| Module | Priority | Note |
|---|---|---|
| M1 Home + Live Companion | P0 | Signature - build deep |
| M2 Smart Scheduling + Intake | P0 | Core |
| M3 Care Journey + Agent | P0 | The heart of the experience |
| M4 Medical Records | P1 | Narrow result-explanation guardrail |
| M5 Medication & Recovery | P1 | Safe recovery guardrail |
| M6 Payments & Insurance | P1 | Frame only, simulated integration - subject to the payment-scope conflict above |
| M7 Family + Bring-someone | P1 | Bring-someone fits the Vietnamese context well |
| M8 Telehealth | P2 | Emergency kept narrow-scope |
| M9 Preventive/Wellness | P2 | Vision, not built |
| M10 Privacy + Accessibility | P1 | Contextual consent is a scoring differentiator |

## 5. User flow

### 5.1 Golden path (13 steps)

Persona used to keep every screen honest to a lived patient experience: bà Nguyễn Thị Lan, 68 tuổi,
đau bụng dưới + sốt nhẹ, con gái (chị Hương) theo dõi từ xa.

```
   MAN HINH APP              BENH NHAN TRAI NGHIEM             AI HO TRO (ngam)
--------------------------------------------------------------------------------
1  Onboarding      --->  Dang nhap OTP, them ho so    --->  (luu di ung, benh nen
                        ba Lan vao tai khoan               -> feed canh bao sau)
                        con gai (Family Care)

2  Dat lich +      --->  Mo ta "dau bung duoi, sot     --->  Intake dinh tuyen
   Intake                nhe 2 hom" bang tieng Viet          -> Ngoai tong quat
                        -> app goi y slot 10:15 it dong       Forecast goi y gio
                        "goi y, khong phai chan doan"

3  Proactive Prep  --->  Toi hom truoc nhan nhac:      --->  chu dong, giam no-show
                        "nhin an tu 22h, mang don cu"

4  Den vien        --->  Quet QR check-in -> app CHUYEN --->  tinh ETA, vao hang
   QR check-in           sang LIVE COMPANION MODE            doi kham

5  Cho kham        --->  Man hinh 1-muc-dich: "dang    --->  Coordinator dan tai
   (Live Companion)      cho kham, ~12 phut" + "Vi sao
                        cho?": 3 nguoi truoc + 1 cap cuu

6  Kham xong,      <---  Lo trinh hien ra: mau -> X-quang <-- Care Plan sinh
   nhan lo trinh         -> sieu am -> quay lai BS               task list (tu chi
                        + "vi sao thu tu nay"                 dinh BS da ky)
                                                             Journey ho tong

7  Di lam dich vu  --->  Tung buoc: "den phong X1 tang --->  cap nhat realtime khi
   theo lo trinh         1" + chi duong + dem nguoc           KTV nhap ket qua

8  SU CO may hong  <---  Thong bao nhe: "Lo trinh vua  <-- Disruption re-plan
                        cap nhat - sieu am truoc, X-quang
                        sau, do may X1 ban. +6 phut."

9  Chat tro ly     --->  "Toi doi qua, an truoc duoc   --->  Journey suy luan:
                        khong?" -> "Mau lay roi, chi an        mau da lay -> cho phep
                        nhe duoc, em giu cho sieu am"         + doi thu tu

10 Con gai theo    --->  Chi Huong (o xa) nhan: "Me vua --->  Bring-someone: chia se
   doi tu xa             xong X-quang, dang cho sieu am"       trang thai realtime

11 Nhan ket qua +  <---  Ket qua co + don thuoc dien tu <-- (tu BS ke don)
   don thuoc             + nhac uong thuoc + canh bao
                        tuong tac

12 Thanh toan      --->  Xem hoa don + BHYT -> thanh      --->  (dong bo billing)
                        toan QR

13 Sau dieu tri    --->  Huong dan cham soc + nhac tai   --->  Recovery (khung an
                        kham + symptom diary                 toan: canh bao->bac si)
```

**Năm khoảnh khắc phải demo được / five moments the source brief calls must-demo (every screen
prioritises serving these five):**

1. **Step 2 - Intake hội thoại tiếng Việt** -> smart routing with the "suggestion, not diagnosis"
   guardrail.
2. **Steps 4-5 - Live Companion Mode** -> signature: the app changes mode by location, "why am I
   waiting."
3. **Step 6 - Care Journey timeline + "why this order"** -> the heart of the experience.
4. **Steps 8-9 - Journey self-updates + "can I eat" chat** -> AI-native, reasoning over real
   constraints.
5. **Step 10 - Bring-someone** -> a remote daughter follows along, a strong fit for Vietnam.

## 6. Technical constraints

### 6.1 Visual/design direction (patient surface)

This is patient-specific detail supplementing, not replacing, the accepted
["Visual design direction"](../specs/10-ui-ux-wireframes.md#visual-design-direction) section already
in spec 10. Where the two differ in emphasis, spec 10 governs the app-wide design system; this section
governs patient-surface nuance.

- **Register:** khác hẳn Clinician - sáng, dịu, trấn an, mobile-first / distinctly unlike the
  clinician surface - light, calm, reassuring, mobile-first. Soft rounded corners, generous white
  space, not a "control room." The user is anxious and may be elderly.
- **Màu ngữ nghĩa (giữ chung với hệ thống) / semantic colour (shared system):** cyan = AI đang giúp
  bạn (AI is helping you) · amber = cần chú ý (needs attention) · đỏ = khẩn (urgent) · xanh lá =
  ổn/xong (ok/done). Nền SÁNG (off-white); cyan sâu hơn để tương phản / light (off-white) background,
  a deeper cyan for contrast.
- **Typography:** cỡ base LỚN (17px+) cho dễ đọc; số/ETA/giờ dùng mono; nhãn tiếng Việt đầy đủ (không
  viết tắt khó hiểu) / large base size for readability; numbers/ETA/time in mono; full Vietnamese
  labels, no confusing abbreviations.
- **Touch target ≥ 48px**, thao tác một tay, nút chính to / one-handed operation, large primary
  buttons.
- **Tab bar 5 mục cố định** + **FAB Trợ lý** nhất quán mọi màn / consistent fixed 5-item tab bar plus
  assistant FAB on every screen.
- **AI cân bằng:** trợ lý là FAB phụ trợ, KHÔNG phải màn hình trung tâm. Reasoning/giải thích viết
  bằng ngôn ngữ đời thường ấm áp / the assistant is an auxiliary FAB, never a central screen; reasoning
  is written in warm, everyday language (unlike the clinician surface's technical mono register).
- **Số liệu là khoảng** ("còn ~5-10 phút"), không số cứng / figures are ranges, never hard numbers.
- **Guardrails hiện rõ:** banner "không phải chẩn đoán" ở Intake; "hãy hỏi bác sĩ" ở kết quả; consent
  tại ngữ cảnh / guardrails stay visible: the "not a diagnosis" banner at Intake, "ask your doctor" at
  results, in-context consent.

Design production sequencing (order to draw for the design tool, source guidance for
`frontend-ui-dev`/design collaborators, not a build schedule):

- **Group 1 - draw in depth, must run (P0, serves the golden path):** `/home` (both modes -
  signature, draw first) -> `/journey` (Care Pathway timeline + "why this order") -> `/assistant`
  (Journey Agent chat) -> `/intake` (conversational intake + guardrail) -> `/book` (booking + AI
  time suggestion) -> `/checkin` (QR check-in, the bridge into Live Companion).
- **Group 2 - draw the frame, prove a complete HIS (P1):** `/journey/step/:id`, `/results`,
  `/medications`, `/recovery`, `/billing`, `/family` (Bring-someone), `/prep/:id`,
  `/notifications`, `/settings`.
- **Group 3 - placeholder (P2):** `/welcome`, `/telehealth`, `/emergency`, `/wellness`,
  `/journey/updates`.

One-line design brief seed (source, kept verbatim for design-tool prompting):

> "Thiết kế một Patient Hospital Companion mobile app, tiếng Việt, cho bệnh nhân lo lắng và người lớn
> tuổi: nền sáng dịu, chữ lớn, dễ chạm một tay. Tab bar 5 mục (Trang chủ · Lịch khám · Lộ trình · Hồ
> sơ · Thêm) + nút Trợ lý nổi. Điểm đặc biệt: màn Trang chủ tự đổi giữa dashboard (ngoài viện) và Live
> Companion 1-mục-đích (trong viện). Cyan nghĩa là 'AI đang giúp bạn', amber 'chú ý', đỏ 'khẩn'. Bắt
> đầu bằng màn `/home` ở CẢ HAI chế độ."

### 6.2 Cross-surface consistency (patient vs coordinator/clinician)

Một sự thật, hai giao diện / one truth, two interfaces - what must stay consistent between the patient
app and the coordinator/clinician-facing surfaces already specified in
[spec 10](../specs/10-ui-ux-wireframes.md):

| Shared data | Patient sees | Coordinator/clinician sees |
|---|---|---|
| ETA & queue | "còn ~5-10 phút" (mono, warm) / a warm range | Exact figure on the load heatmap |
| Pathway | Calm timeline, everyday-language "why" | Technical task list + mono reasoning |
| Results | "in/out of reference range" + ask the doctor | Full value + reference range |
| Disruption / reschedule | Gentle notice + reason | Disruption Center + approval queue |
| Prescription | Dose + reminder | e-Rx + interaction warnings |

Khác biệt register có chủ đích / the register difference is deliberate: the coordinator/clinician
surface is dense and technically mono; the patient surface is light, calm, large-type, and warm. Same
semantic palette, different background tone - "one truth, two points of view."

## 7. Open questions

- [ ] **Payment scope conflict.** Module 6 (Payments & Insurance) describes real online payment
  (wallet/card/QR) inside the patient app, but the accepted spec
  ([FR-05](../specs/05-functional-requirements.md#fr-05), [AS-02](../specs/11-assumptions-constraints.md))
  states the app processes no money at all, only a proceed/paid flag set by an authorised source
  outside the app. Which governs for this release - display-only billing/coverage information, or
  does the release scope for real in-app payment change? Owner: Team lead.
- [ ] **No quantified success metrics.** The source brief gives no baseline/target numbers for wait
  time, no-show rate, or Bring-someone adoption. Related existing open item:
  [OI-08](../specs/11-assumptions-constraints.md#oi-08) (wait/congestion baseline). Owner: Team lead.
- [ ] **Modules with no matching FR yet.** Medical Records (M4), Medication & Recovery (M5), Family
  Care / Bring-someone (M7), Contextual Consent (M10), Proactive Prep (M2), Live Companion Mode (M1),
  and "Why am I waiting?" (M3) describe real capability with no corresponding entry in
  [05-functional-requirements.md](../specs/05-functional-requirements.md) today. Decide: promote some
  or all to new FRs in a future spec revision, or keep them as PRD-level elaboration nested under the
  closer existing FRs (FR-04, FR-06, FR-11, FR-18, FR-20, FR-21) without a spec-05 change. This PRD
  does not decide that on its own authority. Owner: Team lead / ba-analyst on a follow-up pass.
- [ ] **"Why am I waiting?" overlaps an already-open brainstorm.** [OI-22](../specs/11-assumptions-constraints.md#oi-22)
  and [TASK-017](../tasks/active/TASK-017-queue-transparency-brainstorm.md) are actively exploring the
  same queue-position/ticket-transparency concept this PRD's Module 3 describes informally. Reconcile
  before either is built, so the two do not diverge into separate designs for the same feature. Owner:
  `brainstormer` / Team lead.
- [ ] **Missing sibling document.** The source IA brief states it is paired with
  `Clinician_GoldenPath_IA_Sitemap.md` (same truth, different interface for the clinician). That file
  was not present in the repository at relocation time. Confirm whether it exists elsewhere, was
  never authored, or is planned. Owner: Team lead.
- [ ] **Contextual Consent's home.** Module 10 presents contextual, in-flow consent prompts as a new
  differentiator; there is no consent-log FR in [05](../specs/05-functional-requirements.md) or
  [06-access-control.md](../specs/06-access-control.md) today. Decide whether this belongs under
  FR-18 (auth) as an extension, or needs its own FR. Owner: Team lead.

## 8. References

- [FR-12 Coordinator dashboard](../specs/05-functional-requirements.md#fr-12) (routing-table umbrella
  for UI work).
- [SCR-01 Intake chat](../specs/10-ui-ux-wireframes.md#scr-01-intake-chat),
  [SCR-02 Journey timeline](../specs/10-ui-ux-wireframes.md#scr-02-journey-timeline),
  ["Visual design direction"](../specs/10-ui-ux-wireframes.md#visual-design-direction) in
  [spec 10](../specs/10-ui-ux-wireframes.md).
- [BF-01 Intake and routing to a diagnostic consult](../specs/04-business-flows.md),
  [BF-05 Emergency escalation](../specs/04-business-flows.md) in
  [spec 04](../specs/04-business-flows.md).
- [AS-02, AS-06, OI-08, OI-09, OI-22](../specs/11-assumptions-constraints.md) in
  [spec 11](../specs/11-assumptions-constraints.md).
- Data entities referenced: `Patient`, `IntakeSession`, `Appointment`, `CarePlan`, `Task`,
  `Notification`, `Payment`, `ScanEvent` - see [08-data-model.md](../specs/08-data-model.md).
- [TASK-018](../tasks/active/TASK-018-patient-app-prd-relocation.md) (this relocation),
  [TASK-017](../tasks/active/TASK-017-queue-transparency-brainstorm.md) (queue-transparency
  brainstorm, overlaps section 7).
- Original source material (relocated by TASK-018, no longer present at the repo root):
  `Patient_GoldenPath_IA_Sitemap.md` and `Patient_Mobile_App_Feature_Architecture.md` (v2).
