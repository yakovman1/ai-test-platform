import type { CSSProperties } from "react";

import { DocumentPanel } from "../documents/DocumentPanel";
import { ChatPanel } from "./ChatPanel";

const chatHistory = ["Onboarding answers", "Policy review", "Evaluation prompts"];

export function ChatWorkspace() {
  return (
    <main style={styles.workspace}>
      <aside aria-label="Workspace navigation" style={styles.sidebar}>
        <h1>Company AI Test Lab</h1>
        <button type="button">New chat</button>

        <section aria-labelledby="history-heading" style={styles.sidebarSection}>
          <h2 id="history-heading">Chat history</h2>
          <ul style={styles.historyList}>
            {chatHistory.map((chat) => (
              <li key={chat}>
                <button style={styles.historyButton} type="button">
                  {chat}
                </button>
              </li>
            ))}
          </ul>
        </section>

        <DocumentPanel />
      </aside>

      <ChatPanel />
    </main>
  );
}

const styles = {
  workspace: {
    background: "#edf2f7",
    display: "grid",
    gap: "1.5rem",
    gridTemplateColumns: "320px 1fr",
    minHeight: "100vh",
    padding: "1.5rem",
  },
  sidebar: {
    background: "#ffffff",
    borderRadius: "18px",
    display: "grid",
    gap: "1.5rem",
    alignContent: "start",
    padding: "1.25rem",
  },
  sidebarSection: {
    display: "grid",
    gap: "0.75rem",
  },
  historyList: {
    display: "grid",
    gap: "0.5rem",
    listStyle: "none",
    margin: 0,
    padding: 0,
  },
  historyButton: {
    textAlign: "left",
    width: "100%",
  },
} satisfies Record<string, CSSProperties>;
