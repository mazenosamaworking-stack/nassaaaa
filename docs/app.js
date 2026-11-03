/**
 * NASA Space Fire AI System v3.0 - Central Brain Client & Mission Control
 * Features:
 * - Multi-format ingestion for all 4 agents (JSON, CSV, Excel, PDF, Arrays, Media, Text)
 * - User-typed dynamic variables without restricted lists
 * - Agent 2 Custom LLM Config & Data-Grounded RAG
 * - Agent 3 ISS Live API config & Mandatory Training Gate
 * - Agent 4 Dynamic Materials, Conditions, CFD Heatmap & Visual Mirroring
 * - Complete 2-Way Input & Output Front-End Mapping Contracts
 */

const API_BASE = window.location.origin;

let appState = {
    activeTab: 'tab-agent1',
    allVariables: [],
    agent4Materials: [],
    flameSimParams: {
        fuel_material: 'PMMA'
    },
    latestFlameVisualSpec: null,
    currentSimView: 'flame', // 'flame' or 'cfd'
    issEventSource: null,
    flameAnimFrameId: null
};

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    loadAllVariables();
    initAgent1();
    initAgent2LLM();
    initAgent3ISS();
    initAgent4Simulator();
    initVariableManager();
    initUniversalIngestion();
    loadAgentsTrainingStatus();
    refreshAllDashboardSnippets();
});

function refreshAllDashboardSnippets() {
    // Dynamically replace any hardcoded ports in code blocks with the true deployed domain
    const blocks = document.querySelectorAll('.code-block');
    blocks.forEach(block => {
        if (block.textContent.includes('localhost:8500') || block.textContent.includes('localhost:8000')) {
            block.textContent = block.textContent
                .replaceAll('http://localhost:8500', API_BASE)
                .replaceAll('http://localhost:8000', API_BASE);
        }
    });
}

// Toast notification
function showToast(message) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3500);
}

// Clipboard copy
window.copySnippet = function(elementId) {
    const el = document.getElementById(elementId);
    if (!el) return;
    navigator.clipboard.writeText(el.innerText).then(() => {
        showToast('✅ تم نسخ كود الربط إلى الحافظة بنجاح!');
    });
};

/* ==========================================================================
   TABS MANAGEMENT
   ========================================================================== */
function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetId = btn.getAttribute('data-tab');
            tabBtns.forEach(b => b.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));

            btn.classList.add('active');
            const targetPane = document.getElementById(targetId);
            if (targetPane) targetPane.classList.add('active');
            appState.activeTab = targetId;

            if (targetId === 'tab-agent4') {
                triggerFlameSimulation();
            } else if (targetId === 'tab-variables') {
                load2WayContract();
            } else if (targetId === 'tab-training') {
                loadAgentsTrainingStatus();
            }
        });
    });
}

/* ==========================================================================
   GLOBAL VARIABLES MANAGEMENT
   ========================================================================== */
async function loadAllVariables() {
    try {
        const res = await fetch(`${API_BASE}/api/variables`);
        const data = await res.json();
        appState.allVariables = data.variables || [];
        renderVariablesTable();
        renderAgent1Fields();
        renderAgent4Conditions();
        load2WayContract();
    } catch (err) {
        console.error('Error loading variables:', err);
    }
}

/* ==========================================================================
   AGENT 1: NASA FIRE RISK PREDICTOR (DYNAMIC USER-DEFINED INPUTS)
   ========================================================================== */
function initAgent1() {
    const form = document.getElementById('agent1-predict-form');
    const resetBtn = document.getElementById('btn-reset-agent1');

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await runAgent1Prediction();
    });

    resetBtn.addEventListener('click', () => {
        renderAgent1Fields();
        showToast('تمت إعادة ضبط القيم النموذجية');
    });
}

function renderAgent1Fields() {
    const container = document.getElementById('agent1-dynamic-fields-container');
    container.innerHTML = '';

    const activeVars = appState.allVariables.filter(v => 
        (v.agent_id === 'agent1' || v.agent_id === 'global') && v.is_active_for_prediction === 1
    );

    activeVars.forEach(v => {
        const group = document.createElement('div');
        group.className = 'field-group';

        const labelRow = document.createElement('div');
        labelRow.className = 'field-label';
        labelRow.innerHTML = `<span>${v.name_ar}</span> <span class="field-unit">${v.unit || ''}</span>`;

        let input;
        if (v.data_type === 'number') {
            input = document.createElement('input');
            input.type = 'number';
            input.step = 'any';
            if (v.min_val !== null) input.min = v.min_val;
            if (v.max_val !== null) input.max = v.max_val;
            input.value = v.default_val;
        } else {
            input = document.createElement('input');
            input.type = 'text';
            input.value = v.default_val;
        }
        input.className = 'field-input';
        input.name = v.id;
        input.id = `input_${v.id}`;

        const desc = document.createElement('span');
        desc.className = 'field-desc';
        desc.textContent = v.description || `المعرف: ${v.id}`;

        group.appendChild(labelRow);
        group.appendChild(input);
        group.appendChild(desc);
        container.appendChild(group);
    });

    updateAgent12WaySnippet();
}

async function updateAgent12WaySnippet() {
    try {
        const res = await fetch(`${API_BASE}/api/frontend-contract/agent1`);
        const contract = await res.json();
        const snippetEl = document.getElementById('agent1-fetch-snippet');
        if (snippetEl) {
            // Replace with current origin if contract returns default
            const code = contract.complete_fetch_snippet.replaceAll('http://localhost:8500', API_BASE);
            snippetEl.textContent = code;
        }
    } catch (e) {
        console.warn('Contract fetch error:', e);
    }
}

