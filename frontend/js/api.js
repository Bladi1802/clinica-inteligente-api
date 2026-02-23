import { API_BASE_URL } from "./config.js";

const ACCESS_KEY = "ci_access";
const REFRESH_KEY = "ci_refresh";

export function setTokens({ access, refresh } = {}) {
  if (access) localStorage.setItem(ACCESS_KEY, access);
  if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
}

export function getAccessToken() {
  return localStorage.getItem(ACCESS_KEY);
}

export function clearTokens() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
}

async function request(path, { method = "GET", body, auth = true } = {}) {
  const headers = { "Content-Type": "application/json" };

  if (auth) {
    const token = getAccessToken();
    if (!token) throw new Error("No hay token. Inicia sesión primero.");
    headers.Authorization = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (res.status === 204) return null;

  const contentType = res.headers.get("content-type") || "";
  const data = contentType.includes("application/json") ? await res.json() : await res.text();

  if (!res.ok) {
    const msg =
      typeof data === "string"
        ? data
        : (data.detail || data.message || JSON.stringify(data));
    throw new Error(`HTTP ${res.status}: ${msg}`);
  }

  return data;
}

export const api = {
  login: (username, password) =>
    request("/api/auth/token/", { method: "POST", auth: false, body: { username, password } }),

  me: () => request("/api/auth/me/"),

  registerUser: (payload) =>
    request("/api/auth/register/", { method: "POST", auth: false, body: payload }),

  listarCitas: () => request("/api/appointments/"),
  crearCita: (payload) => request("/api/appointments/", { method: "POST", body: payload }),
  editarCitaPATCH: (id, payload) => request(`/api/appointments/${id}/`, { method: "PATCH", body: payload }),
  eliminarCita: (id) => request(`/api/appointments/${id}/`, { method: "DELETE" }),
};