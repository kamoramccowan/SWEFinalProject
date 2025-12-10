import { render, screen, fireEvent } from "@testing-library/react";
import GuessInput from "../GuessInput";

test("allows user to type a guess", () => {
  render(<GuessInput addGuess={() => {}} />);

  const input = screen.getByPlaceholderText(/enter word/i);
  fireEvent.change(input, { target: { value: "test" } });

  expect(input.value).toBe("test");
});