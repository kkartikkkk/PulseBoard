import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const api = axios.create({ baseURL: BASE_URL });

// Attach JWT token automatically
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("pb_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ── Auth ──────────────────────────────────────────────────────────────────
export const register = (email, password) =>
  api.post("/auth/register", { email, password });

export const login = async (email, password) => {
  const form = new FormData();
  form.append("username", email);
  form.append("password", password);
  const res = await api.post("/auth/login", form);
  localStorage.setItem("pb_token", res.data.access_token);
  return res.data;
};

export const logout = () => localStorage.removeItem("pb_token");

export const getProjects = () => api.get("/auth/projects");
export const createProject = (name) => api.post("/auth/projects", { name });

// ── Analytics ─────────────────────────────────────────────────────────────
export const getSummary = (projectId) =>
  api.get(`/analytics/${projectId}/summary`);

export const getMetrics = (projectId, hours = 24, endpoint = null) =>
  api.get(`/analytics/${projectId}/metrics`, {
    params: { hours, ...(endpoint ? { endpoint } : {}) },
  });

export const getAlerts = (projectId, unresolvedOnly = false) =>
  api.get(`/analytics/${projectId}/alerts`, {
    params: { unresolved_only: unresolvedOnly },
  });

export const resolveAlert = (projectId, alertId) =>
  api.patch(`/analytics/${projectId}/alerts/${alertId}/resolve`);

// ── WebSocket ─────────────────────────────────────────────────────────────
export const createLiveSocket = (projectId, onMessage) => {
  const WS_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000")
    .replace("http", "ws");
  const ws = new WebSocket(`${WS_URL}/analytics/${projectId}/live`);
  ws.onmessage = (e) => onMessage(JSON.parse(e.data));
  ws.onerror = (e) => console.error("WebSocket error", e);
  return ws;
};
