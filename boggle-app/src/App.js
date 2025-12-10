import React, { useState, useEffect } from 'react';
import Board from './Board.js';
import GuessInput from './GuessInput.js';
import FoundSolutions from './FoundSolutions.js';
import SummaryResults from './SummaryResults.js';
import ToggleGameState from './ToggleGameState.js';
import { GAME_STATE } from './GameState.js';
import logo from './logo.png';
import './App.css';

// Prefer localhost API by default; allow override via env for other deployments.
const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:8000/api";

function App() {
  const [allSolutions, setAllSolutions] = useState([]);      // solutions from solver
  const [foundSolutions, setFoundSolutions] = useState([]);  // found by user
  const [gameState, setGameState] = useState(GAME_STATE.BEFORE);
  const [grid, setGrid] = useState([]);                      // the grid
  const [totalTime, setTotalTime] = useState(0);             // total time elapsed
  const [size, setSize] = useState(3);                       // selected grid size
  const [game, setGame] = useState({});                      // JSON returned from backend
  const [useSavedGame, setUseSavedGame] = useState(false);
  const [savedGame, setSavedGame] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [savedNames, setSavedNames] = useState([]);
  const [saveError, setSaveError] = useState("");

  // name used to save/load game in localStorage
  const [saveName, setSaveName] = useState("");

  // convert a string (like "['WORD1','WORD2']") into an array of strings
  const Convert = (s) => {
    s = s.replace(/'/g, '');
    s = s.replace('[', '');
    s = s.replace(']', '');
    const tokens = s
      .split(',')
      .map(token => token.trim())
      .filter(token => token !== '');
    return tokens;
  };

  // collect all saved names from localStorage
  function refreshSavedNames() {
    const names = [];
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i);
      if (key && key.startsWith("boggle-save-")) {
        names.push(key.replace("boggle-save-", ""));
      }
    }
    names.sort();
    setSavedNames(names);
  }

  // on first load, discover existing saved games
  useEffect(() => {
    refreshSavedNames();
  }, []);

  // if game ends, remove that saveName from storage (one press nukes the save point)
  useEffect(() => {
    if (gameState === GAME_STATE.ENDED && saveName) {
      localStorage.removeItem(`boggle-save-${saveName}`);
    }
  }, [gameState, saveName]);

  // also clear "saved game mode" when game ends
  useEffect(() => {
    if (gameState === GAME_STATE.ENDED) {
      setSavedGame(null);
      setUseSavedGame(false);
    }
  }, [gameState]);

  // whenever game / grid updates, compute allSolutions from backend `foundwords`
  useEffect(() => {
    if (typeof game.foundwords !== "undefined") {
      let tmpAllSolutions = Convert(game.foundwords);
      setAllSolutions(tmpAllSolutions);
    }
  }, [grid, game.foundwords]);

  // when a new game starts (and it's not a loaded saved game), hit the Django endpoint
  useEffect(() => {
    if (gameState === GAME_STATE.IN_PROGRESS && !useSavedGame) {
      setIsLoading(true);

      const url = `${API_BASE}/game/create/${size}`;
      fetch(url)
        .then((response) => {
          if (!response.ok) {
            throw new Error(`Failed to create game (status ${response.status})`);
          }
          return response.json();
        })
        .then((data) => {
          setGame(data);
          const s = data.grid.replace(/'/g, '"');  // replace single ' with double "
          setGrid(JSON.parse(s));
          setFoundSolutions([]);
        })
        .catch((err) => {
          console.error("Unable to start game:", err.message);
          setSaveError("Unable to start a new game. Please check the backend and try again.");
        })
        .finally(() => {
          setIsLoading(false);
        });
    }
  }, [gameState, size, useSavedGame]);

  function correctAnswerFound(answer) {
    if (!answer) return;

    const normalized =
      answer[0].toUpperCase() + answer.slice(1).toLowerCase();

    console.log("New correct answer:" + normalized);

    if (!foundSolutions.includes(normalized)) {
      setFoundSolutions([...foundSolutions, normalized]);
    }
  }

  function handleEndGame() {
    // delete the current save (so its name can be reused after ending)
    if (saveName) {
      const key = `boggle-save-${saveName}`;
      if (localStorage.getItem(key)) {
        localStorage.removeItem(key);
      }
    }

    setUseSavedGame(false);
    setIsLoading(false);
    refreshSavedNames();
  }

  // save current game to localStorage under saveName
  function handleSaveGame() {
    if (!saveName) {
      setSaveError("Please enter a name for the save.");
      return;
    }

    const key = `boggle-save-${saveName}`;

    // ⬇️ CHANGE: allow overwriting the same save name
    const payload = {
      game,
      grid,
      foundSolutions,
      size,
      totalTime,
    };

    try {
      localStorage.setItem(key, JSON.stringify(payload));
      setSaveError("");
      refreshSavedNames();

      // After saving, go back to the initial screen (no board shown)
      setGameState(GAME_STATE.BEFORE);
      setUseSavedGame(false);
      setIsLoading(false);
    } catch (e) {
      console.log("Error saving game:", e);
      setSaveError("Unable to save game (storage error).");
    }
  }

  // load game from localStorage and start it
  function handleStartSavedGame() {
    if (!saveName) {
      console.log("No save name provided");
      return;
    }

    const raw = localStorage.getItem(`boggle-save-${saveName}`);
    if (!raw) {
      console.log("No saved game found for", saveName);
      return;
    }

    try {
      const payload = JSON.parse(raw);

      if (payload.game) {
        setGame(payload.game);
      }
      if (payload.grid) {
        setGrid(payload.grid);
      }
      if (payload.foundSolutions) {
        setFoundSolutions(payload.foundSolutions);
      } else {
        setFoundSolutions([]);
      }
      if (typeof payload.size === "number") {
        setSize(payload.size);
      }
      if (typeof payload.totalTime === "number") {
        setTotalTime(payload.totalTime);
      }

      setUseSavedGame(true);
      setIsLoading(false);
      setSaveError("");
      setGameState(GAME_STATE.IN_PROGRESS);
    } catch (e) {
      console.log("Unable to load saved game:", e);
    }
  }

  return (
    <div className="App">
      <img
        src={logo}
        width="25%"
        height="25%"
        className="logo"
        alt="Bison Boggle Logo"
      />

      <ToggleGameState
        gameState={gameState}
        setGameState={(state) => {
          // whenever we use the normal controls, go back to "fresh game" mode
          setUseSavedGame(false);
          setGameState(state);
        }}
        setSize={(state) => setSize(state)}
        setTotalTime={(state) => setTotalTime(state)}
        onEndGame={handleEndGame}
        saveName={saveName}
        setSaveName={setSaveName}
        savedNames={savedNames}
        saveError={saveError}
        onSaveGame={handleSaveGame}
        onStartSavedGame={handleStartSavedGame}
        isLoading={isLoading}
      />

      {/* save / load controls */}
      <div style={{ marginTop: '1rem' }}>
        <input
          type="text"
          value={saveName}
          onChange={(e) => setSaveName(e.target.value)}
          placeholder="Save name"
          style={{ padding: '0.25rem', minWidth: '160px' }}
        />
        <button onClick={handleSaveGame} style={{ marginLeft: '0.5rem' }}>
          Save Game
        </button>
        <button onClick={handleStartSavedGame} style={{ marginLeft: '0.5rem' }}>
          Start Saved Game
        </button>
        {saveError && (
          <div style={{ color: 'red', marginTop: '0.5rem' }}>
            {saveError}
          </div>
        )}
      </div>

      {gameState === GAME_STATE.IN_PROGRESS && (
        <div>
          {isLoading ? (
            <p style={{ marginTop: '2rem', fontSize: '1.5rem' }}>Loading game…</p>
          ) : (
            <>
              <Board board={grid} />

              <GuessInput
                allSolutions={allSolutions}
                foundSolutions={foundSolutions}
                correctAnswerCallback={(answer) => correctAnswerFound(answer)}
              />

              <FoundSolutions
                headerText="Solutions you've found"
                words={foundSolutions}
              />
            </>
          )}
        </div>
      )}

      {gameState === GAME_STATE.ENDED && (
        <div>
          <Board board={grid} />
          <SummaryResults words={foundSolutions} totalTime={totalTime} />

          {/* Words you DID find */}
          <FoundSolutions
            headerText="Solutions you've found"
            words={foundSolutions}
          />

          {/* Remaining / missed words */}
          <FoundSolutions
            headerText="Missed Words [wordsize > 3]: "
            words={allSolutions.filter((w) => !foundSolutions.includes(w))}
          />
        </div>
      )}
    </div>
  );
}

export default App;
