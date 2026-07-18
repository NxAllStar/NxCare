
Problem statement
Optimizing the care pathway & reducing wait times
Context: Hospital patients often bunch up at the same times while other slots sit empty, get sent to the wrong area and have to backtrack, and wait without knowing how long — because appointment, registration, clinic, lab, and imaging data aren't connected into a single coordinated view of how each department is operating. Requirements: Build a smart coordination system that links data from appointments, check-in, clinics, labs, imaging, and the real-time status of each hospital department, to support: appointment coordination (allocating patients across doctors, specialties, and time slots to avoid same-time crowding while other slots stay open); patient routing (using symptoms, priority level, patient category, and required services to direct patients to the right area from the start, avoiding repeated trips or wrong queues); wait-time estimation (analyzing the number of patients waiting, average consultation time, and clinic/equipment status to forecast when a patient will be served, shown via app, screen, or SMS); service-sequencing recommendations (auto-ordering tests, ultrasound, X-ray, CT, MRI, and other services based on wait times, fasting requirements, result-turnaround, and equipment status, so patients follow an efficient route with minimal waiting and backtracking); and real-time adjustment (re-coordinating when a clinic is overloaded, equipment fails, a doctor's schedule changes, or an emergency case arrives). For example, a patient needing a blood test, ultrasound, and X-ray before returning to the doctor would be sequenced automatically — draw blood first, take the X-ray while the blood test processes, then ultrasound, then return once all results are ready — instead of queuing at each area on their own. Judging criteria: The goal is to reduce average wait time, ease congestion across areas, raise clinic and equipment utilization, and let patients actively track their own care pathway.

## 1. AI-native nghĩa là gì trong bài toán này

Proposal trước theo mô hình truyền thống: **thuật toán tối ưu là lõi, LLM là lớp vỏ** (intake + explain). Hướng AI-native đảo ngược lại: **AI là bộ não vận hành hệ thống**, còn code truyền thống chỉ là tay chân (tools) và hàng rào an toàn (guardrails). Cụ thể, ba dịch chuyển:

|  | Truyền thống | AI-native |
| --- | --- | --- |
| Ra quyết định | Rule/heuristic cứng viết sẵn cho từng tình huống | Agent **suy luận** trên trạng thái hiện tại, gọi tools, tự quyết trong ranh giới cho phép |
| Xử lý tình huống mới | Sự cố nào chưa code thì bó tay | Agent generalize: "máy CT hỏng" và "bác sĩ về sớm" đều là *resource unavailable*, cùng một khung suy luận |
| Tiến hóa | Sửa code, deploy lại | Learning loop: dự báo sai → dữ liệu mới → model tự cải thiện; agent đọc lại quyết định cũ trong memory |

Với giám khảo, câu chốt định vị: *"Chúng tôi không xây phần mềm quản lý hàng đợi có gắn AI. Chúng tôi xây một đội ngũ điều phối viên AI làm việc 24/7, và phần mềm chỉ là công cụ của họ."*

## 2. Kiến trúc: Multi-Agent Orchestration

Thay vì một Orchestration Engine nguyên khối, hệ thống là **một tập agent chuyên trách** phối hợp qua shared state và message bus — mô phỏng đúng cách một bệnh viện thật vận hành (mỗi khu có điều phối viên riêng, có người điều hành tổng).

### Luồng chăm sóc end-to-end (đúng nghiệp vụ lâm sàng)

Điểm mấu chốt: **AI không tự chẩn đoán và không tự sinh danh sách dịch vụ từ triệu chứng.** Quyết định lâm sàng thuộc về bác sĩ; AI chỉ điều phối logistics *sau khi* bác sĩ đã chẩn đoán. Luồng chuẩn gồm ba pha:

1. **Tiếp nhận & định tuyến khám chẩn đoán.** Intake Agent hội thoại triệu chứng → định tuyến bệnh nhân đến **buổi khám chẩn đoán** đúng chuyên khoa, đúng khung giờ ít đông (Forecast Agent tra tải). Ở pha này AI chưa "biết bệnh" — nó chỉ đưa bệnh nhân đến đúng bác sĩ nhanh nhất.
2. **Bác sĩ khám và chẩn đoán.** Bác sĩ khám → đưa ra **danh sách bệnh/tình trạng** và **chỉ định dịch vụ** cần thực hiện (xét nghiệm máu, siêu âm, X-quang, CT, MRI...). Đây là đầu vào lâm sàng chính thức, có chữ ký bác sĩ, và là *nguồn sự thật* cho mọi bước sau.
3. **AI sinh danh sách task và điều phối.** Từ chỉ định của bác sĩ, **Care Plan Agent** chuyển thành một **danh sách task** — mỗi task là một bước dịch vụ, có:
   - **owner:** bác sĩ / kỹ thuật viên / phòng phụ trách bước đó;
   - **thời lượng dự kiến (duration):** lấy từ Forecast Agent theo owner × loại dịch vụ × khung giờ;
   - **ràng buộc & phụ thuộc:** nhịn ăn, thứ tự bắt buộc, thời gian trả kết quả (turnaround);
   - **trạng thái thanh toán:** `chưa thanh toán` / `đã thanh toán` — **cổng bắt buộc**: một task chỉ được đưa vào hàng đợi và bắt đầu khi đã thanh toán (buổi khám chẩn đoán ở pha 2 cũng vậy);
   - **trạng thái thực hiện:** chờ / đang làm / xong.

   Care Plan Agent sắp thứ tự tối ưu các task, gán slot cho từng owner, rồi bàn giao cho Journey Agent hộ tống. Task chưa thanh toán vẫn nằm trong plan nhưng bị **khóa** (không tính vào hàng đợi của owner, không được xếp slot thực) cho tới khi thanh toán xong — điều này giúp ETA và tải của các phòng phản ánh đúng lượng bệnh nhân *thực sự* sẽ được phục vụ. Về bản chất đây là một **project plan cá nhân hóa cho từng bệnh nhân**: task có người chịu trách nhiệm và thời lượng, y hệt một sprint — chỉ khác là được tái lập lịch động khi có sự cố.

**🧠 Coordinator Agent (điều hành tổng)** — LLM agent trung tâm, vòng lặp perceive → reason → act:

- *Perceive:* nhận event stream (check-in mới, phòng quá tải, máy hỏng, kết quả xét nghiệm xong) + đọc snapshot trạng thái toàn viện.
- *Reason:* quyết định việc gì cần làm, ủy quyền cho agent nào, hoặc tự xử lý.
- *Act:* gọi tools — `get_queue_state()`, `estimate_wait(room)`, `resequence_patient(id)`, `reassign_slot()`, `notify(patient, msg)`.

**🚪 Intake Agent** — hội thoại với bệnh nhân bằng ngôn ngữ tự nhiên (tiếng Việt): triệu chứng → structured output {chuyên khoa nghi ngờ, mức ưu tiên, ràng buộc (nhịn ăn? thai kỳ? di chuyển khó?)} để **định tuyến đến buổi khám chẩn đoán** đúng chỗ. Lưu ý: đây là *triage định tuyến*, không phải chẩn đoán — Intake Agent không kết luận bệnh và không sinh danh sách dịch vụ; việc đó chờ bác sĩ ở pha 2. Đây là cửa ngõ dữ liệu — thay form cứng bằng đối thoại.

**📋 Care Plan Agent** — kích hoạt *sau khi bác sĩ chẩn đoán*. Nhận danh sách bệnh/chỉ định dịch vụ từ bác sĩ → sinh **danh sách task** (mỗi task: owner là bác sĩ/KTV/phòng, duration dự kiến, ràng buộc & phụ thuộc, trạng thái) → sắp thứ tự tối ưu, gán slot cho từng owner qua tool `allocate_slot()`, rồi bàn giao plan cho Journey Agent. Nó không tự thêm/bớt dịch vụ ngoài chỉ định của bác sĩ — chỉ tối ưu *cách thực hiện*, không tối ưu *thực hiện cái gì*.

**🗺️ Journey Agent (mỗi bệnh nhân một instance)** — agent "hộ tống" cá nhân, thực thi **danh sách task** do Care Plan Agent bàn giao; giữ context riêng của bệnh nhân đó: task nào đã xong / đang làm / còn lại, vị trí hiện tại, đã chờ bao lâu, owner của task kế tiếp là ai. Nó chủ động: thấy phòng siêu âm ETA tăng vọt → tự hỏi Coordinator xin đổi thứ tự → thông báo cho bệnh nhân kèm lý do. Nếu task kế tiếp `chưa thanh toán`, Journey Agent nhắc bệnh nhân thanh toán (kèm link/hướng dẫn) và giữ task ở trạng thái khóa cho tới khi payment webhook xác nhận `đã thanh toán` mới đưa vào hàng đợi. Bệnh nhân có thể chat ngược lại ("tôi muốn ăn sáng trước được không?") → agent suy luận trên ràng buộc nhịn ăn và trả lời/điều chỉnh lộ trình.

