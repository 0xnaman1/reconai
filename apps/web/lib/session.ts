/** Remembers the chat session across reloads.
 *
 * The conversation itself lives in the backend; only its id is kept here, so a
 * reload resumes the same transcript rather than starting a new one.
 */

const STORAGE_KEY = "recon-ai.chat-session-id";

export function readStoredSessionId(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(STORAGE_KEY);
}

export function storeSessionId(sessionId: string): void {
  window.localStorage.setItem(STORAGE_KEY, sessionId);
}

export function clearStoredSessionId(): void {
  window.localStorage.removeItem(STORAGE_KEY);
}
