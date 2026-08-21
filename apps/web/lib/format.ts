/** Display helpers shared by the chat and review UI. */

/** Format a decimal string from the API without converting it to a float. */
export function formatAmount(amount: string, currency?: string | null): string {
  const negative = amount.trim().startsWith("-");
  const [whole, fraction = "00"] = amount.replace("-", "").split(".");
  const grouped = whole.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  return `${negative ? "-" : ""}${grouped}.${fraction}${currency ? ` ${currency}` : ""}`;
}

export function formatDate(isoDate: string): string {
  return new Date(isoDate).toLocaleDateString(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

const STATUS_LABELS: Record<string, string> = {
  queued: "Queued",
  processing: "Processing",
  extracting: "Reading the statements",
  matching: "Matching transactions",
  completed: "Completed",
  failed: "Failed",
};

export function formatJobStatus(status: string): string {
  return STATUS_LABELS[status] ?? status;
}

export const TERMINAL_STATUSES = ["completed", "failed"];