**📊 Forecast Agent** — không phải LLM mà là **ML models được bọc thành tool**: dự báo ETA từng phòng (gradient boosting / regression trên queue length, giờ trong ngày, service time lịch sử), dự báo tải theo giờ (time-series), dự báo no-show. LLM agents *gọi* các model này thay vì tự đoán số — nguyên tắc quan trọng: **LLM suy luận, ML dự báo, không lẫn vai**.

**⚡ Disruption Agent** — chuyên xử lý sự cố. Nhận event bất thường → đánh giá blast radius (bao nhiêu bệnh nhân bị ảnh hưởng) → sinh phương án re-plan → những ca ảnh hưởng nhỏ thì tự thực thi, ca lớn (VD: hủy 30 lịch hẹn) thì đề xuất lên dashboard cho điều phối viên người duyệt một chạm. Đây chính là **human-in-the-loop có phân tầng theo mức độ rủi ro** — điểm cộng lớn về an toàn.

### Vì sao suy luận LLM thắng rule cứng ở đây

Ví dụ thật demo được: máy X-quang hỏng lúc 9h. Rule cứng chỉ biết "chuyển bệnh nhân sang máy 2". Coordinator Agent suy luận đa chiều: máy 2 hàng đợi đã dài → bệnh nhân A đằng nào cũng phải chờ kết quả máu 45' nữa → đẩy X-quang của A xuống sau, chèn siêu âm lên trước; bệnh nhân B ưu tiên cao → giữ nguyên máy 2; bệnh nhân C chỉ cần X-quang → nhắn SMS đề nghị đổi khung giờ chiều kèm ETA chính xác. Ba bệnh nhân, ba cách xử lý, không dòng if-else nào viết sẵn cho tình huống này.

## 3. Guardrails — phần bắt buộc phải nói trước khi giám khảo hỏi

AI-native trong y tế chỉ thuyết phục khi ranh giới rõ ràng:

1. **Agent điều phối logistics, không quyết định lâm sàng.** Chẩn đoán và chỉ định dịch vụ là của **bác sĩ ở buổi khám chẩn đoán** — AI chỉ sinh danh sách task *từ* chỉ định đó, không tự thêm/bớt/thay dịch vụ. Phân loại chuyên khoa của Intake Agent chỉ để định tuyến và luôn hiển thị cho nhân viên y tế xác nhận tại quầy.
2. **Action space đóng:** agent chỉ hành động qua bộ tools định nghĩa sẵn với validation cứng (không thể xếp bệnh nhân vào phòng đã đóng, không thể vi phạm ràng buộc nhịn ăn, **không thể bắt đầu task chưa thanh toán** — constraint checker là code thường, chạy trước mọi action).
3. **Phân tầng tự chủ:** ảnh hưởng ≤ N bệnh nhân → tự thực thi; lớn hơn → cần người duyệt.
4. **Audit log toàn bộ reasoning:** mỗi quyết định lưu kèm chain-of-thought → giải trình được ("vì sao tôi bị đổi lịch?").

## 4. Learning loop (chữ "native" nằm ở đây)

Hệ thống tự tốt lên theo dữ liệu vận hành, không cần sửa code:

- **Forecast models** retrain định kỳ trên (dự báo vs thực tế) — demo được bằng cách cho simulator chạy "1 tuần", chỉ số MAE của ETA giảm dần theo ngày.
- **Agent memory:** quyết định + kết quả được lưu (vector store); khi gặp tình huống tương tự, Coordinator retrieve các case cũ làm few-shot context — "lần trước máy CT hỏng giờ cao điểm, phương án chuyển tải sang buổi chiều cho kết quả tốt".
- **Service-time profile** theo bác sĩ × loại bệnh × khung giờ tự cập nhật EMA — đầu vào ngày càng chính xác cho Slot Allocation.

## 5. Ba features của team nằm ở đâu

