# AI Hospital Management System — Clinician / Staff Web App
### Feature Architecture (v1)

## Product Vision

Xây dựng **AI-first Clinical Operations Console** — "nhà bếp" phía sau trải nghiệm bệnh nhân. Nơi bác sĩ, kỹ thuật viên, lễ tân và quản lý *tạo ra* mọi thứ bệnh nhân nhìn thấy: chỉ định dịch vụ, lộ trình, kết quả, hóa đơn. AI agents chạy xuyên suốt để **điều phối luồng, giảm thời gian chờ, và xử lý sự cố realtime**, nhưng luôn dưới sự kiểm soát của con người.

**Nguyên tắc nền tảng:**
1. **Clinician là nguồn sự thật.** AI *không* chẩn đoán, *không* tự chỉ định dịch vụ. Bác sĩ chẩn đoán → AI sinh task điều phối *từ* chỉ định đó.
2. **Human-in-the-loop phân tầng.** Hành động AI ảnh hưởng nhỏ → tự chạy; ảnh hưởng lớn → chờ người duyệt. Mọi hành động có nhãn tự chủ + audit trail.
3. **Một sự thật, nhiều góc nhìn.** Bác sĩ và bệnh nhân nhìn cùng dữ liệu — clinician tạo, patient tiêu thụ.

**Platform:** Web-first (tác vụ nặng, nhiều màn hình, nhập liệu). Mobile companion cho tra cứu nhanh tại giường / hành lang. Console dark, dày đặc, kiểu phòng điều khiển.

**Vai trò (một app, phân quyền theo role):** Lễ tân · Bác sĩ · Kỹ thuật viên · Điều phối viên · Quản lý.

**Ưu tiên:** `P0` = lõi hackathon · `P1` = khác biệt · `P2` = tầm nhìn.

---

# Module 1. Command Center & Role Home `P0`

Màn hình chủ theo từng vai, trên nền một **bảng điều phối vận hành chung**.

## Ops Command Center (điều phối viên / quản lý)
- **KPI realtime**: thời gian chờ TB, mức tắc nghẽn, utilization, số ca đang trong luồng, số hành động AI cần duyệt.
- **Heatmap các khoa**: hàng đợi, trạng thái máy (idle/busy/down), mức tắc nghẽn theo màu.
- **Agent Activity Feed**: dòng chảy realtime mọi hành động AI, kèm reasoning + nhãn tự chủ.
- **Forecast ribbon**: dự báo tải các giờ tới.

## Role Home (bác sĩ / KTV / lễ tân)
- Mỗi vai vào thẳng worklist của mình (xem module tương ứng).
- Việc cần chú ý nổi lên đầu (kết quả cần đọc, ca chờ duyệt, sự cố).

> Ánh xạ Patient M1 (Live Companion): cái bệnh nhân thấy "AI đang giữ chỗ cho bạn" **được sinh ra ở đây**.

---

# Module 2. Smart Scheduling Board (CORE) `P0`

Đầu đối ứng của Patient M2 (Đặt lịch + gợi ý giờ).

- **Bảng lịch toàn viện**: theo bác sĩ / phòng / máy / khung giờ.
- **AI đề xuất slot** theo capacity thật (Capacity brain — Module 10) để **dàn tải, tránh dồn cục**.
- Nhìn thấy và ghi đè đề xuất của AI (lễ tân/điều phối là người quyết).
- Kéo–thả xếp lịch; cảnh báo xung đột (bác sĩ trùng giờ, phòng đóng).
- Overbooking warning trước khi một khung giờ quá tải.
- Quản lý dời/hủy hàng loạt khi có biến động.

---

# Module 3. Intake Confirmation Queue `P0`

Đầu đối ứng của Patient M2 (AI Intake định tuyến). **Người xác nhận cuối.**

- Hàng đợi bệnh nhân đã qua hội thoại Intake Agent.
- Xem **transcript triệu chứng** (tiếng Việt) + **structured output**: chuyên khoa nghi ngờ (kèm phương án thay thế), mức ưu tiên, ràng buộc (nhịn ăn / thai kỳ).
- **Banner guardrail cố định:** "Định tuyến, không phải chẩn đoán".
- Nút **Xác nhận & định tuyến** / **Đổi chuyên khoa** — bắt buộc có người xác nhận.

