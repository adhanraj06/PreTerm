import { type FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { AuthCard } from "../../components/ui/AuthCard";
import { useAuth } from "./useAuth";

export function RegisterPage() {
  const navigate = useNavigate();
  const { register } = useAuth();
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);

    try {
      await register({ display_name: displayName, email, password });
      navigate("/app/monitor", { replace: true });
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Registration failed.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="auth-screen">
      <div className="auth-hero">
        <span className="eyebrow">Registration</span>
        <h2>Create your workspace</h2>
        <p>
          Create an account to save watchlists, planner events, alert settings, and your preferred
          desk setup.
        </p>
      </div>

      <AuthCard
        eyebrow="Create Account"
        title="Register for PreTerm"
        subtitle="Set up your account and start with a personalized prediction-market workspace."
        footer={
          <p>
            Already have an account? <Link to="/login">Sign in</Link>
          </p>
        }
      >
        <form className="auth-form" onSubmit={handleSubmit}>
          <label className="field">
            <span>Display Name</span>
            <input
              type="text"
              value={displayName}
              onChange={(event) => setDisplayName(event.target.value)}
              autoComplete="name"
              required
            />
          </label>

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
              autoComplete="new-password"
              minLength={8}
              required
            />
          </label>

          {error ? <div className="form-error">{error}</div> : null}

          <button type="submit" className="primary-button" disabled={isSubmitting}>
            {isSubmitting ? "Creating Account..." : "Create Account"}
          </button>
        </form>
      </AuthCard>
    </div>
  );
}
