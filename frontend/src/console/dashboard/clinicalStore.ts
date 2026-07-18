import { appendAuditEntry } from './auditStore';

export interface ClinicalPatient {
  id: string;
  name: string;
  patientCode: string;
  suspectedSpecialty: string;
  triageText: string;
  status: 'waiting_consult' | 'in_consult' | 'completed';
  diagnoses: string[];
  orders: string[];
}

export interface ClinicalAppointment {
  id: string;
  timeSlot: string;
  patientName: string;
  doctorName: string;
  status: 'upcoming' | 'checked_in' | 'in_consult' | 'done';
}

export interface ClinicalTask {
  id: string;
  patientName: string;
  patientCode: string;
  serviceName: string;
  status: 'LOCKED' | 'PENDING' | 'IN_PROGRESS' | 'DONE';
  timeSlot: string;
}

// Initial static seed data
const INITIAL_PATIENTS: ClinicalPatient[] = [
  {
    id: 'p-001',
    name: 'Nguyễn Thị Lan',
    patientCode: 'BN-941207',
    suspectedSpecialty: 'Ngoại tổng quát',
    triageText: 'Đau bụng hạ sườn phải kéo dài 2 ngày, sốt nhẹ 37.8 độ, có buồn nôn.',
    status: 'waiting_consult',
    diagnoses: [],
    orders: []
  },
  {
    id: 'p-002',
    name: 'Lê Hoàng Nam',
    patientCode: 'BN-880214',
    suspectedSpecialty: 'Nội tổng quát',
    triageText: 'Ho nhiều, tức ngực nhẹ, sốt cao đột ngột từ tối qua.',
    status: 'in_consult',
    diagnoses: ['Viêm phế quản cấp'],
    orders: ['Xét nghiệm máu']
  },
  {
    id: 'p-003',
    name: 'Trần Minh Quân',
    patientCode: 'BN-921105',
    suspectedSpecialty: 'Ngoại tổng quát',
    triageText: 'Sưng đau khớp cổ chân phải sau chấn thương thể thao.',
    status: 'waiting_consult',
    diagnoses: [],
    orders: []
  }
];

const INITIAL_APPOINTMENTS: ClinicalAppointment[] = [
  { id: 'app-001', timeSlot: '08:00', patientName: 'Nguyễn Thị Lan', doctorName: 'BS. Lê Văn Minh', status: 'upcoming' },
  { id: 'app-002', timeSlot: '09:00', patientName: 'Lê Hoàng Nam', doctorName: 'BS. Lê Thị Hoa', status: 'in_consult' },
  { id: 'app-003', timeSlot: '10:15', patientName: 'Trần Minh Quân', doctorName: 'BS. Lê Văn Minh', status: 'upcoming' }
];

const INITIAL_TASKS: ClinicalTask[] = [
  { id: 'task-001', patientName: 'Lê Hoàng Nam', patientCode: 'BN-880214', serviceName: 'Xét nghiệm máu', status: 'PENDING', timeSlot: '09:15' },
  { id: 'task-002', patientName: 'Lê Hoàng Nam', patientCode: 'BN-880214', serviceName: 'X-quang bụng', status: 'LOCKED', timeSlot: '09:45' }
];

// In-memory state variables
let patients: ClinicalPatient[] = [...INITIAL_PATIENTS];
let appointments: ClinicalAppointment[] = [...INITIAL_APPOINTMENTS];
let tasks: ClinicalTask[] = [...INITIAL_TASKS];
let nextTaskId = 3;
let listeners: Set<() => void> = new Set();

function emit() {
  listeners.forEach((fn) => fn());
}