---

# Module 4. Doctor Workspace (CORE) `P0`

Đầu đối ứng của Patient M3 (Care Journey) + M4/M5 (kết quả, đơn thuốc).

## Smart Worklist
- Danh sách bệnh nhân trong ngày: thứ tự, trạng thái, cờ **"kết quả đã về"**.
- Capacity bar của ngày.

## Chat-with-Worklist ⭐
- Bác sĩ điều phối ngày làm việc bằng **tiếng Việt tự nhiên**: "dồn các ca tái khám lên buổi sáng giúp tôi" → Care Plan Agent đề xuất thay đổi cụ thể → bác sĩ `Áp dụng` / `Hoàn tác`.
- Gợi ý chủ động: "Kết quả máu của P-2041 đã về — khám luôn chứ?"

## Clinical Source-of-Truth & Ký số ⭐ *nâng cấp bắt buộc*
- **Nhập chẩn đoán** (danh sách bệnh/tình trạng).
- **Chỉ định dịch vụ** (xét nghiệm, siêu âm, X-quang, CT, MRI...) — đây là **nguồn sự thật** để AI sinh task điều phối. AI *không* tự thêm/bớt.
- **Ký số** — chỉ định có hiệu lực pháp lý sau khi ký. Không có bước này, toàn bộ AI phía sau mất tính hợp lệ y khoa.

## e-Prescribing
- Kê đơn điện tử với **cảnh báo tương tác thuốc / dị ứng** (đối chiếu EMR — dị ứng, thuốc đang dùng).
- Đơn đẩy thẳng sang Patient M5 + nhà thuốc.

---

# Module 5. Technician Workspace (Lab / Imaging) `P0`

Đầu đối ứng của Patient M3 (queue realtime) + M4 (kết quả).

- **Hàng đợi công việc theo máy / phòng**: ai đang chờ, ưu tiên, ràng buộc (nhịn ăn).
- Đánh dấu **bắt đầu / hoàn thành** từng ca.
- **Nhập / đẩy kết quả** → tự động kích hoạt bước kế trong lộ trình bệnh nhân (event-driven).
- **Báo sự cố thiết bị** (máy hỏng) → kích hoạt Disruption Agent (Module 6).

---

# Module 6. Care Orchestration & Disruption Center (CORE) `P0`

Đầu đối ứng của Patient M3 (Journey tự cập nhật) + Live Companion. **Nơi diễn ra khoảnh khắc demo vàng.**

## Care Orchestration Console
- **Care plan từng bệnh nhân** dạng task list: service, owner (bác sĩ/KTV/phòng), thời lượng dự kiến, ràng buộc & phụ thuộc, trạng thái.
- **Kéo–thả reorder**; **constraint checker** (code thường) chặn thao tác sai (không thể phá ràng buộc nhịn ăn / phụ thuộc kết quả) + giải thích lý do.
- Reasoning stream "vì sao thứ tự này" — cùng logic bệnh nhân thấy, bản kỹ thuật.

## Disruption Center ⭐
- Sự cố (máy hỏng / cấp cứu chen ngang / bác sĩ về sớm / no-show) → Disruption Agent:
  - Đánh giá **blast radius** (bao nhiêu bệnh nhân ảnh hưởng).
  - Sinh **phương án re-plan per-patient** (mỗi bệnh nhân một cách xử lý).
  - Hiển thị **reasoning streaming** trực tiếp.
- **Human-in-the-loop phân tầng:** ≤ N bệnh nhân → tự thực thi (`Tự động`); lớn hơn → **hàng đợi duyệt** với nút `Duyệt / Sửa / Từ chối`.
- Có nút **giả lập sự cố** (demo control): "máy X-quang hỏng", "cấp cứu đến".

---

# Module 7. Autonomy & Approval Console `P0` ⭐ *nâng cấp bắt buộc*

Bộ mặt của nguyên tắc "AI cân bằng" phía clinician — thứ giám khảo hỏi đầu tiên về an toàn.

