const API_BASE = "/api";

export type ChatSession = {
  id: number;
  title: string;
};

export type ChatMessage = {
  id: number;
  role: "user" | "assistant";
  content: string;
  source_summary: string | null;
};

export type ChatResponse = {
  message: ChatMessage;
};

export type DocumentSummary = {
  id: number;
  filename: string;
  status: string;
  error_message: string | null;
};

export async function getJson<TResponse>(path: string): Promise<TResponse> {
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(await response.text());
  }

  return response.json() as Promise<TResponse>;
}

export async function postJson<TResponse>(
  path: string,
  body: unknown,
): Promise<TResponse> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    throw new Error(await response.text());
  }

  return response.json() as Promise<TResponse>;
}

export async function uploadFile<TResponse>(path: string, file: File): Promise<TResponse> {
  const body = new FormData();
  body.append("file", file);

  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    credentials: "include",
    body,
  });

  if (!response.ok) {
    throw new Error(await response.text());
  }

  return response.json() as Promise<TResponse>;
}
