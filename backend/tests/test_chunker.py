from app.services.chunker import chunk_text


def test_chunk_text_splits_long_text_with_indexes() -> None:
    chunks = chunk_text("alpha " * 300, max_chars=200)

    assert len(chunks) > 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].content.startswith("alpha")
