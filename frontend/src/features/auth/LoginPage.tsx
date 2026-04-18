import { type FormEvent, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { AuthCard } from "../../components/ui/AuthCard";
import { useAuth } from "./useAuth";

export function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();
  const [email, setEmail] = useState("demo@preterm.local");
  const [password, setPassword] = useState("demo12345");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const state = location.state as { from?: string } | null;

  const redirectTarget = typeof state?.from === "string" ? state.from : "/app/monitor";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await login({ email, password });
      navigate(redirectTarget, { replace: true });
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Login failed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="auth-screen">
      <div className="auth-hero">
        <span className="eyebrow">Desk Access</span>
        <h2>PreTerm</h2>
        <p>
          A prediction-market workstation for tracking live contracts, interpreting events, and
          keeping important decisions tied to the right market signals.
        </p>
        <ul className="auth-bullet-list">
          <li>Monitor active contracts and save your desk state</li>
          <li>Read event briefs, scenarios, and move timelines in one place</li>
          <li>Map headlines and planning risks directly into relevant markets</li>
        </ul>
      </div>

      <AuthCard
        eyebrow="Sign In"
        title="Open your desk"
        subtitle="Sign in with your account or use the prefilled demo credentials below."
        footer={
          <p>
            Need an account? <Link to="/register">Create one</Link>
          </p>
        }
      >
        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="field">
            <span>Email</span>
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              autoComplete="email"
              required
            />
          </label>

          <label className="field">
            <span>Password</span>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
              required
            />
          </label>

          {error ? <div className="form-error">{error}</div> : null}

          <button type="submit" className="primary-button" disabled={isSubmitting}>
            {isSubmitting ? "Signing In..." : "Sign In"}
          </button>
        </form>
      </AuthCard>
    </div>
  );
}
