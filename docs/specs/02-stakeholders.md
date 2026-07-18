---
title: "Stakeholders"
sidebar_label: "02. Stakeholders"
description: "Roles, interests, influence, and decision rights for VAIC - AI Care Pathway Coordinator."
tags: [specs, stakeholders, vaic]
---

# Stakeholders

<!-- This is a hackathon build. The "stakeholders" are the demo team and the roles the demo
     portrays. Real hospital stakeholders (clinical governance, DPO, hospital IT) are named where a
     production version would need them, and flagged as not-yet-engaged open issues. -->

## Stakeholder map

| ID | Role | Represents | Interest in the system | Influence | Decision rights |
|----|------|-----------|------------------------|-----------|-----------------|
| SH-01 | Team lead | Đội thi / Hackathon team | Chốt scope, ưu tiên, bảo mật demo; là chủ tài liệu / Owns scope, priorities, demo security; document owner | High | Mọi quyết định về scope, ưu tiên, guardrail của bản demo / All demo scope, priority, and guardrail decisions |
| SH-02 | Simulated doctor (demo persona) | Bác sĩ lâm sàng / Clinical doctor | Chẩn đoán và chỉ định dịch vụ là nguồn sự thật / Diagnosis and service orders are the source of truth | Medium | Nội dung chẩn đoán/chỉ định trong kịch bản demo / Diagnosis and order content in the demo script |
| SH-03 | Simulated coordinator (demo persona) | Điều phối viên vận hành / Operations coordinator | Duyệt/từ chối phương án re-plan ảnh hưởng lớn / Approves or rejects large-impact re-plans | Medium | Quyết định vận hành trong kịch bản demo / Operational decisions in the demo script |
| SH-04 | Simulated patient (demo persona) | Bệnh nhân / Patient | Lộ trình rõ ràng, ETA đáng tin, chờ ít / Clear pathway, trustworthy ETA, less waiting | Low | Không - đối tượng phục vụ / None - the served party |
| SH-05 | Hackathon judges | Ban giám khảo / Judges | Đánh giá tính AI-native, hiệu quả, an toàn / Assess AI-nativeness, effectiveness, safety | High | Không quyết định scope nhưng định hình tiêu chí thành công / No scope authority but shape the success criteria |
| SH-06 | Hospital clinical governance | Quản trị lâm sàng (bản production) | An toàn lâm sàng, ranh giới AI / Clinical safety, AI boundaries | High (production only) | Chưa tham gia - see [OI-06](11-assumptions-constraints.md#oi-06) / Not yet engaged |
| SH-07 | Data protection officer (DPO) | Bảo vệ dữ liệu (bản production) | Tuân thủ luật dữ liệu y tế / Health-data compliance | High (production only) | Chưa tham gia - see [OI-07](11-assumptions-constraints.md#oi-07) / Not yet engaged |

## User groups

| Group | Size (approx.) | Technical comfort | Primary tasks | Role in [06](06-access-control.md) |
|-------|----------------|-------------------|---------------|-------------------------------------|
| Bệnh nhân / Patients | Mô phỏng ~50-100/run / simulated ~50-100 per run | Low | Chat triệu chứng, theo dõi timeline, thanh toán, hỏi/đổi lộ trình / Chat symptoms, track timeline, pay, ask or adjust pathway | `role_patient` |
| Bác sĩ / Doctors | Vài persona demo / a few demo personas | Medium | Nhập chẩn đoán và chỉ định dịch vụ; xem worklist / Enter diagnosis and orders; view worklist | `role_doctor` |
| Kỹ thuật viên / Technicians | Vài persona demo / a few demo personas | Medium | Thực hiện dịch vụ (lab/imaging), cập nhật trạng thái task / Perform services, update task status | `role_technician` |
| Điều phối viên / Coordinators | 1-2 persona demo / 1-2 demo personas | High | Giám sát dashboard, duyệt/từ chối re-plan / Monitor dashboard, approve or reject re-plans | `role_coordinator` |
| Quản trị hệ thống / Administrators | 1 demo | High | Cấu hình hệ thống, seed simulator, xem audit log / Configure system, seed simulator, read audit log | `role_admin` |

## Organisational context

- Proposing department: Đội thi hackathon / Hackathon team (SH-01).
- Budget owner: Team lead (SH-01) - phạm vi demo, không có ngân sách vận hành / demo scope, no operational budget.
- Process owner: Không áp dụng cho bản demo; bản production sẽ là khoa khám bệnh + điều phối viện / Not applicable to the demo; production would be the outpatient department plus hospital dispatch.
- Delivery team: Đội thi gồm **nhiều lập trình viên làm việc song song** / The hackathon team - **multiple developers working concurrently**. Điều phối qua board `docs/tasks/master-plan.md`; kỷ luật làm việc song song ở `.claude/rules/git-workflow.md`. / Coordinated via the task board; parallel-work discipline in the git-workflow rule.

## Escalation path

| Situation | Goes to |
|-----------|---------|
| Requirement conflict between user groups | Team lead (SH-01) |
| Scope change with cost impact | Team lead (SH-01) |
| Security or compliance objection | Team lead (SH-01) cho bản demo; bản production leo lên DPO (SH-07) và quản trị lâm sàng (SH-06) / Team lead for the demo; production escalates to DPO and clinical governance |

## Communication and sign-off

| Artefact | Reviewed by | Approved by | Cadence |
|----------|-------------|-------------|---------|
| This specification set | SH-02, SH-03 (persona owners), delivery team | Team lead | One-off (bản demo) / one-off for the demo |

## Open points

- Bản demo không có quản trị lâm sàng hay DPO thật tham gia - production cần, ghi tại [OI-06](11-assumptions-constraints.md#oi-06) và [OI-07](11-assumptions-constraints.md#oi-07). / No real clinical governance or DPO engaged for the demo - production needs both.
