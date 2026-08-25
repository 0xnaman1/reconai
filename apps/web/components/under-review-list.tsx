"use client";

import { useEffect, useState } from "react";
import { MatchReviewCard } from "@/components/match-review-card";
import {
  ApiError,
  approveMatch,
  listMatches,
  listTransactions,
  rejectMatch,
} from "@/lib/api";
import type { Match, Transaction } from "@/lib/types";

/** The matches a reviewer still has to approve or reject. */
export function UnderReviewList({
  jobId,
  onReviewed,
}: {
  jobId: string;
  onReviewed: () => void;
}) {
  const [pending, setPending] = useState<Match[]>([]);
  const [transactions, setTransactions] = useState<Map<string, Transaction>>(
    new Map(),
  );
  const [loading, setLoading] = useState(true);
  const [busyMatchId, setBusyMatchId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const underReview = await listMatches(jobId, "under_review");
        if (cancelled) return;
        setPending(underReview);

        // Matches carry transaction ids only, so index the job's rows once
        // and look both sides up from there.
        if (underReview.length > 0) {
          const rows = await listTransactions(jobId);
          if (cancelled) return;
          setTransactions(new Map(rows.map((row) => [row.id, row])));
        }
        setError(null);
      } catch (caught) {
        if (cancelled) return;
        setError(
          caught instanceof ApiError
            ? caught.message
            : "Could not load the review queue.",
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

  async function decide(matchId: string, approve: boolean) {
    setBusyMatchId(matchId);
    setError(null);
    try {
      await (approve ? approveMatch(matchId) : rejectMatch(matchId));
      // Deciding one match changes the counts and the unmatched pool, so the
      // parent remounts this list rather than patching it.
      onReviewed();
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

  if (loading) {
    return (
      <p className="text-sm text-muted" aria-live="polite">
        Loading the review queue…
      </p>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {error && (
        <p role="alert" className="text-sm text-red-500">
          {error}
        </p>
      )}

      {pending.length === 0 ? (
        <p className="text-sm text-muted">
          Nothing is waiting on you. Every match the engine made was confident
          enough to accept on its own.
        </p>
      ) : (
        pending.map((match) => (
          <MatchReviewCard
            key={match.id}
            match={match}
            bankTransaction={transactions.get(match.bank_transaction_id)}
            ledgerTransaction={transactions.get(match.ledger_transaction_id)}
            onApprove={() => decide(match.id, true)}
            onReject={() => decide(match.id, false)}
            busy={busyMatchId !== null}
          />
        ))
      )}
    </div>
  );
}
