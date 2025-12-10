import React, { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import "./PlayPage.css";
import Board from "../Board";
import { endSession, fetchDailyChallenge, sessionHint, sessionResults, startSession, submitWord } from "../api";

function useQuery() {
  return new URLSearchParams(useLocation().search);
}

export default function PlayPage() {
  const query = useQuery();
  const navigate = useNavigate();
  const challengeId = query.get("challenge");
  const [session, setSession] = useState(null);
  const [daily, setDaily] = useState(null);
  const [word, setWord] = useState("");
  const [messages, setMessages] = useState([]);
  const [error, setError] = useState("");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [grid, setGrid] = useState([]);
  const [timerSeconds, setTimerSeconds] = useState(165); // 2:45 default
  const [timerRunning, setTimerRunning] = useState(false);
  const [autoEnded, setAutoEnded] = useState(false);
  const [hintsUsed, setHintsUsed] = useState(0);
  const [currentHint, setCurrentHint] = useState(null);
  const [manualChallengeId, setManualChallengeId] = useState("");
  const MAX_HINTS = 3;

  const displayGrid = useMemo(() => {
    // If grid state has content (was set by shuffle/rotate or session start), use it
    if (grid && grid.length > 0) {
      return grid;
    }
    // Otherwise use daily grid for initial display
    if (daily && daily.grid) {
      return daily.grid;
    }
    return [];
  }, [daily, grid]);

  const persistedSessionKey = useMemo(() => (challengeId ? `play_session_${challengeId}` : null), [challengeId]);

  const formatTimer = (secs) => {
    const safe = Math.max(0, secs);
    const m = Math.floor(safe / 60)
      .toString()
      .padStart(2, "0");
    const s = (safe % 60).toString().padStart(2, "0");
    return `${m}:${s}`;
  };

  const remainingFromServer = (sess) => {
    const dur = Number(sess?.duration_seconds || sess?.duration || 165);
    const started = sess?.start_time ? Date.parse(sess.start_time) : Date.now();
    const elapsed = Math.max(0, Math.floor((Date.now() - started) / 1000));
    return Math.max(0, dur - elapsed);
  };

  // Restore previous session state (for reload)
  useEffect(() => {
    if (!persistedSessionKey) return;
    try {
      const raw = localStorage.getItem(persistedSessionKey);
      if (!raw) return;
      const saved = JSON.parse(raw);
      if (saved?.session) {
        setSession(saved.session);
        if (saved.grid) setGrid(saved.grid);
        if (typeof saved.remaining_seconds === "number") {
          setTimerSeconds(saved.remaining_seconds);
          if (saved.remaining_seconds > 0) setTimerRunning(true);
        }
      }
    } catch (e) {
      // ignore corrupt storage
    }
  }, [persistedSessionKey]);

  // Persist session state
  useEffect(() => {
    if (!persistedSessionKey || !session) return;
    try {
      localStorage.setItem(
        persistedSessionKey,
        JSON.stringify({ session, grid, remaining_seconds: timerSeconds })
      );
    } catch (e) {
      // ignore storage errors
    }
  }, [persistedSessionKey, session, grid, timerSeconds]);

  useEffect(() => {
    if (!timerRunning) return;
    const id = setInterval(() => {
      setTimerSeconds((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(id);
  }, [timerRunning]);

  useEffect(() => {
    if (timerSeconds === 0 && timerRunning && session && !autoEnded) {
      setTimerRunning(false);
      setAutoEnded(true);
      handleEnd(true);
    }
  }, [timerSeconds, timerRunning, session, autoEnded]);

  const samplePlayers = useMemo(
    () => [
      { name: "You", leader: true, score: 94, words: 8, status: "Playing" },
      { name: "Player2", leader: false, score: 87, words: 9, status: "Playing" },
      { name: "Player3", leader: false, score: 62, words: 7, status: "Playing" },
      { name: "Player4", leader: false, score: 45, words: 6, status: "Playing" },
    ],
    []
  );
  const friendlyPlayers = useMemo(() => {
    if (session && timerRunning) return [{ name: "Player", leader: true, score: 0, words: 0, status: "Playing" }];
    if (session && results) return [{ name: "Player", leader: true, score: results.score || 0, words: results.found_words?.length || 0, status: "Finished" }];
    const source = samplePlayers;
    const seen = new Set();
    return source.filter((p) => {
      const key = p.name || p.player_user_id || JSON.stringify(p);
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    }).map((p) => ({
      ...p,
      name: friendlyName(p.name || p.player_user_id),
    }));
  }, [session, samplePlayers, timerRunning, results]);

  useEffect(() => {
    const loadDaily = async () => {
      try {
        const d = await fetchDailyChallenge();
        setDaily(d);
        // preload grid for visual layout if we got one
        if (d && d.grid && d.grid.length) {
          setGrid(d.grid);
        }
      } catch (e) {
        // ignore
      }
    };
    loadDaily();
  }, []);

  const handleStart = async () => {
    const effectiveId = manualChallengeId || challengeId || (daily && daily.challenge_id);
    if (!effectiveId) {
      setMessages((m) => [...m, "Enter a challenge ID or use the daily challenge."]);
      return;
    }
    setLoading(true);
    setMessages([]);
    setError("");
    try {
      const s = await startSession(Number(effectiveId));
      setSession(s);
      setHintsUsed(0);
      setCurrentHint(null);
      // If backend includes duration, set timer from it (seconds)
      const remaining = remainingFromServer(s);
      setTimerSeconds(Number.isNaN(remaining) ? 165 : remaining);
      setTimerRunning(remaining > 0);
      // if daily provided grid
      if (daily && daily.challenge_id === s.challenge) {
        setGrid(daily.grid);
      } else if (s?.challenge_grid) {
        setGrid(s.challenge_grid);
      } else if (s?.grid) {
        setGrid(s.grid);
      }
    } catch (err) {
      setTimerRunning(false);
      setSession(null);
      setGrid([]);
      const status = err?.response?.status;
      const detail =
        err?.response?.data?.message ||
        err?.response?.data?.detail ||
        (status === 404 ? "Challenge not found." : status === 401 ? "Auth required." : "Unable to start session.");
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitWord = async (e) => {
    e.preventDefault();
    if (!session) return;
    try {
      const resp = await submitWord(session.id, word);
      if (resp.already_found) {
        setMessages((m) => [...m, `${resp.word}: already found! 🔄`]);
      } else if (resp.is_valid) {
        setMessages((m) => [...m, `${resp.word}: correct ✅ (+${resp.score_delta})`]);
      } else {
        setMessages((m) => [...m, `${resp.word}: incorrect ❌`]);
      }
      setWord("");
    } catch (err) {
      setMessages((m) => [...m, "Submission failed."]);
    }
  };

  const handleHint = async () => {
    if (!session) return;
    if (hintsUsed >= MAX_HINTS) {
      setMessages((m) => [...m, "No more hints available (max 3 per game)."]);
      return;
    }
    try {
      const resp = await sessionHint(session.id);
      const hintData = resp.hint || resp;
      let hintText = "";
      if (typeof hintData === 'string') {
        hintText = hintData;
      } else if (hintData.first_letter && hintData.length) {
        // Backend provides first_letter and length
        hintText = `A ${hintData.length}-letter word starts with "${hintData.first_letter.toUpperCase()}"`;
      } else if (hintData.word) {
        // Format hint to show partial word
        const word = hintData.word;
        const revealChars = Math.min(2, Math.floor(word.length / 2));
        const startHint = word.slice(0, revealChars).toUpperCase();
        hintText = `A valid word starts with "${startHint}..." (${word.length} letters)`;
      } else if (hintData.starts_with) {
        hintText = `A valid word starts with "${hintData.starts_with.toUpperCase()}..."`;
      } else if (hintData.ends_with) {
        hintText = `A valid word ends with "...${hintData.ends_with.toUpperCase()}"`;
      } else if (hintData === null) {
        hintText = "No unfound words remain!";
      } else {
        hintText = JSON.stringify(hintData);
      }
      setCurrentHint(hintText);
      setHintsUsed((prev) => prev + 1);
      setMessages((m) => [...m, `💡 Hint ${hintsUsed + 1}/${MAX_HINTS}: ${hintText}`]);
    } catch (err) {
      // Show the actual backend error message if available
      const errorMsg = err?.response?.data?.message || err?.response?.data?.error_code || "No hints available for this challenge.";
      setMessages((m) => [...m, `Hint error: ${errorMsg}`]);
    }
  };

  const handleSaveChallenge = () => {
    // Save challenge for later - just navigate to home (session persisted in localStorage)
    if (persistedSessionKey && session) {
      // Keep the session in localStorage so it shows as "active"
      setMessages((m) => [...m, "Challenge saved! Returning to home..."]);
      setTimeout(() => navigate("/"), 500);
    } else {
      setMessages((m) => [...m, "No active session to save."]);
    }
  };

  // Local shuffle - rearranges tiles randomly
  const handleShuffle = () => {
    if (!session || !displayGrid || !displayGrid.length) return;

    // Flatten grid, shuffle, and rebuild
    const rows = displayGrid.length;
    const cols = displayGrid[0].length;
    const flat = displayGrid.flatMap(row => [...row]);

    // Fisher-Yates shuffle
    for (let i = flat.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [flat[i], flat[j]] = [flat[j], flat[i]];
    }

    // Rebuild grid
    const newGrid = [];
    for (let i = 0; i < rows; i++) {
      newGrid.push(flat.slice(i * cols, (i + 1) * cols));
    }

    setGrid(newGrid);
    setMessages((m) => [...m, "🔀 Board shuffled!"]);
  };

  // Local 90-degree clockwise rotation
  const handleRotate = () => {
    if (!session || !displayGrid || !displayGrid.length) return;

    const n = displayGrid.length;
    // True 90-degree clockwise: new[i][j] = old[n-1-j][i]
    const rotated = [];
    for (let i = 0; i < n; i++) {
      const newRow = [];
      for (let j = 0; j < n; j++) {
        newRow.push(displayGrid[n - 1 - j][i]);
      }
      rotated.push(newRow);
    }

    setGrid(rotated);
    setMessages((m) => [...m, "🔄 Board rotated 90° clockwise!"]);
  };

  const handleEnd = async (auto = false) => {
    if (!session) return;
    try {
      const endResp = await endSession(session.id);
      if (endResp?.results) {
        setResults(endResp.results);
      } else {
        const res = await sessionResults(session.id);
        setResults(res);
      }
      setTimerRunning(false);
      if (persistedSessionKey) {
        localStorage.removeItem(persistedSessionKey);
      }
      if (auto) {
        setMessages((m) => [...m, "Time up. Session ended."]);
      }
    } catch (err) {
      setMessages((m) => [...m, "Unable to end session."]);
    }
  };

  return (
    <div className="page play-page">
      <div className="play-header">
        <div>
          <div className="play-title">
            {session ? session.challenge_title || session.title || "[Challenge]" : "[Challenge Name]"}
          </div>
          <div className="play-meta">
            Round 1 of 3 - {boardSizeLabel(displayGrid)} Board - {difficultyLabel(session?.challenge_difficulty || session?.difficulty)} - {languageLabel(session?.challenge_language || session?.language || daily?.language)}
          </div>
          <div className="play-note">NOTE: Timer counts down • Turns red at :30 • Auto-submit at 0:00</div>
        </div>
        <div className={`timer-box ${timerSeconds <= 30 ? "warn" : ""}`}>[Time: {formatTimer(timerSeconds)}]</div>
        <div className="players-head">
          <div className="players-title">Players (4/8)</div>
          <div className="players-sub">Live updates • Current leader highlighted</div>
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      <div className="play-body">
        <div className="board-wrapper">
          {displayGrid && displayGrid.length > 0 ? (
            <Board board={displayGrid} />
          ) : (
            <div className="placeholder-board">Grid will appear when available.</div>
          )}
        </div>
        <div className="players-list">
          {friendlyPlayers.map((p, idx) => (
            <div className={`player-card ${p.leader ? "leader" : ""}`} key={idx}>
              <div className="player-line">
                <span className="player-name">[{p.name}]</span>
                {p.leader && <span className="leader-tag">(Leader)</span>}
                <span className="player-score">[Score: {p.score ?? "--"}]</span>
              </div>
              <div className="player-subline">[{p.words ?? "--"} words] • [{p.status || "Playing"}]</div>
            </div>
          ))}
        </div>
      </div>

      <div className="controls-bar">
        <div className="controls">
          <input
            type="text"
            placeholder="Challenge ID"
            value={manualChallengeId || challengeId || ""}
            onChange={(e) => setManualChallengeId(e.target.value)}
            disabled={!!session}
          />
          <button onClick={handleStart} disabled={loading || (session && (timerRunning || results))}>
            {loading ? "Starting..." : "Start"}
          </button>
          <button type="button" onClick={handleHint} disabled={!session || !!results || hintsUsed >= MAX_HINTS}>
            Hint ({MAX_HINTS - hintsUsed} left)
          </button>
          <button type="button" onClick={handleShuffle} disabled={!session || !!results}>🔀 Shuffle</button>
          <button type="button" onClick={handleRotate} disabled={!session || !!results}>🔄 Rotate</button>
          <button type="button" onClick={handleSaveChallenge} disabled={!session || !!results}>Save Challenge</button>
          <button type="button" onClick={handleEnd} disabled={!session || !!results}>End Game</button>
        </div>
        <form className="word-form" onSubmit={handleSubmitWord}>
          <input
            value={word}
            onChange={(e) => setWord(e.target.value)}
            placeholder="Enter word"
            disabled={!session || !!results || autoEnded || !timerRunning}
          />
          <button type="submit" disabled={!session || !!results || autoEnded || !timerRunning}>Submit</button>
        </form>
      </div>

      {results && (
        <div className="results">
          <h4>Results</h4>
          <div>Score: {results.score}</div>
          <div>Found: {results.found_words.join(", ")}</div>
          <div>All Valid: {results.all_valid_words.join(", ")}</div>
        </div>
      )}

      <div className="messages">
        {messages.map((m, idx) => (
          <div key={idx}>{m}</div>
        ))}
      </div>
    </div>
  );
}

function difficultyLabel(raw) {
  if (!raw) return "Medium Difficulty";
  const map = { easy: "Easy", medium: "Medium", hard: "Hard" };
  return `${map[raw] || raw} Difficulty`;
}

function boardSizeLabel(grid) {
  if (!grid || !grid.length || !grid[0]) return "4x4";
  const rows = grid.length;
  const cols = Array.isArray(grid[0]) ? grid[0].length : Object.keys(grid[0]).length;
  return `${rows}x${cols}`;
}

function friendlyName(raw) {
  if (!raw) return "Player";
  const str = String(raw);
  if (str.startsWith("fb_stub_")) {
    return "Player";
  }
  if (str.length > 24) {
    return `${str.slice(0, 12)}…${str.slice(-6)}`;
  }
  return str;
}

function languageLabel(raw) {
  const map = { en: "🇺🇸 English", es: "🇪🇸 Spanish", fr: "🇫🇷 French" };
  return map[raw] || map.en;
}
