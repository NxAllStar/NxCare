---
title: "Overview"
sidebar_label: "01. Overview"
description: "Context, problem, goals, scope, and success metrics for VAIC - AI Care Pathway Coordinator."
tags: [specs, overview, vaic]
---

# Overview

## Context

VI: Trong bệnh viện, bệnh nhân thường dồn cục vào cùng khung giờ trong khi các slot khác bỏ trống, bị chỉ sai khu và phải đi lại nhiều lần, và chờ mà không biết còn bao lâu - vì dữ liệu đặt lịch, tiếp nhận, phòng khám, xét nghiệm và chẩn đoán hình ảnh không được nối thành một bức tranh điều phối thống nhất. VAIC là một lớp điều phối AI-native: thay vì "phần mềm quản lý hàng đợi có gắn AI", hệ thống là một đội ngũ agent điều phối làm việc liên tục, còn code truyền thống là công cụ (tools) và hàng rào an toàn (guardrails) của họ.

EN: In a hospital, patients bunch up at the same times while other slots sit empty, get sent to the wrong area and backtrack, and wait without knowing how long - because appointment, check-in, clinic, lab, and imaging data are not joined into a single coordinated view. VAIC is an AI-native coordination layer: rather than "queue software with AI bolted on", it is a team of coordination agents working continuously, with conventional code as their tools and guardrails.

Bối cảnh build này là **bản demo hackathon chạy trên simulator (SimPy)**, không tích hợp hệ thống bệnh viện thật và không dùng dữ liệu bệnh nhân thật. / This build is a **hackathon demo running on a SimPy simulator**, with no real hospital-system integration and no real patient data. See [AS-02](11-assumptions-constraints.md) and [CO-01](11-assumptions-constraints.md).

## App concept and platform