async function runAgent1Prediction() {
    const btn = document.getElementById('btn-predict-agent1');
    btn.disabled = true;
    btn.innerHTML = '<span>⏳ جاري التحليل بالذكاء الاصطناعي...</span>';

    const inputs = {};
    const fieldInputs = document.querySelectorAll('#agent1-dynamic-fields-container .field-input');
    fieldInputs.forEach(inp => {
        inputs[inp.name] = inp.value;
    });

    try {
        const res = await fetch(`${API_BASE}/api/predict/agent1`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ variables: inputs })
        });
        const result = await res.json();

        // Update UI
        const probVal = document.getElementById('agent1-prob-val');
        const probBar = document.getElementById('agent1-prob-bar');
        const hazardBadge = document.getElementById('agent1-hazard-badge');
        const descText = document.getElementById('agent1-description-text');
        const pill = document.getElementById('agent1-status-pill');

        probVal.textContent = `${result.fire_probability_percent}%`;
        probVal.style.color = result.hazard_color;
        probBar.style.width = `${result.fire_probability_percent}%`;

        hazardBadge.textContent = result.hazard_level;
        hazardBadge.style.color = result.hazard_color;
        hazardBadge.style.borderColor = result.hazard_color;

        descText.textContent = result.description;
        pill.textContent = `تم التشخيص: ${result.severity_code}`;
        pill.className = 'chip chip-success';

        // Render Contributions
        const contribContainer = document.getElementById('agent1-contributions-list');
        contribContainer.innerHTML = '';
        const contribs = result.feature_contributions || {};
        const entries = Object.entries(contribs);

        if (entries.length === 0) {
            contribContainer.innerHTML = '<span class="placeholder-text">كافة المتغيرات ضمن المعدلات المستقرة.</span>';
        } else {
            entries.forEach(([feat, val]) => {
                const item = document.createElement('div');
                item.className = 'contrib-item';
                const sign = val > 0 ? `+${val}%` : `${val}%`;
                const cls = val > 0 ? 'contrib-pos' : 'contrib-neg';
                item.innerHTML = `
                    <span>متغير <strong>${feat}</strong>:</span>
                    <span class="contrib-val ${cls}">${sign}</span>
                `;
                contribContainer.appendChild(item);
            });
        }

        showToast('✅ تم تحليل حالة المركبة وأخذ كافة المتغيرات في الحسبان');
    } catch (err) {
        showToast('حدث خطأ في الاتصال بالسيرفر');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span>⚡ تشغيل استدلال وتنبؤ الذكاء الاصطناعي</span>';
    }
}

/* ==========================================================================
   AGENT 2: LLM-RAG CHATBOT & CUSTOM API CONFIG
   ========================================================================== */
function initAgent2LLM() {
    loadAgent2LLMConfig();

    const cfgForm = document.getElementById('agent2-llm-config-form');
    cfgForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const cfgData = {
            base_url: document.getElementById('cfg-llm-base-url').value.trim(),
            model_name: document.getElementById('cfg-llm-model').value.trim(),
            api_key: document.getElementById('cfg-llm-key').value.trim(),
            is_enabled: document.getElementById('cfg-llm-enabled').checked
        };
        try {
            const res = await fetch(`${API_BASE}/api/settings/agent2-llm`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(cfgData)
            });
            const data = await res.json();
            showToast('✅ تم حفظ إعدادات موديل الـ LLM لـ Agent 2 بنجاح!');
            loadAgent2LLMConfig();
        } catch (e) {
            showToast('فشل حفظ إعدادات الـ LLM');
        }
    });

    const chatForm = document.getElementById('agent2-chat-form');
    const input = document.getElementById('agent2-input-msg');

    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const msg = input.value.trim();
        if (!msg) return;

        appendChatMessage('user', msg);
        input.value = '';
        await sendChatToAgent2(msg);
    });
}

async function loadAgent2LLMConfig() {
    try {
        const res = await fetch(`${API_BASE}/api/settings/agent2-llm`);
        const cfg = await res.json();
        document.getElementById('cfg-llm-base-url').value = cfg.base_url || 'https://api.openai.com/v1';
        document.getElementById('cfg-llm-model').value = cfg.model_name || 'gpt-4o-mini';
        document.getElementById('cfg-llm-enabled').checked = Boolean(cfg.is_enabled);
        if (cfg.has_key) {
            document.getElementById('cfg-llm-key').placeholder = `المفتاح محفوظ (${cfg.masked_key})`;
        }

        const chip = document.getElementById('llm-status-chip');
        if (cfg.is_enabled && cfg.has_key) {
            chip.textContent = `نشط: ${cfg.model_name}`;
            chip.className = 'chip chip-live';
        } else {
            chip.textContent = 'محرك RAG الداخلي المعتمد على البيانات';
            chip.className = 'chip chip-success';
        }
    } catch (e) {
        console.warn('Error loading LLM cfg:', e);
    }
}

window.sendQuickPrompt = function(promptText) {
    document.getElementById('agent2-input-msg').value = promptText;
    document.getElementById('btn-send-chat').click();
};

