import { type CSSProperties, type FormEvent, useState } from "react";

export type LoginCredentials = {
  username: string;
  password: string;
};

type LoginPageProps = {
  onLogin: (credentials: LoginCredentials) => Promise<void>;
};

export function LoginPage({ onLogin }: LoginPageProps) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await onLogin({ username, password });
    } catch {
      setError("Unable to sign in. Check your credentials and try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main style={styles.page}>
      <section aria-labelledby="signin-heading" style={styles.card}>
        <h1 id="signin-heading">Sign in</h1>
        <p style={styles.helperText}>Use your workspace credentials to enter the AI test lab.</p>
        <form onSubmit={handleSubmit} style={styles.form}>
          <label style={styles.field}>
            <span>Username</span>
            <input
              autoComplete="username"
              name="username"
              onChange={(event) => setUsername(event.target.value)}
              required
              type="text"
              value={username}
            />
          </label>
          <label style={styles.field}>
            <span>Password</span>
            <input
              autoComplete="current-password"
              name="password"
              onChange={(event) => setPassword(event.target.value)}
              required
              type="password"
              value={password}
            />
          </label>
          {error ? (
            <p role="alert" style={styles.error}>
              {error}
            </p>
          ) : null}
          <button disabled={isSubmitting} type="submit">
            {isSubmitting ? "Signing in..." : "Sign in"}
          </button>
        </form>
      </section>
    </main>
  );
}

const styles = {
  page: {
    alignItems: "center",
    background: "#f6f7fb",
    display: "flex",
    minHeight: "100vh",
    justifyContent: "center",
    padding: "2rem",
  },
  card: {
    background: "#ffffff",
    border: "1px solid #d9deea",
    borderRadius: "16px",
    boxShadow: "0 16px 40px rgba(17, 24, 39, 0.08)",
    maxWidth: "420px",
    padding: "2rem",
    width: "100%",
  },
  helperText: {
    color: "#4b5563",
  },
  form: {
    display: "grid",
    gap: "1rem",
  },
  field: {
    display: "grid",
    gap: "0.35rem",
  },
  error: {
    color: "#b42318",
    margin: 0,
  },
} satisfies Record<string, CSSProperties>;
