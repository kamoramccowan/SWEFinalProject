import GameState from "../GameState";

test("initial game state loads correctly", () => {
  const state = GameState();

  expect(state.score).toBe(0);
  expect(state.foundWords).toEqual([]);
  expect(state.board).toBeDefined();
});