export const clinicalStore = {
  subscribe(listener: () => void) {
    listeners.add(listener);
    return () => {
      listeners.delete(listener);
    };
  },

  getPatients() {
    return patients;
  },

  getAppointments() {
    return appointments;
  },

  getTasks() {
    return tasks;
  },

  // Perform Patient Check-in
  checkInPatient(patientCode: string) {
    const patient = patients.find((p) => p.patientCode === patientCode);
    if (patient) {
      // Find matching appointment and update to checked_in
      const appt = appointments.find((a) => a.patientName === patient.name);
      if (appt && appt.status === 'upcoming') {
        appt.status = 'checked_in';
      }
      emit();
    }
  },

  // Start Consulting for Patient
  startConsult(patientId: string) {
    const patient = patients.find((p) => p.id === patientId);
    if (patient) {
      patient.status = 'in_consult';
      const appt = appointments.find((a) => a.patientName === patient.name);
      if (appt) {
        appt.status = 'in_consult';
      }
      emit();
    }
  },

  // Add Diagnoses and Finalise Orders
  signAndFinaliseOrders(patientId: string, diagnoses: string[], orderedServices: string[]) {
    const patient = patients.find((p) => p.id === patientId);
    if (patient) {
      patient.diagnoses = diagnoses;
      patient.orders = orderedServices;
      patient.status = 'completed';

      // Update appointment status to done
      const appt = appointments.find((a) => a.patientName === patient.name);
      if (appt) {
        appt.status = 'done';
      }

      // Generate technician tasks.
      // First service is PENDING, subsequent are LOCKED (waiting for previous steps / payment).
      orderedServices.forEach((service, index) => {
        tasks.push({
          id: `task-00${nextTaskId++}`,
          patientName: patient.name,
          patientCode: patient.patientCode,
          serviceName: service,
          status: index === 0 ? 'PENDING' : 'LOCKED',
          timeSlot: '11:30' // mock time slot
        });
      });

      // Audit clinical action
      appendAuditEntry({
        actorId: 'doctor',
        actorRole: 'doctor',
        actorDisplayName: 'BS. Lê Văn Minh',
        decision: 'APPROVED',
        targetEventId: patient.id,
        aiRationale: `Bác sĩ kê toa chỉ định ${orderedServices.join(', ')} cho bệnh nhân ${patient.name}.`
      });

      emit();
    }
  },

  // Unlock task (usually done by payment/admin)
  unlockTask(taskId: string) {
    const task = tasks.find((t) => t.id === taskId);
    if (task && task.status === 'LOCKED') {
      task.status = 'PENDING';
      emit();
    }
  },

  // Start performing a task (e.g. scanning QR code at tech booth)
  startTask(taskId: string) {
    const task = tasks.find((t) => t.id === taskId);
    if (task && task.status === 'PENDING') {
      task.status = 'IN_PROGRESS';
      emit();
    }
  },

  // Complete a task
  completeTask(taskId: string) {
    const task = tasks.find((t) => t.id === taskId);
    if (task && task.status === 'IN_PROGRESS') {
      task.status = 'DONE';

      // Find next task for same patient and unlock it if it was LOCKED
      const patientTasks = tasks.filter((t) => t.patientCode === task.patientCode);
      const nextLockedTask = patientTasks.find((t) => t.status === 'LOCKED');
      if (nextLockedTask) {
        nextLockedTask.status = 'PENDING';
      }

      emit();
    }
  },

  // Reset or Seed simulator data
  resetSimulator(seedLevel: 'default' | 'high_load' = 'default') {
    patients = [...INITIAL_PATIENTS];
    appointments = [...INITIAL_APPOINTMENTS];
    tasks = [...INITIAL_TASKS];
    nextTaskId = 3;

    if (seedLevel === 'high_load') {
      // Simulate highly congested hospital state
      patients.push({
        id: 'p-004',
        name: 'Vũ Nam Khánh',
        patientCode: 'BN-910408',
        suspectedSpecialty: 'Chẩn đoán hình ảnh',
        triageText: 'Đau đầu dữ dội, chóng mặt sau ngã xe máy.',
        status: 'waiting_consult',
        diagnoses: [],
        orders: []
      });
      appointments.push({
        id: 'app-004',
        timeSlot: '11:00',
        patientName: 'Vũ Nam Khánh',
        doctorName: 'BS. Lê Thị Hoa',
        status: 'upcoming'
      });
    }

    emit();
  }
};
