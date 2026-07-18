---
title: "Non-functional requirements"
sidebar_label: "07. Non-functional requirements"
description: "Performance, security, reliability, usability, and scalability requirements for VAIC - AI Care Pathway Coordinator."
tags: [specs, nfr, security, vaic]
---

# Non-functional requirements

<!-- Delivery is a hackathon demo on a simulator with synthetic data (no real PHI). Team-lead decision
     (AS-03): the security requirements are documented to FULL production grade - including DPA/DPO -
     regardless of whether the demo implements them. So every requirement below is stated as binding;
     a separate "Demo implementation" note records what the demo actually enforces. The requirement is
     never waived, only its demo implementation may lag. Performance targets were not decided - OI-05. -->

## Summary

| ID | Category | Requirement | Target | Priority |
|----|----------|-------------|--------|----------|
| NFR-PERF-01 | Performance | Phản hồi suy luận agent (Coordinator/Disruption) / agent reasoning response | Đề xuất p95 < 5s; chưa chốt - [OI-05](11-assumptions-constraints.md#oi-05) | Should |
| NFR-SEC-11 | Security | Nội dung người dùng là dữ liệu, không phải chỉ thị / user content is data, not instructions | 100% chat qua bộ lọc untrusted / all chat delimited untrusted | Must |
| NFR-SEC-13 | Security | Constraint checker chặn action ngoài ràng buộc / checker blocks invalid actions | 100% action qua checker trước khi thực thi / every action pre-checked | Must |
| NFR-SEC-20 | Security / Grounding | Số do model sinh phải neo dữ liệu quan sát và validate dải / model numbers grounded and range-checked | 100% con số neo được / every number traceable | Must |
| NFR-REL-04 | Reliability | Vận hành xuống cấp khi Forecast/LLM lỗi / degraded operation on model failure | Fallback baseline, không hành động bừa / baseline fallback, no wild action | Must |

## Performance {#nfr-performance}

| ID | Requirement | Target | Measured how | Applies to |
|----|-------------|--------|--------------|------------|
| NFR-PERF-01 | Phản hồi suy luận agent trung tâm / central agent reasoning | Đề xuất p95 < 5s ở ~50-100 bệnh nhân mô phỏng; **chưa chốt** [OI-05](11-assumptions-constraints.md#oi-05) | Đo server-side quanh vòng lặp agent trong simulator / server-side around the agent loop | [FR-09](05-functional-requirements.md#fr-09), [FR-10](05-functional-requirements.md#fr-10) |
| NFR-PERF-02 | Phản ứng của Journey Agent với event / Journey Agent event reaction | Đề xuất p95 < 3s; chưa chốt [OI-05](11-assumptions-constraints.md#oi-05) | Từ lúc event tới lúc thông báo bệnh nhân / event-to-notification | [FR-06](05-functional-requirements.md#fr-06) |
| NFR-PERF-03 | Trả kết quả tool Forecast / Forecast tool response | Lưu ý: Forecast là LLM-as-a-tool nên < 500ms khó đạt nếu gọi LLM trực tiếp; cần cache/model nhỏ/tính trước. Mục tiêu chưa chốt [OI-05](11-assumptions-constraints.md#oi-05) | Đo quanh lời gọi tool / around the tool call | [FR-07](05-functional-requirements.md#fr-07) |
| NFR-PERF-04 | Cập nhật heatmap dashboard / dashboard heatmap refresh | Đề xuất < 2s sau event; chưa chốt [OI-05](11-assumptions-constraints.md#oi-05) | Đo client-side / client-side | [FR-12](05-functional-requirements.md#fr-12) |

<!-- Every PERF target here is a proposal, not a stakeholder decision - all linked to OI-05. -->

## Security {#nfr-security}

### Data classification

<!-- The demo uses synthetic data, so no real PHI is present. Fields are classified at their
     PRODUCTION-equivalent level so the handling rules carry over; the demo relaxation is AS-04. -->

| Entity.field (from [08](08-data-model.md)) | Classification | Basis | Handling |
|--------------------------------------------|----------------|-------|----------|
| `Patient.full_name` | PII (synthetic in demo) | Danh tính cá nhân / personal identity | Loại khỏi log/analytics; mask khi export / excluded from logs, masked in exports |
| `Patient.phone` | PII (synthetic in demo) | Liên hệ cá nhân / personal contact | Loại khỏi log; chỉ dùng cho kênh thông báo / excluded from logs |
| `Patient.priority_level` | Confidential | Suy ra từ triệu chứng / derived from symptoms | Chỉ role có scope / scope-limited |
| `IntakeSession.transcript` | Sensitive PII (synthetic in demo) | Triệu chứng sức khỏe / health symptoms | Untrusted content; loại khỏi log; không gửi provider ngoài nếu là PHI thật / never logged; not sent to external provider if real PHI |
| `Diagnosis.conditions` | Sensitive PII (synthetic in demo) | Dữ liệu sức khỏe / health data | Chỉ bác sĩ/scope; loại khỏi log / doctor-scope only |
| `ServiceOrder.service_type` | Confidential | Gợi ý tình trạng sức khỏe / implies health state | Scope-limited |
| `Payment.amount` | Confidential | Tài chính (chỉ hiển thị, app không xử lý tiền) / financial (display-only, no processing) | Scope-limited; mask trong log / masked in logs |
| `Patient.patient_code` | Internal | Mã định danh để quét, không tự lộ dữ liệu y tế / scannable identifier | Không nhúng dữ liệu nhạy cảm vào mã / no sensitive data encoded in the code |
| `AuditLogEntry.reasoning` | Confidential | Có thể chứa dữ liệu bệnh nhân / may embed patient data | Áp dụng cùng phân loại nguồn / same classification as source |
| Các trường vận hành (`Task`, `Slot`, `Resource`) / operational fields | Internal | Không định danh cá nhân / not personally identifying | Bình thường / standard |

| ID | Requirement |
|----|-------------|
| NFR-SEC-01 | Mọi trường trong data dictionary mang một classification. Trường PII trở lên bị loại khỏi application log, error report và analytics. / Every field carries a classification; PII-and-above are excluded from logs, error reports, and analytics. |

### Encryption

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-SEC-02 | Mã hóa khi truyền / in transit | Yêu cầu: TLS 1.2+ trên mọi hop ngoài và nội bộ, không fallback plaintext. Demo implementation: chạy cục bộ không hop công khai (yêu cầu vẫn giữ nguyên, [AS-03](11-assumptions-constraints.md)) / Required: TLS 1.2+ everywhere; demo runs locally, requirement still stands |
| NFR-SEC-03 | Mã hóa khi lưu / at rest | Yêu cầu: DB và object storage được mã hóa, khóa quản lý qua KMS, giới hạn ai truy cập khóa. Demo implementation: dữ liệu tổng hợp, có thể chưa mã hóa (yêu cầu vẫn giữ, [AS-03](11-assumptions-constraints.md)) / Required: encrypted DB and storage via KMS; demo may not encrypt synthetic data, requirement still stands |
| NFR-SEC-04 | Sao lưu / backups | Yêu cầu: backup mang cùng classification và cùng mã hóa với nguồn / Required: backups carry the source's classification and encryption |

### Access control model

| ID | Requirement |
|----|-------------|
| NFR-SEC-05 | Phân quyền được enforce phía server ở mọi request; ma trận [06](06-access-control.md) là nguồn duy nhất; UI ẩn nút chỉ là tiện lợi. / Authorisation is enforced server-side on every request; the matrix in 06 is the single source. |
| NFR-SEC-06 | Bộ lọc scope (Own/Assigned/Team/All) áp ở tầng dữ liệu để request giả mạo không nới scope. / Scope filters are applied in the data layer. |
| NFR-SEC-07 | Duyệt re-plan, ký chỉ định, thanh toán được log kèm actor, target, timestamp; log không do actor sửa. / Privileged actions are logged and not writable by the actor. |

### Secret management

| ID | Requirement |
|----|-------------|
| NFR-SEC-08 | Không secret/key/token/connection string nào được commit vào repo hay nhúng client bundle; secrets nằm trong biến môi trường/secret store. / No secrets in the repo or client bundle; secrets live in environment variables or a secret store. |
| NFR-SEC-09 | Secrets (khóa API LLM) xoay được không cần đổi code; cadence xoay chưa chốt - [OI-12](11-assumptions-constraints.md#oi-12). / Secrets are rotatable without a code change; rotation cadence undecided. |
| NFR-SEC-10 | Môi trường phi-production không giữ credential production hay dữ liệu production chưa mask. / Non-prod never holds prod credentials or unmasked prod data. |

### Untrusted content and the model

<!-- Patient symptom chat reaches the LLM (Intake Agent, Journey Agent). These are mandatory. -->

| ID | Requirement |
|----|-------------|
| NFR-SEC-11 | Nội dung từ người dùng (chat triệu chứng, câu hỏi lộ trình) được đưa vào model như **dữ liệu, không phải chỉ thị**: được delimit và gắn nhãn untrusted; không lệnh nào bên trong được thi hành. / User content is passed as data, delimited and labelled untrusted; no embedded instruction is honoured. |
| NFR-SEC-12 | Output của model bị coi là input không tin cậy bởi mọi thứ phía sau: validate theo schema trước khi vào DB/tool/UI; model không được tự đặt tên task, phòng, hay lệnh. / Model output is validated against a schema before reaching a DB, tool, or UI. |
| NFR-SEC-13 | Tool/action của model là tối thiểu cho nhiệm vụ; mọi action bất khả nghịch hoặc vượt ngưỡng blast radius cần bước người duyệt trong [FR-09](05-functional-requirements.md#fr-09); constraint checker (code thường) chạy trước mọi action. / Model tools are least-privilege; irreversible or over-threshold actions need the human step in FR-09; the constraint checker runs before every action. |
| NFR-SEC-14 | Nhà cung cấp model: API model mạnh cho Coordinator/Disruption + Qwen self-hosted cho Intake/Journey **và cho forecast-LLM** ([FR-07](05-functional-requirements.md#fr-07)). Bản demo dùng dữ liệu tổng hợp, không gửi PHI thật ra provider ngoài. Điều khoản lưu trữ của provider API **chưa đọc** - [OI-02](11-assumptions-constraints.md#oi-02); production chỉ gửi PII+ ra ngoài khi có DPA đã ký. / Providers: a strong hosted API for Coordinator/Disruption plus self-hosted Qwen for Intake/Journey and the forecast-LLM. The demo sends only synthetic data; the hosted provider's retention terms are unread (OI-02); production sends PII only under a signed DPA. |
| NFR-SEC-15 | Prompt, completion và mọi nội dung gửi provider được log theo cùng luật classification như dữ liệu nguồn (PII+ không log). / Prompts and completions are logged under the source data's classification rules. |

### Other security requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-SEC-16 | Validate input và encode output / input validation, output encoding | Chặn prompt injection, JSON schema injection, XSS trên UI chat/dashboard / prompt injection, schema injection, XSS on chat and dashboard |
| NFR-SEC-17 | Quản lý phụ thuộc và lỗ hổng / dependency and vuln management | Quét trước demo; lỗ hổng Critical chặn release demo / scan before the demo; Critical blocks release |
| NFR-SEC-18 | Nghĩa vụ tuân thủ / compliance | Yêu cầu: tài liệu tuân thủ đầy đủ (luật dữ liệu/riêng tư y tế VN, DPA với nhà cung cấp, vai trò DPO) phải được lập **dù demo hay production** ([AS-03](11-assumptions-constraints.md)); demo không dùng dữ liệu thật ([SH-01](02-stakeholders.md)); DPO/DPA production [OI-07](11-assumptions-constraints.md#oi-07) / Required: full compliance docs (VN health-data law, provider DPA, DPO role) produced whether demo or production |
| NFR-SEC-19 | Lưu trữ và xóa dữ liệu / retention and deletion | Yêu cầu: chính sách lưu trữ/xóa theo classification được lập; demo: dữ liệu tồn tại theo vòng đời run; giá trị production chưa chốt - [OI-13](11-assumptions-constraints.md#oi-13) / Required: a per-classification retention and deletion policy is documented |
| NFR-SEC-20 | Grounding số do model sinh / grounding of model-produced numbers | Yêu cầu: mọi con số dự báo (ETA/tải/no-show) neo được vào dữ liệu quan sát và validate dải trước khi dùng; đặc biệt then chốt vì Forecast là **LLM-as-a-tool** ([OI-20](11-assumptions-constraints.md#oi-20) resolved) - see [FR-07](05-functional-requirements.md#fr-07) / Required: every forecast number is grounded in observed data and range-validated; critical because Forecast is LLM-backed |

## Reliability {#nfr-reliability}

| ID | Requirement | Target | Notes |
|----|-------------|--------|-------|
| NFR-REL-01 | Sẵn sàng trong buổi demo / availability during the demo | Chạy ổn định suốt kịch bản 5 phút / stable through the 5-minute script | Không có SLA production / no production SLA |
| NFR-REL-02 | RPO | Không áp dụng (dữ liệu mô phỏng, tái tạo được từ seed) / n/a - simulated data regenerable from seed | Production sẽ cần / production would need one |
| NFR-REL-03 | RTO | Demo: khởi động lại run từ seed trong phút / restart the run from seed within minutes | Deterministic seed đảm bảo tái lập / deterministic seed ensures reproducibility |
| NFR-REL-04 | Vận hành xuống cấp / degraded operation | Forecast lỗi -> ước lượng baseline gắn cờ; LLM lỗi/timeout -> giữ trạng thái, không hành động bừa, cảnh báo điều phối viên / on Forecast failure use a flagged baseline; on LLM failure hold state and alert | See [FR-07](05-functional-requirements.md#fr-07), [FR-10](05-functional-requirements.md#fr-10) |
| NFR-REL-05 | Tái lập demo / demo reproducibility | Simulator và Forecast chạy deterministic; seed kịch bản + fallback recording / deterministic sim and forecast; scripted seed plus fallback recording | Chống rủi ro ngẫu nhiên của LLM / guards against LLM nondeterminism |

## Usability {#nfr-usability}

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-USE-01 | Bệnh nhân hoàn tất [UC-01](05-functional-requirements.md) mà không cần đào tạo / first-time patient completes UC-01 without training | Hội thoại tiếng Việt tự nhiên, không form cứng / natural Vietnamese chat, no rigid form |
| NFR-USE-02 | Khả năng tiếp cận / accessibility | Mục tiêu WCAG 2.1 AA cho giao diện bệnh nhân; mức cam kết đầy đủ chưa chốt - [OI-14](11-assumptions-constraints.md#oi-14) / target WCAG 2.1 AA, full commitment undecided |
| NFR-USE-03 | Đa ngôn ngữ / localisation | Giao diện tiếng Việt (chính); codes và enums giữ tiếng Anh / Vietnamese UI; codes and enums stay English |
| NFR-USE-04 | Thông báo lỗi / error messages | Nói bệnh nhân làm gì tiếp theo (VD "task chưa thanh toán, bấm đây để thanh toán"), không chỉ báo lỗi / tell the user what to do next |
| NFR-USE-05 | Minh bạch nội dung do AI tạo / AI-generated content transparency | Nội dung do model tạo (đề xuất slot, lý do re-plan) được gắn nhãn rõ / model-produced content is clearly labelled. See [10](10-ui-ux-wireframes.md) |

## Scalability {#nfr-scalability}

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-SCA-01 | Khối lượng dữ liệu / data volume | Demo: ~50-100 bệnh nhân mỗi run; run A/B đối chiếu cùng cỡ / ~50-100 patients per run |
| NFR-SCA-02 | Đồng thời / concurrency | Demo: ~50-100 bệnh nhân mô phỏng đồng thời; Journey Agent event-driven, Coordinator xử lý batch để giữ chi phí/latency / event-driven agents, batched coordinator |
| NFR-SCA-03 | Dư địa tăng trưởng / growth headroom | Kiến trúc agent + tool cho phép nâng lên cỡ 300+ bệnh nhân (đề cập proposal) mà không đổi kiến trúc; chưa kiểm tải / architecture allows scaling toward 300+ without re-architecture; not load-tested |

## Maintainability and operations {#nfr-maintainability}

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-MNT-01 | Khả năng quan sát / observability | Log event stream, quyết định agent (audit), chỉ số MAE/wait/utilisation của simulator; cảnh báo khi agent không hành động / logs of events, agent decisions, and simulator metrics |
| NFR-MNT-02 | Triển khai / deployment | Chạy cục bộ cho demo (simulator + agents + UI); không yêu cầu downtime / local run for the demo |
| NFR-MNT-03 | Khả năng hỗ trợ / supportability | Đội thi vận hành trong buổi demo; README + seed kịch bản / the hackathon team operates it; README plus scripted seed |

## Open points

- Tất cả target Performance là đề xuất, chưa được stakeholder chốt - [OI-05](11-assumptions-constraints.md#oi-05). / All performance targets are proposals.
- Điều khoản lưu trữ dữ liệu của provider LLM API chưa đọc - [OI-02](11-assumptions-constraints.md#oi-02). / Hosted LLM provider retention terms unread.
- Chính sách lưu trữ/xóa production - [OI-13](11-assumptions-constraints.md#oi-13); mức cam kết accessibility - [OI-14](11-assumptions-constraints.md#oi-14). / Production retention and accessibility commitment undecided.
