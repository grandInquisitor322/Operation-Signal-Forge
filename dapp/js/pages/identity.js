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

export function renderIdentity(root, session) {
    if (!session) {
      root.innerHTML = `<p class="err">Not logged in</p>`;
      return;
    }
  
    const creds = [
      {
        type: session.role,
        issuer: session.org,
        status: "active (mock)",
        expires: "2027-01-01",
      },
      {
        type: "OrganizationMembership",
        issuer: session.org,
        status: "active (mock)",
        expires: "2027-01-01",
      },
    ];
  
    root.innerHTML = `
      <h1>Identity</h1>
      <p class="sub">Mock DID &amp; credentials — illustrates AuthZ context only.</p>
      <div class="panel">
        <p><strong>Name:</strong> ${session.name}</p>
        <p><strong>Email:</strong> ${session.email}</p>
        <p><strong>DID:</strong> <code>${session.did}</code></p>
        <p><strong>Organization:</strong> <code>${session.org}</code></p>
        <p><strong>Role:</strong> <span class="tag active">${session.role}</span></p>
        <p><strong>Logged in at:</strong> ${session.loggedInAt}</p>
        <h3>Derived scopes</h3>
        <p>${session.scopes.map((s) => `<span class="tag">${s}</span> `).join("")}</p>
        <h3>Mock credentials</h3>
        <table>
          <thead><tr><th>Type</th><th>Issuer</th><th>Status</th><th>Expires</th></tr></thead>
          <tbody>
            ${creds
              .map(
                (c) =>
                  `<tr><td>${c.type}</td><td><code>${c.issuer}</code></td><td>${c.status}</td><td>${c.expires}</td></tr>`
              )
              .join("")}
          </tbody>
        </table>
      </div>
    `;
  }