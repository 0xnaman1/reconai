"use client";

import { TransactionSide } from "@/components/transaction-side";
import type { Match, Transaction } from "@/lib/types";

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
        <TransactionSide label="Bank" transaction={bankTransaction} />
        <TransactionSide label="Ledger" transaction={ledgerTransaction} />
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
