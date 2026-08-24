/**
 * Copyright 2026 Operation Signal Forge contributors
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/**
 * Client session helper — authentication is performed by dapp_api.
 * No local password check for authorization decisions.
 */

const SESSION_KEY = "sf_dapp_session";
const API_BASE = localStorage.getItem("sf_dapp_api") || "http://127.0.0.1:8787";

/**
 * Login against server. On success stores token + AuthZContext.
 * Fails closed if API is unreachable (no local privilege grant).
 */
export async function login(email, password) {
  let res;
  try {
    res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
  } catch {
    return {
      ok: false,
      error: "Auth API unreachable. Start: python dapp_api/app.py",
    };
  }

  let data = {};
  try {
    data = await res.json();
  } catch {
    return { ok: false, error: "Invalid response from auth API" };
  }

  if (!res.ok || !data.token) {
    return { ok: false, error: data.error || "Login failed" };
  }

  const authz = data.authz || {};
  const session = {
    email: authz.email || String(email).trim().toLowerCase(),
    name: authz.name || "",
    role: authz.role || "",
    scopes: authz.scopes || [],
    did: authz.subject_id || "",
    org: authz.org_id || "",
    token: data.token,
    authz,
    source: "server",
    loggedInAt: new Date().toISOString(),
  };
  localStorage.setItem(SESSION_KEY, JSON.stringify(session));
  return { ok: true, session };
}

export async function logout() {
  const s = getSession();
  if (s?.token) {
    try {
      await fetch(`${API_BASE}/auth/logout`, {
        method: "POST",
        headers: { Authorization: `Bearer ${s.token}` },
      });
    } catch {
      /* ignore network errors on logout */
    }
  }
  localStorage.removeItem(SESSION_KEY);
}

export function getSession() {
  try {
    const raw = localStorage.getItem(SESSION_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function isLoggedIn() {
  const s = getSession();
  return !!(s && s.token);
}

export function getAccessToken() {
  return getSession()?.token || null;
}