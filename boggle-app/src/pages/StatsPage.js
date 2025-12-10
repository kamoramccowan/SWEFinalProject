import React, { useEffect, useState } from "react";
import "./StatsPage.css";
import { fetchStats } from "../api";

export default function StatsPage() {
  const [stats, setStats] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError("");
      try {
        const resp = await fetchStats();
        setStats(resp.stats);
      } catch (err) {
        setError("Unable to load stats.");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  return (
    <div className="page">
      <h2>Your Statistics</h2>
      {loading && <div>Loading...</div>}
      {error && <div className="error">{error}</div>}
      {!loading && !stats && !error && <div>No stats available yet.</div>}
      {stats && (
        <>
          <div className="stat-grid">
            <div className="stat-card">
              <div>Total Games</div>
              <div className="value">{stats.games_played}</div>
            </div>
            <div className="stat-card">
              <div>Best Score</div>
              <div className="value">{stats.best_score}</div>
            </div>
            <div className="stat-card">
              <div>Average Score</div>
              <div className="value">{Math.round(stats.average_score)}</div>
            </div>
            <div className="stat-card">
              <div>Total Words Found</div>
              <div className="value">{stats.total_valid_words_found}</div>
            </div>
          </div>
          <div className="stat-grid">
            <div className="stat-card">
              <div>Accuracy</div>
              <div className="value">
                {(stats.accuracy * 100).toFixed(1)}% ({stats.correct_submissions}/{stats.total_submissions})
              </div>
            </div>
            <div className="stat-card">
              <div>Current Streak</div>
              <div className="value">{stats.current_streak} days</div>
            </div>
            <div className="stat-card">
              <div>Longest Streak</div>
              <div className="value">{stats.longest_streak} days</div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
