/** Response shapes returned by the Recon AI backend. */

export type JobStatus =
  | "queued"
  | "processing"
  | "extracting"
  | "matching"
  | "completed"
  | "failed";

export type MatchStatus = "matched" | "under_review" | "reconciled" | "rejected";

export type MatchType = "exact" | "fuzzy" | "manual";

export type TransactionSource = "bank" | "ledger";

export type ChatRole = "system" | "user" | "assistant" | "tool";

export interface ReconciliationJob {
  id: string;
  status: JobStatus;
  bank_pdf_path: string;
  ledger_pdf_path: string;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface ReconciliationSummary {
  job_id: string;
  status: JobStatus;
  bank_transaction_count: number;
  ledger_transaction_count: number;
  matched_count: number;
  under_review_count: number;
  reconciled_count: number;
  rejected_count: number;
  unmatched_bank_count: number;
  unmatched_ledger_count: number;
}

export interface ReconciliationDetail {
  job: ReconciliationJob;
  summary: ReconciliationSummary;
}

export interface Transaction {
  id: string;
  job_id: string;
  source: TransactionSource;
  transaction_date: string;
  description: string;
  reference_number: string | null;
  /** Decimal string, signed. Negative is money out. */
  amount: string;
  currency: string | null;
  raw_text: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface Match {
  id: string;
  job_id: string;
  bank_transaction_id: string;
  ledger_transaction_id: string;
  match_type: MatchType;
  confidence_score: number;
  status: MatchStatus;
  reason: string;
  created_at: string;
  updated_at: string;
}

/** A candidate pairing the engine scored too low to assert on its own. */
export interface MatchSuggestion {
  bank_transaction: Transaction;
  ledger_transaction: Transaction;
  score: number;
  reason: string;
}

export interface ChatSession {
  id: string;
  active_job_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ChatMessage {
  id: string;
  session_id: string;
  role: ChatRole;
  content: string;
  metadata: Record<string, unknown>;
  created_at: string;
}
