/**
 * Vietnamese dictionary - the DEFAULT locale (FR-21, NFR-USE-03).
 *
 * Display labels only. Codes and enum values (PENDING, LOCKED, UNPAID, ...)
 * are never translated and never come from this file - see
 * src/components/primitives/StatusChip.tsx and BR-31.
 */
const vi = {
  'app.name': 'VAIC',
  'app.tagline': 'Đồng hành cùng hành trình khám chữa bệnh của bạn',

  'nav.home': 'Trang chủ',
  'nav.book': 'Lịch khám',
  'nav.journey': 'Lộ trình',
  'nav.records': 'Hồ sơ sức khỏe',
  'nav.more': 'Thêm',
  'nav.assistant': 'Trợ lý',
  'nav.notifications': 'Thông báo',

  'login.title': 'Đăng nhập',
  'login.subtitle': 'Chọn hồ sơ bên dưới để đăng nhập (chế độ demo)',
  'login.patientCodeLabel': 'Mã bệnh nhân',
  'login.passwordLabel': 'Mật khẩu',
  'login.submit': 'Đăng nhập',
  'login.submitting': 'Đang đăng nhập...',
  'login.demoAccountsLabel': 'Tài khoản demo',
  'login.errorInvalid':
    'Sai thông tin đăng nhập. Vui lòng kiểm tra lại mã bệnh nhân và mật khẩu.',
  'login.languageToggle': 'Ngôn ngữ',

  'guard.redirecting': 'Đang chuyển về trang đăng nhập...',

  'settings.title': 'Cài đặt',
  'settings.language': 'Ngôn ngữ',
  'settings.logout': 'Đăng xuất',
  'settings.notificationChannelLabel': 'Kênh thông báo',
  'settings.channelInApp': 'Trong ứng dụng',
  'settings.channelSms': 'SMS (mô phỏng)',
  'settings.savedConfirmation': 'Đã lưu cài đặt.',
  'settings.invalidChoice': 'Lựa chọn không hợp lệ bị từ chối.',

  'ai.badge': 'Đề xuất bởi AI',

  'streamingText.label': 'Suy luận AI',
  'streamingText.thinking': 'Đang suy luận...',

  'state.loading': 'Đang tải...',
  'state.empty': 'Chưa có dữ liệu',
  'state.error': 'Đã xảy ra lỗi. Vui lòng thử lại.',
  'state.noPermission': 'Bạn không có quyền xem nội dung này',

  'status.LOCKED': 'Chờ thanh toán',
  'status.PENDING': 'Đang chờ',
  'status.IN_PROGRESS': 'Đang thực hiện',
  'status.DONE': 'Hoàn tất',
  'status.CANCELLED': 'Đã hủy',
  'status.UNPAID': 'Chưa thanh toán',
  'status.PAID': 'Đã thanh toán',
  'status.PROPOSED': 'Đề xuất',
  'status.BOOKED': 'Đã đặt lịch',
  'status.CHECKED_IN': 'Đã check-in',
  'status.IN_CONSULT': 'Đang khám',
  'status.NO_SHOW': 'Không đến',
  'status.DRAFT': 'Nháp',
  'status.ACTIVE': 'Đang thực hiện',
  'status.COMPLETED': 'Đã hoàn tất',

  'placeholder.buildLater': 'Màn hình này sẽ được xây dựng ở bước sau',

  'patientCode.ariaLabel': 'Mã bệnh nhân để nhân viên quét',

  // --- /intake (SCR-01) ---
  'intake.greetingTitle': 'Chào bạn, mình có thể giúp gì?',
  'intake.greetingPrompt': 'Mô tả triệu chứng của bạn bằng vài câu ngắn.',
  'intake.notDiagnosisBanner': 'Đây là gợi ý định tuyến, không phải chẩn đoán.',
  'intake.inputLabel': 'Ô nhập tin nhắn',
  'intake.inputPlaceholder': 'Ví dụ: tôi bị đau bụng dưới và sốt nhẹ 2 hôm nay...',
  'intake.send': 'Gửi',
  'intake.thinking': 'Đang xử lý...',
  'intake.timeoutMessage': 'Xử lý hơi lâu hơn bình thường.',
  'intake.retry': 'Thử lại',
  'intake.errorMessage': 'Đã có lỗi khi xử lý. Vui lòng thử lại hoặc gặp nhân viên tại quầy.',
  'intake.emergencyBanner':
    'Triệu chứng bạn mô tả có thể là tình huống khẩn cấp. Vui lòng liên hệ nhân viên y tế ngay hoặc gọi 115.',
  'intake.slotsHeading': 'Khung giờ đề xuất',
  'intake.bookButton': 'Đặt lịch với khung giờ này',

  // --- /book ---
  'book.title': 'Đặt lịch khám',
  'book.subtitle': 'Chọn một khung giờ còn chỗ bên dưới.',
  'book.slotsHeading': 'Khung giờ trống',
  'book.capacityFull': 'Khung giờ này đã đầy. Vui lòng chọn khung khác.',
  'book.confirmButton': 'Xác nhận đặt lịch',
  'book.confirming': 'Đang xác nhận...',
  'book.successTitle': 'Đã đặt lịch khám thành công',
  'book.goToJourney': 'Xem lộ trình của tôi',
  'book.emptyMessage': 'Hiện chưa có khung giờ nào để hiển thị.',

  // --- /journey (SCR-02) ---
  'journey.title': 'Lộ trình của bạn',
  'journey.emptyMessage': 'Chưa có lộ trình - vui lòng hoàn tất khám chẩn đoán.',
  'journey.payReminderTitle': 'Vui lòng đi thanh toán',
  'journey.payReminderBody': 'Bước này cần thanh toán tại quầy để tiếp tục. Ứng dụng không xử lý thanh toán.',
  'journey.patientCodeLabel': 'Mã bệnh nhân của bạn',
  'journey.patientCodeHint': 'Xuất trình mã này để nhân viên quét khi cần.',
  'journey.replanReasonLabel': 'Lý do thay đổi lộ trình',
  'journey.rescheduleButton': 'Đổi lịch',
  'journey.cancelButton': 'Hủy lịch',
  'journey.cancelConfirm': 'Bạn có chắc muốn hủy buổi khám này?',
  'journey.cancelConfirmYes': 'Xác nhận hủy',
  'journey.cancelConfirmNo': 'Không, giữ lịch',
  'journey.rescheduled': 'Đã đổi lịch khám.',
  'journey.cancelled': 'Đã hủy buổi khám.',
  'journey.askAssistant': 'Hỏi trợ lý về lộ trình',
  'journey.ownerLabel': 'Phụ trách',
  'journey.etaLabel': 'Thời gian dự kiến',

  // --- /home (dual-mode) ---
  'home.modeToggleLabel': 'Chế độ Trang chủ',
  'home.modeDashboard': 'Ngoài viện',
  'home.modeLive': 'Trong viện',
  'home.dashboardTitle': 'Trang chủ',
  'home.nextVisitLabel': 'Lịch khám sắp tới',
  'home.upcomingVisitsHeading': 'Lịch sắp tới',
  'home.prepRemindersHeading': 'Nhắc chuẩn bị',
  'home.newResultsHeading': 'Kết quả mới',
  'home.shortcutsHeading': 'Lối tắt',
  'home.shortcutBook': 'Đặt lịch khám',
  'home.shortcutIntake': 'Mô tả triệu chứng',
  'home.shortcutCheckin': 'Check-in tại viện',
  'home.noUpcomingVisits': 'Bạn chưa có lịch khám sắp tới.',
  'home.liveTitle': 'Đang đồng hành cùng bạn',
  'home.liveCurrentStep': 'Bước hiện tại',
  'home.liveEta': 'Thời gian còn lại (ước tính)',
  'home.liveWayfinding': 'Chỉ đường',
  'home.liveAiDoing': 'AI đang làm gì cho bạn',
  'home.liveAiDoingBody': 'AI đang theo dõi hàng đợi và sẽ báo ngay nếu lộ trình của bạn thay đổi.',
  'home.liveWhyWaiting': 'Vì sao bạn đang chờ',
  'home.liveWhyWaitingBody': 'Hiện có vài bước phía trước, thời gian chờ trung bình mỗi bước khoảng 10-15 phút.',
  'home.liveNoActiveStep': 'Hiện chưa có bước nào đang thực hiện.',

  // --- /checkin ---
  'checkin.title': 'Check-in tại viện',
  'checkin.instructions': 'Xuất trình mã này để nhân viên quét khi bạn đến nơi (không tự thao tác check-in trong ứng dụng).',
  'checkin.demoNote':
    'Chế độ demo: đây chỉ là hiển thị mã, không có bước check-in tự động nào được thực hiện trong ứng dụng.',

  // --- /assistant ---
  'assistant.title': 'Trợ lý AI',
  'assistant.subtitle': 'Hỏi mình về lộ trình khám của bạn.',
  'assistant.inputLabel': 'Ô nhập tin nhắn cho trợ lý',
  'assistant.inputPlaceholder': 'Nhập câu hỏi của bạn...',
  'assistant.send': 'Gửi',
  'assistant.thinking': 'Đang xử lý...',
  'assistant.quickQuestionsHeading': 'Câu hỏi gợi ý',
  'assistant.greeting': 'Chào bạn, mình là trợ lý AI đồng hành cùng lộ trình khám của bạn. Bạn muốn hỏi gì?',

  // --- /notifications (SCR-09) ---
  'notifications.title': 'Trung tâm thông báo',
  'notifications.filterLabel': 'Lọc theo loại',
  'notifications.filterAll': 'Tất cả',
  'notifications.markRead': 'Đánh dấu đã đọc',
  'notifications.readLabel': 'Đã đọc',
  'notifications.unreadLabel': 'Chưa đọc',
  'notifications.emptyMessage': 'Chưa có thông báo',
  'notifications.prevPage': 'Trang trước',
  'notifications.nextPage': 'Trang sau',
  'notifications.pageOf': 'Trang',
  'notifType.APPOINTMENT': 'Lịch khám',
  'notifType.RESULT': 'Kết quả',
  'notifType.BILLING': 'Viện phí',
  'notifType.JOURNEY': 'Lộ trình',

  // --- /journey/step/:id ---
  'journeyStep.title': 'Chi tiết bước',
  'journeyStep.etaRangeLabel': 'Thời gian dự kiến (khoảng)',
  'journeyStep.whyThisOrderLabel': 'Vì sao thứ tự này',
  'journeyStep.wayfindingLabel': 'Chỉ đường',
  'journeyStep.queuePositionLabel': 'Vị trí trong hàng đợi',
  'journeyStep.backToJourney': 'Quay lại lộ trình',
  'journeyStep.notFound': 'Không tìm thấy bước này.',

  // --- /results (PMA-M4) ---
  'results.title': 'Kết quả xét nghiệm / CĐHA',
  'results.emptyMessage': 'Chưa có kết quả nào',
  'results.withinRange': 'Trong ngưỡng tham chiếu',
  'results.outsideRange': 'Ngoài ngưỡng tham chiếu',
  'results.discussWithDoctor': 'Hãy trao đổi với bác sĩ của bạn.',
  'results.referenceRangeLabel': 'Ngưỡng tham chiếu',
  'results.recordedAtLabel': 'Ngày ghi nhận',

  // --- /medications (PMA-M5) ---
  'medications.title': 'Đơn thuốc & nhắc uống',
  'medications.emptyMessage': 'Chưa có đơn thuốc nào',
  'medications.doseLabel': 'Liều dùng',
  'medications.usageLabel': 'Cách dùng',
  'medications.reminderLabel': 'Giờ nhắc uống',
  'medications.interactionWarningLabel': 'Cảnh báo tương tác / dị ứng',

  // --- /recovery (PMA-M5) ---
  'recovery.title': 'Theo dõi hồi phục',
  'recovery.emptyMessage': 'Chưa có nhật ký hồi phục',
  'recovery.responseLabel': 'Phản hồi của bạn',
  'recovery.warningBanner': 'Triệu chứng của bạn cần được bác sĩ xem xét sớm.',
  'recovery.contactDoctor': 'Vui lòng liên hệ bác sĩ.',

  // --- /billing (PMA-M6, display-only) ---
  'billing.title': 'Viện phí & BHYT',
  'billing.estimateHeading': 'Ước tính chi phí',
  'billing.coverageLabel': 'BHYT chi trả',
  'billing.coPayLabel': 'Đồng chi trả',
  'billing.invoiceHeading': 'Hóa đơn & lịch sử',
  'billing.emptyMessage': 'Chưa có hóa đơn nào',
  'billing.displayOnlyNotice': 'Chỉ hiển thị thông tin - vui lòng đi thanh toán tại quầy.',

  // --- /family (PMA-M7) ---
  'family.title': 'Gia đình (Family care)',
  'family.switcherLabel': 'Chuyển đổi hồ sơ',
  'family.selfBadge': 'Hồ sơ hiện tại',
  'family.notImplementedNotice':
    'Xem hồ sơ của người thân chưa được triển khai trong bản demo này - đây chỉ là giao diện mẫu.',
  'family.emptyMessage': 'Chưa có hồ sơ gia đình nào được liên kết',

  // --- /prep/:id (PMA-M2) ---
  'prep.title': 'Chuẩn bị trước buổi khám',
  'prep.emptyMessage': 'Chưa có nhắc nhở nào',
  'prep.notFound': 'Không tìm thấy nhắc nhở cho buổi khám này.',

  // --- Hospital console (TASK-026, staff/coordinator screens) ---
  'console.appName': 'NxCare - Console bệnh viện',
  'console.sidebar.navLabel': 'Điều hướng chính',
  'console.login.title': 'Đăng nhập nhân viên',
  'console.login.subtitle': 'Chọn vai trò bên dưới để đăng nhập',
  'console.role.doctor': 'Bác sĩ',
  'console.role.technician': 'Kỹ thuật viên',
  'console.role.coordinator': 'Điều phối viên',
  'console.role.admin': 'Quản trị viên',
  'console.nav.consult': 'Khám và chỉ định',
  'console.nav.worklist': 'Lịch khám bác sĩ',
  'console.nav.tasks': 'Nhiệm vụ kỹ thuật viên',
  'console.nav.dashboard': 'Dashboard điều phối',
  'console.nav.audit': 'Quản trị và kiểm toán',
  'console.screen.consult.title': 'Màn khám và chỉ định',
  'console.screen.worklist.title': 'Lịch khám bác sĩ',
  'console.screen.tasks.title': 'Màn nhiệm vụ kỹ thuật viên',
  'console.screen.dashboard.title': 'Dashboard điều phối',
  'console.screen.audit.title': 'Trang quản trị và kiểm toán',

  // --- /dashboard (SCR-06, TASK-027) ---
  'console.dashboard.loadingLabel': 'Đang tải dashboard điều phối...',
  'console.dashboard.error.title': 'Điều phối tự động tạm dừng',
  'console.dashboard.error.body':
    'Lộ trình hiện tại được giữ nguyên. Không có gì được tự động áp dụng - vui lòng xem xét thủ công hoặc thử lại.',
  'console.dashboard.heatmap.title': 'Bản đồ tải',
  'console.dashboard.heatmap.caption': 'Tải theo khu vực và khung giờ',
  'console.dashboard.heatmap.level.1': 'Thấp',
  'console.dashboard.heatmap.level.2': 'Thấp',
  'console.dashboard.heatmap.level.3': 'Trung bình',
  'console.dashboard.heatmap.level.4': 'Trung bình',
  'console.dashboard.heatmap.level.5': 'Cao',
  'console.dashboard.heatmap.level.6': 'Cao',
  'console.dashboard.approvalQueue.title': 'Hàng chờ duyệt',
  'console.dashboard.approvalQueue.emptyMessage': 'Hiện không có đề xuất lập lại kế hoạch nào chờ duyệt.',
  'console.dashboard.approvalQueue.aiProposalChip': 'Đề xuất lập lại kế hoạch (AI)',
  'console.dashboard.approvalQueue.blastRadiusLabel': 'Phạm vi ảnh hưởng (số bệnh nhân)',
  'console.dashboard.approvalQueue.optionsLabel': 'Phương án',
  'console.dashboard.approvalQueue.approve': 'Duyệt',
  'console.dashboard.approvalQueue.reject': 'Từ chối',
  'console.dashboard.approvalQueue.confirmRejectPrompt': 'Từ chối đề xuất ảnh hưởng lớn này?',
  'console.dashboard.approvalQueue.confirmRejectYes': 'Xác nhận từ chối',
  'console.dashboard.approvalQueue.confirmRejectNo': 'Hủy',
  'console.dashboard.approvalQueue.actionError': 'Không ghi được quyết định. Vui lòng thử lại.',
  'console.dashboard.reasoning.title': 'Suy luận của trợ lý sự cố',
  
  // --- Clinical Console Screens ---
  'console.consult.queue': 'Hàng đợi chờ khám',
  'console.consult.emptyQueue': 'Không có bệnh nhân chờ khám',
  'console.consult.patientDetails': 'Chi tiết bệnh nhân',
  'console.consult.triageRef': 'Phân loại tham khảo',
  'console.consult.aiRefNotice': 'AI tham khảo - không phải chẩn đoán chính thức',
  'console.consult.enterDiagnosis': 'Nhập chẩn đoán lâm sàng',
  'console.consult.diagnosisPlaceholder': 'Ví dụ: Viêm ruột thừa cấp, Sỏi túi mật...',
  'console.consult.orderServices': 'Chỉ định dịch vụ',
  'console.consult.selectService': 'Chọn dịch vụ...',
  'console.consult.noServicesSelected': 'Chưa chọn chỉ định nào.',
  'console.consult.signAndFinalise': 'Ký và chốt chỉ định',
  'console.consult.scanPrompt': 'Quét mã tiếp nhận bệnh nhân',
  'console.consult.diagnosesRequired': 'Vui lòng nhập chẩn đoán trước khi ký.',
  
  'console.worklist.todaySchedule': 'Lịch khám của tôi hôm nay',
  'console.worklist.empty': 'Không có ca khám nào hôm nay',
  'console.worklist.rearrangeTitle': 'Trợ lý sắp xếp lịch',
  'console.worklist.rearrangePrompt': 'Yêu cầu sắp xếp lại lịch',
  'console.worklist.rearrangePlaceholder': 'Nhập yêu cầu (ví dụ: dồn lịch sáng chiều nghỉ)...',
  'console.worklist.rearrangeConfirm': 'AI đã sắp xếp lại lịch - Bạn có muốn áp dụng?',
  'console.worklist.confirm': 'Xác nhận',
  'console.worklist.cancel': 'Hủy bỏ',
  
  'console.tasks.title': 'Hàng đợi nhiệm vụ kỹ thuật',
  'console.tasks.empty': 'Không có nhiệm vụ nào đang chờ thực hiện',
  'console.tasks.complete': 'Hoàn thành',
  'console.tasks.scanToStart': 'Quét mã bắt đầu',
  'console.tasks.lockedText': 'Chờ thanh toán',
  
  'console.audit.searchPlaceholder': 'Lọc kiểm toán theo bệnh nhân, người thực hiện hoặc hành động...',
  'console.audit.empty': 'Không tìm thấy bản ghi kiểm toán nào',
  'console.admin.simulatorTitle': 'Cấu hình và khởi tạo bộ mô phỏng',
  'console.admin.seedButton': 'Khởi tạo lại bộ mô phỏng',
  'console.admin.seedConfirm': 'Xác nhận khởi tạo lại bộ mô phỏng? Thao tác này sẽ đặt lại toàn bộ bệnh nhân và nhiệm vụ về trạng thái ban đầu.',
} as const;

export default vi;
export type DictKey = keyof typeof vi;
