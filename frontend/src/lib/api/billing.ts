/**
 * Mock billing stub (/billing, PMA-M6 - no backing FR, TASK-023).
 *
 * DISPLAY-ONLY, by hard requirement (FR-05, AS-02 win over PRD-FR-12 M6's
 * "Thanh toan QR / the / vi" line - see TASK-023 Decisions/blockers). This
 * module exposes no function that could move money, set a paid flag, or
 * accept a payment method: read-only cost estimate and invoice history
 * only. The app never processes payment anywhere.
 *
 * No backend exists yet - every export is marked for replacement.
 */
import { DEMO_BILLING_ESTIMATES, DEMO_INVOICES } from './fixtures';
import type { BillingEstimate, Invoice } from './types';

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/** TODO: replace with a real API call (GET /patients/:id/billing/estimates). */
export async function listBillingEstimates(patientId: string): Promise<BillingEstimate[]> {
  await delay(80);
  return DEMO_BILLING_ESTIMATES.filter((e) => e.patientId === patientId);
}

/** TODO: replace with a real API call (GET /patients/:id/invoices). */
export async function listInvoices(patientId: string): Promise<Invoice[]> {
  await delay(80);
  return DEMO_INVOICES.filter((i) => i.patientId === patientId);
}
