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
| 1.5 | 2026-07-18 | ba-analyst | Neo brief cuộc thi (nguyên văn) làm nguồn yêu cầu dẫn dắt trong [01](01-overview.md#contest-brief); thêm bảng truy vết 5 core feature -> FR (Feat 1 -> FR-02/FR-08, Feat 2 -> FR-01/FR-06, Feat 3 -> FR-07/FR-11/FR-15, Feat 4 -> FR-04, Feat 5 -> FR-09/FR-10) và bảng 4 success metric -> G-01..G-04; không FR nào mới, không yêu cầu nào bị diễn giải lại. Ghi nhận một gap thực: "patient category" của Feature 2 chưa có trường tường minh trong schema triage [FR-01](05-functional-requirements.md#fr-01) -> thêm [OI-23](11-assumptions-constraints.md#oi-23). / Anchored the contest brief verbatim as the guiding requirement source in 01-overview.md; added a 5-core-feature-to-FR traceability table and a 4-success-metric-to-goal table; no FR added or restated. Flagged one genuine gap: Feature 2's "patient category" has no explicit field in FR-01's triage schema, recorded as OI-23. | Team lead (pending review) |
| 2.0 | 2026-07-18 | Team lead | Thêm [FR-23](05-functional-requirements.md#fr-23) (điều phối tải động theo hàng đợi từng trạm): định nghĩa thời gian chờ mỗi trạm `station_wait = hàng đợi PAID × thời gian phục vụ TB` từ [FR-07](05-functional-requirements.md#fr-07), sinh lộ trình cân bằng tải động thay vì lịch cố định, và tái cân bằng sau mỗi trạm hoàn tất; BR-33..35, US-22; sắc hóa [BF-03](04-business-flows.md) và liên kết Related từ [FR-04](05-functional-requirements.md#fr-04)/[FR-06](05-functional-requirements.md#fr-06)/[FR-07](05-functional-requirements.md#fr-07). Không đổi data model (`station_wait` là đại lượng suy ra, transient). / Added FR-23 (dynamic queue-driven load-balanced routing): per-station waiting time from FR-07, dynamic load-balanced route generation instead of fixed scheduling, and rebalancing after each completed station; BR-33..35, US-22; sharpened BF-03 and Related links from FR-04/06/07. No data-model change (station_wait is derived, transient). | pending |
| 2.1 | 2026-07-18 | Team lead | Chốt cơ chế cho [OI-19](11-assumptions-constraints.md#oi-19): nhân viên quét mã bệnh nhân tại quầy để xác nhận thanh toán - một quét riêng biệt, sớm hơn quét hiện diện của [FR-17](05-functional-requirements.md#fr-17) (BR-36, AC-05.4); liên kết Related hai chiều FR-05<->FR-17; ghi chú tương ứng trong [08](08-data-model.md) `Payment`. Còn mở: vai trò nhân viên cụ thể được phép quét (OI-19 narrowed). Lưu ý số hiệu: BR-36 (không phải BR-33) để tránh trùng dải BR-33..35 mà v2.0 đã đăng ký cho FR-23. / Decided the mechanism for OI-19: a staff scan of the patient code at the counter confirms payment - distinct from and earlier than FR-17's presence scan (BR-36, AC-05.4); bidirectional Related links FR-05<->FR-17; a matching note in 08's `Payment`. Still open: which staff role. Numbering note: used BR-36, not BR-33, to avoid the BR-33..35 range v2.0 already reserved for FR-23. | Team lead |
| 2.2 | 2026-07-18 | tuan.nguyen15 (TASK-032) | Chốt [OI-15](11-assumptions-constraints.md#oi-15) (store bền vững ngoài Redis) = PostgreSQL qua SQLAlchemy; DDL nguồn sự thật tại `src/vaic/state/sql/schemas.sql`, model SQLAlchemy tại `src/vaic/state/sql/models.py`; di chuyển OI-15 sang mục "Resolved issues" trong [11](11-assumptions-constraints.md); cập nhật "Persistence notes" + "Open points" trong [08](08-data-model.md). Redis vẫn là store mặc định; chưa có `Repository` backend chạy trên Postgres. Không FR mới. / Resolved OI-15 (durable store beyond Redis) as PostgreSQL via SQLAlchemy; DDL source of truth in `src/vaic/state/sql/schemas.sql`, SQLAlchemy models in `src/vaic/state/sql/models.py`; moved OI-15 to the Resolved-issues section in 11; updated 08's persistence notes and open points. Redis remains the default store; no live Postgres `Repository` backend yet. No new FR. | pending |

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
| 1.5 | [01](01-overview.md) | Thêm mục "Contest brief (guiding source)": brief nguyên văn + bảng truy vết feature-to-FR + bảng success-metric-to-goal; cập nhật References / added the contest-brief section, two traceability tables, updated References | Owner yêu cầu brief làm nguồn dẫn dắt (Team lead) |
| 1.5 | [11](11-assumptions-constraints.md) | Thêm OI-23 (gap "patient category" trong FR-01) / added OI-23 | Rà soát brief so với FR-01 |
| 2.0 | [05](05-functional-requirements.md) | Thêm FR-23 + BR-33..35 + US-22 + traceability; liên kết Related ở FR-04/06/07 / added FR-23, BR-33..35, US-22, traceability, Related links | Cân bằng tải động theo nhu cầu thực (owner request) |
| 2.0 | [04](04-business-flows.md) | Sắc hóa BF-03: sắp xếp cân bằng tải theo thời gian chờ mỗi trạm + tái cân bằng sau mỗi trạm / sharpened BF-03 for per-station-wait load balancing and after-each-step rebalance | Đồng bộ với FR-23 |
| 2.1 | [05](05-functional-requirements.md) | FR-05: thêm cơ chế quét xác nhận thanh toán + BR-36 + AC-05.4 + Related->FR-17; FR-17: Related->FR-05 / FR-05 gains the scan mechanism + BR-36 + AC-05.4 + a Related link to FR-17; FR-17 gains a Related link back | Trả lời câu hỏi của Team lead về payment + scan |
| 2.1 | [08](08-data-model.md) | Ghi chú `Payment`: cơ chế xác nhận qua quét, khác `ScanEvent` / noted the scan-based confirmation mechanism, distinct from `ScanEvent` | Đồng bộ với FR-05 BR-36 |
| 2.1 | [11](11-assumptions-constraints.md) | OI-19: cơ chế đã chốt, thu hẹp còn "vai trò nào" / mechanism decided, narrowed to "which role" | Quyết định của Team lead |
| 2.2 | [11](11-assumptions-constraints.md) | OI-15 resolved -> moved to Resolved issues (PostgreSQL/SQLAlchemy) | Durable-store decision (owner request, TASK-032) |
| 2.2 | [08](08-data-model.md) | Cập nhật "Persistence notes" + "Open points" cho OI-15 resolved / updated persistence notes and open points for OI-15 resolved | Đồng bộ với OI-15 |

## Requirement lifecycle

<!-- IDs are never reused. FR-16 is present as Won't (this release), not withdrawn - it keeps its ID
     for a future release. -->

| ID | Status | Version | Note |
|----|--------|---------|------|
| FR-16 | Deferred (Won't this release) | 1.0 | Learning loop ngoài phạm vi bản này; giữ ID cho release sau; mâu thuẫn demo tại [OI-01](11-assumptions-constraints.md#oi-01) / out of scope this release, ID reserved |
| FR-23 | Added | 2.0 | Điều phối tải động theo hàng đợi từng trạm; sắc hóa FR-04/06/07 và BF-03 / dynamic queue-driven load balancing |

## Approval

| Version | Reviewed by | Approved by | Date |
|---------|-------------|-------------|------|
| 1.0 | SH-02, SH-03 (persona owners), delivery team | Team lead | 2026-07-17 |
