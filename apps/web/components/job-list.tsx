"use client";

import { useState } from "react";
import { StatusBadge } from "@/components/status-badge";
import { formatDate } from "@/lib/format";
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
      className="group flex items-center gap-1.5 self-start font-mono text-xs text-muted hover:text-foreground"
    >
      <span className="truncate">{jobId}</span>
      <span className="shrink-0 text-[0.65rem] uppercase tracking-wide opacity-0 transition-opacity group-hover:opacity-100">
        {copied ? "copied" : "copy"}
      </span>
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
    <section className="flex flex-col gap-3">
      <div className="flex flex-col gap-1">
        <h2 className="text-sm font-medium">Your reconciliations</h2>
        <p className="text-xs leading-relaxed text-muted">
          Pick one to work on it. The assistant answers about whichever is
          selected, so you only need the id to ask about a different one.
        </p>
      </div>

      <ul className="grid gap-2 sm:grid-cols-2">
        {jobs.map((job) => {
          const active = job.id === activeJobId;
          return (
            <li key={job.id}>
              <div
                role="button"
                tabIndex={0}
                aria-pressed={active}
                onClick={() => onSelect(job.id)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    onSelect(job.id);
                  }
                }}
                className={`flex cursor-pointer flex-col gap-2 rounded-xl border p-3.5 transition-colors ${
                  active
                    ? "border-accent bg-surface shadow-[0_0_0_1px_var(--accent)]"
                    : "border-border bg-surface hover:border-border-strong"
                }`}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-sm font-medium">
                    {formatDate(job.created_at)}
                  </span>
                  <StatusBadge status={job.status} />
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
