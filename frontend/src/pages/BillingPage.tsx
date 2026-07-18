/**
 * BillingPage - /billing viện phí & BHYT (PMA-M6) - DISPLAY-ONLY.
 *
 * DECISION (spec-guardian lock, TASK-023): FR-05/AS-02 and spec 10 win over
 * PRD-FR-12 M6's "Thanh toan QR / the / vi" (online payment) line. This
 * screen therefore renders a cost estimate, insurance coverage, and invoice
 * history and NOTHING that could move money - no payment form, no
 * button/link resembling a pay action, no QR/card/wallet control. The
 * proceed/paid flag is set by an authorised source outside this app; the
 * patient only ever sees a "go pay at the counter" reminder here.
 */
import { useEffect, useState } from 'react';
import { useI18n } from '@/i18n';
import { useAuth } from '@/auth/AuthContext';
import * as billingApi from '@/lib/api/billing';
import type { BillingEstimate, Invoice } from '@/lib/api/types';
import { Card, ScreenState, SectionLabel, StatusChip, type ViewState } from '@/components/primitives';

export function BillingPage() {
  const { t } = useI18n();
  const { session } = useAuth();
  const patientId = session?.patient.id;

  const [estimates, setEstimates] = useState<BillingEstimate[] | null>(null);
  const [invoices, setInvoices] = useState<Invoice[] | null>(null);
  const [loadError, setLoadError] = useState(false);

  useEffect(() => {
    if (!patientId) return;
    let cancelled = false;
    setLoadError(false);

    Promise.all([billingApi.listBillingEstimates(patientId), billingApi.listInvoices(patientId)])
      .then(([estimateResult, invoiceResult]) => {
        if (cancelled) return;
        setEstimates(estimateResult);
        setInvoices(invoiceResult);
      })
      .catch(() => {
        if (!cancelled) setLoadError(true);
      });

    return () => {
      cancelled = true;
    };
  }, [patientId]);

  const isLoaded = estimates !== null && invoices !== null;
  const viewState: ViewState = loadError
    ? 'error'
    : !isLoaded
      ? 'loading'
      : estimates.length === 0 && invoices.length === 0
        ? 'empty'
        : 'success';

  return (
    <div className="flex flex-col gap-4 px-5 py-4 animate-fade-up">
      <h1 className="text-[22px] font-bold">{t('billing.title')}</h1>
      <p className="rounded-2xl bg-info/10 px-4 py-3 text-[13px] leading-relaxed text-info">
        {t('billing.displayOnlyNotice')}
      </p>

      <ScreenState state={viewState} emptyMessage={t('billing.emptyMessage')}>
        <div className="flex flex-col gap-5">
          {estimates && estimates.length > 0 && (
            <section className="flex flex-col gap-2">
              <SectionLabel>{t('billing.estimateHeading')}</SectionLabel>
              <ol className="flex flex-col gap-3">
                {estimates.map((estimate) => (
                  <li key={estimate.id}>
                    <Card className="flex flex-col gap-2.5">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-[15px] font-semibold">{estimate.serviceLabel}</span>
                        <span className="font-mono text-[15px] font-bold">{estimate.estimatedAmount} VND</span>
                      </div>
                      <span className="text-[13px] text-muted-foreground">{estimate.insuranceCoverageLabel}</span>
                      <div className="flex items-center justify-between gap-2 rounded-xl bg-muted px-3 py-2.5">
                        <span className="text-[13px] font-bold">{t('billing.coPayLabel')}</span>
                        <span className="font-mono text-base font-extrabold text-primary">
                          {estimate.coPayAmount} VND
                        </span>
                      </div>
                    </Card>
                  </li>
                ))}
              </ol>
            </section>
          )}

          {invoices && invoices.length > 0 && (
            <section className="flex flex-col gap-2">
              <SectionLabel>{t('billing.invoiceHeading')}</SectionLabel>
              <ol className="flex flex-col gap-3">
                {invoices.map((invoice) => (
                  <li key={invoice.id}>
                    <Card className="flex flex-col gap-2.5">
                      <div className="flex items-center justify-between gap-2">
                        <span className="text-[15px] font-medium">{invoice.lineItemsLabel}</span>
                        <StatusChip code={invoice.status} />
                      </div>
                      <span className="font-mono text-[13px] font-semibold text-muted-foreground">
                        {invoice.totalAmount} VND
                      </span>
                    </Card>
                  </li>
                ))}
              </ol>
            </section>
          )}
        </div>
      </ScreenState>
    </div>
  );
}