- **Hàng đợi phê duyệt** hợp nhất mọi đề xuất AI cần người duyệt.
- Mỗi mục: agent nào, ảnh hưởng bao nhiêu ca, **reasoning đầy đủ**, nhãn tự chủ (`Tự động` / `Chờ duyệt` / `Chỉ con người`).
- **Chính sách tự chủ cấu hình được**: ngưỡng N bệnh nhân, loại hành động nào luôn cần người.
- **Audit trail toàn bộ**: mỗi quyết định lưu kèm chain-of-thought → giải trình được ("vì sao bệnh nhân này bị đổi lịch?").

---

# Module 8. Electronic Medical Records (EMR) `P1`

Đầu đối ứng của Patient M4 (hồ sơ, kết quả).

- Bệnh án đầy đủ: tiền sử, ghi chú lâm sàng, chẩn đoán, chỉ định, kết quả, hình ảnh — một chỗ.
- Lịch sử liên khoa.
- Ký số, phân quyền truy cập, audit log.
- Xuất Visit Summary (đồng bộ với Patient M4).

## Shift Handoff Agent ⭐ *mới — differentiator riêng của clinician*
- Cuối ca trực, AI **tự tổng hợp bàn giao**: bệnh nhân nào đang dở lộ trình, chờ gì, cần theo dõi gì → sinh bản handoff cho ca sau.
- Nhắm đúng painpoint gốc "poor inter-department coordination" — điểm gãy an toàn kinh điển của bệnh viện.
- Chưa app nào làm tốt; đây là điểm nhận diện của phía clinician.

---

# Module 9. Inpatient Management `P2` *(nếu bật scope nội trú)*

- Quản lý giường, nhập / xuất viện, chuyển khoa.
- Y lệnh, theo dõi sinh hiệu, lịch điều dưỡng.
- Bàn giao ca nội trú (mở rộng của Shift Handoff Agent).

---

# Module 10. Capacity, Roster & Resource Brain `P0` *(xương sống)* ⭐ *nâng cấp bắt buộc*

Ít hào nhoáng nhưng thiếu nó thì scheduling chỉ là đoán mò.

- **Quản lý ca trực** bác sĩ / KTV.
- **Capacity model**: năng lực thật của từng bác sĩ (thời gian khám TB theo loại bệnh) × máy × phòng × khung giờ.
- **Service-time profile tự cập nhật** (EMA) — đầu vào ngày càng chính xác cho Forecast Agent.
- Feed trực tiếp vào Smart Scheduling Board (M2) và Forecast Agent → gợi ý slot cho bệnh nhân mới *đúng*.

---

# Module 11. Billing, Insurance & Admin `P1`

Đầu đối ứng của Patient M6 (viện phí, BHYT).

- Tổng hợp chi phí theo bệnh nhân, xuất hóa đơn.
- Xử lý hồ sơ **BHYT**, đối soát bảo hiểm.
- Quản trị hệ thống: phân quyền, cấu hình, danh mục dịch vụ/giá.

---

# Module 12. Analytics, Digital Twin & Impact `P1`

Cho quản lý — chứng minh hiệu quả + hỗ trợ ra quyết định.

## Impact Analytics
- Dashboard vận hành: wait time, congestion, utilization theo thời gian thực + lịch sử.
- **A/B so sánh**: FIFO baseline vs AI-orchestrated (giảm % chờ, tăng % utilization).
- **Learning curve**: MAE của ETA giảm dần theo ngày — bằng chứng hệ thống *tự học* (điểm riêng của hướng AI-native).

## Digital Twin — What-if ⭐
- "Thêm 1 máy siêu âm → giảm chờ bao nhiêu?", "dời 20% lịch sáng sang chiều → tắc nghẽn giảm ra sao?".
- Biến câu hỏi đầu tư thành mô phỏng một chạm + khuyến nghị ngôn ngữ đời thường.
- Tinh thần Palantir: từ công cụ vận hành → công cụ ra quyết định chiến lược.

---

# Bảng ánh xạ Patient ⟷ Clinician (một sự thật, hai góc nhìn)

