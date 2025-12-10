// Example logic tests – modify to match your real state/logic files

import { initialState, login, startGame, quitGame } from "../state";

test("loginSetToFalseUponLaunch", () => {
  expect(initialState.loggedIn).toBe(false);
});

test("ShowleaderboardsSetToFalseUponLaunch", () => {
  expect(initialState.showLeaderboards).toBe(false);
});

test("level1NotLoad", () => {
  expect(initialState.currentLevel).toBe(0);
});

test("SuccessLogin", async () => {
  const result = await login("user", "pass");
  expect(result.success).toBe(true);
});

test("GameStartsUponLogin", () => {
  const game = startGame();
  expect(game.started).toBe(true);
});

test("QuitGame", () => {
  const game = quitGame();
  expect(game.started).toBe(false);
});