/**
 * Synthetic, in-memory fixtures for the patient mock-data layer (TASK-021).
 *
 * SYNTHETIC DATA ONLY - no real names, phone numbers, or identifiers
 * (agent-guardrails.md "Personal and sensitive data"). Names below are
 * generic Vietnamese placeholder names of the kind used on official forms
 * ("Nguyen Van A" / "Tran Thi B"), not references to real people.
 *
 * There is no backend yet. This module is the single place that seeds the
 * mock data the stub API functions in this directory read from.
 */

import {
  AppointmentStatus,
  CarePlanStatus,
  ExecutionStatus,
  NotificationChannel,
  NotificationType,
  PaymentStatus,
  PaymentSubjectType,
  PriorityLevel,
  ReferenceRangeStatus,
  RecoverySeverity,
  type Appointment,
  type BillingEstimate,
  type CarePlan,
  type FamilyProfile,
  type IntakeSession,
  type Invoice,
  type LabResult,
  type Medication,
  type Notification,
  type Patient,
  type Payment,
  type PrepReminder,
  type RecoveryCheckIn,
  type ScanEvent,
  type Slot,
  type StepDetail,
  type Task,
} from './types';

export const DEMO_PATIENTS: Patient[] = [
  {
    id: 'patient-0001',
    fullName: 'Nguyen Van A',
    phone: '0900000001',
    patientCode: 'BN-000123',
    priorityLevel: PriorityLevel.ROUTINE,
    createdAt: '2026-01-05T02:00:00.000Z',
  },
  {
    id: 'patient-0002',
    fullName: 'Tran Thi B',
    phone: '0900000002',
    patientCode: 'BN-000456',
    priorityLevel: PriorityLevel.ROUTINE,
    createdAt: '2026-02-10T02:00:00.000Z',
  },
];

export const DEMO_INTAKE_SESSIONS: IntakeSession[] = [
  {
    id: 'intake-0001',
    patientId: 'patient-0001',
    transcript: 'Toi bi dau bung tu hom qua, hoi buon non.',
    structuredTriage: { specialty: 'Noi tong quat', priorityLevel: PriorityLevel.ROUTINE, constraints: [] },
    emergencySuspected: false,
    createdAt: '2026-07-17T23:00:00.000Z',
  },
];

export const DEMO_APPOINTMENTS: Appointment[] = [
  {
    id: 'appt-0001',
    patientId: 'patient-0001',
    specialty: 'Noi tong quat',
    status: AppointmentStatus.BOOKED,
    paymentStatus: PaymentStatus.UNPAID,
    slotStart: '2026-07-19T01:30:00.000Z',
    createdAt: '2026-07-17T23:05:00.000Z',
  },
];

export const DEMO_CARE_PLANS: CarePlan[] = [
  {
    id: 'care-plan-0001',
    patientId: 'patient-0001',
    diagnosisId: 'diagnosis-0001',
    status: CarePlanStatus.ACTIVE,
    assignedStaff: ['staff-0009'],
    createdAt: '2026-07-18T01:00:00.000Z',
  },
];

export const DEMO_TASKS: Task[] = [
  {
    id: 'task-0001',
    carePlanId: 'care-plan-0001',
    serviceOrderId: 'order-0001',
    ownerId: 'staff-0009',
    executionStatus: ExecutionStatus.DONE,
    paymentStatus: PaymentStatus.PAID,
    estimatedDurationMin: 15,
    sequenceIndex: 0,
    dependsOn: [],
    createdAt: '2026-07-18T01:05:00.000Z',
    label: 'Kham lam sang / Clinical consult',
  },
  {
    id: 'task-0002',
    carePlanId: 'care-plan-0001',
    serviceOrderId: 'order-0002',
    ownerId: 'staff-0012',
    executionStatus: ExecutionStatus.IN_PROGRESS,
    paymentStatus: PaymentStatus.PAID,
    estimatedDurationMin: 20,
    sequenceIndex: 1,
    dependsOn: ['task-0001'],
    createdAt: '2026-07-18T01:10:00.000Z',
    label: 'Xet nghiem mau / Blood test',
  },
  {
    id: 'task-0003',
    carePlanId: 'care-plan-0001',
    serviceOrderId: 'order-0003',
    ownerId: 'staff-0015',
    executionStatus: ExecutionStatus.LOCKED,
    paymentStatus: PaymentStatus.UNPAID,
    estimatedDurationMin: 30,
    sequenceIndex: 2,
    dependsOn: ['task-0002'],
    createdAt: '2026-07-18T01:12:00.000Z',
    label: 'Chup X-quang / X-ray imaging',
  },
];

export const DEMO_SLOTS: Slot[] = [
  { id: 'slot-0001', taskId: 'task-0002', ownerId: 'staff-0012', start: '2026-07-18T01:15:00.000Z', end: '2026-07-18T01:35:00.000Z' },
];

