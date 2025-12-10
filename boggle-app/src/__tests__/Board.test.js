import { render } from "@testing-library/react";
import Board from "../Board";

test("Board renders without crashing", () => {
  render(<Board board={[]} />);
});