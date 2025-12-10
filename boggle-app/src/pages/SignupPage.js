import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./LoginPage.css";
import { useAuth } from "../AuthContext";
import { signupWithEmailPassword } from "../firebaseClient";

export default function SignupPage() {
  const navigate = useNavigate();
  const { loginWithToken, loading } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [localError, setLocalError] = useState("");
  const [localSuccess, setLocalSuccess] = useState("");

  const handleSignup = async (e) => {
    e.preventDefault();
    setLocalError("");
    setLocalSuccess("");
    if (password !== confirmPassword) {
      setLocalError("Passwords do not match.");
      return;
    }

    try {
      const token = await signupWithEmailPassword(email, password, displayName.trim() || undefined);
      const ok = await loginWithToken(token);
      if (ok) {
        setLocalSuccess("Account created and signed in.");
        navigate("/");
      }
    } catch (err) {
      const message =
        err?.code === "auth/email-already-in-use"
          ? "Email is already registered. Try logging in instead."
          : err?.message || "Signup failed. Check your Firebase auth settings.";
      setLocalError(message);
    }
  };

  return (
    <div className="login-frame">
      <div className="login-card">
        <h1>THEE BOGGLE BOOST</h1>
        <p className="subtitle">Create your account</p>

        <form onSubmit={handleSignup} className="stack">
          <label htmlFor="displayName">Display name (optional)</label>
          <input
            id="displayName"
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="Name shown to others"
          />

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
            minLength={6}
          />

          <label htmlFor="confirmPassword">Confirm password</label>
          <input
            id="confirmPassword"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            minLength={6}
          />

          {localError && <div className="error">{localError}</div>}
          {localSuccess && <div className="success">{localSuccess}</div>}

          <button type="submit" disabled={loading}>
            {loading ? "Creating account..." : "Sign Up"}
          </button>
        </form>

        <div className="divider">
          Already have an account? <Link to="/login">Login</Link>
        </div>
      </div>
    </div>
  );
}
