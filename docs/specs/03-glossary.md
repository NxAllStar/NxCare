---
title: "Glossary"
sidebar_label: "03. Glossary"
description: "Domain vocabulary for VAIC - AI Care Pathway Coordinator - one term, one meaning."
tags: [specs, glossary, vaic]
---

# Glossary

## Domain terms

| Term | Definition | Synonyms and aliases | Where it appears |
|------|-----------|----------------------|------------------|
| Buổi khám chẩn đoán / Diagnostic consult | Buổi bác sĩ khám và ra chẩn đoán + chỉ định dịch vụ; là nguồn sự thật lâm sàng / The visit where a doctor examines, diagnoses, and orders services; the clinical source of truth | Appointment, khám ban đầu | [FR-02](05-functional-requirements.md#fr-02), [FR-03](05-functional-requirements.md#fr-03), `Appointment` |
| Chỉ định dịch vụ / Service order | Yêu cầu của bác sĩ thực hiện một dịch vụ (xét nghiệm máu, siêu âm, X-quang, CT, MRI...) / A doctor's request to perform a service (blood test, ultrasound, X-ray, CT, MRI...) | Y lệnh, order | [FR-03](05-functional-requirements.md#fr-03), `ServiceOrder` |
| Danh sách task / Task list | Các bước dịch vụ do Care Plan Agent sinh từ chỉ định, mỗi bước có owner và thời lượng / The service steps the Care Plan Agent generates from orders, each with an owner and duration | Care plan, kế hoạch cá nhân hóa | [FR-04](05-functional-requirements.md#fr-04), `CarePlan`, `Task` |
| Owner (của task) / Task owner | Bác sĩ, kỹ thuật viên hoặc phòng chịu trách nhiệm thực hiện một task / The doctor, technician, or room responsible for a task | Người phụ trách | [FR-04](05-functional-requirements.md#fr-04), `Task.owner_id` |
| Cổng cho phép tiến hành / Proceed gate | Ràng buộc cứng: task chỉ vào hàng đợi và bắt đầu khi cờ đã thanh toán bật; app KHÔNG xử lý tiền, chỉ giữ cờ / Hard constraint: a task enters the queue only when the paid flag is on; the app processes no money, only the flag | Cổng thanh toán, khóa thanh toán, payment lock | [FR-05](05-functional-requirements.md#fr-05) |
| Mã bệnh nhân / Patient code | Mã định danh (QR) hiển thị trong app để owner quét xác nhận có mặt và cập nhật trạng thái / A scannable patient identifier (QR) shown in the app | QR code, patient QR | [FR-17](05-functional-requirements.md#fr-17), `Patient.patient_code` |
| ETA | Thời điểm dự kiến bệnh nhân được phục vụ tại một phòng/bước / Estimated time a patient will be served at a room or step | Thời gian chờ dự báo | [FR-07](05-functional-requirements.md#fr-07) |
| Re-plan / Tái lập lịch | Sinh lại thứ tự/slot khi có sự cố / Regenerating order and slots when a disruption occurs | Resequence, điều phối lại | [FR-06](05-functional-requirements.md#fr-06), [FR-09](05-functional-requirements.md#fr-09) |
| Blast radius / Bán kính ảnh hưởng | Số bệnh nhân/task bị ảnh hưởng bởi một sự cố / Number of patients or tasks affected by a disruption | Phạm vi ảnh hưởng | [FR-09](05-functional-requirements.md#fr-09) |
| Phân tầng tự chủ / Tiered autonomy | Ảnh hưởng nhỏ agent tự làm; lớn cần người duyệt / Small impact auto-executes; large impact needs human approval | Human-in-the-loop phân tầng | [FR-09](05-functional-requirements.md#fr-09) |
| Snapshot trạng thái / State snapshot | Ảnh chụp trạng thái toàn viện tại một thời điểm (hàng đợi, tải phòng, thiết bị) / A point-in-time picture of hospital-wide state | Hospital snapshot | [FR-10](05-functional-requirements.md#fr-10) |
| Simulator / Bộ mô phỏng | "Thế giới" SimPy nơi các agent vận hành và được đánh giá / The SimPy world the agents operate in and are evaluated against | SimPy world, eval env | [12](12-technical-feasibility.md), [09](09-integration-interface.md) |
| Red-flag cấp cứu / Emergency red-flag | Dấu hiệu Intake Agent gắn cờ để nghi cấp cứu; danh sách do bác sĩ định nghĩa, nhân viên xác nhận, AI không tự kết luận / a signal the Intake Agent flags as a suspected emergency; the list is clinician-defined and staff-confirmed | Emergency signal | [FR-01](05-functional-requirements.md#fr-01), [BF-05](04-business-flows.md) |
| Nhịn ăn / Fasting constraint | Ràng buộc một số dịch vụ yêu cầu bệnh nhân nhịn ăn trước / A constraint that some services require the patient to fast beforehand | Fasting | [FR-04](05-functional-requirements.md#fr-04), `ServiceType.requires_fasting` |
| Turnaround / Thời gian trả kết quả | Thời gian từ khi làm xong dịch vụ đến khi có kết quả / Time from completing a service to its result being ready | TAT | [FR-04](05-functional-requirements.md#fr-04), `ServiceType.turnaround_minutes` |

## Status values and enumerations

| Entity | Value (English, canonical) | Display label | Meaning | Set by |
|--------|---------------------------|---------------|---------|--------|
| `Task` | `PENDING` | Chờ / Pending | Chưa bắt đầu, đang trong hàng đợi hoặc bị khóa / Not started; queued or locked | Care Plan Agent |
| `Task` | `IN_PROGRESS` | Đang làm / In progress | Owner đang thực hiện / Owner is performing it | role_technician / role_doctor / system event |
| `Task` | `DONE` | Xong / Done | Đã thực hiện xong (kết quả có thể còn chờ turnaround) / Completed | role_technician / role_doctor |
| `Task` | `CANCELLED` | Đã hủy / Cancelled | Bị hủy do re-plan hoặc chỉ định thay đổi / Cancelled by re-plan or order change | Disruption Agent / role_doctor |
| `Task` | `LOCKED` | Bị khóa / Locked | Chưa thanh toán nên không vào hàng đợi thực / Unpaid, so excluded from the real queue | Payment gate (derived from `payment_status`) |
| `Task.payment_status` | `UNPAID` | Chưa thanh toán / Unpaid | Chưa thanh toán / Not paid | system / payment webhook (simulated) |
| `Task.payment_status` | `PAID` | Đã thanh toán / Paid | Đã xác nhận thanh toán / Payment confirmed | payment webhook (simulated) |
| `Appointment` | `PROPOSED` | Đề xuất / Proposed | Slot do hệ thống đề xuất, chưa xác nhận / Slot proposed, not confirmed | Intake + Forecast Agent |
| `Appointment` | `BOOKED` | Đã đặt / Booked | Bệnh nhân đã chọn slot / Patient selected the slot | role_patient |
| `Appointment` | `CHECKED_IN` | Đã tiếp nhận / Checked in | Bệnh nhân đã đến / Patient arrived | system event |
| `Appointment` | `IN_CONSULT` | Đang khám / In consult | Bác sĩ đang khám / Doctor is examining | system event |
| `Appointment` | `DONE` | Khám xong / Done | Đã có chẩn đoán và chỉ định / Diagnosis and orders recorded | role_doctor |
| `Appointment` | `NO_SHOW` | Không đến / No-show | Bệnh nhân không đến đúng giờ / Patient did not arrive | system event |
| `Appointment` | `CANCELLED` | Đã hủy / Cancelled | Hủy lịch / Cancelled | role_patient / role_coordinator |
| `CarePlan` | `DRAFT` | Nháp / Draft | Đang sinh, chưa kích hoạt / Being generated | Care Plan Agent |
| `CarePlan` | `ACTIVE` | Đang chạy / Active | Đang thực thi trên timeline / Executing | Care Plan Agent |
| `CarePlan` | `COMPLETED` | Hoàn tất / Completed | Tất cả task xong / All tasks done | Journey Agent |
| `DisruptionEvent` | `DETECTED` | Phát hiện / Detected | Nhận được event bất thường / Abnormal event received | Coordinator Agent |
| `DisruptionEvent` | `ASSESSED` | Đã đánh giá / Assessed | Đã tính blast radius và phương án / Blast radius and options computed | Disruption Agent |
| `DisruptionEvent` | `AUTO_RESOLVED` | Tự xử lý / Auto-resolved | Ảnh hưởng nhỏ, agent tự thực thi / Small impact, auto-executed | Disruption Agent |
| `DisruptionEvent` | `PENDING_APPROVAL` | Chờ duyệt / Pending approval | Ảnh hưởng lớn, chờ điều phối viên / Large impact, awaiting coordinator | Disruption Agent |
| `DisruptionEvent` | `APPROVED` | Đã duyệt / Approved | Điều phối viên duyệt phương án / Coordinator approved | role_coordinator |
| `DisruptionEvent` | `REJECTED` | Từ chối / Rejected | Điều phối viên từ chối / Coordinator rejected | role_coordinator |
| `Patient.priority_level` | `ROUTINE` | Thường / Routine | Ưu tiên thường / Normal priority | Intake Agent (staff-confirmed) |
| `Patient.priority_level` | `URGENT` | Ưu tiên / Urgent | Cần ưu tiên / Elevated priority | Intake Agent (staff-confirmed) |
| `Patient.priority_level` | `EMERGENCY` | Cấp cứu / Emergency | Cấp cứu / Emergency | Intake Agent (staff-confirmed) |

## Roles

| Role (English, canonical) | Who holds it | Defined in |
|---------------------------|--------------|------------|
| `role_patient` | Bệnh nhân / Patients (group in [02](02-stakeholders.md)) | [06](06-access-control.md) |
| `role_doctor` | Bác sĩ / Doctors | [06](06-access-control.md) |
| `role_technician` | Kỹ thuật viên / Technicians | [06](06-access-control.md) |
| `role_coordinator` | Điều phối viên / Coordinators | [06](06-access-control.md) |
| `role_admin` | Quản trị hệ thống / Administrators | [06](06-access-control.md) |

## Abbreviations

| Abbreviation | Expansion | Notes |
|--------------|-----------|-------|
| ETA | Estimated Time of Arrival/service | Ở đây là thời điểm dự kiến được phục vụ, không phải "đến nơi" / Here it means expected time to be served, not physical arrival |
| MAE | Mean Absolute Error | Chỉ số đánh giá sai số dự báo ETA / Metric for ETA forecast error |
| HIS/EMR/LIS/PACS | Hospital/Electronic Medical/Lab Information System, Picture Archiving | Hệ thống viện thật; bản demo mô phỏng, không tích hợp / Real hospital systems; the demo simulates, does not integrate |
| EMA | Exponential Moving Average | Dùng cho service-time profile - out of scope bản này / For the service-time profile - out of scope this release |
| PHI | Protected Health Information | Bản demo dùng dữ liệu tổng hợp, không có PHI thật / The demo uses synthetic data, no real PHI |

## AI and model terms

| Term | Definition in this project |
|------|---------------------------|
| Agent | Một tác nhân LLM có vòng lặp perceive-reason-act, gọi tools trong action space đóng / An LLM actor with a perceive-reason-act loop that calls tools within a closed action space |
| Coordinator Agent | Agent điều hành tổng, nhận event stream và ủy quyền/tự xử lý / The central orchestrator; consumes the event stream and delegates or acts. [FR-10](05-functional-requirements.md#fr-10) |
| Intake Agent | Agent hội thoại triage định tuyến (không chẩn đoán) / The triage-routing conversational agent (does not diagnose). [FR-01](05-functional-requirements.md#fr-01) |
| Care Plan Agent | Agent sinh và sắp thứ tự danh sách task từ chỉ định bác sĩ / The agent that generates and sequences the task list from doctor orders. [FR-04](05-functional-requirements.md#fr-04) |
| Journey Agent | Agent hộ tống mỗi bệnh nhân một instance / The per-patient escort agent. [FR-06](05-functional-requirements.md#fr-06) |
| Forecast Agent | Tool dự báo ETA/tải/no-show; hiện thực là **một LLM-with-reasoning được expose thành tool**, neo vào dữ liệu lịch sử và validate dải / a forecast tool for ETA/load/no-show, implemented as an LLM-with-reasoning exposed as a tool, grounded in historical data and range-validated. [FR-07](05-functional-requirements.md#fr-07), [OI-20](11-assumptions-constraints.md#oi-20) |
| Grounding / Neo dữ liệu | Buộc mọi con số/kết luận của model phải truy được về dữ liệu quan sát, không phỏng đoán tự do / requiring every model number or claim to trace to observed data | Groundedness | [FR-07](05-functional-requirements.md#fr-07), [NFR-SEC-12](07-non-functional-requirements.md#nfr-security) |
| Disruption Agent | Agent xử lý sự cố, phân tầng tự chủ / The disruption-handling agent with tiered autonomy. [FR-09](05-functional-requirements.md#fr-09) |
| Constraint checker | Code thường chạy trước mọi action để chặn vi phạm ràng buộc / Deterministic code run before every action to block constraint violations. [NFR-SEC-13](07-non-functional-requirements.md#nfr-security) |
| Tool | Hàm code có validation mà agent gọi để hành động / A validated code function the agent calls to act (e.g. `allocate_slot()`, `estimate_wait()`) |
| Closed action space | Agent chỉ hành động qua bộ tools định nghĩa sẵn, không hành động tự do / The agent acts only through a predefined tool set, never freely |

## Term collisions

| Term | Meaning A (context) | Meaning B (context) | Resolution |
|------|--------------------|--------------------|------------|
| "Appointment" | Buổi khám chẩn đoán ở pha 2 (bác sĩ khám) / The pha-2 diagnostic consult | Slot của một task dịch vụ ở pha 3 / A service-task time slot in pha 3 | Dùng `Appointment` chỉ cho buổi khám chẩn đoán; slot dịch vụ là `Slot` gắn với `Task` / Use `Appointment` only for the diagnostic consult; a service time slot is a `Slot` attached to a `Task` |
| "Priority" | Mức ưu tiên lâm sàng của bệnh nhân (`priority_level`) / Clinical patient priority | Ưu tiên MoSCoW của FR / MoSCoW priority of an FR | `priority_level` cho bệnh nhân trong [08](08-data-model.md); MoSCoW chỉ trong [05](05-functional-requirements.md) / `priority_level` for patients; MoSCoW only in 05 |
| "Agent" | Agent phần mềm LLM / Software LLM agent | Nhân viên điều phối (người) / Human coordinator | "Agent" luôn là phần mềm; người là `role_coordinator` / "Agent" always means software; humans are `role_coordinator` |
