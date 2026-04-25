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
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ username: "tester" }),
    });
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
    expect(screen.getByRole("button", { name: "Normal chat" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "RAG over documents" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Concise" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Detailed" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Expert" })).toBeInTheDocument();
    expect(screen.getByText("LLM: Gemma 4 via NVIDIA API")).toBeInTheDocument();
    expect(screen.getByLabelText("Message")).toBeInTheDocument();
  });
});
