"use client";

import { formatAmount, formatDate } from "@/lib/format";
import type { Match, Transaction } from "@/lib/types";

function Side({
  label,
  transaction,
}: {
  label: string;
  transaction: Transaction | undefined;
}) {
  if (!transaction) {
    return (
      <p className="text-sm text-muted">{label}: details unavailable</p>
    );
  }

  return (
    <div className="flex flex-col gap-0.5">
      <span className="text-xs font-medium text-muted">{label}</span>
      <span className="text-sm">{transaction.description}</span>
      <span className="text-xs text-muted">
        {formatDate(transaction.transaction_date)}
        {transaction.reference_number
          ? ` · ref ${transaction.reference_number}`
          : " · no reference"}
      </span>
      <span className="text-sm font-medium tabular-nums">
        {formatAmount(transaction.amount, transaction.currency)}
      </span>
    </div>
  );
}

export function MatchReviewCard({
  match,
  bankTransaction,
  ledgerTransaction,
  onApprove,
  onReject,
  busy,
}: {
  match: Match;
  bankTransaction: Transaction | undefined;
  ledgerTransaction: Transaction | undefined;
  onApprove: () => void;
  onReject: () => void;
  busy: boolean;
}) {
  return (
    <div className="flex flex-col gap-3 rounded-lg border border-border p-4">
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-sm font-medium">Needs your decision</span>
        <span className="text-xs text-muted tabular-nums">
          {match.confidence_score}% confident
        </span>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <Side label="Bank" transaction={bankTransaction} />
        <Side label="Ledger" transaction={ledgerTransaction} />
      </div>

      <p className="text-xs text-muted">{match.reason}</p>

      <div className="flex gap-2">
        <button
          type="button"
          onClick={onApprove}
          disabled={busy}
          className="rounded-lg bg-foreground px-3 py-1.5 text-sm font-medium text-background disabled:opacity-40"
        >
          Approve
        </button>
        <button
          type="button"
          onClick={onReject}
          disabled={busy}
          className="rounded-lg border border-border px-3 py-1.5 text-sm font-medium disabled:opacity-40"
        >
          Reject
        </button>
      </div>
    </div>
  );
}
