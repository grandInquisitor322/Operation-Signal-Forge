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

import { SAMPLE_CELL, MOCK_INVESTIGATIONS } from "../mock-data.js";

export function renderDashboard(root, session) {
  const open = MOCK_INVESTIGATIONS.length;
  root.innerHTML = `
    <h1>Dashboard</h1>
    <p class="sub">Welcome, ${session?.name || "user"}. Advisory tools only — Fusion remains off this path.</p>
    <div class="grid">
      <div class="card">
        <h3>Open investigations</h3>
        <div class="metric">${open}</div>
        <p>Mock investigation records</p>
      </div>
      <div class="card">
        <h3>Sample cell fused</h3>
        <div class="metric">${SAMPLE_CELL.fused_probability}</div>
        <p>${SAMPLE_CELL.cell_id}</p>
      </div>
      <div class="card">
        <h3>Your role</h3>
        <div class="metric" style="font-size:1.1rem;color:var(--accent)">${session?.role || "—"}</div>
        <p>Mock AuthZ context</p>
      </div>
    </div>
    <h2>Quick actions</h2>
    <div class="panel row">
      <a class="btn" href="#/investigate?cell_id=${encodeURIComponent(SAMPLE_CELL.cell_id)}">Run investigate_anomaly</a>
      <a class="btn ghost" href="#/brief?cell_id=${encodeURIComponent(SAMPLE_CELL.cell_id)}">View detection brief</a>
      <a class="btn ghost" href="#/investigations">Browse investigations</a>
    </div>
  `;
}