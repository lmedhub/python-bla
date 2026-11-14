import { useState, type SubmitEvent } from "react";
import { Navigate, useLocation } from "react-router";
import { userMessage } from "../../api/errors";
import { useAuth } from "./AuthProvider";
import styles from "./LoginPage.module.css";

export function LoginPage() {
  const { state, signIn } = useAuth();
  const location = useLocation();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  if (state.status === "loading") {
    return <p role="status">Loading…</p>;
  }
  if (state.status === "signedIn") {
    return <Navigate to={returnPath(location.state)} replace />;
  }

  async function handleSubmit(event: SubmitEvent<HTMLFormElement>) {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await signIn(email, password);
    } catch (caught) {
      setError(userMessage(caught));
      setPassword("");
      setSubmitting(false);
    }
  }

  return (
    <main className={styles.page}>
      <h1>Sign in</h1>
      <form className={styles.form} onSubmit={(event) => void handleSubmit(event)}>
        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          autoComplete="username"
          required
          value={email}
          onChange={(event) => {
            setEmail(event.target.value);
          }}
        />
        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(event) => {
            setPassword(event.target.value);
          }}
        />
        {error && (
          <p role="alert" className={styles.error}>
            {error}
          </p>
        )}
        <button type="submit" disabled={submitting}>
          {submitting ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </main>
  );
}

/** Where RequireAuth was sending the visitor, or the task list. */
function returnPath(state: unknown): string {
  if (typeof state === "object" && state !== null && "from" in state) {
    const { from } = state;
    if (typeof from === "string" && from.startsWith("/")) {
      return from;
    }
  }
  return "/tasks";
}
