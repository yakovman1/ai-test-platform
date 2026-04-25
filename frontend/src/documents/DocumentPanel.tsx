import type { CSSProperties } from "react";

const documents = [
  { name: "Evaluation rubric.pdf", status: "Indexed" },
  { name: "Product brief.md", status: "Processing" },
];

export function DocumentPanel() {
  return (
    <section aria-labelledby="documents-heading" style={styles.section}>
      <div style={styles.header}>
        <h2 id="documents-heading">Documents</h2>
        <button type="button">Upload</button>
      </div>
      <p style={styles.helperText}>Attach source material for grounded RAG chats.</p>
      <ul style={styles.list}>
        {documents.map((document) => (
          <li key={document.name} style={styles.documentItem}>
            <span>{document.name}</span>
            <span style={styles.status}>{document.status}</span>
          </li>
        ))}
      </ul>
    </section>
  );
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
} satisfies Record<string, CSSProperties>;
