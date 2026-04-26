import { type CSSProperties, type FormEvent, useState } from "react";

import type { ChatMessage } from "../api/client";

export type ChatMode = "normal" | "rag";
export type ResponseStyle = "concise" | "detailed" | "expert";

type ChatPanelProps = {
  error: string | null;
  isSending: boolean;
  messages: ChatMessage[];
  mode: ChatMode;
  onModeChange: (mode: ChatMode) => void;
  onSend: (message: string) => Promise<void>;
  onStyleChange: (style: ResponseStyle) => void;
  style: ResponseStyle;
};

const welcomeMessage: ChatMessage = {
  id: 0,
  role: "assistant",
  content: "Welcome. Ask a question or switch to RAG to ground answers in uploaded documents.",
  source_summary: null,
};

export function ChatPanel({
  error,
  isSending,
  messages,
  mode,
  onModeChange,
  onSend,
  onStyleChange,
  style,
}: ChatPanelProps) {
  const [draftMessage, setDraftMessage] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const content = draftMessage.trim();
    if (!content) {
      return;
    }

    await onSend(content);
    setDraftMessage("");
  }

  const visibleMessages = messages.length > 0 ? messages : [welcomeMessage];

  return (
    <section aria-labelledby="chat-heading" style={styles.panel}>
      <header style={styles.header}>
        <div>
          <h2 id="chat-heading">Chat workspace</h2>
          <p style={styles.modelIndicator}>LLM: Gemma 4 via NVIDIA API</p>
        </div>
        <div aria-label="Chat mode" style={styles.buttonGroup}>
          <button
            aria-pressed={mode === "normal"}
            onClick={() => onModeChange("normal")}
            type="button"
          >
            Normal chat
          </button>
          <button
            aria-pressed={mode === "rag"}
            onClick={() => onModeChange("rag")}
            type="button"
          >
            RAG over documents
          </button>
        </div>
      </header>

      <div aria-label="Response style" style={styles.buttonGroup}>
        <button
          aria-pressed={style === "concise"}
          onClick={() => onStyleChange("concise")}
          type="button"
        >
          Concise
        </button>
        <button
          aria-pressed={style === "detailed"}
          onClick={() => onStyleChange("detailed")}
          type="button"
        >
          Detailed
        </button>
        <button
          aria-pressed={style === "expert"}
          onClick={() => onStyleChange("expert")}
          type="button"
        >
          Expert
        </button>
      </div>

      <div aria-label="Messages" role="log" style={styles.messages}>
        {visibleMessages.map((message) => (
          <article key={message.id} style={styles.message}>
            <strong>{message.role === "user" ? "You" : "Assistant"}</strong>
            <p>{message.content}</p>
            {message.source_summary ? (
              <small style={styles.sourceSummary}>Sources: {message.source_summary}</small>
            ) : null}
          </article>
        ))}
      </div>

      {error ? (
        <p role="alert" style={styles.error}>
          {error}
        </p>
      ) : null}

      <form aria-label="Send message" onSubmit={handleSubmit} style={styles.composer}>
        <label style={styles.messageField}>
          <span>Message</span>
          <textarea
            name="message"
            onChange={(event) => setDraftMessage(event.target.value)}
            rows={3}
            value={draftMessage}
          />
        </label>
        <button disabled={isSending} type="submit">
          {isSending ? "Sending..." : "Send"}
        </button>
      </form>
    </section>
  );
}

const styles = {
  panel: {
    background: "#ffffff",
    borderRadius: "18px",
    display: "grid",
    gap: "1rem",
    gridTemplateRows: "auto auto minmax(18rem, 1fr) auto",
    minHeight: "calc(100vh - 3rem)",
    padding: "1.5rem",
  },
  header: {
    alignItems: "start",
    display: "flex",
    gap: "1rem",
    justifyContent: "space-between",
  },
  modelIndicator: {
    color: "#44546a",
    margin: "0.25rem 0 0",
  },
  buttonGroup: {
    alignItems: "center",
    display: "flex",
    flexWrap: "wrap",
    gap: "0.5rem",
  },
  messages: {
    alignContent: "start",
    background: "#f8fafc",
    border: "1px solid #e1e7f0",
    borderRadius: "14px",
    display: "grid",
    gap: "0.75rem",
    minHeight: "18rem",
    padding: "1rem",
  },
  message: {
    background: "#ffffff",
    border: "1px solid #dde5ef",
    borderRadius: "12px",
    padding: "0.85rem",
  },
  sourceSummary: {
    color: "#526070",
    display: "block",
    marginTop: "0.5rem",
  },
  error: {
    color: "#b42318",
    margin: 0,
  },
  composer: {
    alignItems: "end",
    display: "grid",
    gap: "0.75rem",
    gridTemplateColumns: "1fr auto",
  },
  messageField: {
    display: "grid",
    gap: "0.35rem",
  },
} satisfies Record<string, CSSProperties>;