function appendChatMessage(sender, text) {
    const chatBox = document.getElementById('agent2-chat-box');
    const msgDiv = document.createElement('div');
    msgDiv.className = `message msg-${sender}`;

    const avatar = sender === 'user' ? '👨‍🚀' : '🤖';
    const title = sender === 'user' ? 'رائد الفضاء (المستخدم):' : 'مساعد طوارئ ناسا (Agent 2):';

    msgDiv.innerHTML = `
        <div class="msg-avatar">${avatar}</div>
        <div class="msg-body">
            <strong>${title}</strong>
            <p style="white-space: pre-wrap;">${text}</p>
        </div>
    `;

    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
}

async function sendChatToAgent2(userMsg) {
    try {
        const res = await fetch(`${API_BASE}/api/chat/agent2`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: userMsg })
        });
        const data = await res.json();
        appendChatMessage('bot', data.chat_response_markdown);
    } catch (err) {
        appendChatMessage('bot', '⚠️ تعذر الاتصال بمحرك تشخيص الطوارئ.');
    }
}

/* ==========================================================================
   AGENT 3: ISS LIVE TELEMETRY & MANDATORY TRAINING GATE
   ========================================================================== */
function initAgent3ISS() {
    loadAgent3Config();

    const cfgForm = document.getElementById('agent3-iss-config-form');
    cfgForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = {
            custom_api_url: document.getElementById('cfg-iss-url').value.trim(),
            api_key: document.getElementById('cfg-iss-key').value.trim()
        };
        try {
            await fetch(`${API_BASE}/api/settings/agent3-iss`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            showToast('✅ تم تحديث إعدادات مصدر بيانات ISS بنجاح!');
            loadAgent3Config();
        } catch (e) {
            showToast('فشل تحديث إعدادات ISS');
        }
    });

    // Start SSE stream
    try {
        const es = new EventSource(`${API_BASE}/api/stream/agent3`);
        appState.issEventSource = es;
        es.onmessage = (event) => {
            const streamData = JSON.parse(event.data);
            updateISSStreamUI(streamData);
        };
    } catch (e) {
        console.error('SSE Error:', e);
    }
}

async function loadAgent3Config() {
    try {
        const res = await fetch(`${API_BASE}/api/settings/agent3-iss`);
        const cfg = await res.json();
        document.getElementById('cfg-iss-url').value = cfg.custom_api_url || '';
        const chip = document.getElementById('iss-source-chip');
        chip.textContent = cfg.custom_api_url ? 'مربوط برابط API مخصص' : 'البث المداري الافتراضي';
    } catch (e) {}
}

function updateISSStreamUI(data) {
    // Top banner
    const tsEl = document.getElementById('iss-timestamp');
    const latEl = document.getElementById('iss-lat');
    const lonEl = document.getElementById('iss-lon');
    const altEl = document.getElementById('iss-alt');
    const speedEl = document.getElementById('iss-speed');

    if (tsEl) tsEl.textContent = data.timestamp.split('T')[1].replace('Z', '');
    if (latEl) latEl.textContent = data.orbital_data.latitude;
    if (lonEl) lonEl.textContent = data.orbital_data.longitude;
    if (altEl) altEl.textContent = data.orbital_data.altitude_km;
    if (speedEl) speedEl.textContent = data.orbital_data.velocity_kmh.toLocaleString();

    // Raw atmospheric telemetry (always streams)
    const atmos = data.atmospheric_telemetry;
    document.getElementById('iss-val-o2').textContent = `${atmos.o2_percent}%`;
    document.getElementById('iss-val-press').textContent = `${atmos.cabin_pressure_kpa} kPa`;
    document.getElementById('iss-val-co2').textContent = `${atmos.co2_percent}%`;
    document.getElementById('iss-val-temp').textContent = `${atmos.ambient_temp_c} °C`;
    document.getElementById('iss-val-flow').textContent = `${atmos.ventilation_flow_ms} m/s`;

    // -------------------------------------------------------------
    // Check Mandatory Training Gate for Agent 3
    // -------------------------------------------------------------
    const ai = data.ai_fire_hazard_evaluation;
    const alertBox = document.getElementById('iss-training-alert');
    const probEl = document.getElementById('iss-prob-val');
    const barEl = document.getElementById('iss-prob-bar');
    const badgeEl = document.getElementById('iss-hazard-badge');
    const descEl = document.getElementById('iss-agent-description');
    const pill = document.getElementById('iss-risk-pill');

    if (!ai.is_model_trained) {
        // NOT TRAINED: Display strict warning and refuse to output numbers
        alertBox.style.display = 'flex';
        probEl.textContent = '--%';
        probEl.style.color = '#64748B';
        barEl.style.width = '0%';
        badgeEl.textContent = 'غير مدرب بعد';
        badgeEl.style.color = '#64748B';
        badgeEl.style.borderColor = '#64748B';
        descEl.textContent = ai.agent_status_description;
        pill.textContent = 'بانتظار التدريب';
        pill.className = 'chip chip-live';
    } else {
        // TRAINED: Show active risk evaluations
        alertBox.style.display = 'none';
        probEl.textContent = `${ai.fire_probability_percent}%`;
        probEl.style.color = ai.hazard_color;
        barEl.style.width = `${ai.fire_probability_percent}%`;
        badgeEl.textContent = ai.hazard_level;
        badgeEl.style.color = ai.hazard_color;
        badgeEl.style.borderColor = ai.hazard_color;
        descEl.textContent = ai.agent_status_description;
        pill.textContent = `خطر ${ai.severity_code}`;
        pill.className = 'chip chip-success';
    }
}

