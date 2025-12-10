import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./LoginPage.css";
import { useAuth } from "../AuthContext";
import {
  loginWithEmailPassword,
  loginWithGoogle,
  loginWithFacebook,
  loginWithTwitter,
} from "../firebaseClient";

export default function LoginPage() {
  const [token, setToken] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [localError, setLocalError] = useState("");
  const [localSuccess, setLocalSuccess] = useState("");
  const navigate = useNavigate();
  const { loginWithToken, error, loading } = useAuth();

  const handleTokenSubmit = async (e) => {
    e.preventDefault();
    const ok = await loginWithToken(token);
    if (ok) navigate("/");
  };

  const handleEmailLogin = async (e) => {
    e.preventDefault();
    setLocalError("");
    setLocalSuccess("");
    try {
      const idToken = await loginWithEmailPassword(email, password);
      const ok = await loginWithToken(idToken);
      if (ok) navigate("/");
    } catch (err) {
      setLocalError("Email/password login failed. Check credentials and auth settings.");
    }
  };

  const handleProviderLogin = async (providerFn, name) => {
    setLocalError("");
    setLocalSuccess("");
    try {
      const token = await providerFn();
      const ok = await loginWithToken(token);
      if (ok) {
        setLocalSuccess(`Signed in with ${name}.`);
        navigate("/");
      }
    } catch (err) {
      const message = err?.message ? ` ${err.message}` : "";
      setLocalError(`${name} sign-in failed.${message || " Ensure the provider is enabled in Firebase."}`);
    }
  };

  return (
    <div className="login-frame">
      <div className="login-card">
        <h1>THEE BOGGLE BOOST</h1>
        <p className="subtitle">Login</p>

        <form onSubmit={handleEmailLogin} className="stack">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {localError && <div className="error">{localError}</div>}
          {localSuccess && <div className="success">{localSuccess}</div>}
          <button type="submit" disabled={loading}>
            {loading ? "Signing in..." : "Login with Email"}
          </button>
          <button
            type="button"
            className="secondary"
            onClick={() => handleProviderLogin(loginWithGoogle, "Google")}
            disabled={loading}
          >
            {loading ? "Please wait..." : "Login with Google"}
          </button>
          <button
            type="button"
            className="secondary"
            onClick={() => handleProviderLogin(loginWithTwitter, "Twitter")}
            disabled={loading}
          >
            {loading ? "Please wait..." : "Login with Twitter"}
          </button>
          <button
            type="button"
            className="secondary"
            onClick={() => handleProviderLogin(loginWithFacebook, "Facebook")}
            disabled={loading}
          >
            {loading ? "Please wait..." : "Login with Facebook"}
          </button>
        </form>

        <div className="divider">or</div>

        <form onSubmit={handleTokenSubmit} className="stack">
          <label htmlFor="token">ID Token</label>
          <textarea
            id="token"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            placeholder="Paste Firebase ID token"
            rows={4}
            required
          />
          {error && <div className="error">{error}</div>}
          <button type="submit" disabled={loading}>
            {loading ? "Validating..." : "Login with Token"}
          </button>
        </form>

        <div className="divider">
          Need an account? <Link to="/signup">Create one</Link>
        </div>
      </div>
    </div>
  );
}
