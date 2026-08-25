import Link from "next/link";
import { SummaryCard } from "@/components/summary-card";
import { getReconciliation, listMatches, listTransactions } from "@/lib/api";
import { formatAmount, formatDate } from "@/lib/format";
import type { Match, Transaction } from "@/lib/types";

export const dynamic = "force-dynamic";

/** Transactions no active match points at: the discrepancies to investigate. */
function unmatched(transactions: Transaction[], matches: Match[]): Transaction[] {
  const claimed = new Set<string>();
  for (const match of matches) {
    if (match.status === "rejected") continue;
    claimed.add(match.bank_transaction_id);
    claimed.add(match.ledger_transaction_id);
  }
  return transactions.filter((row) => !claimed.has(row.id));
}

function TransactionRow({ transaction }: { transaction: Transaction }) {
  return (
    <li className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 border-b border-border py-2 last:border-0">
      <span className="text-sm">{transaction.description}</span>
      <span className="text-xs text-muted">
        {formatDate(transaction.transaction_date)}
        {transaction.reference_number
          ? ` · ref ${transaction.reference_number}`
          : ""}
      </span>
      <span className="text-sm font-medium tabular-nums">
        {formatAmount(transaction.amount, transaction.currency)}
      </span>
    </li>
  );
}

export default async function ReconciliationPage(
  props: PageProps<"/reconciliations/[id]">,
) {
  const { id } = await props.params;

  const [detail, transactions, matches] = await Promise.all([
    getReconciliation(id),
    listTransactions(id),
    listMatches(id),
  ]);

  const loose = unmatched(transactions, matches);
  const bank = loose.filter((row) => row.source === "bank");
  const ledger = loose.filter((row) => row.source === "ledger");

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-baseline justify-between gap-2">
        <h1 className="text-lg font-semibold tracking-tight">Reconciliation</h1>
        <Link href="/" className="text-sm text-muted underline">
          Back to chat
        </Link>
      </div>

      <SummaryCard
        summary={detail.summary}
        errorMessage={detail.job.error_message}
      />

      <section className="flex flex-col gap-2">
        <h2 className="text-sm font-medium">
          Unmatched bank transactions ({bank.length})
        </h2>
        {bank.length === 0 ? (
          <p className="text-sm text-muted">Everything matched.</p>
        ) : (
          <ul>
            {bank.map((row) => (
              <TransactionRow key={row.id} transaction={row} />
            ))}
          </ul>
        )}
      </section>

      <section className="flex flex-col gap-2">
        <h2 className="text-sm font-medium">
          Unmatched ledger transactions ({ledger.length})
        </h2>
        {ledger.length === 0 ? (
          <p className="text-sm text-muted">Everything matched.</p>
        ) : (
          <ul>
            {ledger.map((row) => (
              <TransactionRow key={row.id} transaction={row} />
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
