import httpx

from app.core.config import get_settings
from app.services.nvidia_client import NVIDIA_BASE_URL, NvidiaClient
from app.services.rag import RetrievedChunk, build_no_context_response, build_rag_messages


def test_rag_no_context_response_is_grounded() -> None:
    response = build_no_context_response()

    assert "uploaded documents do not contain enough context" in response.lower()
    assert "normal chat" in response.lower()


def test_build_rag_messages_uses_only_document_context() -> None:
    messages = build_rag_messages(
        question="What is the travel policy?",
        style="concise",
        chunks=[RetrievedChunk(document_name="handbook.md", content="Travel requires approval.")],
    )

    assert messages == [
        {
            "role": "system",
            "content": (
                "Answer using only the provided company document context. "
                "Use the requested style: concise."
            ),
        },
        {
            "role": "user",
            "content": (
                "Context:\nSource: handbook.md\nTravel requires approval."
                "\n\nQuestion:\nWhat is the travel policy?"
            ),
        },
    ]


def test_nvidia_client_sends_embedding_request(monkeypatch) -> None:
    _configure_nvidia_settings(monkeypatch)
    requests: list[httpx.Request] = []
    httpx_client = httpx.Client

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"data": [{"embedding": [0.1, 0.2]}]})

    monkeypatch.setattr(
        "app.services.nvidia_client.httpx.Client",
        lambda **kwargs: httpx_client(transport=httpx.MockTransport(handler), **kwargs),
    )

    embedding = NvidiaClient().embed("hello")

    assert embedding == [0.1, 0.2]
    assert requests[0].url == httpx.URL(f"{NVIDIA_BASE_URL}/embeddings")
    assert requests[0].headers["authorization"] == "Bearer nvapi-test"
    assert requests[0].read() == b'{"model":"embed","input":"hello"}'


def test_nvidia_client_sends_chat_request(monkeypatch) -> None:
    _configure_nvidia_settings(monkeypatch)
    requests: list[httpx.Request] = []
    httpx_client = httpx.Client

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={"choices": [{"message": {"content": "answer"}}]})

    monkeypatch.setattr(
        "app.services.nvidia_client.httpx.Client",
        lambda **kwargs: httpx_client(transport=httpx.MockTransport(handler), **kwargs),
    )

    answer = NvidiaClient().chat([{"role": "user", "content": "hi"}])

    assert answer == "answer"
    assert requests[0].url == httpx.URL(f"{NVIDIA_BASE_URL}/chat/completions")
    assert requests[0].headers["authorization"] == "Bearer nvapi-test"
    assert requests[0].read() == b'{"model":"gemma","messages":[{"role":"user","content":"hi"}]}'


def _configure_nvidia_settings(monkeypatch) -> None:
    monkeypatch.setenv("APP_DOMAIN", "ai.example.com")
    monkeypatch.setenv("LETSENCRYPT_EMAIL", "admin@example.com")
    monkeypatch.setenv("DATABASE_URL", "sqlite://")
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    monkeypatch.setenv("INITIAL_USER_USERNAME", "tester")
    monkeypatch.setenv("INITIAL_USER_PASSWORD", "correct-password")
    monkeypatch.setenv("NVIDIA_API_KEY", "nvapi-test")
    monkeypatch.setenv("NVIDIA_EMBEDDING_MODEL", "embed")
    monkeypatch.setenv("NVIDIA_LLM_MODEL", "gemma")
    get_settings.cache_clear()