/* ==========================================================================
   AGENT 4: DYNAMIC MATERIALS, CONDITIONS, AND CFD SIMULATION
   ========================================================================== */
function initAgent4Simulator() {
    loadAgent4Materials();

    const matSelect = document.getElementById('sim-material-select');
    matSelect.addEventListener('change', () => {
        appState.flameSimParams.fuel_material = matSelect.value;
        triggerFlameSimulation();
    });

    const addMatForm = document.getElementById('add-material-form');
    addMatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const matData = {
            id: document.getElementById('mat-id').value.trim(),
            name_ar: document.getElementById('mat-name-ar').value.trim(),
            flame_temp_base: parseFloat(document.getElementById('mat-temp').value),
            limiting_oxygen_index: parseFloat(document.getElementById('mat-loi').value),
            sooting_propensity: parseFloat(document.getElementById('mat-soot').value)
        };
        try {
            await fetch(`${API_BASE}/api/materials`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(matData)
            });
            showToast(`✅ تمت إضافة المادة الجديدة "${matData.name_ar}" فوراً!`);
            closeMaterialModal();
            loadAgent4Materials();
        } catch (e) {
            showToast('فشل حفظ المادة');
        }
    });

    startFlameCanvasLoop();
    triggerFlameSimulation();
}

async function loadAgent4Materials() {
    try {
        const res = await fetch(`${API_BASE}/api/materials`);
        const data = await res.json();
        appState.agent4Materials = data.materials || [];

        const select = document.getElementById('sim-material-select');
        select.innerHTML = '';
        appState.agent4Materials.forEach(m => {
            const opt = document.createElement('option');
            opt.value = m.id;
            opt.textContent = `${m.name_ar} (LOI: ${m.limiting_oxygen_index}%)`;
            select.appendChild(opt);
        });

        document.getElementById('materials-count-chip').textContent = `${appState.agent4Materials.length} مواد مسجلة`;
        if (appState.agent4Materials.length > 0) {
            appState.flameSimParams.fuel_material = appState.agent4Materials[0].id;
        }
    } catch (e) {}
}

window.showAddMaterialModal = function() {
    document.getElementById('material-modal').style.display = 'flex';
};

window.closeMaterialModal = function() {
    document.getElementById('material-modal').style.display = 'none';
};

window.deleteCurrentMaterial = async function() {
    const sel = document.getElementById('sim-material-select');
    const matId = sel.value;
    if (!matId) return;
    if (!confirm(`هل أنت متأكد من حذف المادة "${matId}" من محاكي الاحتراق؟`)) return;

    try {
        await fetch(`${API_BASE}/api/materials/${matId}`, { method: 'DELETE' });
        showToast(`تم حذف المادة ${matId}`);
        loadAgent4Materials();
        triggerFlameSimulation();
    } catch (e) {
        showToast('فشل حذف المادة');
    }
};

function renderAgent4Conditions() {
    const container = document.getElementById('agent4-conditions-container');
    container.innerHTML = '';

    const condVars = appState.allVariables.filter(v => 
        (v.agent_id === 'agent4' || v.agent_id === 'global') && v.data_type === 'number'
    );

    condVars.forEach(v => {
        const group = document.createElement('div');
        group.className = 'form-group mb-4';

        const header = document.createElement('div');
        header.className = 'slider-header';
        header.innerHTML = `
            <div>
                <strong>${v.name_ar}</strong> (${v.unit || ''}):
                <button class="btn-icon-del btn-sm" style="margin-right: 6px;" onclick="deleteConditionVariable('${v.id}')">حذف</button>
            </div>
            <span class="slider-val" id="val_disp_${v.id}">${v.default_val}</span>
        `;

        const slider = document.createElement('input');
        slider.type = 'range';
        slider.className = 'form-range';
        slider.id = `slider_${v.id}`;
        slider.min = v.min_val ?? 0;
        slider.max = v.max_val ?? 100;
        slider.step = (v.max_val - v.min_val) > 20 ? 1 : 0.05;
        slider.value = v.default_val;

        slider.addEventListener('input', () => {
            const valDisp = document.getElementById(`val_disp_${v.id}`);
            valDisp.textContent = `${slider.value} ${v.unit || ''}`;
            appState.flameSimParams[v.id] = parseFloat(slider.value);
            triggerFlameSimulation();
        });

        // Register in state
        appState.flameSimParams[v.id] = parseFloat(v.default_val);

        group.appendChild(header);
        group.appendChild(slider);
        container.appendChild(group);
    });
}

window.deleteConditionVariable = async function(varId) {
    if (!confirm(`هل تريد بالتأكيد حذف المتغير "${varId}" من محاكاة العميل 4؟`)) return;
    try {
        await fetch(`${API_BASE}/api/variables/${varId}`, { method: 'DELETE' });
        showToast(`تم حذف الشرط ${varId}`);
        delete appState.flameSimParams[varId];
        loadAllVariables();
        triggerFlameSimulation();
    } catch (e) {
        showToast('فشل حذف المتغير');
    }
};

window.showAddConditionModal = function() {
    // Switch to variables tab with agent4 pre-selected
    document.querySelector('.tab-btn[data-tab="tab-variables"]').click();
    document.getElementById('var-agent-select').value = 'agent4';
    showToast('قم بكتابة وحفظ المتغير الجديد للعميل 4 من هذه الشاشة');
};