export const DEMO_PAYMENTS: Payment[] = [
  {
    id: 'payment-0001',
    subjectType: PaymentSubjectType.TASK,
    subjectId: 'task-0003',
    amount: '350000',
    status: PaymentStatus.UNPAID,
    confirmedBy: null,
    confirmedAt: null,
  },
];

// 7 entries for patient-0001 (deliberately > one page, see notifications.ts
// PAGE_SIZE) spanning every NotificationType, mixed read/unread, so SCR-09's
// pagination and type filter both have real data to exercise. patient-0002
// gets one entry, kept separate to prove own-scope filtering.
export const DEMO_NOTIFICATIONS: Notification[] = [
  {
    id: 'notif-0001',
    patientId: 'patient-0001',
    channel: NotificationChannel.IN_APP,
    body: 'Buoi kham cua ban da duoc xac nhan luc 08:30 ngay mai.',
    reason: null,
    createdAt: '2026-07-17T23:06:00.000Z',
    read: true,
    aiGenerated: false,
    notificationType: NotificationType.APPOINTMENT,
  },
  {
    id: 'notif-0002',
    patientId: 'patient-0001',
    channel: NotificationChannel.IN_APP,
    body: 'Lo trinh cua ban vua duoc sap xep lai do co ca cap cuu uu tien truoc.',
    reason: 'Emergency pre-emption tai phong xet nghiem (+8 phut)',
    createdAt: '2026-07-18T01:11:00.000Z',
    read: false,
    aiGenerated: true,
    notificationType: NotificationType.JOURNEY,
  },
  {
    id: 'notif-0003',
    patientId: 'patient-0001',
    channel: NotificationChannel.IN_APP,
    body: 'Ket qua xet nghiem mau cua ban da co.',
    reason: null,
    createdAt: '2026-07-18T02:00:00.000Z',
    read: false,
    aiGenerated: false,
    notificationType: NotificationType.RESULT,
  },
  {
    id: 'notif-0004',
    patientId: 'patient-0001',
    channel: NotificationChannel.SMS,
    body: 'Hoa don cua ban da san sang, vui long xem trong muc Vien phi.',
    reason: null,
    createdAt: '2026-07-18T03:00:00.000Z',
    read: false,
    aiGenerated: false,
    notificationType: NotificationType.BILLING,
  },
  {
    id: 'notif-0005',
    patientId: 'patient-0001',
    channel: NotificationChannel.IN_APP,
    body: 'Nho nhin an tu 22h hom nay truoc buoi sieu am ngay mai.',
    reason: null,
    createdAt: '2026-07-17T13:00:00.000Z',
    read: true,
    aiGenerated: false,
    notificationType: NotificationType.APPOINTMENT,
  },
  {
    id: 'notif-0006',
    patientId: 'patient-0001',
    channel: NotificationChannel.IN_APP,
    body: 'Buoi chup X-quang can thanh toan truoc khi tiep tuc.',
    reason: null,
    createdAt: '2026-07-18T01:13:00.000Z',
    read: false,
    aiGenerated: false,
    notificationType: NotificationType.BILLING,
  },
  {
    id: 'notif-0007',
    patientId: 'patient-0001',
    channel: NotificationChannel.IN_APP,
    body: 'Buoc sieu am tiep theo da san sang cho ban.',
    reason: null,
    createdAt: '2026-07-18T01:20:00.000Z',
    read: false,
    aiGenerated: false,
    notificationType: NotificationType.JOURNEY,
  },
  {
    id: 'notif-1001',
    patientId: 'patient-0002',
    channel: NotificationChannel.IN_APP,
    body: 'Lich kham cua ban da duoc ghi nhan.',
    reason: null,
    createdAt: '2026-07-10T01:00:00.000Z',
    read: false,
    aiGenerated: false,
    notificationType: NotificationType.APPOINTMENT,
  },
];

export const DEMO_STEP_DETAILS: StepDetail[] = [
  {
    taskId: 'task-0002',
    etaRangeLabel: '~10-15 phut',
    whyThisOrder: 'Xet nghiem mau duoc uu tien truoc vi ket qua can co truoc khi bac si doc lai.',
    wayfindingInstructions: 'Di thang hanh lang chinh, phong lay mau o tang 1, canh quay so 3.',
    queuePositionLabel: '2 nguoi phia truoc ban',
  },
  {
    taskId: 'task-0003',
    etaRangeLabel: '~20-30 phut',
    whyThisOrder: 'Chup X-quang duoc xep sau xet nghiem mau de ket qua mau ho tro doc phim chinh xac hon.',
    wayfindingInstructions: 'Len thang may tang 2, phong X-quang X1 ben trai thang may.',
    queuePositionLabel: '3 nguoi phia truoc, 1 ca cap cuu vua duoc uu tien',
  },
];

