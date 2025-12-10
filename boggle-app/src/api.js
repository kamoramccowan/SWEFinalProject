import axios from "axios";

const API_BASE = process.env.REACT_APP_API_BASE || "http://localhost:8000/api";

const api = axios.create({
  baseURL: API_BASE,
});

export function setAuthToken(token) {
  if (token) {
    api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
    localStorage.setItem("authToken", token);
  } else {
    delete api.defaults.headers.common["Authorization"];
    localStorage.removeItem("authToken");
  }
}

// Auth
export async function verifyLogin() {
  const resp = await api.post("/auth/login/verify/");
  return resp.data;
}

// Challenges
export async function fetchMyChallenges() {
  const resp = await api.get("/challenges/mine/");
  return resp.data;
}

export async function createChallenge(payload) {
  const resp = await api.post("/challenges/", payload);
  return resp.data;
}

export async function fetchChallengeBySlug(slug) {
  const resp = await api.get(`/challenges/by-slug/${slug}/`);
  return resp.data;
}

export async function deleteChallenge(id) {
  const resp = await api.delete(`/challenges/${id}/`);
  return resp.data;
}

// Sessions
export async function startSession(challengeId) {
  const resp = await api.post("/sessions/", { challenge_id: challengeId, mode: "challenge" });
  return resp.data;
}

export async function submitWord(sessionId, word) {
  const resp = await api.post(`/sessions/${sessionId}/submit-word/`, { word });
  return resp.data;
}

export async function endSession(sessionId) {
  const resp = await api.post(`/sessions/${sessionId}/end/`);
  return resp.data;
}

export async function sessionResults(sessionId) {
  const resp = await api.get(`/sessions/${sessionId}/results/`);
  return resp.data;
}

export async function sessionHint(sessionId) {
  const resp = await api.get(`/sessions/${sessionId}/hint/`);
  return resp.data;
}

// Leaderboards
export async function fetchDailyLeaderboard() {
  const resp = await api.get("/leaderboards/daily/");
  return resp.data;
}

// Daily challenge
export async function fetchDailyChallenge() {
  const resp = await api.get("/daily-challenge/");
  return resp.data;
}

// Stats
export async function fetchStats() {
  const resp = await api.get("/stats/");
  return resp.data;
}

// Settings
export async function fetchSettings() {
  const resp = await api.get("/settings/");
  return resp.data;
}

export async function updateSettings(payload) {
  const resp = await api.patch("/settings/", payload);
  return resp.data;
}

// Dictionary
export async function fetchDefinition(word) {
  const resp = await api.get(`/words/${encodeURIComponent(word)}/definition/`);
  return resp.data;
}

export default api;
