import { apiRequest } from "./api";

const ACCESS_KEY = "ci_access_token";
const REFRESH_KEY = "ci_refresh_token";
const USER_KEY = "ci_user";

export async function loginUser(credentials) {
  return apiRequest("/api/auth/token/", {
    method: "POST",
    body: JSON.stringify(credentials),
  });
}

export async function registerPatient(payload) {
  return apiRequest("/api/auth/register/", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchMe(token) {
  return apiRequest("/api/auth/me/", {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
}

export function saveSession({ access, refresh, user }) {
  localStorage.setItem(ACCESS_KEY, access);
  localStorage.setItem(REFRESH_KEY, refresh);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function getAccessToken() {
  return localStorage.getItem(ACCESS_KEY);
}

export function getRefreshToken() {
  return localStorage.getItem(REFRESH_KEY);
}

export function getStoredUser() {
  const raw = localStorage.getItem(USER_KEY);
  return raw ? JSON.parse(raw) : null;
}

export function isAuthenticated() {
  return Boolean(getAccessToken());
}

export function getRoleHomePath(role) {
  if (role === "PATIENT") return "/patient";
  if (role === "DOCTOR") return "/doctor";
  if (role === "CLINIC") return "/clinic";
  return "/login";
}

export function clearSession() {
  localStorage.removeItem(ACCESS_KEY);
  localStorage.removeItem(REFRESH_KEY);
  localStorage.removeItem(USER_KEY);
}
