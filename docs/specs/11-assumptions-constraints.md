---
title: "Assumptions and constraints"
sidebar_label: "11. Assumptions and constraints"
description: "What was assumed, what binds the design, and what is still open for VAIC - AI Care Pathway Coordinator."
tags: [specs, assumptions, constraints, open-issues, vaic]
---

# Assumptions and constraints

<!-- This file is where nothing was invented. Every gap in 01-10 that could not be answered from the
     proposal or the elicitation lives here as an assumption (proceeding on it) or an open issue
     (not proceeding). The Team lead owns most of them because the delivery is a demo. -->

## Assumptions

| ID | Assumption | Why we are assuming it | Impact if false | Owner | Confirmed |
|----|-----------|------------------------|-----------------|-------|-----------|
| AS-01 | Tên hệ thống là "VAIC - AI Care Pathway Coordinator" / system name is "VAIC - AI Care Pathway Coordinator" | Nguồn không nêu tên; suy từ thư mục `vaic` và mô tả / source states no name; derived from the `vaic` directory | Đổi tên -> sửa frontmatter và tiêu đề (rẻ) / rename touches titles only (cheap) | Team lead | No |
| AS-02 | App KHÔNG xử lý thanh toán; "thanh toán" chỉ là một cờ cho phép tiến hành, việc trả tiền diễn ra ngoài app (quầy/hệ thống viện) / the app processes no payment; "payment" is only a proceed-gate flag, actual paying happens outside the app | Team lead chốt: không có thanh toán trong app / Team lead: no payment in the app | Nếu sau này cần thu tiền trong app -> thêm tích hợp cổng thật ([INT-02](09-integration-interface.md)) / adding in-app charging needs a real gateway | Team lead | Yes (elicitation) |
| AS-03 | Bản demo dùng dữ liệu tổng hợp, không có PHI thật. Tài liệu bảo mật (bao gồm DPA + DPO) phải đầy đủ mức production **dù demo hay production**; chỉ phần *hiện thực* trong demo có thể chưa enforce hết / demo uses synthetic data, no real PHI. Security documentation (incl. DPA + DPO) must be full production grade whether demo or production; only the demo *implementation* may lag | Team lead yêu cầu tài liệu đầy đủ dù có triển khai hay không / Team lead requires full docs regardless of deployment | Nếu tài liệu thiếu -> mất điểm AI Safety & Trust và không thể lên production / missing docs cost the safety score and block production | Team lead | Yes (elicitation) |
| AS-04 | Quy mô demo ~50-100 bệnh nhân mỗi run / demo scale ~50-100 patients per run | Team lead chọn "smaller is fine" / elicitation | Quy mô 300+ -> cần kiểm tải và tinh chỉnh batch/latency / larger scale needs load work | Team lead | Yes (elicitation) |
| AS-05 | Phân quyền theo scoping chuẩn (patient Own; doctor/tech Assigned + Own worklist; coordinator/admin All) / standard permission scoping | Team lead chọn scoping chuẩn / elicitation | Đổi scope -> sửa ma trận [06](06-access-control.md) và bộ lọc dữ liệu / changes touch the matrix and filters | Team lead | Yes (elicitation) |
| AS-06 | Không có tự đăng ký bệnh nhân bản này; bệnh nhân tạo qua seed/tiếp nhận / no patient self-registration this release; patients created via seed/intake | Team lead chọn "believable-but-lean" và không chọn onboarding tự phục vụ / elicitation | Nếu cần self-registration -> thêm luồng đăng ký/onboarding và màn hình / adding it needs a registration/onboarding flow and screen | Team lead | Yes (elicitation) |

## Constraints

