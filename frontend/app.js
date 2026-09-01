const API_BASE = window.location.hostname === 'localhost'
    ? 'http://localhost:8000'
    : 'https://directorgpt-api.onrender.com';

const generateBtn = document.getElementById('generateBtn');
const scriptBtn = document.getElementById('scriptBtn');
const downloadBtn = document.getElementById('downloadBtn');
const statusSection = document.getElementById('status');
const statusText = document.getElementById('statusText');
const resultsSection = document.getElementById('results');

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
        enable_video: false,
        enable_audio: document.getElementById('enableAudio').checked,
        llm_provider: 'gemini',
        llm_model: 'gemini-2.0-flash',
    };
}

function getScriptRequestData() {
    return {
        prompt: document.getElementById('prompt').value,
        genre: document.getElementById('genre').value,
        duration: parseFloat(document.getElementById('duration').value) || 60,
        llm_provider: 'gemini',
        llm_model: 'gemini-2.0-flash',
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
            <div class="stat-label">Est. Duration</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${report.sound_cues || 0}</div>
            <div class="stat-label">Sound Cues</div>
        </div>
    `;
}

function renderScript(script) {
    const output = document.getElementById('scriptOutput');
    output.innerHTML = `<pre>${escapeHtml(JSON.stringify(script, null, 2))}</pre>`;
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

generateBtn.addEventListener('click', async () => {
    const data = getRequestData();
    if (!data.prompt.trim()) {
        alert('Please enter a film prompt');
        return;
    }

    generateBtn.disabled = true;
    showStatus('Initializing DirectorGPT agents...');

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
    }
});

scriptBtn.addEventListener('click', async () => {
    const data = getScriptRequestData();
    if (!data.prompt.trim()) {
        alert('Please enter a film prompt');
        return;
    }

    scriptBtn.disabled = true;
    showStatus('Screenwriter is generating screenplay...');

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
            downloadBtn.onclick = () => downloadJson(result.script, 'screenplay.json');
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
