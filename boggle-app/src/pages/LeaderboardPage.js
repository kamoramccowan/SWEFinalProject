import React, { useEffect, useState } from "react";
import "./LeaderboardPage.css";
import { fetchDailyLeaderboard } from "../api";

export default function LeaderboardPage() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      setError("");
      try {
        const resp = await fetchDailyLeaderboard();
        setEntries(resp.entries || []);
      } catch (err) {
        setError("Unable to load leaderboard.");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  return (
    <div className="page">
      <h2>Leaderboard</h2>
      {loading && <div>Loading...</div>}
      {error && <div className="error">{error}</div>}
      {!loading && entries.length === 0 && <div>No leaderboard entries yet.</div>}
      <table className="leaderboard">
        <thead>
          <tr>
            <th>Rank</th>
            <th>Player</th>
            <th>Score</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((e, idx) => (
            <tr key={idx}>
              <td>{e.rank}</td>
              <td>{e.display_name || e.player_user_id || "Player"}</td>
              <td>{e.score}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
