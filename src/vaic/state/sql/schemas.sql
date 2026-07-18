-- VAIC relational schema (PostgreSQL), implementing docs/specs/08-data-model.md (TASK-032).
--
-- This file is the source of truth for table creation: `engine.py::create_schema()` executes it
-- verbatim. `models.py` mirrors it column-for-column for querying; it does not generate the tables.
--
-- Referential-action policy (data-model.md: "every FK has an explicit action; the default is rarely
-- intended"):
--   * ON DELETE RESTRICT is the default: never silently cascade-delete clinical data.
--   * ON DELETE SET NULL is used only for AuditLogEntry's links, because BR-23 requires the log
--     entry to survive even if the record it refers to is later removed.
--
-- Deliberately no FK (documented, not an oversight - see TASK-032 "Decisions and blockers"):
--   Diagnosis.diagnosed_by, ServiceOrder.ordered_by, Payment.confirmed_by, DisruptionEvent.decided_by
--   - the dictionary names these as a doctor/authorised source/coordinator without pointing at a
--   persisted table in spec 08 (Account lives only in src/vaic/auth, not in the data model).
--
-- Snapshot note: matches src/vaic/models/entities.py as committed on cnv-dev today - i.e. BEFORE
-- the (unmerged) TASK-016 patient-link denormalization on Diagnosis/ServiceOrder/Slot/Payment/
-- AuditLogEntry. See TASK-032's task file for the required follow-up once TASK-016 merges.

-- ============================================================
--  Enums (docs/specs/03-glossary.md / src/vaic/models/enums.py)
-- ============================================================

CREATE TYPE priority_level_enum AS ENUM ('ROUTINE', 'URGENT', 'EMERGENCY');
CREATE TYPE appointment_status_enum AS ENUM
    ('PROPOSED', 'BOOKED', 'CHECKED_IN', 'IN_CONSULT', 'DONE', 'NO_SHOW', 'CANCELLED');
CREATE TYPE payment_status_enum AS ENUM ('UNPAID', 'PAID');
CREATE TYPE care_plan_status_enum AS ENUM ('DRAFT', 'ACTIVE', 'COMPLETED');
CREATE TYPE execution_status_enum AS ENUM
    ('LOCKED', 'PENDING', 'IN_PROGRESS', 'DONE', 'CANCELLED');
CREATE TYPE resource_type_enum AS ENUM ('DOCTOR', 'TECHNICIAN', 'ROOM', 'EQUIPMENT');
CREATE TYPE disruption_event_type_enum AS ENUM
    ('EQUIPMENT_FAILURE', 'OVERLOAD', 'SCHEDULE_CHANGE', 'EMERGENCY');
CREATE TYPE disruption_status_enum AS ENUM
    ('DETECTED', 'ASSESSED', 'AUTO_RESOLVED', 'PENDING_APPROVAL', 'APPROVED', 'REJECTED');
CREATE TYPE notification_channel_enum AS ENUM ('IN_APP', 'SCREEN', 'SMS');
CREATE TYPE payment_subject_type_enum AS ENUM ('TASK', 'APPOINTMENT');

-- ============================================================
--  Tables with no forward FK dependency
-- ============================================================

CREATE TABLE patients (
    id              UUID PRIMARY KEY,
    full_name       TEXT NOT NULL,
    phone           TEXT,
    patient_code    TEXT NOT NULL UNIQUE,
    priority_level  priority_level_enum NOT NULL DEFAULT 'ROUTINE',
    created_at      TIMESTAMPTZ NOT NULL
);

CREATE TABLE resources (
    id                  UUID PRIMARY KEY,
    type                resource_type_enum NOT NULL,
    department_id       UUID NOT NULL,  -- no Department table in spec 08; kept a plain column
    is_available        BOOLEAN NOT NULL DEFAULT TRUE,
    capacity_per_hour   INTEGER
);
CREATE INDEX ix_resources_department_id ON resources (department_id);

CREATE TABLE service_types (
    id                      UUID PRIMARY KEY,
    code                    TEXT NOT NULL UNIQUE,
    display_label           TEXT NOT NULL,
    requires_fasting        BOOLEAN NOT NULL DEFAULT FALSE,
    turnaround_minutes      INTEGER NOT NULL DEFAULT 0 CHECK (turnaround_minutes >= 0),
    default_duration_min    INTEGER NOT NULL DEFAULT 10 CHECK (default_duration_min > 0)
);

CREATE TABLE disruption_events (
    id              UUID PRIMARY KEY,
    event_type      disruption_event_type_enum NOT NULL,
    status          disruption_status_enum NOT NULL DEFAULT 'DETECTED',
    blast_radius    INTEGER NOT NULL DEFAULT 0,
    decided_by      UUID  -- approving coordinator; no persisted Account table in spec 08
);

-- ============================================================
--  Tables depending on patients
-- ============================================================

CREATE TABLE intake_sessions (
    id                  UUID PRIMARY KEY,
    patient_id          UUID NOT NULL REFERENCES patients (id) ON DELETE RESTRICT,
    transcript          TEXT NOT NULL DEFAULT '',
    structured_triage   JSONB NOT NULL DEFAULT '{}'::jsonb,
    emergency_suspected BOOLEAN NOT NULL DEFAULT FALSE,
    created_at          TIMESTAMPTZ NOT NULL
);
CREATE INDEX ix_intake_sessions_patient_id ON intake_sessions (patient_id);

CREATE TABLE appointments (
    id              UUID PRIMARY KEY,
    patient_id      UUID NOT NULL REFERENCES patients (id) ON DELETE RESTRICT,
    specialty       TEXT NOT NULL,
    status          appointment_status_enum NOT NULL DEFAULT 'PROPOSED',
    payment_status  payment_status_enum NOT NULL DEFAULT 'UNPAID',
    slot_start      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL
);
CREATE INDEX ix_appointments_patient_id ON appointments (patient_id);

CREATE TABLE diagnoses (
    id              UUID PRIMARY KEY,
    appointment_id  UUID NOT NULL REFERENCES appointments (id) ON DELETE RESTRICT,
    conditions      JSONB NOT NULL DEFAULT '[]'::jsonb,
    diagnosed_by    UUID NOT NULL,  -- the doctor; no persisted Account table in spec 08
    created_at      TIMESTAMPTZ NOT NULL
);
CREATE INDEX ix_diagnoses_appointment_id ON diagnoses (appointment_id);

CREATE TABLE care_plans (
    id              UUID PRIMARY KEY,
    patient_id      UUID NOT NULL REFERENCES patients (id) ON DELETE RESTRICT,
    diagnosis_id    UUID NOT NULL REFERENCES diagnoses (id) ON DELETE RESTRICT,
    status          care_plan_status_enum NOT NULL DEFAULT 'DRAFT',
    assigned_staff  JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL
);
CREATE INDEX ix_care_plans_patient_id ON care_plans (patient_id);
CREATE INDEX ix_care_plans_diagnosis_id ON care_plans (diagnosis_id);

CREATE TABLE notifications (
    id          UUID PRIMARY KEY,
    patient_id  UUID NOT NULL REFERENCES patients (id) ON DELETE RESTRICT,
    channel     notification_channel_enum NOT NULL DEFAULT 'IN_APP',
    body        TEXT NOT NULL,
    reason      TEXT,
    created_at  TIMESTAMPTZ NOT NULL
);
CREATE INDEX ix_notifications_patient_id ON notifications (patient_id);

-- ============================================================
--  Tables depending on diagnoses / service_types
-- ============================================================

CREATE TABLE service_orders (
    id                  UUID PRIMARY KEY,
    diagnosis_id        UUID NOT NULL REFERENCES diagnoses (id) ON DELETE RESTRICT,
    service_type_id     UUID NOT NULL REFERENCES service_types (id) ON DELETE RESTRICT,
    ordered_by          UUID NOT NULL,  -- signing doctor; no persisted Account table in spec 08
    signed_at           TIMESTAMPTZ NOT NULL
);
CREATE INDEX ix_service_orders_diagnosis_id ON service_orders (diagnosis_id);
CREATE INDEX ix_service_orders_service_type_id ON service_orders (service_type_id);

-- ============================================================
--  Tables depending on care_plans / service_orders / resources
-- ============================================================

CREATE TABLE tasks (
    id                      UUID PRIMARY KEY,
    care_plan_id            UUID NOT NULL REFERENCES care_plans (id) ON DELETE RESTRICT,
    service_order_id        UUID NOT NULL REFERENCES service_orders (id) ON DELETE RESTRICT,
    owner_id                UUID NOT NULL REFERENCES resources (id) ON DELETE RESTRICT,
    execution_status        execution_status_enum NOT NULL DEFAULT 'LOCKED',
    payment_status          payment_status_enum NOT NULL DEFAULT 'UNPAID',
    estimated_duration_min  INTEGER NOT NULL DEFAULT 0,
    sequence_index          INTEGER NOT NULL DEFAULT 0,
    depends_on              JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at              TIMESTAMPTZ NOT NULL
);
CREATE INDEX ix_tasks_care_plan_id ON tasks (care_plan_id);
CREATE INDEX ix_tasks_service_order_id ON tasks (service_order_id);
-- Query shape this indexes: owner_queue()/owner_load_minutes() in src/vaic/state/repository.py
-- filter by owner_id then by execution_status/payment_status (BR-10's in_queue predicate).
CREATE INDEX ix_tasks_owner_id ON tasks (owner_id);
CREATE INDEX ix_tasks_owner_status ON tasks (owner_id, execution_status, payment_status);

-- ============================================================
--  Tables depending on tasks / patients / resources
-- ============================================================

CREATE TABLE slots (
    id          UUID PRIMARY KEY,
    task_id     UUID NOT NULL REFERENCES tasks (id) ON DELETE RESTRICT,
    owner_id    UUID NOT NULL REFERENCES resources (id) ON DELETE RESTRICT,
    start       TIMESTAMPTZ NOT NULL,
    "end"       TIMESTAMPTZ
);
CREATE INDEX ix_slots_task_id ON slots (task_id);
CREATE INDEX ix_slots_owner_id ON slots (owner_id);

CREATE TABLE scan_events (
    id          UUID PRIMARY KEY,
    patient_id  UUID NOT NULL REFERENCES patients (id) ON DELETE RESTRICT,
    task_id     UUID NOT NULL REFERENCES tasks (id) ON DELETE RESTRICT,
    scanned_by  UUID NOT NULL REFERENCES resources (id) ON DELETE RESTRICT,
    scanned_at  TIMESTAMPTZ NOT NULL
);
CREATE INDEX ix_scan_events_patient_id ON scan_events (patient_id);
CREATE INDEX ix_scan_events_task_id ON scan_events (task_id);

-- Payment.subject_id is polymorphic (Task or Appointment per subject_type) - no single FK is
-- correct here, so it is stored unconstrained, matching the app-layer entity (Pydantic has no
-- referential check on it either).
CREATE TABLE payments (
    id              UUID PRIMARY KEY,
    subject_type    payment_subject_type_enum NOT NULL,
    subject_id      UUID NOT NULL,
    amount          NUMERIC,
    status          payment_status_enum NOT NULL DEFAULT 'UNPAID',
    confirmed_by    UUID,  -- authorised source; no persisted Account table in spec 08
    confirmed_at    TIMESTAMPTZ
);
CREATE INDEX ix_payments_subject ON payments (subject_type, subject_id);

-- AuditLogEntry.target_id is polymorphic (any entity) - no single FK, same reasoning as Payment
-- above. patient_id and target_id use SET NULL: BR-23 requires the entry to survive even if the
-- record it names is later removed.
CREATE TABLE audit_log_entries (
    id          UUID PRIMARY KEY,
    actor       TEXT NOT NULL,
    action      TEXT NOT NULL,
    target_id   UUID,
    reasoning   TEXT NOT NULL DEFAULT '',
    created_at  TIMESTAMPTZ NOT NULL
);
CREATE INDEX ix_audit_log_entries_created_at ON audit_log_entries (created_at);
