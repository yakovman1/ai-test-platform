import { type ChangeEvent, type CSSProperties, useRef } from "react";

import type { DocumentSummary } from "../api/client";

type DocumentPanelProps = {
  documents: DocumentSummary[];
  isUploading: boolean;
  onUpload: (file: File) => void;
};

export function DocumentPanel({ documents, isUploading, onUpload }: DocumentPanelProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file) {
      onUpload(file);
      event.target.value = "";
    }
  }

  return (
    <section aria-labelledby="documents-heading" style={styles.section}>
      <div style={styles.header}>
        <h2 id="documents-heading">Documents</h2>
        <button
          disabled={isUploading}
          onClick={() => fileInputRef.current?.click()}
          type="button"
        >
          {isUploading ? "Uploading..." : "Upload"}
        </button>
        <input
          accept=".pdf,.docx,.txt,.md"
          aria-label="Document file"
          onChange={handleFileChange}
          ref={fileInputRef}
          style={styles.fileInput}
          type="file"
        />
      </div>
      <p style={styles.helperText}>Attach source material for grounded RAG chats.</p>
      {documents.length > 0 ? (
        <ul style={styles.list}>
          {documents.map((document) => (
            <li key={document.id} style={styles.documentItem}>
              <span>{document.filename}</span>
              <span style={styles.status}>{formatStatus(document)}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p style={styles.emptyText}>No documents uploaded yet.</p>
      )}
    </section>
  );
}

function formatStatus(document: DocumentSummary) {
  if (document.error_message) {
    return `${document.status}: ${document.error_message}`;
  }
  return document.status;
}

const styles = {
  section: {
    display: "grid",
    gap: "0.75rem",
  },
  header: {
    alignItems: "center",
    display: "flex",
    gap: "0.75rem",
    justifyContent: "space-between",
  },
  helperText: {
    color: "#526070",
    fontSize: "0.9rem",
    margin: 0,
  },
  list: {
    display: "grid",
    gap: "0.5rem",
    listStyle: "none",
    margin: 0,
    padding: 0,
  },
  documentItem: {
    background: "#f8fafc",
    border: "1px solid #dbe3ef",
    borderRadius: "10px",
    display: "grid",
    gap: "0.25rem",
    padding: "0.7rem",
  },
  status: {
    color: "#315a9b",
    fontSize: "0.82rem",
    fontWeight: 600,
  },
  emptyText: {
    color: "#526070",
    margin: 0,
  },
  fileInput: {
    display: "none",
  },
} satisfies Record<string, CSSProperties>;