| ID | Constraint | Type | Source | Consequence for the design |
|----|-----------|------|--------|----------------------------|
| CO-01 | Bản demo hackathon chạy trên simulator, không tích hợp hệ thống bệnh viện thật, không dữ liệu thật / hackathon demo on a simulator, no real hospital integration, no real data | Business / Time | Team lead (elicitation) | Loại HIS/EMR/LIS/PACS thật; simulator vừa là "thế giới" vừa là môi trường eval / no real hospital systems |
| CO-02 | AI không quyết định lâm sàng và không sinh chỉ định dịch vụ; chẩn đoán/chỉ định là của bác sĩ / AI never makes clinical decisions or generates service orders | Business / Safety | Proposal muc 3 guardrail 1 | Ranh giới 3 pha bắt buộc; `ServiceOrder` chỉ do bác sĩ tạo (BR-05) |
| CO-03 | Agent chỉ hành động qua action space đóng; constraint checker (code) chạy trước mọi action / agents act only through a closed action space; a checker runs before every action | Technical | Proposal muc 3 guardrail 2 | Không action tự do; validation cứng ([NFR-SEC-13](07-non-functional-requirements.md#nfr-security)) |
| CO-04 | Phân tầng tự chủ: ảnh hưởng > N cần người duyệt / tiered autonomy: impact > N needs human approval | Business / Safety | Proposal muc 3 guardrail 3 | Cần luồng duyệt và dashboard ([FR-09](05-functional-requirements.md#fr-09), [FR-12](05-functional-requirements.md#fr-12)) |
| CO-05 | Mọi con số dự báo phải neo được vào dữ liệu quan sát và được validate dải (grounding); LLM không được bịa số tự do / every forecast number must be grounded in observed data and range-validated; no free-form fabrication | Technical / Safety | Team lead (elicitation); proposal muc 8 | Ràng buộc là *grounding*, không phải "phải là ML"; Forecast đã chốt = **LLM-as-a-tool** ([OI-20](#oi-20) resolved) / the binding rule is grounding; Forecast decided = LLM-as-a-tool |
| CO-06 | Prose song ngữ VI+EN; codes/IDs/enums/tên thực thể giữ tiếng Anh / bilingual VI+EN prose; codes stay English | Organisational | Team lead (elicitation) | Áp dụng toàn bộ [docs/specs](README.md) |
| CO-07 | Learning loop ngoài phạm vi bản này / learning loop is out of scope this release | Time / Scope | Team lead (elicitation) | [FR-16](05-functional-requirements.md#fr-16) là Won't; bước demo MAE-giảm đã bỏ ([OI-01](#oi-01) resolved) / the MAE-improvement demo step is dropped |

## Open issues

| ID | Question | Blocks | Owner | Needed by | Status |
|----|----------|--------|-------|-----------|--------|
| OI-02 {#oi-02} | Điều khoản lưu trữ dữ liệu của nhà cung cấp LLM API đã đọc chưa, có train trên dữ liệu gửi lên không? / has the hosted LLM provider's data-retention policy been read? | [NFR-SEC-14](07-non-functional-requirements.md#nfr-security) | Team lead | Trước khi gọi API với dữ liệu bất kỳ / before any API call | Open |
| OI-03 {#oi-03} | Giá trị ngưỡng N (số bệnh nhân) phân tầng tự chủ là bao nhiêu? / what is the value of threshold N for tiered autonomy? | [FR-09](05-functional-requirements.md#fr-09) | Team lead | Trước khi build Disruption Agent / before building disruption handling | Open |
| OI-05 {#oi-05} | Các target Performance (p95 latency agent, MAE ETA) là bao nhiêu? / what are the performance targets? | [NFR-PERF-01](07-non-functional-requirements.md#nfr-performance)..04 | Team lead | Trước eval demo / before demo eval | Open |
| OI-06 {#oi-06} | Ai là quản trị lâm sàng ký duyệt an toàn cho bản production? / who is the clinical-governance sign-off for production? | Production go-live | Team lead -> hospital | Trước production (tương lai) / before production | Open |
| OI-07 {#oi-07} | Ai là DPO và luật dữ liệu y tế nào áp dụng cho production? / who is the DPO and which health-data law applies? | [NFR-SEC-18](07-non-functional-requirements.md#nfr-security) | Team lead -> hospital | Trước production (tương lai) | Open |
| OI-08 {#oi-08} | Baseline thời gian chờ/ùn tắc hiện tại là bao nhiêu (để so A/B có ý nghĩa)? / what are the current wait/congestion baselines? | Success metrics [01](01-overview.md) | Team lead | Từ FIFO baseline run / from the FIFO baseline run | Open |
| OI-09 {#oi-09} | Cơ chế escalate đã định nghĩa ở [BF-05](04-business-flows.md); còn lại: **nội dung danh sách red-flag lâm sàng** (dấu hiệu nào Intake gắn cờ) là quyết định lâm sàng, cần bác sĩ cung cấp / the escalation mechanism is defined in BF-05; what remains is the clinical red-flag list content, a clinical decision the doctor must provide | [FR-01](05-functional-requirements.md#fr-01), [BF-05](04-business-flows.md) | Persona bác sĩ (SH-02) | Trước eval intake / before intake eval | Open (narrowed) |
| OI-10 {#oi-10} | Chat worklist của bác sĩ chỉ đổi lịch của chính mình hay cả khoa? / does doctor worklist chat affect only the doctor or the whole department? | [FR-14](05-functional-requirements.md#fr-14) | Team lead | Trước build [FR-14](05-functional-requirements.md#fr-14) (Could) | Open |
| OI-11 {#oi-11} | Auth demo đã có qua [FR-18](05-functional-requirements.md#fr-18) (đăng nhập + phân quyền theo vai); còn lại: **identity provider/SSO, session lifetime, MFA cho production** / demo auth done via FR-18; production SSO, session lifetime, MFA remain | [06](06-access-control.md) auth (production) | Team lead -> hospital IT | Trước production (tương lai) | Open (narrowed) |
| OI-12 {#oi-12} | Cadence xoay secret/khóa API? / secret and API-key rotation cadence? | [NFR-SEC-09](07-non-functional-requirements.md#nfr-security) | Team lead | Trước production; demo dùng biến môi trường / before production | Open |
| OI-13 {#oi-13} | Chính sách lưu trữ/xóa theo classification cho production? / production retention and deletion policy? | [NFR-SEC-19](07-non-functional-requirements.md#nfr-security) | Team lead -> DPO | Trước production (tương lai) | Open |
| OI-14 {#oi-14} | Mức cam kết accessibility (WCAG 2.1 AA đầy đủ hay tập con)? / accessibility commitment level? | [NFR-USE-02](07-non-functional-requirements.md#nfr-usability) | Team lead | Trước hoàn thiện UI / before UI polish | Open |
| OI-16 {#oi-16} | Một `ServiceOrder` sinh 1 hay nhiều `Task` (có bước chuẩn bị)? / order-to-task cardinality? | [FR-04](05-functional-requirements.md#fr-04), [08](08-data-model.md) | Persona bác sĩ (SH-02) | Trước build Care Plan Agent / before care-plan build | Open |
| OI-17 {#oi-17} | Nhà cung cấp SMS cho production? / SMS provider for production? | [FR-15](05-functional-requirements.md#fr-15), [INT-03](09-integration-interface.md) | Team lead | Trước production; demo mô phỏng / before production | Open |
| OI-18 {#oi-18} | Nhà cung cấp LLM API cụ thể và có triển khai production không? / specific LLM vendor and production deployment? | [INT-04](09-integration-interface.md) | Team lead | Trước eval và trước production / before eval and production | Open |
| OI-19 {#oi-19} | **Cơ chế đã chốt**: nhân viên quét mã bệnh nhân (`patient_code`) tại quầy để xác nhận thanh toán - một sự kiện quét riêng biệt, sớm hơn quét hiện diện tại phòng của [FR-17](05-functional-requirements.md#fr-17) (BR-36). **Còn mở**: vai trò nhân viên cụ thể được phép thực hiện quét này (chỉ nhân viên quầy/điều phối viên, hay cả bác sĩ/KTV)? / **Mechanism decided**: staff confirm payment by scanning the patient's code at the counter - a distinct, earlier scan than FR-17's room-presence scan (BR-36). **Still open**: which staff role may perform this scan (front-desk/coordinator only, or also doctor/technician)? | [FR-05](05-functional-requirements.md#fr-05), [FR-17](05-functional-requirements.md#fr-17) | Team lead | Trước build FR-05/careplan-dev (TASK-008) / before FR-05 is built | Open (narrowed) |
| OI-22 {#oi-22} | **Tính năng minh bạch hàng đợi / số thứ tự** (unifying tracking): bệnh nhân thấy còn bao nhiêu người trước mình + thời gian chờ; bác sĩ thấy số bệnh nhân dự kiến. Câu hỏi mở cho brainstorm: (a) số thứ tự theo từng dịch vụ/khám hay một số cho cả lượt khám? (b) hệ thống số online theo dõi xuyên suốt exam-to-exam hay giấy (baseline thực tế)? (c) tương tác: task `LOCKED`/chưa thanh toán có tính vào "người trước bạn" không; ưu tiên (cấp cứu chen ngang) hiển thị ra sao; vị trí thay đổi khi agent re-sequence động - hiển thị thế nào để không mất niềm tin. / **Queue-position / ticket transparency feature**: patients see how many are ahead + wait; doctors see anticipated patient count. Open for brainstorm: (a) per-service vs per-visit ticket; (b) online exam-to-exam tracking vs paper baseline; (c) interactions with the payment gate, priority pre-emption, and dynamic re-sequencing (how to show a changing position without eroding trust). Feeds an ADR + a candidate FR. | Một FR ứng viên (chưa đánh số) / a candidate FR (unnumbered yet); [TASK-017](../tasks/active/) | Team lead (brainstormer + tech-researcher) | Trước khi đặc tả FR mới / before speccing the new FR | Open |
| OI-23 {#oi-23} | Brief cuộc thi ([01](01-overview.md#contest-brief), Feature 2 "Patient Routing") nêu định tuyến theo **"patient category"** (VD trẻ em/người lớn tuổi/nhóm bảo hiểm) bên cạnh symptom/priority/service; schema triage hiện tại của [FR-01](05-functional-requirements.md#fr-01) là `{specialty, priority_level, constraints}` và không có trường patient-category tường minh. Cần Team lead xác nhận: có phải bổ sung trường này, hay "category" đã được phủ ngầm định qua `constraints` (VD "thai kỳ", "đi lại khó")? / The contest brief ([01](01-overview.md#contest-brief), Feature 2 "Patient Routing") names routing by **"patient category"** (e.g. child/elderly/insurance class) alongside symptom/priority/service; FR-01's current triage schema is `{specialty, priority_level, constraints}` with no explicit patient-category field. Needs Team lead confirmation: add the field, or is "category" already implicitly covered by `constraints` (e.g. pregnancy, limited mobility)? | [FR-01](05-functional-requirements.md#fr-01) | Team lead | Trước khi mở rộng schema triage / before extending the triage schema | Open |

### Resolved issues

| ID | Question | Resolution | Decided by |
|----|----------|-----------|------------|
| OI-00a | Delivery là demo hay production? / demo or production? | Hackathon demo trên simulator, không dữ liệu thật / hackathon demo on simulator | Team lead |
| OI-00b | Ngôn ngữ tài liệu? / documentation language? | Song ngữ VI+EN, codes tiếng Anh / bilingual VI+EN | Team lead |
| OI-00c | Learning loop trong scope? / learning loop in scope? | Ngoài scope bản này / out of scope this release | Team lead |
| OI-00d | Ai sở hữu quyết định bảo mật? / security decision owner? | Team lead (demo, không PHI thật) / Team lead | Team lead |
| OI-00e | MoSCoW priorities? | Duyệt như đề xuất (11 Must, 2 Should, 2 Could, 1 Won't) / approved as proposed | Team lead |
| OI-00f | Phạm vi quyền theo role? / permission scope? | Scoping chuẩn / standard scoping | Team lead |
| OI-00g | Hình dạng app? / app shape? | Một web app responsive, phân quyền theo vai / one responsive role-gated web app ([FR-18](05-functional-requirements.md#fr-18)) | Team lead |
| OI-00h | Mức độ hoàn thiện demo? / rounding depth? | Believable-but-lean; thêm FR-18..22 chức năng hỗ trợ tối giản / add FR-18..22 as minimal supporting functions | Team lead |
| OI-00i | Thiết kế/UI-UX? / design direction? | Định nghĩa design system nhẹ (Tailwind + shadcn/ui) trong [10](10-ui-ux-wireframes.md) / lightweight design system defined in 10 | Team lead |
| OI-01 {#oi-01} | Learning loop và mâu thuẫn demo step 5 (MAE giảm)? / learning loop and the demo-step-5 conflict? | Learning loop **ngoài scope** bản này; **bỏ** bước demo MAE-giảm-theo-tuần. Lý do: Forecast là LLM-as-a-tool (không train ML), nên learning loop kiểu retrain chưa áp dụng / learning loop out of scope; drop the MAE-over-a-week demo step, since Forecast is LLM-as-a-tool with no ML training | Team lead |
| OI-20 {#oi-20} | Forecast dùng ML hay LLM? / ML or LLM forecast? | **LLM-with-reasoning expose thành một tool** (chọn vì siêu nhanh, tránh train ML). Kết quả của forecast-LLM trả về cho agent điều phối qua giao diện tool. Grounding + validate dải vẫn bắt buộc ([NFR-SEC-20](07-non-functional-requirements.md#nfr-security)) / an LLM-with-reasoning exposed as a tool, chosen for speed over ML training; output returns through the tool interface; grounding still mandatory | Team lead |
| OI-21 {#oi-21} | Quét mã thật hay mô phỏng? / real or simulated scan? | **Mô phỏng** trong demo (nút quét), không cần camera/QR thật / simulated in the demo (a scan button), no real camera needed | Team lead |
| OI-15 {#oi-15} | Store bền vững ngoài Redis (nếu cần lưu qua nhiều run)? / durable store beyond Redis? | **PostgreSQL qua SQLAlchemy** (TASK-032): DDL tại `src/vaic/state/sql/schemas.sql` (nguồn sự thật), model SQLAlchemy tại `src/vaic/state/sql/models.py`. Redis vẫn là store mặc định của app; chưa có `Repository` backend chạy trên Postgres - chỉ mới có schema. / **PostgreSQL via SQLAlchemy** (TASK-032): DDL in `src/vaic/state/sql/schemas.sql` (source of truth), SQLAlchemy models in `src/vaic/state/sql/models.py`. Redis remains the app's default store; no live `Repository` backend runs on Postgres yet - only the schema exists so far. | tuan.nguyen15 |

## Dependencies

| ID | Dependency | Depends on (team or system) | Needed by | Risk if late |
|----|-----------|-----------------------------|-----------|--------------|
| DP-01 | Truy cập LLM provider API / LLM API access | Nhà cung cấp bên ngoài ([INT-04](09-integration-interface.md)) | Trước eval / before eval | Coordinator/Disruption không suy luận được / no strong reasoning |
| DP-02 | Triển khai Qwen self-hosted / self-hosted Qwen | Đội thi ([INT-05](09-integration-interface.md)) | Trước build Intake/Journey / before intake and journey | Chi phí LLM tăng, tiếng Việt kém hơn / higher cost |
| DP-03 | Simulator SimPy sẵn sàng / SimPy simulator ready | Đội thi ([INT-01](09-integration-interface.md)) | Trước mọi eval / before any eval | Không có "thế giới" cho agent và metrics / no world or metrics |
| DP-04 | Forecast models huấn luyện trên dữ liệu seed / trained forecast models | Đội thi ([FR-07](05-functional-requirements.md#fr-07)) | Trước build agent phụ thuộc ETA / before ETA-dependent agents | Agent không có số để suy luận / no numbers to reason on |

## What is explicitly NOT specified

- Tích hợp HIS/EMR/LIS/PACS thật - hoàn toàn ngoài phạm vi bản demo. / Real hospital-system integrations are entirely out of scope.
- Học máy tự cải thiện (learning loop) - [FR-16](05-functional-requirements.md#fr-16) Won't; xem [OI-01](#oi-01). / The self-improving learning loop.
- Chẩn đoán, gợi ý điều trị, hay bất kỳ quyết định lâm sàng nào - CO-02. / Any clinical decision-making.
- Quy trình tài chính thật (hóa đơn, hoàn tiền) - chỉ mô phỏng cổng thanh toán. / Real financial workflows beyond a simulated gate.
- Chính sách vận hành production (SLA, on-call, DR đã diễn tập) - bản demo không cam kết. / Production operational policies.
