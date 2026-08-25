"use client";

import { useEffect, useState } from "react";
import { SummaryCard } from "@/components/summary-card";
import { UnderReviewList } from "@/components/under-review-list";
import { UnmatchedPanel } from "@/components/unmatched-panel";
import { ApiError, getReconciliation } from "@/lib/api";
import type { JobStatus, ReconciliationSummary } from "@/lib/types";

type Tab = "review" | "unmatched";

function TabButton({
  active,
  count,
  label,
  onClick,
}: {
  active: boolean;
  count: number;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      role="tab"
      aria-selected={active}
      onClick={onClick}
      className={`rounded-lg px-3 py-1.5 text-sm font-medium ${
        active
          ? "bg-foreground text-background"
          : "border border-border text-muted"
      }`}
    >
      {label}
      <span className="ml-1.5 tabular-nums">{count}</span>
    </button>
  );
}

/** Everything about one job: its outcome, then its two queues of work.
 *
 * The queues are tabs rather than stacked sections because they are separate
 * jobs of work — deciding the engine's guesses, and pairing what it could not
 * guess at all — and a reviewer does one at a time.
 */
export function JobPanel({
  jobId,
  status,
}: {
  jobId: string;
  /** Passed in so the panel reloads as the worker moves the job along. */
  status: JobStatus;
}) {
  const [summary, setSummary] = useState<ReconciliationSummary | null>(null);
  const [jobError, setJobError] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("review");

  // Bumped by any decision so the counts and both queues reload: reconciling
  // or rejecting one pair changes what is left in the other tab.
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const detail = await getReconciliation(jobId);
        if (cancelled) return;
        setSummary(detail.summary);
        setJobError(detail.job.error_message);
        setError(null);
      } catch (caught) {
        if (cancelled) return;
        setError(
          caught instanceof ApiError
            ? caught.message
            : "Could not load this reconciliation.",
        );
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, [jobId, status, refreshKey]);

  if (error) {
    return (
      <p role="alert" className="text-sm text-red-500">
        {error}
      </p>
    );
  }

  if (!summary) {
    return (
      <p className="text-sm text-muted" aria-live="polite">
        Loading this reconciliation…
      </p>
    );
  }

  const unmatchedCount =
    summary.unmatched_bank_count + summary.unmatched_ledger_count;
  const refresh = () => setRefreshKey((current) => current + 1);

  return (
    <div className="flex flex-col gap-3">
      <SummaryCard summary={summary} errorMessage={jobError} />

      {summary.status === "completed" && (
        <>
          <div role="tablist" className="flex gap-2">
            <TabButton
              active={tab === "review"}
              count={summary.under_review_count}
              label="Awaiting review"
              onClick={() => setTab("review")}
            />
            <TabButton
              active={tab === "unmatched"}
              count={unmatchedCount}
              label="Unmatched"
              onClick={() => setTab("unmatched")}
            />
          </div>

          {tab === "review" ? (
            <UnderReviewList
              key={`review-${refreshKey}`}
              jobId={jobId}
              onReviewed={refresh}
            />
          ) : (
            <UnmatchedPanel
              key={`unmatched-${refreshKey}`}
              jobId={jobId}
              onReconciled={refresh}
            />
          )}
        </>
      )}
    </div>
  );
}
