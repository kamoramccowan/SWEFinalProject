import React from "react";
import "./Board.css";

export default function Board({ board }) {
  // Normalize board to an array of arrays of strings
  const normalized = Array.isArray(board)
    ? board.map((row) => (Array.isArray(row) ? row : Object.values(row || {})))
    : Object.values(board || {}).map((row) => Object.values(row || {}));

  const size = normalized.length || 0;

  return (
    <div className="Board-div" style={{ gridTemplateColumns: `repeat(${size || 1}, 1fr)` }}>
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
