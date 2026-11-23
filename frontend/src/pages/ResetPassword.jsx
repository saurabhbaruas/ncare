import { useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import api, { errorText } from "../api";

// One page, two steps:
//   /forgot-password           -> ask for the reset link
//   /reset-password?token=...  -> choose a new password (the link from the "email")
export default function ResetPassword() {
  const [params] = useSearchParams();
  const token = params.get("token");

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [done, setDone] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");

    if (token && password !== confirm) return setError("The two passwords do not match.");
    if (!token && !/^\S+@\S+\.\S+$/.test(email)) return setError("Please enter a valid email address.");

    setSubmitting(true);
    try {
      const res = token
        ? await api.post("/auth/password-reset/confirm", { token, new_password: password })
        : await api.post("/auth/password-reset/request", { email: email.trim() });
      setDone(res.data.message);
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
        <p className="muted">{token ? "Choose a new password" : "Reset your password"}</p>

        {error && <div className="alert alert-error">{error}</div>}
        {done && <div className="alert alert-success">{done}</div>}

        {!done && token && (
          <>
            <label>New password
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
            </label>
            <label>Confirm password
              <input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} />
            </label>
            <p className="hint">At least 8 characters with upper &amp; lower case, a number and a symbol.</p>
          </>
        )}

        {!done && !token && (
          <label>Email
            <input type="email" value={email} autoFocus onChange={(e) => setEmail(e.target.value)} />
          </label>
        )}

        {!done && (
          <button className="btn btn-block" disabled={submitting}>
            {submitting ? "Please wait..." : token ? "Update password" : "Send reset link"}
          </button>
        )}
        <p className="center"><Link className="link" to="/login">Back to sign in</Link></p>
      </form>
    </div>
  );
}
