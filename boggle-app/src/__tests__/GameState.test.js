import GameState from "../GameState";

test("GameState initializes without crashing", () => {
  const state = GameState();
  expect(state).toBeDefined();
});