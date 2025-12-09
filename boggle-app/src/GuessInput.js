import React, { useState } from 'react';
import TextField from "@material-ui/core/TextField";
import './GuessInput.css';

function GuessInput({allSolutions, foundSolutions, correctAnswerCallback}) {

  const [labelText, setLabelText] = useState("Make your first guess!");
  const [input, setInput] = useState("");

  // helper to normalize for case-insensitive compare
  const norm = (w) => w.trim().toUpperCase();

  function evaluateInput() {
    const guess = norm(input);

    const foundNorm = foundSolutions.map(norm);
    const allNorm   = allSolutions.map(norm);

    if (foundNorm.includes(guess)) {
      setLabelText(input + " has already been found!");
    } else if (allNorm.includes(guess)) {
      correctAnswerCallback(input);
      setLabelText(input + " is correct!");
    } else {
      setLabelText(input + " is incorrect!");
    }
  }

  function keyPress(e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      evaluateInput();
      setInput("");
      e.target.value = "";
    }
  }

  return (
    <div className="Guess-input">
      <div>
        {labelText}
      </div>
      <TextField
        value={input}
        onKeyPress={(e) => keyPress(e)}
        onChange={(event) => setInput(event.target.value)}
      />
    </div>
  );
}

export default GuessInput;