async function triggerFlameSimulation() {
    try {
        const res = await fetch(`${API_BASE}/api/simulate/agent4`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ variables: appState.flameSimParams })
        });
        const sim = await res.json();
        appState.latestFlameVisualSpec = sim;

        // Update metrics
        document.getElementById('sim-radius-val').textContent = `${sim.flame_radius_mm} mm`;
        document.getElementById('sim-height-val').textContent = `${sim.aspect_ratio}`;
        document.getElementById('sim-temp-val').textContent = `${sim.peak_temperature_k} K`;
        document.getElementById('sim-blue-val').textContent = `${Math.round(sim.blue_chemiluminescence_ratio * 100)}%`;
        document.getElementById('sim-flicker-val').textContent = `${sim.flicker_frequency_hz} Hz`;
        document.getElementById('sim-burnrate-val').textContent = `${sim.burning_rate_mms} mm/s`;

        if (appState.currentSimView === 'cfd') {
            renderCFDHeatmap(sim.cfd_thermal_grid);
        }
    } catch (e) {
        console.warn('Simulation error:', e);
    }
}

window.switchSimView = function(view) {
    appState.currentSimView = view;
    document.getElementById('btn-toggle-flame').classList.toggle('active', view === 'flame');
    document.getElementById('btn-toggle-cfd').classList.toggle('active', view === 'cfd');

    const fCanvas = document.getElementById('flame-canvas');
    const cCanvas = document.getElementById('cfd-canvas');
    if (view === 'flame') {
        fCanvas.style.display = 'block';
        cCanvas.style.display = 'none';
    } else {
        fCanvas.style.display = 'none';
        cCanvas.style.display = 'block';
        if (appState.latestFlameVisualSpec) {
            renderCFDHeatmap(appState.latestFlameVisualSpec.cfd_thermal_grid);
        }
    }
};

function renderCFDHeatmap(cfdGrid) {
    const canvas = document.getElementById('cfd-canvas');
    if (!canvas || !cfdGrid) return;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const matrix = cfdGrid.scalar_matrix || [];
    const rows = matrix.length;
    if (rows === 0) return;
    const cols = matrix[0].length;

    const cellW = canvas.width / cols;
    const cellH = canvas.height / rows;

    for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
            const temp = matrix[r][c];
            // Normalize temp (300K to 2200K)
            const norm = Math.max(0, Math.min(1, (temp - 300) / 1800));
            // Color map: Blue -> Cyan -> Yellow -> Red
            const red = Math.floor(norm > 0.5 ? 255 : norm * 2 * 255);
            const green = Math.floor(norm > 0.7 ? 180 * (1 - norm) : norm * 255);
            const blue = Math.floor(norm < 0.4 ? 255 : (1 - norm) * 200);

            ctx.fillStyle = `rgb(${red}, ${green}, ${blue})`;
            ctx.fillRect(c * cellW, r * cellH, cellW + 1, cellH + 1);
        }
    }

    ctx.fillStyle = '#FFF';
    ctx.font = '12px Cairo';
    ctx.fillText(`CFD Scalar Heatmap (Peak: ${cfdGrid.max_temp_k} K)`, 10, 20);
}

