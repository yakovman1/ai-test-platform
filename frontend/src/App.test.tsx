import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { App } from "./App";

describe("App", () => {
  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("shows the login screen first", () => {
    render(<App />);

    expect(screen.getByRole("heading", { name: "Sign in" })).toBeInTheDocument();
  });

  it("shows the workspace after a successful login", async () => {
    const fetchMock = createFetchMock();
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    fireEvent.change(screen.getByLabelText("Username"), {
      target: { value: "tester" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "secret" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

    expect(fetchMock).toHaveBeenCalledWith("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ username: "tester", password: "secret" }),
    });

    await waitFor(() => {
      expect(screen.getByText("Company AI Test Lab")).toBeInTheDocument();
    });

    expect(screen.getByRole("region", { name: "Documents" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Chat history" })).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Real backend chat" })).toBeInTheDocument();
    });
    expect(screen.queryByRole("button", { name: "Onboarding answers" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Normal chat" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "RAG over documents" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Concise" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Detailed" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Expert" })).toBeInTheDocument();
    expect(screen.getByText("LLM: Gemma 4 via NVIDIA API")).toBeInTheDocument();
    expect(screen.getByLabelText("Message")).toBeInTheDocument();
  });

  it("keeps the workspace mounted when the chat form is submitted", async () => {
    vi.stubGlobal("fetch", createFetchMock());

    render(<App />);

    fireEvent.change(screen.getByLabelText("Username"), {
      target: { value: "tester" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "secret" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => {
      expect(screen.getByText("Company AI Test Lab")).toBeInTheDocument();
    });

    const form = screen.getByRole("form", { name: "Send message" });
    const submitEvent = new Event("submit", { bubbles: true, cancelable: true });

    const wasNotPrevented = form.dispatchEvent(submitEvent);

    expect(wasNotPrevented).toBe(false);
    expect(screen.getByText("Company AI Test Lab")).toBeInTheDocument();
  });

  it("sends messages with the selected mode and style and renders the backend answer", async () => {
    const fetchMock = createFetchMock();
    vi.stubGlobal("fetch", fetchMock);

    render(<App />);

    fireEvent.change(screen.getByLabelText("Username"), {
      target: { value: "tester" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "secret" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Real backend chat" })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("button", { name: "RAG over documents" }));
    fireEvent.click(screen.getByRole("button", { name: "Expert" }));
    fireEvent.change(screen.getByLabelText("Message"), {
      target: { value: "Что написано в документах?" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));

    await waitFor(() => {
      expect(screen.getByText("Grounded backend answer")).toBeInTheDocument();
    });

    expect(screen.getByRole("button", { name: "RAG over documents" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
    expect(screen.getByRole("button", { name: "Expert" })).toHaveAttribute("aria-pressed", "true");
    expect(fetchMock).toHaveBeenCalledWith("/api/chats/42/messages", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({
        message: "Что написано в документах?",
        mode: "rag",
        style: "expert",
      }),
    });
  });
});

function createFetchMock() {
  return vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    const method = init?.method ?? "GET";

    if (url === "/api/auth/login" && method === "POST") {
      return jsonResponse({ id: 1, username: "tester" });
    }

    if (url === "/api/chats" && method === "GET") {
      return jsonResponse([{ id: 42, title: "Real backend chat" }]);
    }

    if (url === "/api/chats/42/messages" && method === "GET") {
      return jsonResponse([
        { id: 1, role: "assistant", content: "Previous persisted answer", source_summary: null },
      ]);
    }

    if (url === "/api/documents" && method === "GET") {
      return jsonResponse([{ id: 7, filename: "real-policy.pdf", status: "ready" }]);
    }

    if (url === "/api/chats/42/messages" && method === "POST") {
      return jsonResponse({
        message: {
          id: 3,
          role: "assistant",
          content: "Grounded backend answer",
          source_summary: "real-policy.pdf",
        },
      });
    }

    throw new Error(`Unhandled request: ${method} ${url}`);
  });
}

function jsonResponse(body: unknown) {
  return {
    ok: true,
    json: async () => body,
    text: async () => JSON.stringify(body),
  };
}
