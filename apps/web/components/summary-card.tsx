import { StatusBadge } from "@/components/status-badge";
import type { ReconciliationSummary } from "@/lib/types";

function Stat({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone?: "success" | "warning" | "danger";
}) {
  const color =
    tone === "success"
      ? "text-success"
      : tone === "warning"
        ? "text-warning"
        : tone === "danger"
          ? "text-danger"
          : "text-foreground";

  return (
    <div className="flex flex-col gap-0.5">
      <span className={`numeric text-2xl font-semibold tracking-tight ${color}`}>
        {value}
      </span>
      <span className="text-xs text-muted">{label}</span>
    </div>
  );
}

export function SummaryCard({
  summary,
  errorMessage,
}: {
  summary: ReconciliationSummary;
  errorMessage?: string | null;
}) {
  const unmatched =
    summary.unmatched_bank_count + summary.unmatched_ledger_count;

  return (
    <div className="card flex flex-col gap-4 p-5">
      <div className="flex items-center justify-between gap-3">
        <span className="text-sm font-medium">Reconciliation</span>
        <StatusBadge status={summary.status} />
      </div>

      {errorMessage && (
        <p className="rounded-lg border border-danger/30 bg-danger/5 px-3 py-2 text-sm text-danger">
          {errorMessage}
        </p>
      )}

      <div className="grid grid-cols-3 gap-x-4 gap-y-5 sm:grid-cols-5">
        <Stat label="Bank rows" value={summary.bank_transaction_count} />
        <Stat label="Ledger rows" value={summary.ledger_transaction_count} />
        <Stat label="Matched" value={summary.matched_count} tone="success" />
        <Stat
          label="Awaiting review"
          value={summary.under_review_count}
          tone={summary.under_review_count > 0 ? "warning" : undefined}
        />
        <Stat
          label="Unmatched"
          value={unmatched}
          tone={unmatched > 0 ? "danger" : undefined}
        />
      </div>

      {(summary.reconciled_count > 0 || summary.rejected_count > 0) && (
        <p className="border-t border-border pt-3 text-xs text-muted">
          You approved{" "}
          <span className="numeric font-medium text-foreground">
            {summary.reconciled_count}
          </span>{" "}
          and rejected{" "}
          <span className="numeric font-medium text-foreground">
            {summary.rejected_count}
          </span>
          .
        </p>
      )}
    </div>
  );
}
