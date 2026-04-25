from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TextChunk:
    chunk_index: int
    content: str
    source_locator: str | None = None


def chunk_text(text: str, max_chars: int = 1200) -> list[TextChunk]:
    if max_chars < 1:
        raise ValueError("max_chars must be positive")

    words = text.split()
    if not words:
        return []

    chunks: list[TextChunk] = []
    current_words: list[str] = []
    current_length = 0

    for word in words:
        projected_length = len(word) if not current_words else current_length + 1 + len(word)
        if current_words and projected_length > max_chars:
            chunks.append(TextChunk(chunk_index=len(chunks), content=" ".join(current_words)))
            current_words = [word]
            current_length = len(word)
            continue

        current_words.append(word)
        current_length = projected_length

    if current_words:
        chunks.append(TextChunk(chunk_index=len(chunks), content=" ".join(current_words)))

    return chunks
