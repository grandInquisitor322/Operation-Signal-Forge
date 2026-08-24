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
 * Capability API client — requires server Bearer token.
 * 401/403 are returned to the UI (no privileged mock bypass).
 * Offline mock only when the API is unreachable AND the caller already
 * holds a server session is not available — then fail closed for investigate.
 */
import { SAMPLE_CELL, mockBrief, mockInvestigate, mockRecommend } from "./mock-data.js";
import { getAccessToken } from "./mock-auth.js";

const API_BASE = localStorage.getItem("sf_dapp_api") || "http://127.0.0.1:8787";

async function tryFetch(path, body) {
  const token = getAccessToken();
  if (!token) {
    return {
      ok: false,
      error: "Not authenticated — log in against the AuthZ API",
      status: 401,
      source: "client",
    };
  }

  const headers = {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };

  try {
    const res = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));

    if (res.status === 401 || res.status === 403) {
      return {
        ok: false,
        error: data.error || `HTTP ${res.status}`,
        status: res.status,
        data,
        source: "api",
      };
    }
    if (!res.ok) {
      return {
        ok: false,
        error: data.error || `HTTP ${res.status}`,
        status: res.status,
        data,
        source: "api",
      };
    }
    return { ok: true, data, source: "api" };
  } catch (e) {
    return {
      ok: false,
      error: `Auth API unreachable: ${e}`,
      network: true,
      source: "network",
    };
  }
}

export async function generateBrief(cellId = SAMPLE_CELL.cell_id) {
  return tryFetch("/capabilities/generate_detection_brief", { cell_id: cellId });
}

export async function recommendNextSensor(cellId = SAMPLE_CELL.cell_id) {
  return tryFetch("/capabilities/recommend_next_sensor", { cell_id: cellId });
}

export async function investigateAnomaly(cellId = SAMPLE_CELL.cell_id) {
  return tryFetch("/capabilities/investigate_anomaly", { cell_id: cellId });
}

/**
 * Optional: UI-only preview when documenting mock shapes (not used for authZ).
 * Do not call these for real authorization paths.
 */
export function debugMockBrief() {
  return mockBrief();
}
export function debugMockInvestigate() {
  return mockInvestigate();
}
export function debugMockRecommend() {
  return mockRecommend();
}