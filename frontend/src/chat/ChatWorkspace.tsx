import { type CSSProperties, useEffect, useState } from "react";

import {
  type ChatMessage,
  type ChatResponse,
  type ChatSession,
  type DocumentSummary,
  getJson,
  postJson,
  uploadFile,
} from "../api/client";
import { DocumentPanel } from "../documents/DocumentPanel";
import { type ChatMode, ChatPanel, type ResponseStyle } from "./ChatPanel";

export function ChatWorkspace() {
  const [chatSessions, setChatSessions] = useState<ChatSession[]>([]);
  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isLoadingWorkspace, setIsLoadingWorkspace] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [mode, setMode] = useState<ChatMode>("normal");
  const [selectedSessionId, setSelectedSessionId] = useState<number | null>(null);
  const [style, setStyle] = useState<ResponseStyle>("concise");

  useEffect(() => {
    void loadWorkspace();
  }, []);

  async function loadWorkspace() {
    setIsLoadingWorkspace(true);
    setError(null);

    try {
      const [sessions, loadedDocuments] = await Promise.all([
        getJson<ChatSession[]>("/chats"),
        getJson<DocumentSummary[]>("/documents"),
      ]);
      setChatSessions(sessions);
      setDocuments(loadedDocuments);

      if (sessions[0]) {
        await selectChat(sessions[0].id);
      } else {
        setMessages([]);
        setSelectedSessionId(null);
      }
    } catch {
      setError("Unable to load workspace data. Please sign in again if the session expired.");
    } finally {
      setIsLoadingWorkspace(false);
    }
  }

  async function createChat() {
    setError(null);
    try {
      const session = await postJson<ChatSession>("/chats", {});
      setChatSessions((currentSessions) => [session, ...currentSessions]);
      setSelectedSessionId(session.id);
      setMessages([]);
    } catch {
      setError("Unable to create a new chat.");
    }
  }

  async function selectChat(sessionId: number) {
    setError(null);
    setSelectedSessionId(sessionId);
    try {
      setMessages(await getJson<ChatMessage[]>(`/chats/${sessionId}/messages`));
    } catch {
      setError("Unable to load chat messages.");
    }
  }

  async function sendMessage(message: string) {
    setError(null);
    setIsSending(true);

    const optimisticMessage: ChatMessage = {
      id: -Date.now(),
      role: "user",
      content: message,
      source_summary: null,
    };

    try {
      let sessionId = selectedSessionId;
      if (sessionId === null) {
        const session = await postJson<ChatSession>("/chats", {});
        sessionId = session.id;
        setSelectedSessionId(session.id);
        setChatSessions((currentSessions) => [session, ...currentSessions]);
      }

      setMessages((currentMessages) => [...currentMessages, optimisticMessage]);
      const response = await postJson<ChatResponse>(`/chats/${sessionId}/messages`, {
        message,
        mode,
        style,
      });
      setMessages((currentMessages) => [...currentMessages, response.message]);
    } catch {
      setError("Chat response failed. Please try again.");
    } finally {
      setIsSending(false);
    }
  }

  async function handleUpload(file: File) {
    setIsUploading(true);
    setError(null);
    try {
      await uploadFile<DocumentSummary>("/documents", file);
      setDocuments(await getJson<DocumentSummary[]>("/documents"));
    } catch {
      setError("Document upload failed.");
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <main style={styles.workspace}>
      <aside aria-label="Workspace navigation" style={styles.sidebar}>
        <h1>Company AI Test Lab</h1>
        <button onClick={() => void createChat()} type="button">
          New chat
        </button>

        <section aria-labelledby="history-heading" style={styles.sidebarSection}>
          <h2 id="history-heading">Chat history</h2>
          {chatSessions.length > 0 ? (
            <ul style={styles.historyList}>
              {chatSessions.map((chat) => (
                <li key={chat.id}>
                  <button
                    aria-pressed={selectedSessionId === chat.id}
                    onClick={() => void selectChat(chat.id)}
                    style={styles.historyButton}
                    type="button"
                  >
                    {chat.title}
                  </button>
                </li>
              ))}
            </ul>
          ) : (
            <p style={styles.emptyText}>
              {isLoadingWorkspace ? "Loading chats..." : "No chats yet."}
            </p>
          )}
        </section>

        <DocumentPanel documents={documents} isUploading={isUploading} onUpload={handleUpload} />
      </aside>

      <ChatPanel
        error={error}
        isSending={isSending}
        messages={messages}
        mode={mode}
        onModeChange={setMode}
        onSend={sendMessage}
        onStyleChange={setStyle}
        style={style}
      />
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
  emptyText: {
    color: "#526070",
    margin: 0,
  },
} satisfies Record<string, CSSProperties>;
