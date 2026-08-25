/** Client for the Recon AI backend.
 *
 * Every call goes through `request`, so error handling and the base URL are
 * defined once. Errors surface as ApiError carrying the backend's own detail
 * message, which is what the UI shows the user.
 */

import type {
  ChatMessage,
  ChatSession,
  Match,
  MatchStatus,
  MatchSuggestion,
  ReconciliationDetail,
  Transaction,
} from "./types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, init);
  } catch {
    // fetch only rejects when the request never reached the server.
    throw new ApiError(`Cannot reach the API at ${API_BASE_URL}`, 0);
  }

  if (!response.ok) {
    const detail = await response
      .json()
      .then((body) => body?.detail)
      .catch(() => null);
    throw new ApiError(
      detail ?? `Request failed with status ${response.status}`,
      response.status,
    );
  }

  return response.json() as Promise<T>;
}

function json(body: unknown): RequestInit {
  return {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  };
}

export async function checkHealth(): Promise<boolean> {
  try {
    await request<{ status: string }>("/health");
    return true;
  } catch {
    return false;
  }
}

export function createReconciliation(
  bankPdf: File,
  ledgerPdf: File,
): Promise<{ job_id: string; status: string }> {
  const form = new FormData();
  form.append("bank_pdf", bankPdf);
  form.append("ledger_pdf", ledgerPdf);
  return request("/reconciliations", { method: "POST", body: form });
}

export function getReconciliation(jobId: string): Promise<ReconciliationDetail> {
  return request(`/reconciliations/${jobId}`);
}

export function listTransactions(jobId: string): Promise<Transaction[]> {
  return request(`/reconciliations/${jobId}/transactions`);
}

export function listMatches(
  jobId: string,
  status?: MatchStatus,
): Promise<Match[]> {
  const query = status ? `?status=${status}` : "";
  return request(`/reconciliations/${jobId}/matches${query}`);
}

export function approveMatch(matchId: string): Promise<Match> {
  return request(`/matches/${matchId}/approve`, { method: "POST" });
}

export function rejectMatch(matchId: string): Promise<Match> {
  return request(`/matches/${matchId}/reject`, { method: "POST" });
}

export function listMatchSuggestions(
  jobId: string,
): Promise<MatchSuggestion[]> {
  return request(`/reconciliations/${jobId}/suggestions`);
}

export function createManualMatch(
  jobId: string,
  bankTransactionId: string,
  ledgerTransactionId: string,
): Promise<Match> {
  return request(
    `/reconciliations/${jobId}/manual-match`,
    json({
      bank_transaction_id: bankTransactionId,
      ledger_transaction_id: ledgerTransactionId,
    }),
  );
}

export function createChatSession(activeJobId?: string): Promise<ChatSession> {
  return request("/chat/sessions", json({ active_job_id: activeJobId ?? null }));
}

export function getChatSession(sessionId: string): Promise<ChatSession> {
  return request(`/chat/sessions/${sessionId}`);
}

export function listChatMessages(sessionId: string): Promise<ChatMessage[]> {
  return request(`/chat/sessions/${sessionId}/messages`);
}

/** Send a user message and return every message the agent's turn appended. */
export function sendChatMessage(
  sessionId: string,
  content: string,
): Promise<ChatMessage[]> {
  return request(
    `/chat/sessions/${sessionId}/messages`,
    json({ role: "user", content, metadata: {} }),
  );
}
