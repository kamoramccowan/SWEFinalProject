import { render } from "@testing-library/react";
import Board from "../Board";

test("Board component renders without crashing", () => {
  render(<Board board={[]} />);
});