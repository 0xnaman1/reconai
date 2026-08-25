"use client";

import { useEffect, useState } from "react";
import { MatchReviewCard } from "@/components/match-review-card";
import { SummaryCard } from "@/components/summary-card";
import {
  ApiError,
  approveMatch,
  getReconciliation,
  listMatches,
  listTransactions,
  rejectMatch,
} from "@/lib/api";
import type { Match, ReconciliationSummary, Transaction } from "@/lib/types";

/** Summary and the review queue for one job, refreshed after each decision. */
export function ReviewPanel({
  jobId,
  onReviewed,
}: {
  jobId: string;
  onReviewed?: () => void;
}) {
  const [summary, setSummary] = useState<ReconciliationSummary | null>(null);
  const [jobError, setJobError] = useState<string | null>(null);
  const [pending, setPending] = useState<Match[]>([]);
  const [transactions, setTransactions] = useState<Map<string, Transaction>>(
    new Map(),
  );
  const [busyMatchId, setBusyMatchId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Bumped by a decision so the effect below reloads the counts and queue.
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const [detail, underReview] = await Promise.all([
          getReconciliation(jobId),
          listMatches(jobId, "under_review"),
        ]);
        if (cancelled) return;
        setSummary(detail.summary);
        setJobError(detail.job.error_message);
        setPending(underReview);

        // Matches carry transaction ids only, so index the job's rows once
        // and look both sides up from there.
        if (underReview.length > 0) {
          const rows = await listTransactions(jobId);
          if (cancelled) return;
          setTransactions(new Map(rows.map((row) => [row.id, row])));
        }
      } catch (caught) {
        if (cancelled) return;
        setError(
          caught instanceof ApiError
            ? caught.message
            : "Could not load the review queue.",
        );
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [jobId, refreshKey]);

  async function decide(matchId: string, approve: boolean) {
    setBusyMatchId(matchId);
    setError(null);
    try {
      await (approve ? approveMatch(matchId) : rejectMatch(matchId));
      setRefreshKey((key) => key + 1);
      onReviewed?.();
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : "Could not save that decision.",
      );
    } finally {
      setBusyMatchId(null);
    }
  }

  if (!summary) return null;

  return (
    <div className="flex flex-col gap-3">
      <SummaryCard summary={summary} errorMessage={jobError} />

      {error && (
        <p role="alert" className="text-sm text-red-500">
          {error}
        </p>
      )}

      {pending.map((match) => (
        <MatchReviewCard
          key={match.id}
          match={match}
          bankTransaction={transactions.get(match.bank_transaction_id)}
          ledgerTransaction={transactions.get(match.ledger_transaction_id)}
          onApprove={() => decide(match.id, true)}
          onReject={() => decide(match.id, false)}
          busy={busyMatchId !== null}
        />
      ))}
    </div>
  );
}
