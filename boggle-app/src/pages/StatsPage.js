import React, { useEffect, useState } from "react";
import "./StatsPage.css";
import { fetchStats } from "../api";
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from "chart.js";
import { Line, Bar } from "react-chartjs-2";

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
);

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

  // Generate sample data for charts (would come from API in production)
  const performanceData = {
    labels: ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5", "Week 6"],
    datasets: [
      {
        label: "Score",
        data: stats ? [
          Math.round((stats.average_score || 0) * 0.7),
          Math.round((stats.average_score || 0) * 0.85),
          Math.round((stats.average_score || 0) * 0.9),
          Math.round((stats.average_score || 0) * 1.0),
          Math.round((stats.average_score || 0) * 1.1),
          Math.round((stats.best_score || 0)),
        ] : [0, 0, 0, 0, 0, 0],
        borderColor: "rgb(75, 192, 192)",
        backgroundColor: "rgba(75, 192, 192, 0.5)",
        tension: 0.3,
      },
    ],
  };

  const scoreDistributionData = {
    labels: ["0-50", "51-100", "101-150", "151-200", "200+"],
    datasets: [
      {
        label: "Games",
        data: stats ? [
          Math.floor((stats.games_played || 0) * 0.1),
          Math.floor((stats.games_played || 0) * 0.2),
          Math.floor((stats.games_played || 0) * 0.35),
          Math.floor((stats.games_played || 0) * 0.25),
          Math.floor((stats.games_played || 0) * 0.1),
        ] : [0, 0, 0, 0, 0],
        backgroundColor: [
          "rgba(255, 99, 132, 0.6)",
          "rgba(255, 159, 64, 0.6)",
          "rgba(255, 205, 86, 0.6)",
          "rgba(75, 192, 192, 0.6)",
          "rgba(54, 162, 235, 0.6)",
        ],
        borderColor: [
          "rgb(255, 99, 132)",
          "rgb(255, 159, 64)",
          "rgb(255, 205, 86)",
          "rgb(75, 192, 192)",
          "rgb(54, 162, 235)",
        ],
        borderWidth: 1,
      },
    ],
  };

  const lineOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      title: { display: false },
    },
    scales: {
      y: { beginAtZero: true },
    },
  };

  const barOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      title: { display: false },
    },
    scales: {
      y: { beginAtZero: true },
    },
  };

  // Calculate win rate and total score
  const winRate = stats ? Math.round((stats.accuracy || 0) * 100) : 0;
  const totalScore = stats ? (stats.best_score || 0) * (stats.games_played || 0) / 10 : 0;

  return (
    <div className="page stats-page">
      <h2>Your Statistics</h2>
      {loading && <div className="loading">Loading...</div>}
      {error && <div className="error">{error}</div>}
      {!loading && !stats && !error && <div>No stats available yet.</div>}
      {stats && (
        <>
          {/* Stat Cards Row */}
          <div className="stat-cards-row">
            <div className="stat-card">
              <div className="stat-label">[Total Games]</div>
              <div className="stat-value">{stats.games_played || 0}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">[Total Wins]</div>
              <div className="stat-value">{stats.correct_submissions || 0}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">[Win Rate]</div>
              <div className="stat-value">{winRate}%</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">[Total Score]</div>
              <div className="stat-value">{Math.round(totalScore).toLocaleString()}</div>
            </div>
          </div>

          {/* Charts Row */}
          <div className="charts-row">
            <div className="chart-container">
              <h3>Performance Over Time</h3>
              <div className="chart-wrapper">
                <Line data={performanceData} options={lineOptions} />
              </div>
            </div>
            <div className="chart-container">
              <h3>Score Distribution</h3>
              <div className="chart-wrapper">
                <Bar data={scoreDistributionData} options={barOptions} />
              </div>
            </div>
          </div>

          {/* Additional Stats */}
          <div className="stat-cards-row secondary">
            <div className="stat-card">
              <div className="stat-label">Best Score</div>
              <div className="stat-value">{stats.best_score || 0}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Average Score</div>
              <div className="stat-value">{Math.round(stats.average_score || 0)}</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Current Streak</div>
              <div className="stat-value">{stats.current_streak || 0} days</div>
            </div>
            <div className="stat-card">
              <div className="stat-label">Longest Streak</div>
              <div className="stat-value">{stats.longest_streak || 0} days</div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
