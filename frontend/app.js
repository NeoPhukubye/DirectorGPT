const API_BASE = window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : 'https://directorgpt-api.onrender.com';

const generateBtn = document.getElementById('generateBtn');
const scriptBtn = document.getElementById('scriptBtn');
const downloadBtn = document.getElementById('downloadBtn');
const statusSection = document.getElementById('status');
const statusText = document.getElementById('statusText');
const resultsSection = document.getElementById('results');

let statusEventSource = null;

function showStatus(message) {
    statusText.textContent = message;
    statusSection.classList.remove('hidden');
    resultsSection.classList.add('hidden');
}

function hideStatus() {
    statusSection.classList.add('hidden');
}

function showResults() {
    resultsSection.classList.remove('hidden');
    hideStatus();
}

function getRequestData() {
    return {
        prompt: document.getElementById('prompt').value,
        title: document.getElementById('title').value || 'Untitled',
        genre: document.getElementById('genre').value,
        duration: parseFloat(document.getElementById('duration').value) || 60,
        fps: 24,
        resolution: '1920x1080',
        enable_images: document.getElementById('enableImages').checked,
        enable_video: document.getElementById('enableVideo').checked,
        enable_audio: document.getElementById('enableAudio').checked,
        llm_provider: 'gemini',
        llm_model: document.getElementById('model').value,
        llm_api_key: document.getElementById('apiKey').value || null,
    };
}

function getScriptRequestData() {
    return {
        prompt: document.getElementById('prompt').value,
        genre: document.getElementById('genre').value,
        duration: parseFloat(document.getElementById('duration').value) || 60,
        llm_provider: 'gemini',
        llm_model: document.getElementById('model').value,
        llm_api_key: document.getElementById('apiKey').value || null,
    };
}

function renderReport(report) {
    const stats = document.getElementById('reportStats');
    stats.innerHTML = `
        <div class="stat-card">
            <div class="stat-value">${report.scenes || 0}</div>
            <div class="stat-label">Scenes</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${report.total_shots || 0}</div>
            <div class="stat-label">Shots</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${report.characters || 0}</div>
            <div class="stat-label">Characters</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${(report.estimated_duration || 0).toFixed(1)}s</div>
            <div class="stat-label">Duration</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${report.sound_cues || 0}</div>
            <div class="stat-label">Sound Cues</div>
        </div>
    `;
}

function renderScript(script) {
    const output = document.getElementById('scriptOutput');
    if (!script || !script.scenes) {
        output.innerHTML = `<pre>${escapeHtml(JSON.stringify(script, null, 2))}</pre>`;
        return;
    }

    const charactersHtml = (script.characters || []).map(c => `
        <div class="character-card">
            <div class="character-name">${escapeHtml(c.name)}</div>
            <div class="character-desc">${escapeHtml(c.description)}</div>
            <div class="character-voice">Voice: ${escapeHtml(c.voice_description || 'N/A')}</div>
        </div>
    `).join('');

    const scenesHtml = (script.scenes || []).map(s => {
        const shotsHtml = (s.shots || []).map(sh => `
            <div class="shot-card">
                <div class="shot-header">
                    <span class="shot-number">Shot ${sh.shot_number}</span>
                    <span class="shot-type">${sh.shot_type}</span>
                    <span class="shot-duration">${sh.duration_seconds}s</span>
                </div>
                <div class="shot-body">${escapeHtml(sh.description)}</div>
                ${sh.dialogue ? `<div class="shot-dialogue">"${escapeHtml(sh.dialogue)}"</div>` : ''}
                <div class="shot-meta">Camera: ${escapeHtml(sh.camera_movement || 'static')}</div>
            </div>
        `).join('');

        return `
            <div class="scene-card">
                <div class="scene-header">
                    <span class="scene-number">Scene ${s.scene_number}</span>
                    <span class="scene-title">${escapeHtml(s.title)}</span>
                </div>
                <div class="scene-meta">
                    <span class="badge">${s.time_of_day}</span>
                    <span class="badge">${s.emotional_tone}</span>
                </div>
                <div class="scene-body">${escapeHtml(s.description)}</div>
                <div class="scene-location"><strong>Location:</strong> ${escapeHtml(s.location)}</div>
                <div class="shots-grid">${shotsHtml}</div>
            </div>
        `;
    }).join('');

    output.innerHTML = `
        <div class="script-structured">
            <div class="script-header">
                <h2 class="script-title">${escapeHtml(script.title)}</h2>
                <p class="script-logline">${escapeHtml(script.logline)}</p>
            </div>
            <div class="script-section">
                <h3>Characters</h3>
                <div class="characters-grid">${charactersHtml}</div>
            </div>
            <div class="script-section">
                <h3>Scenes</h3>
                ${scenesHtml}
            </div>
        </div>
    `;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function callApi(endpoint, data) {
    const response = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
}

function connectStatusStream() {
    if (statusEventSource) {
        statusEventSource.close();
    }
    statusEventSource = new EventSource(`${API_BASE}/api/stream`);
    statusEventSource.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        showStatus(msg.message);
    };
    statusEventSource.onerror = () => {
        statusEventSource.close();
        statusEventSource = null;
    };
}

generateBtn.addEventListener('click', async () => {
    const data = getRequestData();
    if (!data.llm_api_key) {
        alert('Please enter your Gemini API key');
        return;
    }
    if (!data.prompt) {
        alert('Please enter a film prompt');
        return;
    }

    generateBtn.disabled = true;
    showStatus('Connecting to status stream...');
    connectStatusStream();

    try {
        const result = await callApi('/api/produce', data);

        if (result.success) {
            renderReport(result.report);
            renderScript(result.script);
            showResults();
            downloadBtn.onclick = () => downloadJson(result.script, `${data.title.replace(/\s+/g, '_')}_script.json`);
        }
    } catch (error) {
        showStatus(`Error: ${error.message}`);
        statusSection.classList.remove('hidden');
    } finally {
        generateBtn.disabled = false;
        if (statusEventSource) {
            statusEventSource.close();
            statusEventSource = null;
        }
    }
});

scriptBtn.addEventListener('click', async () => {
    const data = getScriptRequestData();
    if (!data.llm_api_key) {
        alert('Please enter your Gemini API key');
        return;
    }
    if (!data.prompt) {
        alert('Please enter a film prompt');
        return;
    }

    scriptBtn.disabled = true;
    showStatus('Generating script...');

    try {
        const result = await callApi('/api/script', data);
        if (result.success) {
            renderReport({
                scenes: result.script.scenes?.length || 0,
                total_shots: result.script.scenes?.reduce((sum, s) => sum + (s.shots?.length || 0), 0) || 0,
                characters: result.script.characters?.length || 0,
                estimated_duration: result.script.total_duration_estimate || 0,
                sound_cues: 0,
            });
            renderScript(result.script);
            showResults();
            downloadBtn.onclick = () => downloadJson(result.script, 'script_only.json');
        }
    } catch (error) {
        showStatus(`Error: ${error.message}`);
        statusSection.classList.remove('hidden');
    } finally {
        scriptBtn.disabled = false;
    }
});

function downloadJson(data, filename) {
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
}
