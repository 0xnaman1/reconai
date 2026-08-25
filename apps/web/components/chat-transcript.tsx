"use client";

import { useEffect, useRef } from "react";
import type { ChatMessage } from "@/lib/types";

/** A tool call the agent made, recorded on an assistant message. */
interface ToolCall {
  function?: { name?: string };
}

function toolNames(message: ChatMessage): string[] {
  const calls = message.metadata?.tool_calls as ToolCall[] | undefined;
  return calls?.map((call) => call.function?.name ?? "tool") ?? [];
}

function Bubble({ message }: { message: ChatMessage }) {
  const fromUser = message.role === "user";
  return (
    <div className={`flex ${fromUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
          fromUser
            ? "rounded-br-md bg-accent text-accent-foreground"
            : "card rounded-bl-md"
        }`}
      >
        {message.content}
      </div>
    </div>
  );
}

/** What the agent did, shown quietly: useful to see, not meant to be read. */
function ToolTrace({ tools }: { tools: string[] }) {
  return (
    <div className="flex flex-wrap items-center gap-1.5 px-1">
      <span className="text-xs text-muted">Looked up</span>
      {tools.map((tool, index) => (
        <span key={`${tool}-${index}`} className="badge badge-neutral font-mono">
          {tool}
        </span>
      ))}
    </div>
  );
}

export function ChatTranscript({
  messages,
  pending,
}: {
  messages: ChatMessage[];
  pending: boolean;
}) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, pending]);

  return (
    <div className="flex flex-col gap-3">
      {messages.map((message) => {
        // Tool results are context for the model, not something to read.
        if (message.role === "tool" || message.role === "system") return null;

        const tools = toolNames(message);
        if (tools.length > 0) {
          return <ToolTrace key={message.id} tools={tools} />;
        }

        if (!message.content.trim()) return null;
        return <Bubble key={message.id} message={message} />;
      })}

      {pending && (
        <p className="px-1 text-xs text-muted" aria-live="polite">
          Thinking…
        </p>
      )}
      <div ref={endRef} />
    </div>
  );
}
