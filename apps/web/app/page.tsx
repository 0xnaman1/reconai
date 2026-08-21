import { API_BASE_URL, checkHealth } from "@/lib/api";

export const dynamic = "force-dynamic";

export default async function HomePage() {
  const online = await checkHealth();

  return (
    <div className="flex flex-1 flex-col gap-8">
      <section className="flex flex-col gap-3">
        <h1 className="text-2xl font-semibold tracking-tight">
          Reconcile a bank statement against your ledger
        </h1>
        <p className="max-w-2xl text-muted">
          Upload both PDFs and the transactions are extracted, normalized, and
          matched. Confident pairs are matched automatically; anything uncertain
          is held for you to approve or reject in chat.
        </p>
      </section>

      <section className="rounded-lg border border-border bg-surface p-4">
        <div className="flex items-center gap-2 text-sm">
          <span
            aria-hidden
            className={`inline-block size-2 rounded-full ${
              online ? "bg-green-500" : "bg-red-500"
            }`}
          />
          <span className="font-medium">
            {online ? "Connected to the API" : "Cannot reach the API"}
          </span>
          <code className="text-muted">{API_BASE_URL}</code>
        </div>
        {!online && (
          <p className="mt-2 text-sm text-muted">
            Start the backend with{" "}
            <code className="font-mono">
              uv run --package recon-ai-api uvicorn recon_ai_api.main:app --reload
            </code>
            , then reload this page.
          </p>
        )}
      </section>

      <section className="rounded-lg border border-dashed border-border p-6 text-sm text-muted">
        The chat interface arrives in the next phase.
      </section>
    </div>
  );
}
