"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ChatTranscript } from "@/components/chat-transcript";
import { JobList } from "@/components/job-list";
import { JobPanel } from "@/components/job-panel";
import { MessageInput } from "@/components/message-input";
import { StatementUpload } from "@/components/statement-upload";
import {
  ApiError,
  createChatSession,
  createReconciliation,
  getChatSession,
  listChatMessages,
  listReconciliations,
  sendChatMessage,
  setActiveJob,
} from "@/lib/api";
import { TERMINAL_STATUSES } from "@/lib/format";
import {
  clearStoredSessionId,
  readStoredSessionId,
  storeSessionId,
} from "@/lib/session";
import type { ChatMessage, ReconciliationJob } from "@/lib/types";

const POLL_INTERVAL_MS = 2000;

const SUGGESTIONS = [
  "How did it go?",
  "What's still unmatched?",
  "What needs my review?",
];

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return error.message;
  return "Something went wrong. Please try again.";
}

export function Chat() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [jobs, setJobs] = useState<ReconciliationJob[]>([]);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [thinking, setThinking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  // A completed job should prompt the agent once, not on every poll tick.
  const announcedJobs = useRef<Set<string>>(new Set());

  const activeJob = jobs.find((job) => job.id === activeJobId) ?? null;
  const processing = jobs.some(
    (job) => !TERMINAL_STATUSES.includes(job.status),
  );

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

  // Resume the stored conversation, or start a new one, and load past jobs.
  useEffect(() => {
    let cancelled = false;

    async function start() {
      try {
        const stored = readStoredSessionId();
        let session = null;

        if (stored) {
          try {
            session = await getChatSession(stored);
            const history = await listChatMessages(stored);
            if (cancelled) return;
            setMessages(history);
          } catch (caught) {
            // The backend no longer has this session, so the stored id is
            // dead and keeping it would strand the user on an error with no
            // way to type. Forget it and start a fresh conversation instead.
            if (!(caught instanceof ApiError) || caught.status !== 404) {
              throw caught;
            }
            clearStoredSessionId();
          }
        }

        if (session === null) {
          session = await createChatSession();
          if (cancelled) return;
          storeSessionId(session.id);
        }

        const existing = await listReconciliations();
        if (cancelled) return;

        setSessionId(session.id);
        setJobs(existing);
        // A job the conversation already covered has been announced already.
        existing
          .filter((job) => job.status === "completed")
          .forEach((job) => announcedJobs.current.add(job.id));

        if (session.active_job_id) setActiveJobId(session.active_job_id);
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

  // Follow every job the worker is still processing. Reloading the whole list
  // keeps one poll covering any number of running jobs.
  useEffect(() => {
    if (!processing) return;

    let cancelled = false;
    const timer = setInterval(async () => {
      try {
        const latest = await listReconciliations();
        if (!cancelled) setJobs(latest);
      } catch (caught) {
        if (!cancelled) setError(errorMessage(caught));
      }
    }, POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [processing]);

  // Once the selected job finishes, let the agent report on it.
  useEffect(() => {
    if (activeJob?.status !== "completed") return;
    if (announcedJobs.current.has(activeJob.id)) return;
    announcedJobs.current.add(activeJob.id);
    void send("The reconciliation finished. How did it go?");
  }, [activeJob, send]);

  const selectJob = useCallback(
    async (jobId: string) => {
      setActiveJobId(jobId);
      if (!sessionId) return;
      try {
        // Binding the job to the session is what lets the user ask "what's
        // unmatched?" without repeating an id the agent would otherwise need.
        await setActiveJob(sessionId, jobId);
      } catch (caught) {
        setError(errorMessage(caught));
      }
    },
    [sessionId],
  );

  async function upload(bankPdf: File, ledgerPdf: File) {
    setError(null);
    setUploading(true);
    try {
      const created = await createReconciliation(bankPdf, ledgerPdf);
      setJobs(await listReconciliations());
      await selectJob(created.job_id);
    } catch (caught) {
      setError(errorMessage(caught));
    } finally {
      setUploading(false);
    }
  }

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

  const empty = messages.length === 0;

  return (
    <div className="flex flex-1 flex-col gap-6">
      <StatementUpload onSubmit={upload} disabled={uploading || !sessionId} />

      <JobList
        jobs={jobs}
        activeJobId={activeJobId}
        onSelect={(jobId) => void selectJob(jobId)}
      />

      {error && (
        <div
          role="alert"
          className="rounded-xl border border-danger/30 bg-danger/5 px-4 py-3 text-sm text-danger"
        >
          {error}
        </div>
      )}

      {activeJob && (
        <JobPanel
          key={activeJob.id}
          jobId={activeJob.id}
          status={activeJob.status}
        />
      )}

      <div className="flex flex-1 flex-col gap-3">
        {empty ? (
          <div className="flex flex-col gap-3 py-2">
            <p className="text-sm leading-relaxed text-muted">
              Upload a bank statement and a general ledger PDF, and I&apos;ll
              reconcile them. I match what I can defend, and ask you about
              anything I&apos;m unsure of.
            </p>
            {activeJob && (
              <div className="flex flex-wrap gap-2">
                {SUGGESTIONS.map((suggestion) => (
                  <button
                    key={suggestion}
                    type="button"
                    onClick={() => void send(suggestion)}
                    disabled={thinking}
                    className="btn btn-ghost"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            )}
          </div>
        ) : (
          <ChatTranscript messages={messages} pending={thinking} />
        )}
      </div>

      <MessageInput
        onSend={send}
        disabled={thinking || uploading || !sessionId}
      />
    </div>
  );
}
