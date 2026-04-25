import { useState } from "react";

import { postJson } from "./api/client";
import { type LoginCredentials, LoginPage } from "./auth/LoginPage";
import { ChatWorkspace } from "./chat/ChatWorkspace";

export function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  async function handleLogin(credentials: LoginCredentials) {
    await postJson("/auth/login", credentials);
    setIsAuthenticated(true);
  }

  if (!isAuthenticated) {
    return <LoginPage onLogin={handleLogin} />;
  }

  return <ChatWorkspace />;
}
