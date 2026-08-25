"use client";

import { useEffect, useState } from "react";
import { TransactionSide } from "@/components/transaction-side";
import { ApiError, createManualMatch, listMatchSuggestions } from "@/lib/api";
import type { MatchSuggestion, Transaction } from "@/lib/types";

interface Group {
  bankTransaction: Transaction;
  candidates: MatchSuggestion[];
}

/** Group the flat suggestion list by the bank transaction being reconciled.
 *
 * The API returns suggestions already ranked and ordered by bank transaction,
 * so grouping preserves that order rather than imposing its own.
 */
function groupByBankTransaction(suggestions: MatchSuggestion[]): Group[] {
  const groups: Group[] = [];
  const seen = new Map<string, Group>();

  for (const suggestion of suggestions) {
    const key = suggestion.bank_transaction.id;
    let group = seen.get(key);
    if (!group) {
      group = { bankTransaction: suggestion.bank_transaction, candidates: [] };
      seen.set(key, group);
      groups.push(group);
    }
    group.candidates.push(suggestion);
  }

  return groups;
}

export function UnmatchedPanel({
  jobId,
  onReconciled,
}: {
  jobId: string;
  onReconciled: () => void;
}) {
  const [groups, setGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const suggestions = await listMatchSuggestions(jobId);
        if (cancelled) return;
        setGroups(groupByBankTransaction(suggestions));
        setError(null);
      } catch (caught) {
        if (cancelled) return;
        setError(
          caught instanceof ApiError
            ? caught.message
            : "Could not load suggestions.",
        );
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [jobId]);

  async function reconcile(suggestion: MatchSuggestion) {
    const key = `${suggestion.bank_transaction.id}:${suggestion.ledger_transaction.id}`;
    setPending(key);
    setError(null);
    try {
      await createManualMatch(
        jobId,
        suggestion.bank_transaction.id,
        suggestion.ledger_transaction.id,
      );
      // Reconciling one pair removes both sides from every other suggestion,
      // so the parent remounts this panel rather than patching the list.
      onReconciled();
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : "Could not reconcile those transactions.",
      );
    } finally {
      setPending(null);
    }
  }

  if (loading) {
    return (
      <p className="text-sm text-muted" aria-live="polite">
        Looking for possible matches…
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      <p className="text-xs text-muted">
        Nothing scored high enough for the engine to pair these automatically.
        If you recognize a counterpart, reconcile it yourself.
      </p>

      {error && (
        <div
          role="alert"
          className="rounded-lg border border-red-500/40 bg-red-500/5 px-4 py-2.5 text-sm"
        >
          {error}
        </div>
      )}

      {groups.length === 0 && !error && (
        <p className="text-sm text-muted">
          Every transaction on both sides is accounted for.
        </p>
      )}

      {groups.map((group) => (
        <div
          key={group.bankTransaction.id}
          className="flex flex-col gap-3 rounded-lg border border-border p-4"
        >
          <TransactionSide label="Bank" transaction={group.bankTransaction} />

          <div className="flex flex-col gap-2 border-t border-border pt-3">
            <span className="text-xs font-medium text-muted">
              Closest ledger entries
            </span>

            {group.candidates.map((candidate) => {
              const key = `${candidate.bank_transaction.id}:${candidate.ledger_transaction.id}`;
              return (
                <div
                  key={candidate.ledger_transaction.id}
                  className="flex flex-col gap-2 rounded-lg bg-surface p-3 sm:flex-row sm:items-start sm:justify-between"
                >
                  <div className="flex flex-col gap-1">
                    <TransactionSide
                      label="Ledger"
                      transaction={candidate.ledger_transaction}
                    />
                    <p className="text-xs text-muted">{candidate.reason}</p>
                  </div>

                  <div className="flex shrink-0 items-center gap-2">
                    <span className="text-xs text-muted tabular-nums">
                      {candidate.score}% match
                    </span>
                    <button
                      type="button"
                      onClick={() => void reconcile(candidate)}
                      disabled={pending !== null}
                      className="rounded-lg border border-border px-3 py-1.5 text-sm font-medium disabled:opacity-40"
                    >
                      {pending === key ? "Reconciling…" : "Reconcile"}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ))}
    </div>
  );
}
