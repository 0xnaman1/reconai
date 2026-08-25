"use client";

import { useState } from "react";

function FilePicker({
  label,
  file,
  onPick,
  disabled,
}: {
  label: string;
  file: File | null;
  onPick: (file: File | null) => void;
  disabled: boolean;
}) {
  return (
    <label className="flex flex-1 cursor-pointer flex-col gap-1">
      <span className="text-xs font-medium">{label}</span>
      <input
        type="file"
        accept="application/pdf"
        disabled={disabled}
        onChange={(event) => onPick(event.target.files?.[0] ?? null)}
        className="text-xs text-muted file:mr-2 file:rounded-md file:border file:border-border file:bg-background file:px-2 file:py-1 file:text-xs file:text-foreground"
      />
      {file && <span className="truncate text-xs text-muted">{file.name}</span>}
    </label>
  );
}

export function StatementUpload({
  onSubmit,
  disabled,
}: {
  onSubmit: (bankPdf: File, ledgerPdf: File) => void;
  disabled: boolean;
}) {
  const [bankPdf, setBankPdf] = useState<File | null>(null);
  const [ledgerPdf, setLedgerPdf] = useState<File | null>(null);

  const ready = bankPdf !== null && ledgerPdf !== null;

  return (
    <div className="flex flex-col gap-3 rounded-lg border border-border bg-surface p-4">
      <p className="text-sm font-medium">New reconciliation</p>
      <div className="flex flex-col gap-3 sm:flex-row">
        <FilePicker
          label="Bank statement PDF"
          file={bankPdf}
          onPick={setBankPdf}
          disabled={disabled}
        />
        <FilePicker
          label="General ledger PDF"
          file={ledgerPdf}
          onPick={setLedgerPdf}
          disabled={disabled}
        />
      </div>
      <button
        type="button"
        disabled={!ready || disabled}
        onClick={() => ready && onSubmit(bankPdf, ledgerPdf)}
        className="self-start rounded-lg bg-foreground px-4 py-2 text-sm font-medium text-background disabled:opacity-40"
      >
        {disabled ? "Uploading…" : "Reconcile"}
      </button>
      <p className="text-xs text-muted">
        Text-based PDFs only. Scanned statements are not supported.
      </p>
    </div>
  );
}
