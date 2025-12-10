import React, { useMemo, useState } from "react";
import "./CreateChallengePage.css";
import { createChallenge } from "../api";
import { useNavigate } from "react-router-dom";

export default function CreateChallengePage() {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [difficulty, setDifficulty] = useState("easy");
  const [gridText, setGridText] = useState("");
  const [timeLimit, setTimeLimit] = useState("3");
  const [customTime, setCustomTime] = useState("");
  const [boardSize, setBoardSize] = useState("4x4");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const boardTemplates = useMemo(
    () => ({
      "4x4": "ABCD\nEFGH\nIJKL\nMNOP",
      "5x5": "ABCDE\nFGHIJ\nKLMNO\nPQRST\nUVWXY",
      "6x6": "ABCDEF\nGHIJKL\nMNOPQR\nSTUVWX\nYZABCD\nEFGHIJ",
    }),
    []
  );

  const parseGrid = () => {
    const rows = gridText
      .split("\n")
      .map((r) => r.trim())
      .filter(Boolean)
      .map((row) => row.split("").map((c) => c.toUpperCase()));
    const size = rows.length ? rows[0].length : 0;
    if (!rows.length || rows.some((r) => r.length !== size)) {
      throw new Error("Grid must be a square with equal-length rows.");
    }
    return rows;
  };

  const selectTime = (value) => {
    setTimeLimit(value);
    if (value !== "custom") {
      setCustomTime("");
    }
  };

  const selectBoard = (value) => {
    setBoardSize(value);
    if (boardTemplates[value]) {
      setGridText(boardTemplates[value]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    try {
      const grid = parseGrid();
      setLoading(true);
      const created = await createChallenge({
        title,
        description,
        difficulty,
        grid,
      });
      const challengeId = created?.id || created?.challenge_id;
      setSuccess("Challenge created successfully.");
      // Navigate to play view if we have an id; otherwise back home.
      setTimeout(() => {
        if (challengeId) {
          navigate(`/play?challenge=${challengeId}`);
        } else {
          navigate("/");
        }
      }, 400);
    } catch (err) {
      setError(err.message || "Unable to create challenge.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page create-page">
      <div className="panel">
        <h2>Create New Challenge</h2>
        <p className="subtle">Configure game settings and invite players.</p>

        <form className="challenge-form" onSubmit={handleSubmit}>
          <div className="field">
            <label>Challenge Name</label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Friday Night Boggle"
              required
            />
            <div className="helper">Max 50 characters • Auto-generated if left blank</div>
          </div>

          <div className="field">
            <label>Time Limit</label>
            <div className="pill-row">
              {["1", "3", "5", "custom"].map((val) => (
                <button
                  key={val}
                  type="button"
                  className={`pill ${timeLimit === val ? "active" : ""}`}
                  onClick={() => selectTime(val)}
                >
                  {val === "custom" ? "[Custom]" : `[${val} min]`}
                </button>
              ))}
            </div>
            {timeLimit === "custom" && (
              <input
                className="inline-input"
                type="number"
                min="1"
                placeholder="Enter minutes"
                value={customTime}
                onChange={(e) => setCustomTime(e.target.value)}
              />
            )}
            <div className="helper">Toggle buttons • Custom opens input field</div>
          </div>

          <div className="field">
            <label>Board Size</label>
            <div className="pill-grid">
              {["4x4", "5x5", "6x6"].map((val) => (
                <div
                  key={val}
                  className={`tile ${boardSize === val ? "active" : ""}`}
                  onClick={() => selectBoard(val)}
                  role="button"
                >
                  <div className="tile-title">[{val}]</div>
                  <div className="tile-sub">
                    {val === "4x4" && "Classic"}
                    {val === "5x5" && "Big Boggle"}
                    {val === "6x6" && "Super Boggle"}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="field">
            <label>Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional description or clues"
              rows={2}
            />
          </div>

          <div className="field">
            <label>Difficulty</label>
            <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
              <option value="easy">Easy</option>
              <option value="medium">Medium</option>
              <option value="hard">Hard</option>
            </select>
          </div>

          <div className="field">
            <label>Grid</label>
            <textarea
              value={gridText}
              onChange={(e) => setGridText(e.target.value)}
              rows={6}
              placeholder={boardTemplates["4x4"]}
              required
            />
          </div>

          {error && <div className="error">{error}</div>}
          {success && <div className="success">{success}</div>}

          <div className="actions">
            <button type="submit" disabled={loading}>
              {loading ? "Saving..." : "Create Challenge"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
