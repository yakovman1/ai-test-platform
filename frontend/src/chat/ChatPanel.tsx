import { type CSSProperties, type FormEvent, useState } from "react";

const messages = [
  {
    author: "Assistant",
    text: "Welcome. Ask a question or switch to RAG to ground answers in uploaded documents.",
  },
];

export function ChatPanel() {
  const [draftMessage, setDraftMessage] = useState("");
  const [visibleMessages, setVisibleMessages] = useState(messages);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const content = draftMessage.trim();
    if (!content) {
      return;
    }

    setVisibleMessages((currentMessages) => [
      ...currentMessages,
      { author: "You", text: content },
      {
        author: "Assistant",
        text: "Message received. API chat integration is ready on the backend and will be wired into this composer next.",
      },
    ]);
    setDraftMessage("");
  }

  return (
    <section aria-labelledby="chat-heading" style={styles.panel}>
      <header style={styles.header}>
        <div>
          <h2 id="chat-heading">Chat workspace</h2>
          <p style={styles.modelIndicator}>LLM: Gemma 4 via NVIDIA API</p>
        </div>
        <div aria-label="Chat mode" style={styles.buttonGroup}>
          <button type="button">Normal chat</button>
          <button type="button">RAG over documents</button>
        </div>
      </header>

      <div aria-label="Response style" style={styles.buttonGroup}>
        <button type="button">Concise</button>
        <button type="button">Detailed</button>
        <button type="button">Expert</button>
      </div>

      <div aria-label="Messages" role="log" style={styles.messages}>
        {visibleMessages.map((message, index) => (
          <article key={`${message.author}-${index}-${message.text}`} style={styles.message}>
            <strong>{message.author}</strong>
            <p>{message.text}</p>
          </article>
        ))}
      </div>

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
        <button type="submit">Send</button>
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