function startFlameCanvasLoop() {
    const canvas = document.getElementById('flame-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let time = 0;

    function render() {
        time += 0.05;
        if (appState.currentSimView === 'flame') {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            const sim = appState.latestFlameVisualSpec;
            if (sim && sim.visual_spec && sim.visual_spec.flame_type !== 'EXTINGUISHED') {
                const spec = sim.visual_spec;
                const cx = canvas.width / 2;
                const cy = canvas.height * 0.62;
                const isMicrogravity = spec.flame_type === 'SPHERICAL_DIFFUSION';
                const flickerAmp = isMicrogravity ? 0.015 : 0.08 + Math.sin(time * (sim.flicker_frequency_hz || 8)) * 0.06;

                const rx = spec.radius_x_px * (1 + Math.sin(time * 3) * flickerAmp);
                const ry = spec.radius_y_px * (1 + Math.cos(time * 3.5) * flickerAmp);

                // Halo
                const glowRad = Math.max(rx, ry) * 1.8;
                const glowGrad = ctx.createRadialGradient(cx, cy, rx * 0.2, cx, cy, glowRad);
                glowGrad.addColorStop(0, spec.color_palette.glow_halo);
                glowGrad.addColorStop(1, 'transparent');
                ctx.fillStyle = glowGrad;
                ctx.beginPath();
                ctx.arc(cx, cy, glowRad, 0, Math.PI * 2);
                ctx.fill();

                if (isMicrogravity) {
                    // Symmetrical diffusion sphere
                    const outerGrad = ctx.createRadialGradient(cx, cy, rx * 0.3, cx, cy, rx);
                    outerGrad.addColorStop(0, spec.color_palette.chemiluminescence_core);
                    outerGrad.addColorStop(0.7, spec.color_palette.outer_soot_incandescence);
                    outerGrad.addColorStop(0.95, spec.color_palette.chemiluminescence_core);
                    outerGrad.addColorStop(1, 'transparent');

                    ctx.fillStyle = outerGrad;
                    ctx.beginPath();
                    ctx.ellipse(cx, cy, rx, ry, 0, 0, Math.PI * 2);
                    ctx.fill();

                    // Core reaction
                    const coreGrad = ctx.createRadialGradient(cx, cy, 2, cx, cy, rx * 0.45);
                    coreGrad.addColorStop(0, '#FFFFFF');
                    coreGrad.addColorStop(0.5, spec.color_palette.inner_reaction_zone);
                    coreGrad.addColorStop(1, 'transparent');
                    ctx.fillStyle = coreGrad;
                    ctx.beginPath();
                    ctx.ellipse(cx, cy, rx * 0.45, ry * 0.45, 0, 0, Math.PI * 2);
                    ctx.fill();
                } else {
                    // Buoyant teardrop
                    const tipY = cy - ry * 1.5 + Math.sin(time * (sim.flicker_frequency_hz || 8)) * 8;
                    const baseY = cy + ry * 0.3;

                    const tearGrad = ctx.createLinearGradient(cx, baseY, cx, tipY);
                    tearGrad.addColorStop(0, spec.color_palette.chemiluminescence_core);
                    tearGrad.addColorStop(0.35, spec.color_palette.outer_soot_incandescence);
                    tearGrad.addColorStop(0.85, spec.color_palette.soot_tip);
                    tearGrad.addColorStop(1, 'transparent');

                    ctx.fillStyle = tearGrad;
                    ctx.beginPath();
                    ctx.moveTo(cx, tipY);
                    ctx.bezierCurveTo(cx + rx * 1.2, cy - ry * 0.4, cx + rx * 0.7, baseY, cx, baseY + 6);
                    ctx.bezierCurveTo(cx - rx * 0.7, baseY, cx - rx * 1.2, cy - ry * 0.4, cx, tipY);
                    ctx.closePath();
                    ctx.fill();
                }

                // Fuel burner nozzle
                ctx.fillStyle = '#CBD5E1';
                ctx.beginPath();
                ctx.arc(cx, cy + (isMicrogravity ? 0 : 8), 5, 0, Math.PI * 2);
                ctx.fill();
            }
        }
        appState.flameAnimFrameId = requestAnimationFrame(render);
    }
    render();
}

/* ==========================================================================
   2-WAY DYNAMIC VARIABLES & FRONT-END CONTRACTS
   ========================================================================== */
function initVariableManager() {
    const form = document.getElementById('add-variable-form');
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const varData = {
            id: document.getElementById('var-id-input').value.trim(),
            agent_id: document.getElementById('var-agent-select').value,
            name_ar: document.getElementById('var-name-ar').value.trim(),
            name_en: document.getElementById('var-name-en').value.trim(),
            data_type: 'number',
            unit: document.getElementById('var-unit').value.trim(),
            min_val: parseFloat(document.getElementById('var-min').value),
            max_val: parseFloat(document.getElementById('var-max').value),
            default_val: document.getElementById('var-default').value.trim(),
            is_active_for_prediction: document.getElementById('var-active-pred').checked ? 1 : 0
        };

        try {
            await fetch(`${API_BASE}/api/variables`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(varData)
            });
            showToast(`✅ تم حفظ المتغير الجديد "${varData.name_ar}" وتفعيله فوراً!`);
            form.reset();
            loadAllVariables();
        } catch (e) {
            showToast('حدث خطأ أثناء حفظ المتغير');
        }
    });
}

function renderVariablesTable() {
    const tbody = document.getElementById('vars-table-body');
    const countChip = document.getElementById('vars-count-chip');
    tbody.innerHTML = '';
    countChip.textContent = `${appState.allVariables.length} متغيرات مسجلة`;

    appState.allVariables.forEach(v => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>
                <strong>${v.name_ar}</strong><br>
                <code style="font-size: 0.74rem; color: var(--cyan-nasa);">${v.id}</code>
            </td>
            <td><span class="chip">${v.agent_id}</span></td>
            <td>${v.unit ? v.unit : '-'} (${v.min_val ?? 0} إلى ${v.max_val ?? 100})</td>
            <td>
                <input type="checkbox" class="toggle-switch" ${v.is_active_for_prediction ? 'checked' : ''} 
                    onchange="toggleVariablePrediction('${v.id}', this.checked)">
            </td>
            <td>
                <button class="btn-icon-del" onclick="deleteGlobalVariable('${v.id}')">حذف</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

window.toggleVariablePrediction = async function(varId, isActive) {
    await fetch(`${API_BASE}/api/variables/prediction_status`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: varId, is_active: isActive })
    });
    loadAllVariables();
};

window.deleteGlobalVariable = async function(varId) {
    if (!confirm(`هل تريد بالتأكيد حذف المتغير "${varId}" نهائياً من المنظومة؟`)) return;
    await fetch(`${API_BASE}/api/variables/${varId}`, { method: 'DELETE' });
    showToast(`تم حذف المتغير ${varId}`);
    loadAllVariables();
};

window.load2WayContract = async function() {
    const select = document.getElementById('select-agent-contract');
    const agentId = select ? select.value : 'agent1';
    try {
        const res = await fetch(`${API_BASE}/api/frontend-contract/${agentId}`);
        const contract = await res.json();
        const snippetEl = document.getElementById('contract-code-snippet');
        if (snippetEl) {
            const code = contract.complete_fetch_snippet.replaceAll('http://localhost:8500', API_BASE);
            snippetEl.textContent = code;
        }
    } catch (e) {}
};

/* ==========================================================================
   UNIVERSAL MULTI-FORMAT INGESTION & TRAINING (AGENTS 1, 2, 3, 4)
   ========================================================================== */
