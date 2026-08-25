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
    <label
      className={`flex flex-1 flex-col gap-1.5 rounded-xl border border-dashed p-3.5 transition-colors ${
        disabled
          ? "border-border"
          : "cursor-pointer border-border-strong hover:border-accent"
      }`}
    >
      <span className="text-xs font-medium">{label}</span>
      <input
        type="file"
        accept="application/pdf"
        disabled={disabled}
        onChange={(event) => onPick(event.target.files?.[0] ?? null)}
        className="text-xs text-muted file:mr-2 file:cursor-pointer file:rounded-lg file:border file:border-border-strong file:bg-surface file:px-2.5 file:py-1 file:text-xs file:font-medium file:text-foreground"
      />
      {file && (
        <span className="truncate text-xs text-accent" title={file.name}>
          {file.name}
        </span>
      )}
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
    <div className="card flex flex-col gap-4 p-5">
      <div className="flex flex-col gap-1">
        <p className="text-sm font-medium">New reconciliation</p>
        <p className="text-xs text-muted">
          Text-based PDFs only. Scanned statements are not supported.
        </p>
      </div>

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
        className="btn btn-primary self-start"
      >
        {disabled ? "Uploading…" : "Reconcile"}
      </button>
    </div>
  );
}
