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

import { MOCK_INVESTIGATIONS } from "../mock-data.js";

export function renderInvestigations(root) {
  const rows = MOCK_INVESTIGATIONS.map(
    (i) => `
    <tr>
      <td>${i.id}</td>
      <td><a class="link" href="#/investigate?cell_id=${encodeURIComponent(i.cell_id)}">${i.cell_id}</a></td>
      <td>${i.site_id}</td>
      <td>${i.fused_probability}</td>
      <td><span class="tag active">${i.status}</span></td>
      <td>${i.summary}</td>
    </tr>`
  ).join("");

  root.innerHTML = `
    <h1>Investigations</h1>
    <p class="sub">Browse advisory investigation records (mock list + live run on Investigate).</p>
    <div class="panel">
      <table>
        <thead>
          <tr>
            <th>ID</th><th>Cell</th><th>Site</th><th>Fused</th><th>Status</th><th>Summary</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}