function initUniversalIngestion() {
    const fileInput = document.getElementById('file-upload-input');
    const formatSelect = document.getElementById('ingest-format-select');
    const txtArea = document.getElementById('batch-data-input');
    const tagsInput = document.getElementById('custom-tags-input');

    if (fileInput) {
        fileInput.addEventListener('change', async () => {
            if (!fileInput.files || fileInput.files.length === 0) return;
            const file = fileInput.files[0];
            const name = file.name.toLowerCase();

            // 1. Auto-detect format from file extension
            let detectedFormat = null;
            if (name.endsWith('.csv')) detectedFormat = 'csv';
            else if (name.endsWith('.json') || name.endsWith('.jsonl')) detectedFormat = 'json';
            else if (name.endsWith('.xlsx') || name.endsWith('.xls')) detectedFormat = 'excel';
            else if (name.endsWith('.pdf')) detectedFormat = 'pdf';
            else if (name.endsWith('.txt') || name.endsWith('.log')) detectedFormat = 'text';
            else if (name.match(/\.(png|jpg|jpeg|webp|bmp)$/)) detectedFormat = 'image';
            else if (name.match(/\.(mp4|webm|mov|avi)$/)) detectedFormat = 'video';

            if (detectedFormat && formatSelect) {
                formatSelect.value = detectedFormat;
                onFormatChange();
            }

            // 2. Auto-fill batch name from filename if default or empty
            const batchNameInput = document.getElementById('batch-name-input');
            if (batchNameInput && (!batchNameInput.value || batchNameInput.value.startsWith('NASA_Exp_Batch_') || batchNameInput.value.startsWith('Batch_'))) {
                const baseName = file.name.replace(/\.[^/.]+$/, "").replace(/[^a-zA-Z0-9_-]/g, "_");
                batchNameInput.value = baseName;
            }

            // 3. If text format (CSV, JSON, TXT), preview content and auto-extract tags
            const curFormat = detectedFormat || formatSelect.value;
            if (['csv', 'json', 'text'].includes(curFormat)) {
                try {
                    const text = await readFileAsText(file);
                    if (txtArea) {
                        txtArea.value = text.slice(0, 10000); // Preview up to 10k chars
                    }

                    // Auto-fill tags from CSV header if empty
                    if (curFormat === 'csv' && tagsInput && !tagsInput.value.trim()) {
                        const firstLine = text.split('\n')[0];
                        if (firstLine && (firstLine.includes(',') || firstLine.includes(';') || firstLine.includes('\t'))) {
                            const sep = firstLine.includes('\t') ? '\t' : (firstLine.includes(';') ? ';' : ',');
                            const cols = firstLine.split(sep)
                                .map(c => c.trim().replace(/^["']|["']$/g, '').toLowerCase().replace(/\s+/g, '_'))
                                .filter(c => c && !['id', 'risk_score', 'target', 'timestamp', 'date', 'time'].includes(c));
                            if (cols.length > 0) {
                                tagsInput.value = cols.join(', ');
                            }
                        }
                    }
                } catch (err) {
                    console.warn('File preview read error:', err);
                }
            }

            showToast(`📂 تم اختيار الملف: ${file.name} (الصيغة المحددة: ${(detectedFormat || formatSelect.value).toUpperCase()})`);
        });
    }
}

window.onFormatChange = function() {
    const fmt = document.getElementById('ingest-format-select').value;
    const txtArea = document.getElementById('text-input-area');
    if (['excel', 'pdf', 'image', 'video'].includes(fmt)) {
        txtArea.style.display = 'none';
    } else {
        txtArea.style.display = 'block';
    }
};

window.loadSampleDataByFormat = function() {
    const fmt = document.getElementById('ingest-format-select').value;
    const txtArea = document.getElementById('batch-data-input');
    const tagsInput = document.getElementById('custom-tags-input');

    if (fmt === 'json') {
        txtArea.value = JSON.stringify([
            { "o2_percent": 24.5, "co2_percent": 0.8, "wire_temp_c": 75.0, "risk_score": 52.0 },
            { "o2_percent": 30.0, "co2_percent": 0.3, "wire_temp_c": 110.0, "risk_score": 88.0 },
            { "o2_percent": 18.5, "co2_percent": 1.2, "wire_temp_c": 25.0, "risk_score": 12.0 }
        ], null, 2);
        tagsInput.value = "o2_percent, co2_percent, wire_temp_c";
    } else if (fmt === 'csv') {
        txtArea.value = "o2_percent,cabin_pressure_kpa,co2_percent,ambient_temp_c,air_flow_velocity_ms,material_flammability_index,wire_temp_c,coolant_pressure_kpa,risk_score\n27.79,66.3,1.07,29.6,0.702,3.1,127.3,136.5,95.4\n19.37,90.3,0.24,28.3,0.621,2.65,48.0,232.0,29.6\n31.19,65.3,2.85,54.3,0.33,1.33,135.0,184.0,99.0";
        tagsInput.value = "o2_percent, cabin_pressure_kpa, co2_percent, ambient_temp_c, air_flow_velocity_ms, material_flammability_index, wire_temp_c, coolant_pressure_kpa";
    } else if (fmt === 'scientific_array') {
        txtArea.value = "24.5  0.8  75.0  52.0\n30.0  0.3  110.0  88.0\n18.5  1.2  25.0  12.0";
        tagsInput.value = "o2_percent, co2_percent, wire_temp_c, risk_score";
    } else if (fmt === 'text') {
        txtArea.value = "تقرير سلامة طوارئ وحدة كولومبوس:\nعند ارتفاع حرارة أسلاك التوزيع عن 90C مع نسبة أكسجين تفوق 28%، يجب فوراً فصل قاطع الدائرة الرئيسي وإغلاق منافذ تدفق الهواء لمنع انتشار اللهب في بيئة انعدام الجاذبية.";
        tagsInput.value = "wire_temp_c, o2_percent";
    } else {
        showToast('يرجى اختيار ملف لرفعه من جهازك لهذه الصيغة.');
    }
};

window.submitUniversalIngestion = async function() {
    const agentId = document.getElementById('ingest-agent-select').value;
    const formatType = document.getElementById('ingest-format-select').value;
    const batchName = document.getElementById('batch-name-input').value.trim() || `Batch_${Date.now()}`;
    const rawTags = document.getElementById('custom-tags-input').value.trim();
    const userVars = rawTags ? rawTags.split(',').map(s => s.trim().replace(/\s+/g, '_')).filter(Boolean) : [];

    const fileInput = document.getElementById('file-upload-input');
    const textData = document.getElementById('batch-data-input') ? document.getElementById('batch-data-input').value : '';

    const hasFile = fileInput && fileInput.files && fileInput.files.length > 0;
    const hasText = textData && textData.trim().length > 0;

    if (!hasFile && !hasText) {
        showToast('⚠️ يرجى اختيار ملف من جهازك أو إدخال نص البيانات أولاً');
        return;
    }

    const btn = document.getElementById('btn-submit-ingest');
    const originalBtnContent = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span>⏳ جاري معالجة البيانات وتدريب الذكاء الاصطناعي...</span>';

    const logBox = document.getElementById('training-log-console');
    if (logBox) {
        logBox.textContent = `⏳ جاري معالجة ورفع دفعة البيانات (${batchName}) للعميل ${agentId}...`;
    }

    try {
        let contentPayload = "";
        let filename = `${batchName}.${formatType}`;
        const isTextFormat = ['csv', 'json', 'scientific_array', 'text'].includes(formatType);

        if (hasFile) {
            const file = fileInput.files[0];
            filename = file.name;
            if (isTextFormat) {
                // Send text directly to preserve UTF-8 and formatting cleanly
                contentPayload = await readFileAsText(file);
            } else {
                // Binary formats (Excel, PDF, image, video) require base64
                contentPayload = await readFileAsBase64(file);
            }
        } else {
            contentPayload = textData;
        }

        const res = await fetch(`${API_BASE}/api/upload/${agentId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                batch_name: batchName,
                format_type: formatType,
                content: contentPayload,
                user_defined_variables: userVars,
                filename: filename
            })
        });

        const data = await res.json();

        if (!res.ok || data.success === false) {
            const errMsg = data.error || `خطأ ${res.status}: فشلت معالجة الخادم للبيانات`;
            showToast(`❌ ${errMsg}`);
            if (logBox) {
                logBox.textContent = `❌ فشلت معالجة الدفعة:\n• السبب: ${errMsg}\n• تحقق من توافق محتوى الملف مع الصيغة المحددة.`;
            }
            return;
        }

        // Detailed success log
        const metricsStr = data.training_metrics
            ? `\n• دقة النموذج AI Accuracy: ${(data.training_metrics.accuracy_score * 100).toFixed(1)}%\n• إجمالي العينات بعد الدمج: ${data.training_metrics.total_samples}`
            : '';

        if (logBox) {
            logBox.textContent = `✅ تم استيعاب وتدريب البيانات بنجاح!\n` +
                `• العميل: ${data.agent_id}\n` +
                `• التنسيق المعالج: ${data.format_type}\n` +
                `• السجلات المستخرجة: ${data.rows_extracted}\n` +
                `• المتغيرات المعتمدة (${(data.discovered_variables || []).length}): ${(data.discovered_variables || []).join(', ')}` +
                metricsStr;
        }

        showToast(`🚀 تم تدريب العميل ${agentId} بنجاح (${data.rows_extracted} سجل)!`);
        await loadAgentsTrainingStatus();
        await loadAllVariables();

        if (agentId === 'agent4' && typeof loadAgent4Materials === 'function') {
            loadAgent4Materials();
        }
    } catch (e) {
        console.error('Data ingestion error:', e);
        showToast('❌ حدث خطأ أثناء رفع ومعالجة البيانات');
        if (logBox) {
            logBox.textContent = `❌ خطأ في الاتصال أو المعالجة:\n• التفاصيل: ${e.message}`;
        }
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalBtnContent;
    }
};

function readFileAsText(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = error => reject(error);
        reader.readAsText(file, 'utf-8');
    });
}

function readFileAsBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result.split(',')[1] || reader.result);
        reader.onerror = error => reject(error);
        reader.readAsDataURL(file);
    });
}

async function loadAgentsTrainingStatus() {
    for (let i = 1; i <= 4; i++) {
        const aid = `agent${i}`;
        try {
            const res = await fetch(`${API_BASE}/api/training-status/${aid}`);
            const stat = await res.json();
            const badge = document.getElementById(`badge-${aid}`);
            if (badge) {
                if (stat.is_trained) {
                    badge.textContent = `مدرب (${stat.sample_count} عينة)`;
                    badge.className = 'badge online-pulse';
                } else {
                    badge.textContent = 'غير مدرب بعد';
                    badge.className = 'badge';
                    badge.style.color = '#F59E0B';
                }
            }
        } catch (e) {}
    }
}