VI: VAIC là **một web app responsive, phân quyền theo vai** (patient/doctor/technician/coordinator/admin) - một lần đăng nhập, định tuyến theo vai ([FR-18](05-functional-requirements.md#fr-18)). Giao diện bệnh nhân ưu tiên mobile (chat + timeline + mã QR); giao diện nhân viên/điều phối ưu tiên desktop. Mức độ hoàn thiện cho bản demo là **"believable-but-lean"**: đủ khung để trông như sản phẩm thật (xác thực đơn giản, dữ liệu seed, trang chủ theo vai, trung tâm thông báo, cài đặt + chuyển ngôn ngữ VI/EN, tìm bệnh nhân cho nhân viên) nhưng các chức năng hỗ trợ được giữ tối giản. Hướng thiết kế nhẹ (design system) được định nghĩa trong [10](10-ui-ux-wireframes.md).

EN: VAIC is **one responsive, role-gated web app** (patient/doctor/technician/coordinator/admin) - a single login with role-based routing ([FR-18](05-functional-requirements.md#fr-18)). Patient views are mobile-first (chat + timeline + QR); staff/coordinator views are desktop-first. Demo completeness is **"believable-but-lean"**: enough scaffolding to read as a real product (simple auth, seeded data, a per-role home, a notifications center, settings + VI/EN toggle, staff patient search) while supporting features stay minimal. A lightweight design direction is defined in [10](10-ui-ux-wireframes.md).

## Problem statement

VI: Dữ liệu vận hành của các khu (đặt lịch, tiếp nhận, phòng khám, lab, imaging, trạng thái thiết bị) rời rạc, nên không ai có cái nhìn thời gian thực về tải toàn viện. Hệ quả: ùn tắc theo giờ, bệnh nhân đi sai khu và lặp lại hàng đợi, thời gian chờ không dự báo được, công suất phòng/thiết bị thấp.

EN: Operational data across areas (appointments, check-in, clinics, labs, imaging, equipment status) is fragmented, so no one has a real-time view of hospital-wide load. The result: hourly congestion, patients sent to the wrong area and re-queuing, unpredictable wait times, and low room/equipment utilisation.

| Aspect | Today |
|--------|-------|
| Who is affected | Bệnh nhân, bác sĩ, kỹ thuật viên, điều phối viên / Patients, doctors, technicians, coordinators |
| Current process | Đặt lịch và xếp hàng thủ công theo FIFO từng khu; mỗi khu tự quản hàng đợi, không điều phối chéo / Manual FIFO queueing per area; each area manages its own queue, no cross-area coordination |
| Cost of the status quo | Không định lượng trong nguồn - see [OI-08](11-assumptions-constraints.md#oi-08) / Not quantified in the source - see [OI-08](11-assumptions-constraints.md#oi-08) |
| Trigger for change | Cuộc thi hackathon AI-native; mục tiêu chứng minh điều phối bằng agent vượt rule cứng / Hackathon; goal is to show agent-based coordination beating hard-coded rules |

## Goals

| ID | Goal | Rationale |
|----|------|-----------|
| G-01 | Giảm thời gian chờ trung bình so với baseline FIFO trên cùng tập mô phỏng / Reduce average wait time versus a FIFO baseline on the same simulated cohort | Tiêu chí chấm điểm chính / The primary judging criterion |
| G-02 | Giảm ùn tắc (đỉnh tải) giữa các khu / Ease congestion (peak load) across areas | Dàn tải làm tăng thông lượng / Load levelling raises throughput |
| G-03 | Tăng công suất sử dụng phòng và thiết bị / Raise room and equipment utilisation | Slot trống bên cạnh nơi quá tải là lãng phí / Empty slots beside overloaded ones are waste |
| G-04 | Cho bệnh nhân chủ động theo dõi lộ trình / Let patients actively track their own care pathway | Minh bạch chờ đợi giảm lo lắng và cuộc gọi hỏi / Transparency reduces anxiety and inbound questions |
| G-05 | Chứng minh suy luận agent xử lý sự cố tổ hợp rule cứng không phủ nổi / Demonstrate agent reasoning handling combinatorial disruptions hard rules cannot cover | Luận điểm định vị AI-native trước giám khảo / The AI-native positioning argument to judges |

## Non-goals

- VAIC **không chẩn đoán và không chỉ định dịch vụ**; quyết định lâm sàng thuộc về bác sĩ. / VAIC does **not diagnose and does not order clinical services**; clinical decisions belong to the doctor. See [FR-01](05-functional-requirements.md#fr-01) and the guardrails in [06](06-access-control.md).
- Không tích hợp HIS/EMR/LIS/PACS thật trong bản demo. / No real HIS/EMR/LIS/PACS integration in the demo.
- App KHÔNG xử lý thanh toán; "thanh toán" chỉ là một cờ cho phép tiến hành, việc trả tiền diễn ra ngoài app. / The app processes no payment; "payment" is only a proceed-gate flag, actual paying happens outside the app. See [FR-05](05-functional-requirements.md#fr-05).
- Không phải hồ sơ bệnh án điện tử; VAIC chỉ điều phối logistics. / Not an electronic medical record; VAIC only coordinates logistics.
- Không có tự đăng ký bệnh nhân trong bản này; bệnh nhân được tạo qua seed/tiếp nhận, không có onboarding tự phục vụ. / No patient self-registration this release; patients are created via seed/intake, not a self-service onboarding. See [AS-06](11-assumptions-constraints.md).

## Scope

### In scope

- Tiếp nhận và định tuyến hội thoại / Conversational intake and routing: [FR-01](05-functional-requirements.md#fr-01)
- Đề xuất khung giờ ít đông / Least-crowded slot recommendation: [FR-02](05-functional-requirements.md#fr-02)
- Ghi nhận chẩn đoán và chỉ định của bác sĩ / Doctor diagnosis and service-order capture: [FR-03](05-functional-requirements.md#fr-03)
- Sinh và sắp thứ tự danh sách task / Task-list generation and sequencing: [FR-04](05-functional-requirements.md#fr-04)
- Cổng thanh toán khóa task / Payment gate locking tasks: [FR-05](05-functional-requirements.md#fr-05)
- Hộ tống bệnh nhân và tái sắp xếp / Per-patient escort and resequencing: [FR-06](05-functional-requirements.md#fr-06)
- Dự báo ETA/tải/no-show / ETA, load, and no-show forecasting: [FR-07](05-functional-requirements.md#fr-07)
- Xếp slot theo capacity bác sĩ / Slot allocation on doctor capacity: [FR-08](05-functional-requirements.md#fr-08)
- Xử lý sự cố phân tầng tự chủ / Disruption handling with tiered autonomy: [FR-09](05-functional-requirements.md#fr-09)
- Vòng lặp điều phối trung tâm / Central coordination loop: [FR-10](05-functional-requirements.md#fr-10)
- Thông báo bệnh nhân trên timeline / Patient timeline notifications: [FR-11](05-functional-requirements.md#fr-11)
- Dashboard điều phối / Coordinator dashboard: [FR-12](05-functional-requirements.md#fr-12)
- Nhật ký suy luận agent / Agent reasoning audit log: [FR-13](05-functional-requirements.md#fr-13)
- Quét mã bệnh nhân cập nhật trạng thái (hệ sinh thái bệnh nhân - bác sĩ - viện) / Patient-code scan status update (patient-doctor-hospital ecosystem): [FR-17](05-functional-requirements.md#fr-17)
- Chức năng hỗ trợ (rounded app) / Supporting functions: xác thực & phân quyền [FR-18](05-functional-requirements.md#fr-18), đổi/hủy lịch [FR-19](05-functional-requirements.md#fr-19), trung tâm thông báo [FR-20](05-functional-requirements.md#fr-20), cài đặt + ngôn ngữ VI/EN [FR-21](05-functional-requirements.md#fr-21), tìm bệnh nhân [FR-22](05-functional-requirements.md#fr-22)
- Hướng thiết kế nhẹ (design system) / lightweight design direction: [10](10-ui-ux-wireframes.md) "Visual design direction"

### Out of scope

- Chat của bác sĩ với worklist / Doctor worklist chat: [FR-14](05-functional-requirements.md#fr-14) - Could, cắt trước nếu thiếu thời gian / first to cut.
- Kênh SMS / SMS channel: [FR-15](05-functional-requirements.md#fr-15) - Could; demo dùng thông báo in-app / demo uses in-app notifications.
- Learning loop (retrain forecast, agent memory, EMA service-time) / Learning loop: [FR-16](05-functional-requirements.md#fr-16) - Won't this release; bước demo "MAE giảm theo tuần" đã bỏ ([OI-01](11-assumptions-constraints.md#oi-01) resolved) / the MAE-improvement demo step is dropped.

## Success metrics

| Metric | Baseline (today) | Target | How it is measured |
|--------|------------------|--------|--------------------|
| Thời gian chờ trung bình / Avg wait time | FIFO baseline run - unknown cho tới khi chạy, see [OI-08](11-assumptions-constraints.md#oi-08) | Giảm so với baseline / Lower than baseline (số cụ thể chưa chốt - [OI-05](11-assumptions-constraints.md#oi-05)) | So sánh A/B trên cùng tập mô phỏng / A/B on the same simulated cohort |
| Đỉnh tải theo khu / Peak load per area | FIFO baseline run | Đỉnh thấp hơn, phân bố phẳng hơn / Lower peak, flatter distribution | Heatmap + thống kê hàng đợi / Heatmap + queue stats in the simulator |
| Công suất phòng/thiết bị / Room-equipment utilisation | FIFO baseline run | Cao hơn baseline / Higher than baseline | % thời gian bận / % busy time in the simulator |
| Sai số dự báo ETA (MAE) / ETA forecast error (MAE) | Chưa đo / Not measured | Đủ thấp để bệnh nhân tin ETA / Low enough to be actionable - target chưa chốt [OI-05](11-assumptions-constraints.md#oi-05) | Dự báo vs thực tế mô phỏng / Predicted vs simulated actual |

## Judging criteria

VI: Bài thi được chấm trên 6 tiêu chí, tổng 100 điểm. Bảng dưới nối mỗi tiêu chí với nơi bộ đặc tả đáp ứng - dùng khi chuẩn bị phần trình bày và phòng thủ (Presentation & Defensibility).

EN: The entry is scored on six criteria totalling 100 points. The table maps each criterion to where this spec set addresses it - use it when preparing the pitch and defence.

| Criterion | Points | Addressed in |
|-----------|--------|--------------|
| Technical Implementation | 20 | [05](05-functional-requirements.md) FRs, [08](08-data-model.md) data model, [09](09-integration-interface.md) integrations, [12](12-technical-feasibility.md) approach and PoCs |
| AI-Native Architecture & Innovation | 20 | Multi-agent orchestration [FR-09](05-functional-requirements.md#fr-09), [FR-10](05-functional-requirements.md#fr-10); [04](04-business-flows.md) flows; the ecosystem scan [FR-17](05-functional-requirements.md#fr-17) |
| Business Viability & Pilot Pathway | 20 | [01](01-overview.md) goals and metrics; [11](11-assumptions-constraints.md) demo-to-production open issues; [12](12-technical-feasibility.md) pilot risks and effort |
| AI-Native UX & Design Thinking | 15 | [10](10-ui-ux-wireframes.md) chat + timeline + dashboard, the "Visual design direction" design system, model-assisted elements and AI labelling ([NFR-USE-05](07-non-functional-requirements.md#nfr-usability)); one responsive role-gated app ([FR-18](05-functional-requirements.md#fr-18)) |
| AI Safety, Grounding & Trust | 15 | Guardrails [CO-02..CO-05](11-assumptions-constraints.md); [07](07-non-functional-requirements.md#nfr-security) security; grounding [NFR-SEC-20](07-non-functional-requirements.md#nfr-security); audit [FR-13](05-functional-requirements.md#fr-13) |
| Presentation & Defensibility | 10 | This map; the honest open issues in [11](11-assumptions-constraints.md) and Partial/No rows in [12](12-technical-feasibility.md) |

<!-- Note the tension worth defending out loud: Forecast is now an LLM-backed tool (OI-20), chosen for
     speed over ML training - which pressures the 15-point AI Safety score. Defence: grounding +
     range-validation (NFR-SEC-20) keeps every number traceable to observed data. -->

## System context

```mermaid
flowchart LR
  P["Patient"] --> S["VAIC - AI Care Pathway Coordinator"]
  D["Doctor"] --> S
  C["Coordinator"] --> S
  S --> F["Forecast tools (ML models)"]
  S --> SIM["Hospital simulator (SimPy world)"]
  S --> DB[("State store and audit log")]
```

## AI in this system

VI: LLM suy luận và điều phối; Forecast là một **LLM-with-reasoning expose thành tool** sinh số; code kiểm tra ràng buộc. Nguyên tắc: mọi con số dự báo phải neo được vào dữ liệu quan sát (grounding) và validate dải, không bịa tự do; và LLM không quyết định lâm sàng.

EN: The LLM reasons and coordinates; the Forecast tool is an **LLM-with-reasoning exposed as a tool** that produces numbers; deterministic code enforces constraints. Principle: every forecast number must be grounded in observed data and range-validated, never fabricated freely, and the LLM never makes a clinical decision. See [OI-20](11-assumptions-constraints.md#oi-20).

| Question | Answer |
|----------|--------|
| What the model produces | Định tuyến triage, thứ tự task, phương án re-plan, tin nhắn giải thích / Triage routing, task ordering, re-plan options, explanation messages |
| Who or what consumes it | Bệnh nhân (Journey Agent), điều phối viên (dashboard), các agent khác / Patients, coordinators, other agents |
| Is a human in the loop | Có - phân tầng: ảnh hưởng lớn cần điều phối viên duyệt; phân loại chuyên khoa luôn hiển thị cho nhân viên xác nhận / Yes - tiered: large-impact actions need coordinator approval; specialty classification is always shown to staff to confirm. See [FR-09](05-functional-requirements.md#fr-09) |
| What happens when it is wrong | Constraint checker chặn action sai; điều phối viên override; audit log giải trình / Constraint checker blocks invalid actions; coordinator overrides; audit log explains. See [FR-13](05-functional-requirements.md#fr-13) |
| Untrusted content reaching the model | Có - chat triệu chứng bệnh nhân bằng ngôn ngữ tự nhiên / Yes - patient symptom chat. Treated as data, never instructions - see [NFR-SEC-11](07-non-functional-requirements.md#nfr-security) |

## References

- `docs/proposal.md` - AI-native proposal (bilingual): problem statement and multi-agent architecture, sections 1-8.
- Elicitation session: 4 decisions confirmed by Team lead (delivery = hackathon/demo on simulator; language = bilingual; learning loop = out of scope; security owner = Team lead, no real PHI).
