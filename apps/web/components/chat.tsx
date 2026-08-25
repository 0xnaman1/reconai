"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ChatTranscript } from "@/components/chat-transcript";
import { MessageInput } from "@/components/message-input";
import { ReviewPanel } from "@/components/review-panel";
import { StatementUpload } from "@/components/statement-upload";
import {
  ApiError,
  createChatSession,
  createReconciliation,
  getChatSession,
  getReconciliation,
  listChatMessages,
  sendChatMessage,
} from "@/lib/api";
import { TERMINAL_STATUSES, formatJobStatus } from "@/lib/format";
import { readStoredSessionId, storeSessionId } from "@/lib/session";
import type { ChatMessage, JobStatus } from "@/lib/types";

const POLL_INTERVAL_MS = 2000;

const WELCOME =
  "Upload a bank statement and a general ledger PDF, and I'll reconcile them. " +
  "I'll match what I can confidently, and ask you about anything I'm unsure of.";

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  return "Something went wrong. Please try again.";
}

export function Chat() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [jobId, setJobId] = useState<string | null>(null);
  const [jobStatus, setJobStatus] = useState<JobStatus | null>(null);
  const [uploading, setUploading] = useState(false);
  const [thinking, setThinking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  // A completed job should prompt the agent once, not on every poll tick.
  const announcedJob = useRef<string | null>(null);

  // Bumped after a decision so the panel reloads its counts.
  const [reviewKey, setReviewKey] = useState(0);
  const bumpReview = useCallback(() => setReviewKey((n) => n + 1), []);

  const send = useCallback(
    async (text: string) => {
      if (!sessionId) return;
      setError(null);
      setThinking(true);

      const optimistic: ChatMessage = {
        id: `pending-${Date.now()}`,
        session_id: sessionId,
        role: "user",
        content: text,
        metadata: {},
        created_at: new Date().toISOString(),
      };
      setMessages((current) => [...current, optimistic]);

      try {
        const appended = await sendChatMessage(sessionId, text);
        // The server returns the whole turn, including its own copy of the
        // user message, so drop the placeholder rather than showing it twice.
        setMessages((current) => [
          ...current.filter((message) => message.id !== optimistic.id),
          ...appended,
        ]);
      } catch (caught) {
        setMessages((current) =>
          current.filter((message) => message.id !== optimistic.id),
        );
        setError(errorMessage(caught));
      } finally {
        setThinking(false);
      }
    },
    [sessionId],
  );

  // Resume the stored conversation, or start a new one.
  useEffect(() => {
    let cancelled = false;

    async function start() {
      try {
        const stored = readStoredSessionId();
        if (stored) {
          const session = await getChatSession(stored);
          const history = await listChatMessages(stored);
          if (cancelled) return;
          setSessionId(session.id);
          setMessages(history);
          if (session.active_job_id) {
            setJobId(session.active_job_id);
            announcedJob.current = session.active_job_id;
          }
        } else {
          const session = await createChatSession();
          if (cancelled) return;
          storeSessionId(session.id);
          setSessionId(session.id);
        }
      } catch (caught) {
        if (!cancelled) setError(errorMessage(caught));
      } finally {
        if (!cancelled) setReady(true);
      }
    }

    void start();
    return () => {
      cancelled = true;
    };
  }, []);

  // Follow a job while the worker is still processing it.
  useEffect(() => {
    if (!jobId) return;
    if (jobStatus && TERMINAL_STATUSES.includes(jobStatus)) return;

    let cancelled = false;
    const timer = setInterval(async () => {
      try {
        const detail = await getReconciliation(jobId);
        if (cancelled) return;
        setJobStatus(detail.job.status);
        if (detail.job.status === "failed") {
          setError(detail.job.error_message ?? "The reconciliation failed.");
        }
      } catch (caught) {
        if (!cancelled) setError(errorMessage(caught));
      }
    }, POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [jobId, jobStatus]);

  // Once processing finishes, let the agent report on it.
  useEffect(() => {
    if (!jobId || jobStatus !== "completed") return;
    if (announcedJob.current === jobId) return;
    announcedJob.current = jobId;
    void send(
      `I've uploaded the statements. The reconciliation job id is ${jobId}. ` +
        `How did it go?`,
    );
  }, [jobId, jobStatus, send]);

  async function upload(bankPdf: File, ledgerPdf: File) {
    setError(null);
    setUploading(true);
    try {
      const created = await createReconciliation(bankPdf, ledgerPdf);
      setJobId(created.job_id);
      setJobStatus(created.status as JobStatus);
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setUploading(false);
    }
  }

  const processing =
    jobStatus !== null && !TERMINAL_STATUSES.includes(jobStatus);
  const busy = thinking || uploading || processing;

  // The session id comes from localStorage and the transcript from an effect,
  // so nothing interactive exists until the browser has run. Rendering the
  // controls before then would make the server's HTML disagree with the
  // client's first render.
  if (!ready) {
    return (
      <p className="text-sm text-muted" aria-live="polite">
        Starting a session…
      </p>
    );
  }

  return (
    <div className="flex flex-1 flex-col gap-4">
      {!jobId && (
        <StatementUpload onSubmit={upload} disabled={uploading || !sessionId} />
      )}

      {processing && jobStatus && (
        <p className="rounded-lg border border-border bg-surface px-4 py-2.5 text-sm">
          {formatJobStatus(jobStatus)}…{" "}
          <span className="text-muted">This usually takes under a minute.</span>
        </p>
      )}

      {error && (
        <div
          role="alert"
          className="rounded-lg border border-red-500/40 bg-red-500/5 px-4 py-2.5 text-sm"
        >
          {error}
        </div>
      )}

      {jobId && jobStatus === "completed" && (
        <ReviewPanel key={reviewKey} jobId={jobId} onReviewed={bumpReview} />
      )}

      <div className="flex-1">
        {messages.length === 0 ? (
          <p className="text-sm text-muted">{WELCOME}</p>
        ) : (
          <ChatTranscript messages={messages} pending={thinking} />
        )}
      </div>

      <MessageInput onSend={send} disabled={busy || !sessionId} />
    </div>
  );
}
