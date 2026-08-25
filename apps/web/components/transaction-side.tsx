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

  const negative = transaction.amount.trim().startsWith("-");

  return (
    <div className="flex flex-col gap-1">
      <span className="text-[0.7rem] font-medium uppercase tracking-wider text-muted">
        {label}
      </span>
      <span className="text-sm leading-snug">{transaction.description}</span>
      <span
        className={`numeric text-sm font-medium ${
          negative ? "text-foreground" : "text-success"
        }`}
      >
        {formatAmount(transaction.amount, transaction.currency)}
      </span>
      <span className="text-xs text-muted">
        {formatDate(transaction.transaction_date)}
        {transaction.reference_number ? (
          <>
            {" · "}
            <span className="font-mono">{transaction.reference_number}</span>
          </>
        ) : (
          " · no reference"
        )}
      </span>
    </div>
  );
}
