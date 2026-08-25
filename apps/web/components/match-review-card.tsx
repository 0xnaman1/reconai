"use client";

import { TransactionSide } from "@/components/transaction-side";
import type { Match, Transaction } from "@/lib/types";

/** Confidence reads as a judgement, so give the number a tone to match. */
function confidenceTone(score: number): string {
  if (score >= 85) return "badge-success";
  if (score >= 75) return "badge-warning";
  return "badge-danger";
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
    <div className="card flex flex-col gap-4 p-5">
      <div className="flex items-center justify-between gap-3">
        <span className="text-sm font-medium">Needs your decision</span>
        <span className={`badge ${confidenceTone(match.confidence_score)}`}>
          <span className="numeric">{match.confidence_score}</span> confident
        </span>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <TransactionSide label="Bank" transaction={bankTransaction} />
        <div className="border-t border-border pt-4 sm:border-l sm:border-t-0 sm:pl-5 sm:pt-0">
          <TransactionSide label="Ledger" transaction={ledgerTransaction} />
        </div>
      </div>

      <p className="text-xs leading-relaxed text-muted">{match.reason}</p>

      <div className="flex gap-2">
        <button
          type="button"
          onClick={onApprove}
          disabled={busy}
          className="btn btn-primary"
        >
          Approve
        </button>
        <button
          type="button"
          onClick={onReject}
          disabled={busy}
          className="btn btn-danger"
        >
          Reject
        </button>
      </div>
    </div>
  );
}
