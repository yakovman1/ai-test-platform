from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievedChunk:
    document_name: str
    content: str


def build_no_context_response() -> str:
    return (
        "The uploaded documents do not contain enough context to answer this in RAG mode. "
        "Upload more relevant material or switch to normal chat."
    )


def build_rag_messages(
    question: str,
    style: str,
    chunks: list[RetrievedChunk],
) -> list[dict[str, str]]:
    context = "\n\n".join(f"Source: {chunk.document_name}\n{chunk.content}" for chunk in chunks)
    return [
        {
            "role": "system",
            "content": (
                "Answer using only the provided company document context. "
                f"Use the requested style: {style}."
            ),
        },
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion:\n{question}"},
    ]
