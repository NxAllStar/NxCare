/**
 * SCR-07 Admin and audit console (role_admin full, role_coordinator
 * read-only) - on-brand stub, TASK-026. The route admits both roles per the
 * locked contract; the audit-read-only-for-coordinator /
 * simulator-config-admin-only sub-element split is deferred to the real
 * SCR-07 task.
 */
import { StubScreen } from './StubScreen';

export function AdminAuditScreen() {
  return <StubScreen titleKey="console.screen.audit.title" />;
}
