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

/** Mock operational + identity data for UX prototype */

export const SAMPLE_CELL = {
  cell_id: "10.4806_-66.9036",
  site_id: "caracas-site-7",
  lat: 10.4806,
  lon: -66.9036,
  radar_score: 0.72,
  thermal_score: 0.55,
  acoustic_score: 0.4,
  starlink_score: 0.63,
  celltower_score: 0.0,
  fused_probability: 0.81,
  status: "unassigned",
};

export const TRUST_REGISTRY = [
  {
    issuer_did: "did:example:org-relief-alpha",
    display_name: "Relief Alpha NGO",
    status: "active",
    allowed_credential_types: [
      "OrganizationMembership",
      "HumanitarianAnalyst",
      "IncidentCommander",
      "SensorOperator",
    ],
    revocation_method: "status_list",
    effective_from: "2026-01-15",
  },
  {
    issuer_did: "did:example:org-partner-research",
    display_name: "Partner Research Institute",
    status: "active",
    allowed_credential_types: ["ResearchPartner", "OrganizationMembership"],
    revocation_method: "status_endpoint",
    effective_from: "2026-03-01",
  },
  {
    issuer_did: "did:example:org-suspended-demo",
    display_name: "Demo Suspended Org",
    status: "suspended",
    allowed_credential_types: ["HumanitarianAnalyst"],
    revocation_method: "status_list",
    effective_from: "2025-11-01",
  },
];

export const MOCK_INVESTIGATIONS = [
  {
    id: "inv-001",
    cell_id: "10.4806_-66.9036",
    site_id: "caracas-site-7",
    status: "complete",
    fused_probability: 0.81,
    created_at: "2026-08-05T14:22:00Z",
    summary: "Elevated multi-sensor confidence; advisory triage priority",
  },
  {
    id: "inv-002",
    cell_id: "10.4810_-66.9040",
    site_id: "caracas-site-7",
    status: "complete",
    fused_probability: 0.42,
    created_at: "2026-08-04T09:10:00Z",
    summary: "Moderate confidence; corroboration recommended",
  },
];

export function mockBrief(cell = SAMPLE_CELL) {
  const fused = cell.fused_probability;
  const band = fused >= 0.75 ? "high" : fused >= 0.4 ? "moderate" : "low";
  return {
    headline: `Cell ${cell.cell_id} @ site ${cell.site_id}: fused=${fused.toFixed(3)} (${band}), status=${cell.status}`,
    cell_id: cell.cell_id,
    site_id: cell.site_id,
    lat: cell.lat,
    lon: cell.lon,
    status: cell.status,
    fused_probability: fused,
    confidence_band: band,
    scores: {
      radar: cell.radar_score,
      thermal: cell.thermal_score,
      acoustic: cell.acoustic_score,
      starlink: cell.starlink_score,
      celltower: cell.celltower_score,
    },
    active_modalities: ["radar", "thermal", "acoustic", "starlink"],
    narrative: "Active modalities: radar, thermal, acoustic, starlink.",
    recommendations: [
      "Prioritize ground team assessment; high-confidence triage lead only.",
      "Cell unassigned — command may set status to searching.",
    ],
    advisory_only: true,
  };
}

export function mockRecommend(cell = SAMPLE_CELL) {
  return {
    recommendation_status: "complete",
    cell_id: cell.cell_id,
    site_id: cell.site_id,
    recommended_sensor: "celltower",
    priority: "low",
    expected_investigative_value:
      "Incremental improvement on weakest modality (celltower)",
    rationale:
      "Evidence coverage is relatively complete; residual value is incremental.",
    why_selected:
      "celltower was selected because residual gap is celltower enrichment.",
    advisory_only: true,
    does_not_task_sensors: true,
    current_fused_probability: cell.fused_probability,
  };
}

export function mockInvestigate(cell = SAMPLE_CELL) {
  const brief = mockBrief(cell);
  const next = mockRecommend(cell);
  return {
    investigation_status: "complete",
    cell_id: cell.cell_id,
    site_id: cell.site_id,
    overall_assessment:
      "Elevated fused confidence with usable multi-sensor context. Treat as a triage priority for human review, not a confirmed find.",
    confidence_explanation: `Fused probability is ${cell.fused_probability.toFixed(
      3
    )} from the Fusion Engine (deterministic). Capability Layer does not recompute fusion.`,
    detection_brief: brief,
    next_sensor: next,
    supporting_capabilities: [
      { capability: "generate_detection_brief", status: "ok" },
      { capability: "recommend_next_sensor", status: "ok" },
    ],
    recommended_actions: [
      "Queue for analyst review and possible ground-team tasking.",
      `Next sensor suggestion (${next.priority}): ${next.recommended_sensor}.`,
    ],
    analyst_considerations: [
      "This output is advisory decision support only.",
      "Do not clear or confirm a cell solely on this investigation result.",
    ],
    advisory_only: true,
    does_not_modify_system_state: true,
  };
}