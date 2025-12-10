import React, { useState } from "react";
import { fetchDefinition } from "../api";
import "./DefinitionLookup.css";

export default function DefinitionLookup() {
  const [word, setWord] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLookup = async () => {
    if (!word) return;
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const data = await fetchDefinition(word);
      setResult(data);
    } catch (err) {
      setError("Definition not found or service unavailable.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="def-card">
      <div className="def-row">
        <input
          value={word}
          onChange={(e) => setWord(e.target.value)}
          placeholder="Lookup word"
        />
        <button onClick={handleLookup} disabled={loading}>
          {loading ? "Searching..." : "Define"}
        </button>
      </div>
      {error && <div className="error">{error}</div>}
      {result && (
        <div className="def-results">
          <h4>{result.word}</h4>
          <ul>
            {(result.definitions || []).map((d, idx) => (
              <li key={idx}>
                <strong>{d.part_of_speech}</strong>: {d.definition}
                {d.example && <em> — {d.example}</em>}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
