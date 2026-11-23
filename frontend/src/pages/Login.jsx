import { useState } from "react";
import { Link, Navigate } from "react-router-dom";
import { HOME, useAuth } from "../auth";
import { errorText } from "../api";

export default function Login() {
  const { user, loading, login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // already logged in? go straight to the dashboard
  if (!loading && user) return <Navigate to={HOME[user.role]} replace />;

  async function handleSubmit(e) {
    e.preventDefault(); // stops the page from reloading
    setError("");

    // simple checks before bothering the server
    if (!/^\S+@\S+\.\S+$/.test(email)) return setError("Please enter a valid email address.");
    if (!password) return setError("Please enter your password.");

    setSubmitting(true);
    try {
      await login(email.trim(), password); // the redirect happens automatically once the user is set
    } catch (err) {
      setError(errorText(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={handleSubmit} noValidate>
        <h1 className="brand-big">Ncare</h1>
        <p className="muted">Sign in to your account</p>

        {error && <div className="alert alert-error">{error}</div>}

        <label>Email
          <input type="email" value={email} autoFocus placeholder="you@company.com"
                 onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label>Password
          <input type="password" value={password} placeholder="Your password"
                 onChange={(e) => setPassword(e.target.value)} />
        </label>

        <button className="btn btn-block" disabled={submitting}>
          {submitting ? "Signing in..." : "Sign in"}
        </button>
        <p className="center"><Link className="link" to="/forgot-password">Forgot your password?</Link></p>

        {/* handy for reviewers trying the demo */}
        <div className="demo-box">
          <strong>Demo accounts</strong> (password <code>Demo@1234</code>)
          <div>admin@ncare.com</div>
          <div>manager.us.ar@ncare.com</div>
          <div>user.us.ar@ncare.com</div>
        </div>
      </form>
    </div>
  );
}
