"use client";

import { useState } from "react";
import { formatDate, formatJobStatus } from "@/lib/format";
import type { ReconciliationJob } from "@/lib/types";

/** Copy a job id so it can be pasted into the chat or another tool. */
function CopyId({ jobId }: { jobId: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(jobId);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 1500);
    } catch {
      // Clipboard access can be refused. The id is on screen either way, so
      // there is nothing to recover from.
    }
  }

  return (
    <button
      type="button"
      onClick={(event) => {
        event.stopPropagation();
        void copy();
      }}
      title={jobId}
      aria-label={`Copy job id ${jobId}`}
      className="font-mono text-xs text-muted underline decoration-dotted underline-offset-2"
    >
      {copied ? "copied" : jobId}
    </button>
  );
}

export function JobList({
  jobs,
  activeJobId,
  onSelect,
}: {
  jobs: ReconciliationJob[];
  activeJobId: string | null;
  onSelect: (jobId: string) => void;
}) {
  if (jobs.length === 0) return null;

  return (
    <section className="flex flex-col gap-2">
      <h2 className="text-sm font-medium">Your reconciliations</h2>
      <p className="text-xs text-muted">
        Pick one to work on it. The assistant answers about whichever is
        selected, so you only need the id to ask about a different one.
      </p>

      <ul className="flex flex-col gap-2">
        {jobs.map((job) => {
          const active = job.id === activeJobId;
          return (
            <li key={job.id}>
              <div
                role="button"
                tabIndex={0}
                onClick={() => onSelect(job.id)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    onSelect(job.id);
                  }
                }}
                className={`flex cursor-pointer flex-col gap-1 rounded-lg border p-3 ${
                  active ? "border-foreground" : "border-border"
                }`}
              >
                <div className="flex items-baseline justify-between gap-2">
                  <span className="text-sm font-medium">
                    {formatDate(job.created_at)}
                  </span>
                  <span className="text-xs text-muted">
                    {formatJobStatus(job.status)}
                  </span>
                </div>
                <CopyId jobId={job.id} />
              </div>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