- **Feat 1** (phòng busy → đi bước khác) → trở thành hành vi mặc định của **Journey Agent**: nó liên tục so ETA các task còn lại trong danh sách và tự đề xuất hoán đổi thứ tự (trong giới hạn phụ thuộc bác sĩ đã đặt), tổng quát hơn hẳn phiên bản 1-bước.
- **Feat 2** (recommend giờ khám, agent điều hướng) → chính là **Intake Agent + Forecast Agent**: đối thoại → phân loại → tra dự báo tải → đề xuất khung giờ ít đông nhất. Ý tưởng "agent tự check và tạo test version" của team khớp hoàn toàn với hướng agentic này.
- **Feat 3** (xếp slot theo capacity bác sĩ) → tool `allocate_slot()` mà Coordinator gọi, chạy trên capacity model của Forecast Agent; bác sĩ có thêm khả năng *chat với worklist của mình* ("dồn các ca tái khám lên buổi sáng giúp tôi") — một điểm demo AI-native rất bắt mắt.

## 6. Tech stack đề xuất

- **Agent framework:** LangGraph (phù hợp roadmap LLM Engineering bạn đang theo) — mỗi agent là một graph node, state chung là hospital snapshot; hoặc tự viết loop tool-use trên FastAPI nếu muốn gọn.
- **LLM:** API model mạnh cho Coordinator/Disruption (cần reasoning tốt), Qwen self-hosted cho Intake/Journey (nhiều instance, chi phí thấp, tiếng Việt ổn).
- **Forecast:** scikit-learn/LightGBM, bọc thành FastAPI tools.
- **State & events:** Redis + WebSocket; **Simulator:** SimPy làm "thế giới" cho agents sống trong đó — đây đồng thời là môi trường eval.
- **Frontend:** React — giao diện bệnh nhân giờ là **chat + timeline** (nói chuyện với Journey Agent của mình), dashboard admin có ô "approve/reject" đề xuất của Disruption Agent.

## 7. Demo script 5 phút

1. Bệnh nhân chat triệu chứng bằng tiếng Việt → Intake Agent định tuyến đến buổi khám chẩn đoán, đề xuất khung giờ ít đông (Feat 2) → bác sĩ chẩn đoán, chỉ định 3 dịch vụ → Care Plan Agent sinh **danh sách task** (mỗi task hiện rõ owner là bác sĩ nào + thời lượng dự kiến, đang ở trạng thái `chưa thanh toán` nên bị khóa) → bệnh nhân bấm thanh toán → task mở khóa, vào hàng đợi, lộ trình "chạy" trên timeline.
2. Simulator bơm 300 bệnh nhân dồn cục buổi sáng → dashboard heatmap đỏ rực → agents tự dàn tải, heatmap dịu dần.
3. **Khoảnh khắc vàng:** bấm nút "máy X-quang hỏng" → Disruption Agent hiện reasoning trực tiếp trên màn hình (streaming chain-of-thought) → ba bệnh nhân được xử lý ba cách khác nhau → bệnh nhân nhận thông báo kèm lời giải thích tự nhiên.
4. Bệnh nhân chat "tôi đói quá, ăn trước được không?" → Journey Agent từ chối khéo vì còn xét nghiệm máu, và chủ động đổi xét nghiệm máu lên bước đầu tiên để bệnh nhân được ăn sớm nhất.
5. Chốt bằng metrics A/B: baseline FIFO vs agent-orchestrated trên cùng 500 bệnh nhân mô phỏng — giảm % wait time, tăng % utilization, kèm biểu đồ MAE của ETA giảm theo ngày (learning loop).

## 8. Rủi ro riêng của hướng AI-native và cách phòng

- **Latency/chi phí LLM khi 300 bệnh nhân cùng lúc:** Journey Agent không chạy vòng lặp liên tục mà **event-driven** (chỉ wake khi có event liên quan); Coordinator xử lý theo batch. Nói rõ điều này khi pitch.
- **LLM ảo giác con số:** đã chặn bằng nguyên tắc "LLM không tự sinh số — mọi con số đến từ Forecast tools", và constraint checker chặn action sai.
- **Demo trục trặc do tính ngẫu nhiên của LLM:** chuẩn bị seed kịch bản + fallback recording; phần simulator và forecast chạy deterministic nên metrics luôn tái lập được.
- **Giám khảo bảo "over-engineering, dùng rule là đủ":** trả lời bằng chính demo bước 3 — tình huống tổ hợp (máy hỏng × ràng buộc nhịn ăn × mức ưu tiên khác nhau) bùng nổ tổ hợp, rule không phủ nổi; và bước 4 — tương tác ngôn ngữ tự nhiên hai chiều là thứ rule-based không làm được.

---