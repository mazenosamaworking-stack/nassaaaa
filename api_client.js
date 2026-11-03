/**
 * NASA Space Fire AI - Official Front-End Integration Client SDK (v3.1)
 * Drop this file into your front-end project (React, Vue, Svelte, or Vanilla JS)
 * to connect all 4 AI agents with 1 single line of configuration.
 */

class SpaceFireClient {
  /**
   * @param {string} baseUrl - The deployed backend URL (e.g. 'https://your-app.onrender.com' or 'http://localhost:8500')
   */
  constructor(baseUrl = 'http://localhost:8500') {
    this.baseUrl = baseUrl.replace(/\/$/, '');
  }

  /**
   * Change backend endpoint URL dynamically (e.g. switching between local test and GitHub/Cloud deployment)
   * @param {string} newUrl 
   */
  setBaseUrl(newUrl) {
    this.baseUrl = newUrl.replace(/\/$/, '');
  }

  // =========================================================================
  // AGENT 1: NASA Spacecraft Fire Risk Predictor
  // =========================================================================
  /**
   * Predicts fire occurrence probability and qualitative diagnosis
   * @param {Object} inputVariables - Object containing your dynamic fields, e.g.:
   *   { o2_percent: 24.5, cabin_pressure_kpa: 101.3, ambient_temp_c: 25.0, co_percent: 0.1 }
   * @returns {Promise<{
   *   fire_probability_percent: number,
   *   hazard_level: string,
   *   severity_code: string,
   *   hazard_color: string,
   *   description: string,
   *   feature_contributions: Object
   * }>}
   */
  async predictFireRisk(inputVariables) {
    const res = await fetch(`${this.baseUrl}/api/predict/agent1`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ variables: inputVariables })
    });
    if (!res.ok) throw new Error(`Agent 1 prediction failed: ${res.statusText}`);
    return await res.json();
  }

  // =========================================================================
  // AGENT 2: Spacecraft Fire Incident Safety & Emergency Assistant (LLM-RAG)
  // =========================================================================
  /**
   * Sends user description of fire/anomaly and returns data-grounded safety protocol
   * @param {string} userMessage - e.g. "أرى شرراً ودخاناً خفيفاً في لوحة التوزيع"
   * @returns {Promise<{
   *   chat_response_markdown: string,
   *   root_cause_diagnosis: string,
   *   affected_subsystem: string,
   *   hazard_level: string,
   *   recommended_actions: Array<string>
   * }>}
   */
  async askSafetyAssistant(userMessage) {
    const res = await fetch(`${this.baseUrl}/api/chat/agent2`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: userMessage })
    });
    if (!res.ok) throw new Error(`Agent 2 query failed: ${res.statusText}`);
    return await res.json();
  }

  // =========================================================================
  // AGENT 3: Real-Time ISS Live Telemetry Streamer (1-Second Tick)
  // =========================================================================
  /**
   * Subscribes to live SSE stream ticking every 1 second
   * @param {Function} onTickCallback - Callback receiving live ISS telemetry & AI fire evaluation
   * @param {Function} onErrorCallback - Optional error callback
   * @returns {EventSource} The active SSE connection (call .close() to unsubscribe)
   */
  subscribeISSTelemetry(onTickCallback, onErrorCallback = null) {
    const eventSource = new EventSource(`${this.baseUrl}/api/stream/agent3`);
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onTickCallback(data);
      } catch (err) {
        console.error('Failed to parse ISS telemetry packet:', err);
      }
    };
    if (onErrorCallback) {
      eventSource.onerror = onErrorCallback;
    }
    return eventSource;
  }

  /**
   * Fetches single current snapshot of ISS telemetry without streaming
   */
  async getISSSnapshot() {
    const res = await fetch(`${this.baseUrl}/api/iss/current`);
    if (!res.ok) throw new Error(`ISS snapshot failed: ${res.statusText}`);
    return await res.json();
  }

  // =========================================================================
  // AGENT 4: AI & CFD Flame Dynamics & Visual Simulation
  // =========================================================================
  /**
   * Simulates flame geometry and CFD thermal matrix
   * @param {Object} conditions - e.g.:
   *   { fuel_material: 'PMMA', gravity_level_g: 0.0, sim_o2_percent: 21.0, sim_pressure_kpa: 101.3 }
   * @returns {Promise<{
   *   aspect_ratio: number,
   *   flame_radius_mm: number,
   *   peak_temperature_k: number,
   *   blue_chemiluminescence_ratio: number,
   *   flicker_frequency_hz: number,
   *   burning_rate_mms: number,
   *   visual_spec: {
   *     flame_type: string,
   *     svg_outer_path: string,
   *     svg_core_path: string,
   *     color_palette: Object
   *   },
   *   cfd_thermal_grid: {
   *     max_temp_k: number,
   *     scalar_matrix: Array<Array<number>>
   *   }
   * }>}
   */
  async simulateFlame(conditions) {
    const res = await fetch(`${this.baseUrl}/api/simulate/agent4`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ variables: conditions })
    });
    if (!res.ok) throw new Error(`Agent 4 simulation failed: ${res.statusText}`);
    return await res.json();
  }

  /**
   * Fetches registered combustion fuel materials
   */
  async getMaterials() {
    const res = await fetch(`${this.baseUrl}/api/materials`);
    if (!res.ok) throw new Error(`Failed to load materials: ${res.statusText}`);
    return await res.json();
  }

  /**
   * Universal dataset ingestion and AI model training endpoint for any agent
   * @param {string} agentId - 'agent1', 'agent2', 'agent3', or 'agent4'
   * @param {string} batchName - Name/Identifier for this batch
   * @param {string} formatType - 'csv', 'json', 'excel', 'pdf', 'scientific_array', 'image', 'video', 'text'
   * @param {string} content - Raw content (string, CSV/JSON text, or Base64 for binary)
   * @param {Array<string>} userDefinedVariables - Optional custom variable tags
   * @param {string} filename - Optional file name
   */
  async uploadDataset(agentId, batchName, formatType, content, userDefinedVariables = [], filename = null) {
    const res = await fetch(`${this.baseUrl}/api/upload/${agentId}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        batch_name: batchName,
        format_type: formatType,
        content: content,
        user_defined_variables: userDefinedVariables,
        filename: filename || `${batchName}.${formatType}`
      })
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.error || `Upload failed: ${res.statusText}`);
    }
    return await res.json();
  }

  // =========================================================================
  // DYNAMIC SCHEMAS & FIELD SPECIFICATION
  // =========================================================================
  /**
   * Automatically retrieves dynamic prediction fields configured on the server
   * Allows your frontend to dynamically render input fields without hardcoding!
   * @param {string} agentId - 'agent1' or 'agent4'
   */
  async getDynamicFields(agentId = 'agent1') {
    const res = await fetch(`${this.baseUrl}/api/variables?agent_id=${agentId}&only_prediction=1`);
    if (!res.ok) throw new Error(`Failed to load fields: ${res.statusText}`);
    return await res.json();
  }
}

// Export for ES Modules (React / Next.js / Vite) and Node.js
if (typeof module !== 'undefined' && module.exports) {
  module.exports = SpaceFireClient;
}
if (typeof window !== 'undefined') {
  window.SpaceFireClient = SpaceFireClient;
}
