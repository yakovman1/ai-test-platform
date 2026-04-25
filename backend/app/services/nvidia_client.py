from __future__ import annotations

import httpx

from app.core.config import get_settings

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"


class NvidiaClient:
    def __init__(self) -> None:
        settings = get_settings()
        self._api_key = settings.nvidia_api_key
        self._embedding_model = settings.nvidia_embedding_model
        self._llm_model = settings.nvidia_llm_model

    def embed(self, text: str) -> list[float]:
        response = self._post("/embeddings", {"model": self._embedding_model, "input": text})
        return list(response["data"][0]["embedding"])

    def chat(self, messages: list[dict[str, str]]) -> str:
        response = self._post(
            "/chat/completions",
            {"model": self._llm_model, "messages": messages},
        )
        return str(response["choices"][0]["message"]["content"])

    def _post(self, path: str, payload: dict[str, object]) -> dict:
        headers = {"Authorization": f"Bearer {self._api_key}"}
        with httpx.Client(base_url=NVIDIA_BASE_URL, headers=headers, timeout=30.0) as client:
            response = client.post(path, json=payload)
            response.raise_for_status()
            return response.json()
