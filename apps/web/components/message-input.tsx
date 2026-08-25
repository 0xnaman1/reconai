"use client";

import { useState } from "react";

export function MessageInput({
  onSend,
  disabled,
}: {
  onSend: (text: string) => void;
  disabled: boolean;
}) {
  const [value, setValue] = useState("");

  function submit(event: React.FormEvent) {
    event.preventDefault();
    const text = value.trim();
    if (!text || disabled) return;
    setValue("");
    onSend(text);
  }

  return (
    <form
      onSubmit={submit}
      className="sticky bottom-0 flex gap-2 bg-background/85 py-3 backdrop-blur"
    >
      <input
        value={value}
        onChange={(event) => setValue(event.target.value)}
        disabled={disabled}
        placeholder="Ask about the reconciliation…"
        aria-label="Message"
        className="field flex-1"
      />
      <button
        type="submit"
        disabled={disabled || !value.trim()}
        className="btn btn-primary"
      >
        Send
      </button>
    </form>
  );
}
