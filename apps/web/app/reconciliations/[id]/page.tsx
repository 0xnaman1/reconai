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
    <li className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1 border-b border-border px-4 py-3 last:border-0">
      <span className="text-sm">{transaction.description}</span>
      <span className="text-xs text-muted">
        {formatDate(transaction.transaction_date)}
        {transaction.reference_number ? (
          <>
            {" · "}
            <span className="font-mono">{transaction.reference_number}</span>
          </>
        ) : null}
      </span>
      <span className="numeric text-sm font-medium">
        {formatAmount(transaction.amount, transaction.currency)}
      </span>
    </li>
  );
}

function UnmatchedSection({
  title,
  rows,
}: {
  title: string;
  rows: Transaction[];
}) {
  return (
    <section className="flex flex-col gap-2">
      <h2 className="text-sm font-medium">
        {title} <span className="numeric text-muted">({rows.length})</span>
      </h2>
      {rows.length === 0 ? (
        <p className="text-sm text-muted">Everything matched.</p>
      ) : (
        <ul className="card overflow-hidden">
          {rows.map((row) => (
            <TransactionRow key={row.id} transaction={row} />
          ))}
        </ul>
      )}
    </section>
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
        <h1 className="text-xl font-semibold tracking-tight">Reconciliation</h1>
        <Link href="/" className="text-sm text-accent hover:underline">
          Back to chat
        </Link>
      </div>

      <SummaryCard
        summary={detail.summary}
        errorMessage={detail.job.error_message}
      />

      <UnmatchedSection title="Unmatched bank transactions" rows={bank} />
      <UnmatchedSection title="Unmatched ledger transactions" rows={ledger} />

    </div>
  );
}
