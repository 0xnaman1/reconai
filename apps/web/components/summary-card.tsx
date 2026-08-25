import { formatJobStatus } from "@/lib/format";
import type { ReconciliationSummary } from "@/lib/types";

function Stat({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex flex-col">
      <span className="text-lg font-semibold tabular-nums">{value}</span>
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
  return (
    <div className="flex flex-col gap-3 rounded-lg border border-border bg-surface p-4">
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-sm font-medium">Reconciliation</span>
        <span className="text-xs text-muted">
          {formatJobStatus(summary.status)}
        </span>
      </div>

      {errorMessage && (
        <p className="text-sm text-red-500">{errorMessage}</p>
      )}

      <div className="grid grid-cols-3 gap-4 sm:grid-cols-5">
        <Stat label="Bank rows" value={summary.bank_transaction_count} />
        <Stat label="Ledger rows" value={summary.ledger_transaction_count} />
        <Stat label="Matched" value={summary.matched_count} />
        <Stat label="Awaiting review" value={summary.under_review_count} />
        <Stat
          label="Unmatched"
          value={summary.unmatched_bank_count + summary.unmatched_ledger_count}
        />
      </div>

      {(summary.reconciled_count > 0 || summary.rejected_count > 0) && (
        <p className="text-xs text-muted">
          You approved {summary.reconciled_count} and rejected{" "}
          {summary.rejected_count}.
        </p>
      )}
    </div>
  );
}