| Patient App thấy | ⟶ Clinician App tạo ra |
|---|---|
| M2 Intake định tuyến | M3 Intake Confirmation Queue |
| M2 Đặt lịch + gợi ý giờ | M2 Smart Scheduling Board + M10 Capacity brain |
| M3 Care Journey timeline | M6 Care Orchestration Console |
| M3 Journey Agent chat | M4 Chat-with-Worklist |
| M3 "Why am I waiting" | M6 Disruption + M1 Ops feed |
| M1 "AI đang làm gì cho bạn" | M6 Disruption Center + M7 Autonomy Console |
| M4 Kết quả + giải thích | M4 Source-of-Truth + M5 nhập kết quả |
| M5 Đơn thuốc + cảnh báo | M4 e-Prescribing |
| M6 Viện phí + BHYT | M11 Billing & Insurance |
| M7 Bring-someone realtime | (dùng chung dữ liệu trạng thái) |

---

# Bảng phân tầng ưu tiên (chốt scope)

| Module | Ưu tiên | Ghi chú |
|---|---|---|
| M1 Command Center + Role Home | **P0** | Bộ mặt vận hành |
| M2 Smart Scheduling Board | **P0** | Lõi |
| M3 Intake Confirmation Queue | **P0** | Guardrail người xác nhận |
| M4 Doctor Workspace (+ Source-of-Truth, e-Rx) | **P0** | Nguồn sự thật — bắt buộc |
| M5 Technician Workspace | **P0** | Nhập kết quả kích hoạt luồng |
| M6 Care Orchestration + Disruption | **P0** | Khoảnh khắc demo vàng |
| M7 Autonomy & Approval Console | **P0** | An toàn — giám khảo hỏi đầu tiên |
| M10 Capacity & Roster Brain | **P0** | Xương sống — không hào nhoáng nhưng bắt buộc |
| M8 EMR + Shift Handoff | P1 | Handoff là differentiator |
| M11 Billing & Insurance | P1 | Vẽ khung |
| M12 Analytics + Digital Twin | P1 | Chứng minh + chiến lược |
| M9 Inpatient | P2 | Nếu bật scope nội trú |

**Nguyên tắc cắt:** 8 module P0 là bộ khung tối thiểu để "golden path" chạy xuyên suốt. Làm sâu chúng; P1 vẽ khung để chứng minh HIS đầy đủ; P2 bỏ.

---

# Sáu AI Agents hiện diện trong Clinician App

| Agent | Xuất hiện ở |
|---|---|
| 🚪 Intake | M3 (đề xuất định tuyến để lễ tân duyệt) |
| 📋 Care Plan | M4 (chat-with-worklist), M6 (sinh task list) |
| 🗺️ Journey | M6 (theo dõi từng ca) |
| 📊 Forecast | M2 (gợi ý slot), M10 (capacity), M12 (dự báo) |
| ⚡ Disruption | M5 (nhận báo hỏng), M6 (re-plan), M7 (đưa lên duyệt) |
| 🧠 Coordinator | M1 (điều hành tổng), M7 (phân tầng tự chủ) |
| 🔄 Shift Handoff | M8 (bàn giao ca) — *agent mới riêng cho clinician* |

---

# Ghi chú quan trọng về an toàn (nói trước khi giám khảo hỏi)

1. **AI điều phối logistics, không quyết định lâm sàng.** Chẩn đoán & chỉ định là của bác sĩ (M4, có ký số). AI chỉ tối ưu *cách thực hiện*, không tối ưu *thực hiện cái gì*.
2. **Action space đóng:** AI chỉ hành động qua tools định nghĩa sẵn + constraint checker (code thường) chạy trước mọi action.
3. **Phân tầng tự chủ** (M7): ảnh hưởng nhỏ tự chạy, lớn cần người duyệt.
4. **Audit toàn bộ reasoning** (M7): mọi quyết định giải trình được.
5. **LLM suy luận, ML dự báo, không lẫn vai:** mọi con số (ETA, tải) đến từ Forecast tools, không phải LLM tự sinh → chặn ảo giác số.
