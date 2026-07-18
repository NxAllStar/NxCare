---
title: "Revision history"
sidebar_label: "13. Revision history"
description: "Version history of the VAIC - AI Care Pathway Coordinator specification set."
tags: [specs, history, vaic]
---

# Revision history

<!-- One row per version of the spec SET, not per file edit. A row is added when the contract
     changes. Fill the date when you write the row. -->

## Versions

| Version | Date | Author | Change summary | Approved by |
|---------|------|--------|----------------|-------------|
| 1.0 | 2026-07-17 | Team lead | Bộ đặc tả ban đầu (13 mục) từ `docs/proposal.md` + phiên elicitation. 16 FR, guardrails AI-native, delivery demo trên simulator. / Initial 13-section set from the proposal and elicitation; 16 FRs, AI-native guardrails, demo-on-simulator delivery. | Team lead |
| 1.1 | 2026-07-17 | Team lead | Thêm [FR-17](05-functional-requirements.md#fr-17) (quét mã bệnh nhân - hệ sinh thái); re-scope [FR-05](05-functional-requirements.md#fr-05) thành cờ cho phép tiến hành (app không xử lý tiền); nới ràng buộc Forecast (ML hoặc LLM neo dữ liệu, [OI-20](11-assumptions-constraints.md#oi-20)); tăng cường tài liệu bảo mật lên mức production đầy đủ ([AS-03](11-assumptions-constraints.md)); thêm tiêu chí chấm điểm vào [01](01-overview.md). / Added FR-17 (patient-code scan); re-scoped FR-05 to a proceed-flag (no money); relaxed the Forecast constraint (ML or grounded LLM); strengthened security docs to full production grade; added judging criteria. | Team lead |
| 1.2 | 2026-07-17 | Team lead | Chốt [OI-20](11-assumptions-constraints.md#oi-20) (Forecast = LLM-as-a-tool), [OI-21](11-assumptions-constraints.md#oi-21) (quét mô phỏng), [OI-01](11-assumptions-constraints.md#oi-01) (learning loop ngoài scope, bỏ bước demo MAE). / Resolved OI-20, OI-21, OI-01. | Team lead |
| 1.3 | 2026-07-17 | Team lead | Thêm Grounding contract cho forecast-LLM (retrieve-reason-validate) trong [FR-07](05-functional-requirements.md#fr-07) + AC-07.3/07.4; thêm luồng cấp cứu [BF-05](04-business-flows.md) và thu hẹp [OI-09](11-assumptions-constraints.md#oi-09) còn danh sách red-flag lâm sàng; thêm `IntakeSession.emergency_suspected`. / Added the forecast-LLM grounding contract and BF-05 emergency escalation; narrowed OI-09. | Team lead |
| 1.4 | 2026-07-18 | Team lead | Định nghĩa "rounded app": một web app responsive phân quyền theo vai; thêm 5 FR hỗ trợ [FR-18](05-functional-requirements.md#fr-18)..[FR-22](05-functional-requirements.md#fr-22) (auth, đổi/hủy lịch, trung tâm thông báo, cài đặt+VI/EN, tìm bệnh nhân); thêm màn hình SCR-08..11; thêm "Visual design direction" (design system Tailwind+shadcn) trong [10](10-ui-ux-wireframes.md); thêm mục "App concept and platform" trong [01](01-overview.md); non-goal: không tự đăng ký bệnh nhân (AS-06); thu hẹp OI-11 (auth demo qua FR-18). / Defined the rounded app: one responsive role-gated web app; added FR-18..22, screens SCR-08..11, a design-system direction, an app-concept section; no self-registration; narrowed OI-11. | Team lead |

<!-- Versioning: 1.0 first complete set; 1.x clarifications and resolved open issues; 2.0 the
     contract moved (an FR added, dropped, or materially changed). -->

## Changes by section

<!-- Only for versions after 1.0. -->

| Version | Section | Change | Reason |
|---------|---------|--------|--------|
| 1.1 | [05](05-functional-requirements.md) | Thêm FR-17; re-scope FR-05; nới BR-14/BR-15 cho FR-07 / added FR-17, re-scoped FR-05, relaxed FR-07 rules | Ý tưởng quét mã + không thanh toán trong app + rủi ro train ML (Team lead) |
| 1.1 | [07](07-non-functional-requirements.md) | Bảo mật full production docs; thêm NFR-SEC-20 grounding / full security docs, added grounding NFR | Tài liệu bảo mật đầy đủ dù demo (Team lead) |
| 1.1 | [08](08-data-model.md), [09](09-integration-interface.md) | Thêm `ScanEvent`, `Patient.patient_code`; Payment thành cờ; INT-02 thành nguồn cờ / added scan entity and code, Payment as flag | Đồng bộ với FR-05/FR-17 |
| 1.1 | [01](01-overview.md) | Thêm bảng tiêu chí chấm điểm / added judging-criteria map | Chuẩn bị Presentation & Defensibility |
| 1.4 | [05](05-functional-requirements.md) | Thêm FR-18..FR-22 (auth, đổi/hủy lịch, thông báo, cài đặt, tìm bệnh nhân) + US-17..21 + traceability / added supporting FRs | Định nghĩa rounded app (Team lead) |
| 1.4 | [10](10-ui-ux-wireframes.md) | Thêm SCR-08..11 + "Visual design direction" (design system) + nav/login | Rounded app + UX criterion |
| 1.4 | [01](01-overview.md) | Thêm "App concept and platform"; scope + non-goal (no self-registration) | App shape decision |
| 1.4 | [11](11-assumptions-constraints.md) | AS-06; resolved OI-00g/h/i; narrowed OI-11 | Recorded decisions |

## Requirement lifecycle

<!-- IDs are never reused. FR-16 is present as Won't (this release), not withdrawn - it keeps its ID
     for a future release. -->

| ID | Status | Version | Note |
|----|--------|---------|------|
| FR-16 | Deferred (Won't this release) | 1.0 | Learning loop ngoài phạm vi bản này; giữ ID cho release sau; mâu thuẫn demo tại [OI-01](11-assumptions-constraints.md#oi-01) / out of scope this release, ID reserved |

## Approval

| Version | Reviewed by | Approved by | Date |
|---------|-------------|-------------|------|
| 1.0 | SH-02, SH-03 (persona owners), delivery team | Team lead | 2026-07-17 |
