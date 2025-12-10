import React, { useEffect, useMemo, useState } from "react";
import { useLocation } from "react-router-dom";
import "./PlayPage.css";
import Board from "../Board";
import { endSession, fetchDailyChallenge, sessionHint, sessionResults, startSession, submitWord } from "../api";

function useQuery() {
  return new URLSearchParams(useLocation().search);
}

export default function PlayPage() {
  const query = useQuery();
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

  const displayGrid = useMemo(() => {
    if (daily && session && daily.challenge_id === session.challenge) {
      return daily.grid;
    }
    return grid;
  }, [daily, session, grid]);

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
    const source = session?.players && session.players.length ? session.players : samplePlayers;
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
  }, [session, samplePlayers]);

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
    const effectiveId = challengeId || (daily && daily.challenge_id);
    if (!effectiveId) {
      setMessages((m) => [...m, "Provide challenge id via ?challenge=ID or use daily challenge."]);
      return;
    }
    setLoading(true);
    setMessages([]);
    setError("");
    try {
      const s = await startSession(Number(effectiveId));
      setSession(s);
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
      setMessages((m) => [...m, `${resp.word}: ${resp.is_valid ? "correct" : "incorrect"}`]);
      setWord("");
    } catch (err) {
      setMessages((m) => [...m, "Submission failed."]);
    }
  };

  const handleHint = async () => {
    if (!session) return;
    try {
      const resp = await sessionHint(session.id);
      setMessages((m) => [...m, `Hint: ${JSON.stringify(resp.hint)}`]);
    } catch (err) {
      setMessages((m) => [...m, "No hints available."]);
    }
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
            Round 1 of 3 - {boardSizeLabel(displayGrid)} Board - {difficultyLabel(session?.challenge_difficulty || session?.difficulty)}
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
            defaultValue={challengeId || ""}
            readOnly
          />
          <button onClick={handleStart} disabled={loading || (session && (timerRunning || results))}>
            {loading ? "Starting..." : "Start"}
          </button>
          <button type="button" onClick={handleHint} disabled={!session || !!results}>Hint</button>
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

