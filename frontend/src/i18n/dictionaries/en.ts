/**
 * English dictionary - the EN toggle target (FR-21).
 *
 * `satisfies Record<DictKey, string>` below fails to compile if this file's
 * key set drifts from the Vietnamese dictionary - keeping the two in sync
 * is enforced by the type checker, not by convention.
 */
import type { DictKey } from './vi';

const en = {
  'app.name': 'VAIC',
  'app.tagline': 'Your care journey, accompanied end to end',

  'nav.home': 'Home',
  'nav.book': 'Appointments',
  'nav.journey': 'Journey',
  'nav.records': 'Health records',
  'nav.more': 'More',
  'nav.assistant': 'Assistant',
  'nav.notifications': 'Notifications',

  'login.title': 'Log in',
  'login.subtitle': 'Pick a profile below to log in (demo mode)',
  'login.patientCodeLabel': 'Patient code',
  'login.passwordLabel': 'Password',
  'login.submit': 'Log in',
  'login.submitting': 'Logging in...',
  'login.demoAccountsLabel': 'Demo accounts',
  'login.errorInvalid': 'Invalid credentials. Check the patient code and password and try again.',
  'login.languageToggle': 'Language',

  'guard.redirecting': 'Redirecting to login...',

  'settings.title': 'Settings',
  'settings.language': 'Language',
  'settings.logout': 'Log out',
  'settings.notificationChannelLabel': 'Notification channel',
  'settings.channelInApp': 'In-app',
  'settings.channelSms': 'SMS (simulated)',
  'settings.savedConfirmation': 'Settings saved.',
  'settings.invalidChoice': 'Invalid choice rejected.',

  'ai.badge': 'AI-suggested',

  'state.loading': 'Loading...',
  'state.empty': 'Nothing here yet',
  'state.error': 'Something went wrong. Please try again.',
  'state.noPermission': 'You do not have permission to view this',

  'status.LOCKED': 'Awaiting payment',
  'status.PENDING': 'Pending',
  'status.IN_PROGRESS': 'In progress',
  'status.DONE': 'Done',
  'status.CANCELLED': 'Cancelled',
  'status.UNPAID': 'Unpaid',
  'status.PAID': 'Paid',
  'status.PROPOSED': 'Proposed',
  'status.BOOKED': 'Booked',
  'status.CHECKED_IN': 'Checked in',
  'status.IN_CONSULT': 'In consult',
  'status.NO_SHOW': 'No-show',
  'status.DRAFT': 'Draft',
  'status.ACTIVE': 'Active',
  'status.COMPLETED': 'Completed',

  'placeholder.buildLater': 'This screen will be built in a later batch',

  'patientCode.ariaLabel': 'Patient code for staff to scan',

  // --- /intake (SCR-01) ---
  'intake.greetingTitle': 'Hi, how can I help?',
  'intake.greetingPrompt': 'Describe your symptoms in a few short sentences.',
  'intake.notDiagnosisBanner': 'This is a routing suggestion, not a diagnosis.',
  'intake.inputLabel': 'Message input',
  'intake.inputPlaceholder': 'For example: I have had lower abdominal pain and a mild fever for 2 days...',
  'intake.send': 'Send',
  'intake.thinking': 'Thinking...',
  'intake.timeoutMessage': 'This is taking longer than usual.',
  'intake.retry': 'Retry',
  'intake.errorMessage': 'Something went wrong. Please retry or see staff at the front desk.',
  'intake.emergencyBanner':
    'What you described may be an emergency. Please contact medical staff now or call 115.',
  'intake.slotsHeading': 'Suggested time slots',
  'intake.bookButton': 'Book this slot',

  // --- /book ---
  'book.title': 'Book an appointment',
  'book.subtitle': 'Pick an available slot below.',
  'book.slotsHeading': 'Available slots',
  'book.capacityFull': 'This slot is full. Please pick another one.',
  'book.confirmButton': 'Confirm booking',
  'book.confirming': 'Confirming...',
  'book.successTitle': 'Appointment booked',
  'book.goToJourney': 'View my journey',
  'book.emptyMessage': 'No slots to show right now.',

  // --- /journey (SCR-02) ---
  'journey.title': 'Your journey',
  'journey.emptyMessage': 'No journey yet - please complete the diagnostic consult.',
  'journey.payReminderTitle': 'Please go pay',
  'journey.payReminderBody': 'This step needs payment at the counter to continue. The app does not process payment.',
  'journey.patientCodeLabel': 'Your patient code',
  'journey.patientCodeHint': 'Present this code for staff to scan when needed.',
  'journey.replanReasonLabel': 'Reason for the change',
  'journey.rescheduleButton': 'Reschedule',
  'journey.cancelButton': 'Cancel',
  'journey.cancelConfirm': 'Are you sure you want to cancel this appointment?',
  'journey.cancelConfirmYes': 'Confirm cancellation',
  'journey.cancelConfirmNo': 'No, keep it',
  'journey.rescheduled': 'Appointment rescheduled.',
  'journey.cancelled': 'Appointment cancelled.',
  'journey.askAssistant': 'Ask the assistant about your journey',
  'journey.ownerLabel': 'Owner',
  'journey.etaLabel': 'Estimated time',

  // --- /home (dual-mode) ---
  'home.modeToggleLabel': 'Home mode',
  'home.modeDashboard': 'Out of hospital',
  'home.modeLive': 'In hospital',
  'home.dashboardTitle': 'Home',
  'home.nextVisitLabel': 'Next appointment',
  'home.upcomingVisitsHeading': 'Upcoming visits',
  'home.prepRemindersHeading': 'Prep reminders',
  'home.newResultsHeading': 'New results',
  'home.shortcutsHeading': 'Shortcuts',
  'home.shortcutBook': 'Book an appointment',
  'home.shortcutIntake': 'Describe symptoms',
  'home.shortcutCheckin': 'Check in at the hospital',
  'home.noUpcomingVisits': 'You have no upcoming visits.',
  'home.liveTitle': 'Accompanying you now',
  'home.liveCurrentStep': 'Current step',
  'home.liveEta': 'Time remaining (estimated)',
  'home.liveWayfinding': 'Wayfinding',
  'home.liveAiDoing': 'What AI is doing for you',
  'home.liveAiDoingBody': 'AI is watching the queue and will notify you right away if your journey changes.',
  'home.liveWhyWaiting': 'Why you are waiting',
  'home.liveWhyWaitingBody': 'A few steps are still ahead of you; each step averages about 10-15 minutes.',
  'home.liveNoActiveStep': 'No step is currently in progress.',

  // --- /checkin ---
  'checkin.title': 'Hospital check-in',
  'checkin.instructions': 'Present this code for staff to scan when you arrive (no self check-in happens in the app).',
  'checkin.demoNote':
    'Demo mode: this only displays the code - no automatic check-in step runs inside the app.',

  // --- /assistant ---
  'assistant.title': 'AI assistant',
  'assistant.subtitle': 'Ask me about your care journey.',
  'assistant.inputLabel': 'Message input for the assistant',
  'assistant.inputPlaceholder': 'Type your question...',
  'assistant.send': 'Send',
  'assistant.thinking': 'Thinking...',
  'assistant.quickQuestionsHeading': 'Suggested questions',
  'assistant.greeting': 'Hi, I am the AI assistant accompanying your care journey. What would you like to ask?',

  // --- /notifications (SCR-09) ---
  'notifications.title': 'Notifications center',
  'notifications.filterLabel': 'Filter by type',
  'notifications.filterAll': 'All',
  'notifications.markRead': 'Mark as read',
  'notifications.readLabel': 'Read',
  'notifications.unreadLabel': 'Unread',
  'notifications.emptyMessage': 'No notifications yet',
  'notifications.prevPage': 'Previous page',
  'notifications.nextPage': 'Next page',
  'notifications.pageOf': 'Page',
  'notifType.APPOINTMENT': 'Appointment',
  'notifType.RESULT': 'Result',
  'notifType.BILLING': 'Billing',
  'notifType.JOURNEY': 'Journey',

  // --- /journey/step/:id ---
  'journeyStep.title': 'Step detail',
  'journeyStep.etaRangeLabel': 'Estimated time (range)',
  'journeyStep.whyThisOrderLabel': 'Why this order',
  'journeyStep.wayfindingLabel': 'Wayfinding',
  'journeyStep.queuePositionLabel': 'Queue position',
  'journeyStep.backToJourney': 'Back to journey',
  'journeyStep.notFound': 'Step not found.',

  // --- /results (PMA-M4) ---
  'results.title': 'Lab & imaging results',
  'results.emptyMessage': 'No results yet',
  'results.withinRange': 'Within reference range',
  'results.outsideRange': 'Outside reference range',
  'results.discussWithDoctor': 'Please discuss this with your doctor.',
  'results.referenceRangeLabel': 'Reference range',
  'results.recordedAtLabel': 'Recorded on',

  // --- /medications (PMA-M5) ---
  'medications.title': 'Medications & reminders',
  'medications.emptyMessage': 'No prescriptions yet',
  'medications.doseLabel': 'Dose',
  'medications.usageLabel': 'Usage',
  'medications.reminderLabel': 'Reminder times',
  'medications.interactionWarningLabel': 'Interaction / allergy warning',

  // --- /recovery (PMA-M5) ---
  'recovery.title': 'Recovery tracking',
  'recovery.emptyMessage': 'No recovery diary yet',
  'recovery.responseLabel': 'Your response',
  'recovery.warningBanner': 'Your symptoms need a doctor to review them soon.',
  'recovery.contactDoctor': 'Please contact your doctor.',

  // --- /billing (PMA-M6, display-only) ---
  'billing.title': 'Hospital fees & insurance',
  'billing.estimateHeading': 'Cost estimate',
  'billing.coverageLabel': 'Insurance coverage',
  'billing.coPayLabel': 'Co-pay',
  'billing.invoiceHeading': 'Invoices & history',
  'billing.emptyMessage': 'No invoices yet',
  'billing.displayOnlyNotice': 'Display only - please go pay at the counter.',

  // --- /family (PMA-M7) ---
  'family.title': 'Family care',
  'family.switcherLabel': 'Switch profile',
  'family.selfBadge': 'Current profile',
  'family.notImplementedNotice':
    'Viewing a family member\'s record is not implemented in this demo - this is a UI shell only.',
  'family.emptyMessage': 'No family profiles linked yet',

  // --- /prep/:id (PMA-M2) ---
  'prep.title': 'Pre-visit prep',
  'prep.emptyMessage': 'No reminders yet',
  'prep.notFound': 'No prep reminder found for this visit.',
} satisfies Record<DictKey, string>;

export default en;
