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

import { TRUST_REGISTRY } from "../mock-data.js";

export function renderTrustRegistry(root) {
  const rows = TRUST_REGISTRY.map((e) => {
    const st =
      e.status === "active"
        ? "active"
        : e.status === "suspended"
          ? "suspended"
          : "";
    return `
      <tr>
        <td>${e.display_name}</td>
        <td><code>${e.issuer_did}</code></td>
        <td><span class="tag ${st}">${e.status}</span></td>
        <td>${e.allowed_credential_types.join(", ")}</td>
        <td>${e.revocation_method}</td>
        <td>${e.effective_from}</td>
      </tr>`;
  }).join("");

  root.innerHTML = `
    <h1>Trust Registry</h1>
    <p class="sub">Mock trusted issuers — no chain. Verifiers would consult this list in production.</p>
    <div class="panel">
      <table>
        <thead>
          <tr>
            <th>Name</th><th>Issuer DID</th><th>Status</th>
            <th>Allowed types</th><th>Revocation</th><th>Effective</th>
          </tr>
        </thead>
        <tbody>${rows}</tbody>
      </table>
    </div>
  `;
}