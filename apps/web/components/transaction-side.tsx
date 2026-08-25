"use client";

import { formatAmount, formatDate } from "@/lib/format";
import type { Transaction } from "@/lib/types";

/** One side of a pairing, shown so a reviewer can judge it. */
export function TransactionSide({
  label,
  transaction,
}: {
  label: string;
  transaction: Transaction | undefined;
}) {
  if (!transaction) {
    return <p className="text-sm text-muted">{label}: details unavailable</p>;
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
