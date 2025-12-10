
import { render } from "@testing-library/react";
import GuessInput from "../GuessInput";

test("GuessInput renders without crashing", () => {
  render(<GuessInput addGuess={() => {}} />);
});