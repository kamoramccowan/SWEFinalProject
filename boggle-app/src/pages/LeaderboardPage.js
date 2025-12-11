import React, { useEffect, useState } from "react";
import "./LeaderboardPage.css";
import { fetchDailyLeaderboard } from "../api";

export default function LeaderboardPage() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [timeFilter, setTimeFilter] = useState("all");

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
  }, [timeFilter]); // Reload when filter changes

  // Filter entries based on time selection (mock implementation)
  // In production, this would be handled by the API
  const filteredEntries = entries;

  return (
    <div className="page leaderboard-page">
      <div className="leaderboard-header">
        <h2>Leaderboard</h2>
        <div className="time-filters">
          {[
            { key: "all", label: "[All Time]" },
            { key: "month", label: "[This Month]" },
            { key: "week", label: "[This Week]" },
            { key: "today", label: "[Today]" },
          ].map((filter) => (
            <button
              key={filter.key}
              className={`filter-btn ${timeFilter === filter.key ? "active" : ""}`}
              onClick={() => setTimeFilter(filter.key)}
            >
              {filter.label}
            </button>
          ))}
        </div>
      </div>

      {loading && <div className="loading">Loading...</div>}
      {error && <div className="error">{error}</div>}
      {!loading && filteredEntries.length === 0 && !error && (
        <div className="empty">No leaderboard entries yet. Be the first to play!</div>
      )}

      {!loading && filteredEntries.length > 0 && (
        <div className="table-container">
          <table className="leaderboard-table">
            <thead>
              <tr>
                <th className="rank-col">Rank</th>
                <th className="player-col">Player</th>
                <th className="games-col">Games</th>
                <th className="wins-col">Wins</th>
                <th className="winrate-col">Win Rate</th>
                <th className="score-col">Total Score</th>
              </tr>
            </thead>
            <tbody>
              {filteredEntries.map((entry, idx) => {
                // Use actual backend data, fallback to 0 for missing fields
                const games = entry.games_played || 0;
                const wins = entry.wins || 0;
                const winRate = games > 0 ? ((wins / games) * 100).toFixed(1) : 0;
                const totalScore = entry.total_score || entry.score || 0;

                return (
                  <tr key={idx} className={idx < 3 ? `top-${idx + 1}` : ""}>
                    <td className="rank-col">
                      <span className="rank-badge">
                        {idx === 0 && "🥇"}
                        {idx === 1 && "🥈"}
                        {idx === 2 && "🥉"}
                        {idx > 2 && (entry.rank || idx + 1)}
                      </span>
                    </td>
                    <td className="player-col">
                      <div className="player-info">
                        <div className="player-avatar">
                          {(entry.display_name || entry.player_user_id || "P")[0].toUpperCase()}
                        </div>
                        <span className="player-name">
                          {entry.display_name || entry.player_user_id || "Player"}
                        </span>
                      </div>
                    </td>
                    <td className="games-col">{games}</td>
                    <td className="wins-col">{wins}</td>
                    <td className="winrate-col">{winRate}%</td>
                    <td className="score-col">{totalScore.toLocaleString()}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
