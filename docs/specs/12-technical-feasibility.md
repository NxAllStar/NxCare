---
title: "Technical feasibility"
sidebar_label: "12. Technical feasibility"
description: "Per-requirement feasibility, risks, and proof-of-concept recommendations for VAIC - AI Care Pathway Coordinator."
tags: [specs, feasibility, risk, vaic]
---

# Technical feasibility

<!-- Feasibility is judged against the demo delivery (simulator, synthetic data, ~50-100 patients).
     The Partial rows are the honest ones: multi-agent LLM orchestration is powerful but its
     reliability, latency, and cost at scale are the real risks - and they are cheap to flag now. -->

## Feasibility by requirement

| FR | Requirement | Feasible | Reason / dependency | Confidence | Mitigation |
|----|-------------|----------|---------------------|------------|------------|
| [FR-01](05-functional-requirements.md#fr-01) | Intake triage routing | Partial | Định tuyến bằng LLM khả thi; độ chính xác phân loại chuyên khoa và phát hiện cấp cứu chưa kiểm chứng / LLM routing works, but specialty and emergency-signal accuracy is unproven | Medium | Bắt buộc nhân viên xác nhận (BR-02); PoC-1; luồng cấp cứu [OI-09](11-assumptions-constraints.md#oi-09) |
| [FR-02](05-functional-requirements.md#fr-02) | Least-crowded slot recommendation | Yes | Tra Forecast + sắp xếp là bài toán đã giải / forecast lookup and ranking is well-trodden | High | - |
| [FR-03](05-functional-requirements.md#fr-03) | Diagnosis and order capture | Yes | CRUD form + chữ ký, không AI trong quyết định / CRUD with signing | High | - |
| [FR-04](05-functional-requirements.md#fr-04) | Care-plan generation and sequencing | Partial | Sắp thứ tự theo ràng buộc khả thi; độ tin của LLM khi tối ưu và cardinality order->task chưa chốt / constrained sequencing works, LLM optimisation reliability and cardinality open | Medium | Constraint solver hỗ trợ LLM; PoC-2; [OI-16](11-assumptions-constraints.md#oi-16) |
| [FR-05](05-functional-requirements.md#fr-05) | Payment gate | Yes | Cổng thanh toán mô phỏng + trạng thái khóa là logic đơn giản / simulated gate and lock state | High | - |
| [FR-06](05-functional-requirements.md#fr-06) | Journey Agent escort and resequencing | Partial | Mỗi bệnh nhân một instance LLM; chi phí/latency là rủi ro ở quy mô lớn, demo ~50-100 ổn / per-patient LLM instances, cost/latency risk at scale | Medium | Event-driven (BR-12); PoC-3; giữ quy mô demo (AS-04) |
| [FR-07](05-functional-requirements.md#fr-07) | ETA/load/no-show forecasting | Partial | Đã chốt LLM-as-a-tool ([OI-20](11-assumptions-constraints.md#oi-20) resolved) - nhanh, tránh train ML; rủi ro còn lại là độ chính xác và grounding của số do LLM sinh / decided: LLM-as-a-tool, fast, no ML training; residual risk is accuracy and grounding of LLM numbers | Medium | Grounding + validate dải bắt buộc ([NFR-SEC-20](07-non-functional-requirements.md#nfr-security)); PoC-5 xác nhận độ chính xác |
| [FR-08](05-functional-requirements.md#fr-08) | Slot allocation on doctor capacity | Yes | Gán slot theo capacity với validation là chuẩn / capacity-constrained allocation | High | - |
| [FR-09](05-functional-requirements.md#fr-09) | Disruption handling, tiered autonomy | Partial | Suy luận tổ hợp là điểm nhấn nhưng độ tin/latency là rủi ro; ngưỡng N chưa chốt / combinatorial reasoning is the highlight but reliability and N are open | Medium | Constraint checker chặn action sai; PoC-4; [OI-03](11-assumptions-constraints.md#oi-03) |
| [FR-10](05-functional-requirements.md#fr-10) | Coordinator orchestration loop | Partial | Vòng lặp điều phối khả thi; batching để kiểm soát chi phí/latency cần tinh chỉnh / loop works, batching needs tuning | Medium | Xử lý batch (BR-20); PoC-3; degrade [NFR-REL-04](07-non-functional-requirements.md#nfr-reliability) |
| [FR-11](05-functional-requirements.md#fr-11) | Patient timeline notifications | Yes | Thông báo in-app trên timeline là chuẩn / in-app notifications | High | Kiểm scope tránh rò rỉ chéo (AC-11.2) |
| [FR-12](05-functional-requirements.md#fr-12) | Coordinator dashboard | Yes | Heatmap + hàng chờ duyệt + stream là chuẩn / heatmap, queue, stream | High | - |
| [FR-13](05-functional-requirements.md#fr-13) | Agent reasoning audit log | Yes | Ghi append-only kèm reasoning là đơn giản / append-only logging | High | - |
| [FR-14](05-functional-requirements.md#fr-14) | Doctor worklist chat | Partial | Khả thi nhưng phạm vi (own vs khoa) chưa chốt; Could nên cắt trước / feasible but scope open, first to cut | Medium | [OI-10](11-assumptions-constraints.md#oi-10); giữ là Could |
| [FR-15](05-functional-requirements.md#fr-15) | SMS notification channel | Partial | Mô phỏng SMS: Yes; nhà cung cấp thật chưa chọn / simulated yes, real provider not chosen | Medium | Mô phỏng cho demo; [OI-17](11-assumptions-constraints.md#oi-17) |
| [FR-16](05-functional-requirements.md#fr-16) | Learning loop | No | Ngoài phạm vi bản này theo quyết định; bước demo MAE đã bỏ / out of scope by decision; MAE demo step dropped | High | [OI-01](11-assumptions-constraints.md#oi-01) resolved; đưa vào release sau / defer to a later release |
| [FR-17](05-functional-requirements.md#fr-17) | Patient-code scan status update | Yes | Quét QR + cập nhật trạng thái là chuẩn; demo dùng quét mô phỏng (nút) / QR scan and status update are standard; demo uses a simulated scan button | High | [OI-21](11-assumptions-constraints.md#oi-21) resolved: mô phỏng cho demo / simulated for the demo |
| [FR-18](05-functional-requirements.md#fr-18) | Auth and role-based access | Yes | Đăng nhập + phân quyền phía server là chuẩn; demo auth đơn giản, SSO/MFA production là OI-11 / standard; demo auth simple, production SSO/MFA is OI-11 | High | [OI-11](11-assumptions-constraints.md#oi-11) for production only |
| [FR-19](05-functional-requirements.md#fr-19) | Reschedule / cancel appointment | Yes | CRUD theo state machine + tái dùng FR-02 / CRUD along the state machine, reuses FR-02 | High | - |
| [FR-20](05-functional-requirements.md#fr-20) | Notifications center | Yes | Danh sách có phân trang + trạng thái đã đọc / paginated list with read state | High | - |
| [FR-21](05-functional-requirements.md#fr-21) | Settings + VI/EN toggle | Yes | i18n nhãn hiển thị, codes giữ tiếng Anh / label i18n, codes stay English | High | - |
| [FR-22](05-functional-requirements.md#fr-22) | Staff patient search | Yes | Tìm kiếm lọc theo scope ở tầng dữ liệu / scope-filtered search in the data layer | High | - |
| [FR-23](05-functional-requirements.md#fr-23) | Aggregated per-station wait & AI route recommendation | Partial | Gộp `estimate_wait()` là logic đơn giản (Yes); ưu tiên hàng đợi + đánh dấu song song trong sequencing hiện có kế thừa cùng rủi ro độ tin của LLM như FR-04 / aggregating `estimate_wait()` is simple, but queue-preferential ordering and parallel-eligible flagging inside the existing sequencer inherit FR-04's LLM-reliability risk | Medium | Fallback về thứ tự chỉ theo BR-08 khi không đề xuất được hợp lệ (giống FR-04); UI cho khung nhìn gộp/tuyến đề xuất trên SCR-02 chưa được vẽ |

## Technical approach

<!-- From proposal muc 6. These are candidates the team proposed, not fully ratified decisions;
     each stays "No - OI" where a genuine choice remains. -->

| Layer | Approach | Decided | Notes |
|-------|----------|---------|-------|
| Agent framework | LangGraph (mỗi agent một graph node, state chung là hospital snapshot) hoặc loop tool-use trên FastAPI / LangGraph or a FastAPI tool-use loop | No - [OI-18](11-assumptions-constraints.md#oi-18) | LangGraph hợp roadmap; FastAPI gọn hơn / LangGraph fits, FastAPI is leaner |
| LLM (reasoning) | API model mạnh cho Coordinator/Disruption / hosted strong model | No - [OI-18](11-assumptions-constraints.md#oi-18) | Cần reasoning tốt; điều khoản lưu trữ [OI-02](11-assumptions-constraints.md#oi-02) |
| LLM (intake/journey) | Qwen self-hosted (nhiều instance, chi phí thấp, tiếng Việt ổn) / self-hosted Qwen | No - [OI-18](11-assumptions-constraints.md#oi-18) | Nhiều instance chi phí thấp / low-cost many instances |
| Forecast | LLM-with-reasoning expose thành một tool (forecast-LLM), trả kết quả qua giao diện tool / an LLM-with-reasoning exposed as a tool | Yes ([OI-20](11-assumptions-constraints.md#oi-20) resolved) | Chọn vì siêu nhanh, tránh train ML; bắt buộc grounding + validate dải (BR-14, [NFR-SEC-20](07-non-functional-requirements.md#nfr-security)) |
| State and events | Redis + WebSocket / Redis and WebSocket | Yes (candidate) | Store bền vững [OI-15](11-assumptions-constraints.md#oi-15) |
| Simulator | SimPy làm "thế giới" và môi trường eval / SimPy world and eval env | Yes (candidate) | DP-03; deterministic seed |
| Frontend | React (chat + timeline bệnh nhân; dashboard điều phối) / React | Yes (candidate) | Chat + timeline thay form cứng |

## Model feasibility

| Question | Answer | Evidence |
|----------|--------|----------|
| Năng lực có ở chất lượng chấp nhận hôm nay? / capability at acceptable quality today? | Partial - điều phối/suy luận: có; định tuyến triage an toàn: cần kiểm / coordination yes, safe triage needs testing | Chưa test trên dữ liệu / not yet tested - PoC-1 |
| Ngưỡng chính xác để chấp nhận output? / accuracy threshold to accept output? | Chưa chốt cho triage/ETA / undecided | [OI-05](11-assumptions-constraints.md#oi-05), [FR-01](05-functional-requirements.md#fr-01) |
| Đo chất lượng thế nào, ground truth nào? / how is quality measured? | Simulator là ground truth cho ETA (dự báo vs thực tế); triage cần bộ eval do đội xây / simulator for ETA, team-built eval for triage | Đội thi sở hữu / team-owned |
| Chi phí mỗi thao tác ở quy mô kỳ vọng? / cost per operation at expected volume? | Journey per-patient là chi phí lớn nhất; Qwen self-hosted giảm chi phí / per-patient Journey is the cost driver | [NFR-SCA-01](07-non-functional-requirements.md#nfr-scalability); chưa ước lượng cứng / not yet estimated |
| Latency ở quy mô kỳ vọng? / latency at expected volume? | Chưa đo; event-driven + batch để kiểm soát / not measured; event-driven and batched | [NFR-PERF-01](07-non-functional-requirements.md#nfr-performance), [OI-05](11-assumptions-constraints.md#oi-05) |
| Điều khoản lưu trữ provider phù hợp classification? / provider retention compatible? | Unread | [OI-02](11-assumptions-constraints.md#oi-02), [NFR-SEC-14](07-non-functional-requirements.md#nfr-security) |
| Hành vi khi model sai? / behaviour when the model is wrong? | Constraint checker chặn; fallback baseline; giữ trạng thái / checker blocks, baseline fallback, hold | [NFR-REL-04](07-non-functional-requirements.md#nfr-reliability), [FR-07](05-functional-requirements.md#fr-07) |

## Risks

| ID | Risk | Likelihood | Impact | Affects | Mitigation | Owner |
|----|------|------------|--------|---------|------------|-------|
| R-01 | LLM ảo giác con số / LLM fabricates a number - rủi ro **hiện hữu** vì Forecast đã chốt dùng LLM-as-a-tool ([OI-20](11-assumptions-constraints.md#oi-20) resolved) / an active risk since Forecast is now an LLM-backed tool | High | High | [FR-06](05-functional-requirements.md#fr-06), [FR-07](05-functional-requirements.md#fr-07), [FR-09](05-functional-requirements.md#fr-09), [FR-10](05-functional-requirements.md#fr-10) | Grounding bắt buộc: neo vào thống kê truy hồi + validate dải + từ chối số ngoài dải (CO-05, BR-14, [NFR-SEC-20](07-non-functional-requirements.md#nfr-security)); PoC-5 đo độ chính xác | Team lead |
| R-02 | Latency/chi phí LLM khi nhiều bệnh nhân đồng thời / LLM latency and cost under concurrency | Medium | Medium | [FR-06](05-functional-requirements.md#fr-06), [FR-10](05-functional-requirements.md#fr-10) | Journey event-driven, Coordinator batch; giữ quy mô demo; PoC-3 | Team lead |
| R-03 | Demo trục trặc do tính ngẫu nhiên của LLM / demo flakiness from LLM nondeterminism | Medium | High | Demo script | Seed kịch bản + fallback recording; sim/forecast deterministic ([NFR-REL-05](07-non-functional-requirements.md#nfr-reliability)) | Team lead |
| R-04 | Prompt injection qua chat bệnh nhân / prompt injection via patient chat | Medium | High | [FR-01](05-functional-requirements.md#fr-01), [FR-06](05-functional-requirements.md#fr-06) | Nội dung là dữ liệu, delimit untrusted; constraint checker ([NFR-SEC-11](07-non-functional-requirements.md#nfr-security), [NFR-SEC-13](07-non-functional-requirements.md#nfr-security)) | Team lead |
| R-05 | Giám khảo phản biện "over-engineering, rule là đủ" / judges say rules suffice | Medium | Medium | Positioning | Demo bước 3 (sự cố tổ hợp) và bước 4 (đối thoại hai chiều) - rule không phủ nổi | Team lead |
| R-06 | Vượt ranh giới lâm sàng (AI tự sinh chỉ định) / AI crosses the clinical boundary | Low | High | CO-02, an toàn / safety | Ranh giới 3 pha cứng; `ServiceOrder` chỉ bác sĩ tạo (BR-05); AC-03.2 | Team lead |
| R-07 | Forecast kém chính xác làm ETA sai, bệnh nhân mất tin / poor forecast erodes ETA trust | Medium | Medium | [FR-07](05-functional-requirements.md#fr-07) | Đo MAE trên simulator; fallback baseline gắn cờ; target [OI-05](11-assumptions-constraints.md#oi-05) | Team lead |

## Proof-of-concept recommendations

| # | PoC | Question it answers | Effort | Blocks |
|---|-----|---------------------|--------|--------|
| 1 | Test 20 hội thoại triệu chứng thật/giả -> so phân loại chuyên khoa với nhãn / 20 symptom chats vs specialty labels | Intake định tuyến đủ chính xác và an toàn? / is triage accurate and safe? | 1-2 ngày / days | [FR-01](05-functional-requirements.md#fr-01) |
| 2 | Sinh care plan cho 5 ca chỉ định mẫu, kiểm ràng buộc nhịn ăn/phụ thuộc / 5 sample order sets | Sắp thứ tự tôn trọng ràng buộc và tối ưu? / does sequencing respect constraints? | 2 ngày / days | [FR-04](05-functional-requirements.md#fr-04) |
| 3 | Chạy 50 bệnh nhân trên simulator, đo latency/chi phí vòng lặp agent / 50-patient sim run | Latency/chi phí có trong ngưỡng chấp nhận? / within latency and cost budget? | 2-3 ngày / days | [FR-06](05-functional-requirements.md#fr-06), [FR-10](05-functional-requirements.md#fr-10) |
| 4 | Kịch bản "máy X-quang hỏng" với 3 bệnh nhân khác hồ sơ / X-ray failure scenario | Disruption Agent xử lý tổ hợp đúng và an toàn? / does disruption reasoning hold? | 2 ngày / days | [FR-09](05-functional-requirements.md#fr-09) |
| 5 | Đo forecast-LLM (neo dữ liệu) so với baseline thống kê cho ETA 1 phòng / grounded forecast-LLM vs a statistical baseline for one room's ETA | LLM-as-a-tool có đủ chính xác (MAE) và grounding không? / is the chosen LLM tool accurate and grounded enough? | 1-2 ngày / days | [FR-07](05-functional-requirements.md#fr-07) |

**Exit criteria**: PoC-1 "go" nếu phân loại đúng chuyên khoa >= ngưỡng do Team lead đặt ([OI-05](11-assumptions-constraints.md#oi-05)) và không bỏ sót dấu hiệu cấp cứu; nếu không, giữ định tuyến nhưng tăng vai trò xác nhận của nhân viên. PoC-3 "go" nếu p95 latency trong ngưỡng đề xuất ([NFR-PERF-01](07-non-functional-requirements.md#nfr-performance)); nếu không, giảm phạm vi agent hoặc tăng batch. / Decide go/no-go before each PoC runs.

## Effort indication

| Requirement group | Indicative effort | Assumes |
|-------------------|-------------------|---------|
| Nền: simulator, Forecast tools, state/bus / foundation | 1 tuần / week | Đội 3-4 người, stack đề xuất / 3-4 people, proposed stack |
| Agent core: Coordinator, Intake, Care Plan, Journey / core agents | 1-2 tuần / weeks | DP-01..04 sẵn sàng / dependencies ready |
| Disruption + dashboard + audit / disruption and dashboard | 1 tuần / week | Ngưỡng N chốt ([OI-03](11-assumptions-constraints.md#oi-03)) |

## Coverage check

- [x] Every FR in [05](05-functional-requirements.md) has a row above (22 FRs, 22 rows).
- [x] Every "Partial" and every "No" names a specific blocker.
- [x] Every "No" traces to a decision or open issue ([FR-16](05-functional-requirements.md#fr-16) -> [OI-01](11-assumptions-constraints.md#oi-01) resolved: out of scope by decision).
