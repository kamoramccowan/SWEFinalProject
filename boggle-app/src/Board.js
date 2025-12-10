import React from "react";
import "./Board.css";

export default function Board({ board }) {
  // Normalize board to an array of arrays of strings
  const normalized = Array.isArray(board)
    ? board.map((row) => (Array.isArray(row) ? row : Object.values(row || {})))
    : Object.values(board || {}).map((row) => Object.values(row || {}));

  const rows = normalized.length || 0;
  const cols = rows && normalized[0] ? normalized[0].length || 0 : 0;

  return (
    <div className="Board-div" style={{ gridTemplateColumns: `repeat(${cols || 1}, 1fr)` }}>
      {normalized.map((row, rIdx) =>
        row.map((cell, cIdx) => (
          <div className="Tile" key={`${rIdx}-${cIdx}`}>
            <div className="Tile-inner">[{cell || " "}]</div>
          </div>
        ))
      )}
    </div>
  );
}
