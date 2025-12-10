import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import "./HomePage.css";
import { fetchDailyChallenge, fetchMyChallenges } from "../api";
import { useAuth } from "../AuthContext";

export default function HomePage() {
  const { user } = useAuth();
  const [daily, setDaily] = useState(null);
  const [mine, setMine] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const greetingName = user?.display_name || user?.email || "Player";
  const greetingTime = () => {
    const hour = new Date().getHours();
    if (hour < 12) return "Good morning";
    if (hour < 18) return "Good afternoon";
    return "Good evening";
  };

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError("");
      try {
        const [d, m] = await Promise.all([fetchDailyChallenge(), fetchMyChallenges()]);
        setDaily(d);
        setMine(m);
      } catch (err) {
        setError("Unable to load dashboard data.");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  return (
    <div className="page home">
      <div className="hero">
        <h2>Welcome Back, {greetingName}</h2>
        <p className="subtle">{greetingTime()} — ready to jump back in?</p>
        <div className="cta-grid">
          <div className="cta-card" onClick={() => navigate("/create")}>
            <div className="cta-title">Create New Challenge</div>
            <div className="cta-text">Start a new game with custom settings</div>
          </div>
          <div className="cta-card" onClick={() => navigate("/play")}>
            <div className="cta-title">Join Challenge</div>
            <div className="cta-text">Enter a challenge code or browse open games</div>
          </div>
        </div>
      </div>

      {loading && <div className="muted">Loading...</div>}
      {error && <div className="error">{error}</div>}

      {daily && (
        <section className="section">
          <div className="section-head">
            <h3>Daily Challenge</h3>
            <span className="section-note">Click to resume</span>
          </div>
          <div className="list-card" role="button" onClick={() => navigate(`/play?challenge=${daily.challenge_id}`)}>
            <div>
              <div className="card-title">{daily.title}</div>
              <div className="meta">Difficulty: {daily.difficulty}</div>
            </div>
            <button className="outline-button">Play</button>
          </div>
        </section>
      )}

      <section className="section">
        <h3>Active Challenges {mine.length ? `(${mine.length})` : ""}</h3>
        <div className="list">
          {mine.length === 0 && <div className="muted">No challenges yet. Create or join one to get started.</div>}
          {mine.map((c) => (
            <div className="list-card" key={c.id}>
              <div>
                <div className="card-title">{c.title}</div>
                <div className="meta">
                  {c.difficulty ? `Difficulty: ${c.difficulty}` : "In Progress"}{" "}
                  {c.players ? `• ${c.players} players` : ""}
                </div>
              </div>
              <Link className="outline-button" to={`/play?challenge=${c.id}`}>
                Play
              </Link>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
