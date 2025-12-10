import { render, screen } from "@testing-library/react";
import App from "../App";

test("renders Boggle Boost application", () => {
  render(<App />);
  expect(screen.getByText(/boggle/i)).toBeInTheDocument();
});