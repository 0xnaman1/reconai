import { formatJobStatus } from "@/lib/format";
import type { JobStatus } from "@/lib/types";

/** Colour carries the meaning here, so the tone map is the whole component. */
const TONE: Record<JobStatus, string> = {
  queued: "badge-neutral",
  processing: "badge-accent",
  extracting: "badge-accent",
  matching: "badge-accent",
  completed: "badge-success",
  failed: "badge-danger",
};

export function StatusBadge({ status }: { status: JobStatus }) {
  const running = status !== "completed" && status !== "failed";
  return (
    <span className={`badge ${TONE[status]}`}>
      {running && (
        <span className="size-1.5 animate-pulse rounded-full bg-current" />
      )}
      {formatJobStatus(status)}
    </span>
  );
}
