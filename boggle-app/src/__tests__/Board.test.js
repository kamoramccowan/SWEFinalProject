import { render, screen } from "@testing-library/react";
import Board from "../Board";

test("renders board grid", () => {
  const board = [
    ["A", "B", "C", "D"],
    ["E", "F", "G", "H"],
    ["I", "J", "K", "L"],
    ["M", "N", "O", "P"],
  ];

  render(<Board board={board} />);

  expect(screen.getByText("A")).toBeInTheDocument();
  expect(screen.getByText("P")).toBeInTheDocument();
});