export const DEMO_LAB_RESULTS: LabResult[] = [
  {
    id: 'result-0001',
    patientId: 'patient-0001',
    label: 'Duong huyet luc doi (Glucose)',
    value: '92',
    unit: 'mg/dL',
    referenceRangeLabel: '70-100 mg/dL',
    status: ReferenceRangeStatus.WITHIN_RANGE,
    recordedAt: '2026-07-18T01:20:00.000Z',
  },
  {
    id: 'result-0002',
    patientId: 'patient-0001',
    label: 'Bach cau (WBC)',
    value: '13.2',
    unit: 'x10^9/L',
    referenceRangeLabel: '4.0-11.0 x10^9/L',
    status: ReferenceRangeStatus.OUTSIDE_RANGE,
    recordedAt: '2026-07-18T01:20:00.000Z',
  },
];

export const DEMO_MEDICATIONS: Medication[] = [
  {
    id: 'med-0001',
    patientId: 'patient-0001',
    drugName: 'Paracetamol 500mg',
    dose: '1 vien / lan',
    usageInstructions: 'Uong sau an, cach nhau it nhat 6 gio',
    reminderTimes: ['08:00', '14:00', '20:00'],
    interactionWarning: null,
  },
  {
    id: 'med-0002',
    patientId: 'patient-0001',
    drugName: 'Amoxicillin 500mg',
    dose: '1 vien / lan',
    usageInstructions: 'Uong sau an, du 5 ngay',
    reminderTimes: ['08:00', '20:00'],
    interactionWarning: 'Co the tuong tac voi thuoc di ung penicillin ban da khai bao truoc do - hay bao bac si neu co bieu hien la.',
  },
];

export const DEMO_RECOVERY_CHECKINS: RecoveryCheckIn[] = [
  {
    id: 'recovery-0001',
    patientId: 'patient-0001',
    question: 'Hom nay ban co con dau bung khong?',
    patientResponse: 'Do nhieu roi, chi con hoi tuc.',
    severity: RecoverySeverity.NORMAL,
    createdAt: '2026-07-18T09:00:00.000Z',
  },
  {
    id: 'recovery-0002',
    patientId: 'patient-0001',
    question: 'Ban co bi sot lai hay vet mo hong khong?',
    patientResponse: 'Co, toi bi sot 38.5 do tu toi qua.',
    severity: RecoverySeverity.WARNING,
    createdAt: '2026-07-19T08:00:00.000Z',
  },
];

export const DEMO_BILLING_ESTIMATES: BillingEstimate[] = [
  {
    id: 'estimate-0001',
    patientId: 'patient-0001',
    serviceLabel: 'Chup X-quang nguc',
    estimatedAmount: '350000',
    insuranceCoverageLabel: 'BHYT chi tra 80%',
    coPayAmount: '70000',
  },
];

export const DEMO_INVOICES: Invoice[] = [
  {
    id: 'invoice-0001',
    patientId: 'patient-0001',
    issuedAt: '2026-07-10T02:00:00.000Z',
    totalAmount: '450000',
    status: PaymentStatus.PAID,
    lineItemsLabel: 'Kham lam sang + xet nghiem mau',
  },
  {
    id: 'invoice-0002',
    patientId: 'patient-0001',
    issuedAt: '2026-07-18T01:12:00.000Z',
    totalAmount: '350000',
    status: PaymentStatus.UNPAID,
    lineItemsLabel: 'Chup X-quang',
  },
];

export const DEMO_FAMILY_PROFILES: FamilyProfile[] = [
  {
    id: 'family-profile-0001',
    ownerAccountId: 'patient-0001',
    displayName: 'Ban than',
    relationshipLabel: 'Ban than / Self',
    isSelf: true,
  },
  {
    id: 'family-profile-0002',
    ownerAccountId: 'patient-0001',
    displayName: 'Me (BN Nguyen Thi L.)',
    relationshipLabel: 'Me / Mother',
    isSelf: false,
  },
];

export const DEMO_PREP_REMINDERS: PrepReminder[] = [
  {
    id: 'prep-0001',
    appointmentId: 'appt-0001',
    instructions: [
      'Nhin an tu 22h hom truoc buoi kham.',
      'Mang theo don thuoc cu va ket qua xet nghiem gan nhat (neu co).',
      'Mang theo the BHYT va giay to tuy than.',
    ],
  },
];

export const DEMO_SCAN_EVENTS: ScanEvent[] = [
  {
    id: 'scan-0001',
    patientId: 'patient-0001',
    taskId: 'task-0001',
    scannedBy: 'staff-0009',
    scannedAt: '2026-07-18T01:04:00.000Z',
  },
];
