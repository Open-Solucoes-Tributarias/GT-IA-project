const API_URL = "http://localhost:8000";
// Chave definida no .env (idealmente gerenciada via proxy seguro em prod, aqui hardcoded para MVP)
const API_KEY = "minha_chave_secreta_padrao";

document.addEventListener('DOMContentLoaded', () => {
    checkApiStatus();
    setupEventListeners();
});

async function checkApiStatus() {
    const statusEl = document.getElementById('api-status');
    try {
        const response = await fetch(`${API_URL}/status`);
        if (response.ok) {
            statusEl.innerHTML = '<i class="fa-solid fa-circle-check"></i> Sistema Online';
            statusEl.classList.add('online');
        } else {
            throw new Error('API Error');
        }
    } catch (error) {
        statusEl.innerHTML = '<i class="fa-solid fa-circle-xmark"></i> Sistema Offline';
        statusEl.classList.add('offline');
        console.error("API Status Check Failed:", error);
    }
}

function setupEventListeners() {
    const hero = document.getElementById('hero');
    const formSection = document.getElementById('analysis-form');
    const resultsSection = document.getElementById('results');

    // Start Button
    document.getElementById('btn-start').addEventListener('click', () => {
        hero.classList.add('hidden');
        formSection.classList.remove('hidden');
    });

    // Cancel Button
    document.getElementById('btn-cancel').addEventListener('click', () => {
        formSection.classList.add('hidden');
        hero.classList.remove('hidden');
    });

    // New Analysis Button
    document.getElementById('btn-new-analysis').addEventListener('click', () => {
        resultsSection.classList.add('hidden');
        formSection.classList.remove('hidden');
        document.getElementById('audit-form').reset();
        document.getElementById('csv-file').value = ""; // Reset file
        document.getElementById('file-name').textContent = "";
    });

    // File Upload Events
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('csv-file');
    const btnSelect = document.getElementById('btn-select-file');

    btnSelect.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            document.getElementById('file-name').textContent = e.target.files[0].name;
        }
    });

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            fileInput.files = e.dataTransfer.files;
            document.getElementById('file-name').textContent = e.dataTransfer.files[0].name;
        }
    });

    // Form Submit
    // Form Submit
    document.getElementById('audit-form').addEventListener('submit', handleAuditSubmit);

    // Initialize Chat
    if (document.getElementById('chat-widget')) setupChat();
}

async function handleAuditSubmit(e) {
    e.preventDefault();

    // Show Overlay
    const overlay = document.getElementById('ai-processing');
    overlay.classList.remove('hidden');

    // Simulate AI Progression (Visual feedback)
    await runProgressAnimation();

    const fileInput = document.getElementById('csv-file');

    try {
        let response;

        if (fileInput.files.length > 0) {
            // Upload CSV Flow
            const formData = new FormData();
            formData.append("file", fileInput.files[0]);
            formData.append("company_name", document.getElementById('company_name').value);
            formData.append("cnpj", document.getElementById('company_cnpj').value);
            formData.append("regime", document.getElementById('company_regime').value);
            formData.append("activity_code", document.getElementById('company_activity').value);

            response = await fetch(`${API_URL}/upload-csv`, {
                method: 'POST',
                headers: { 'x-api-key': API_KEY },
                body: formData
            });

        } else {
            // Manual Data Flow
            const formData = {
                company: {
                    name: document.getElementById('company_name').value,
                    cnpj: document.getElementById('company_cnpj').value,
                    activity_code: document.getElementById('company_activity').value,
                    regime: document.getElementById('company_regime').value
                },
                history: [
                    {
                        period: "Mês Atual", // MVP simplification
                        revenue: parseFloat(document.getElementById('fiscal_revenue').value || 0),
                        payroll: parseFloat(document.getElementById('fiscal_payroll').value || 0),
                        paid_amount: parseFloat(document.getElementById('fiscal_paid').value || 0),
                        paid_regime: document.getElementById('company_regime').value,
                        costs: {
                            energia_eletrica: parseFloat(document.getElementById('cost_energy').value || 0),
                            insumos_diretos: parseFloat(document.getElementById('cost_supplies').value || 0),
                            aluguel_predios: parseFloat(document.getElementById('cost_rent').value || 0),
                            maquinas_equipamentos: parseFloat(document.getElementById('cost_machines').value || 0)
                        }
                    }
                ]
            };

            response = await fetch(`${API_URL}/analise-completa`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'x-api-key': API_KEY
                },
                body: JSON.stringify(formData)
            });
        }

        if (!response.ok) {
            const errText = await response.text();
            throw new Error(errText || 'Falha na análise');
        }

        const result = await response.json();

        // Hide Overlay
        overlay.classList.add('hidden');

        // Show Results
        document.getElementById('analysis-form').classList.add('hidden');
        document.getElementById('results').classList.remove('hidden');

        // Populate Data
        document.getElementById('result-savings').textContent = result.total_savings_potential;
        document.getElementById('result-count').textContent = result.opportunities_count;
        document.getElementById('btn-download').href = `${API_URL}${result.download_link}`;

    } catch (error) {
        overlay.classList.add('hidden');
        alert("Erro ao processar análise: " + error.message);
        console.error(error);
    }
}

async function runProgressAnimation() {
    const steps = ['step-1', 'step-2', 'step-3', 'step-4'];

    for (const stepId of steps) {
        const el = document.getElementById(stepId);
        el.classList.add('active');
        el.querySelector('i').className = "fa-solid fa-spinner fa-spin";

        // Wait random time between 800ms and 1500ms to simulate varied processing
        await new Promise(r => setTimeout(r, 800 + Math.random() * 700));

        el.querySelector('i').className = "fa-solid fa-check-circle";
    }
}

// Chat Logic
function setupChat() {
    const chatWidget = document.getElementById('chat-widget');
    const fab = document.getElementById('chat-fab');
    const toggleBtn = document.getElementById('chat-toggle-btn');
    const sendBtn = document.getElementById('chat-send-btn');
    const chatInput = document.getElementById('chat-input');
    const messagesContainer = document.getElementById('chat-messages');

    // Toggle
    function toggleChat() {
        chatWidget.classList.toggle('closed');
        if (!chatWidget.classList.contains('closed')) {
            setTimeout(() => chatInput.focus(), 300);
        }
    }

    fab.addEventListener('click', toggleChat);
    toggleBtn.addEventListener('click', toggleChat);

    // Send Message
    async function sendMessage() {
        const text = chatInput.value.trim();
        if (!text) return;

        // User Message
        appendMessage(text, 'user');
        chatInput.value = '';
        chatInput.disabled = true;

        // Bot Loading
        const loadingId = appendMessage('<i class="fa-solid fa-circle-notch fa-spin"></i> Consultando legislação...', 'bot');

        try {
            const response = await fetch(`${API_URL}/ask-legal`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'x-api-key': API_KEY
                },
                body: JSON.stringify({ question: text })
            });

            const data = await response.json();

            // Remove Loading
            const loadingEl = document.getElementById(loadingId);
            if (loadingEl) loadingEl.remove();

            if (data.error) {
                console.error("Chat Error:", data.error);
                appendMessage(`⚠️ <strong>Erro no Sistema:</strong> ${data.error}`, 'bot');
            } else {
                let answer = `<strong>${data.decision_summary || "Análise concluída."}</strong>`;

                if (data.applied_law_bases && data.applied_law_bases.length > 0) {
                    answer += `<br><br><small><strong>Base Legal:</strong> ${data.applied_law_bases.join(', ')}</small>`;
                }

                if (data.risk_level) {
                    const riskColor = data.risk_level === 'HIGH' ? 'red' : (data.risk_level === 'MEDIUM' ? 'orange' : 'green');
                    answer += `<br><small style="color:${riskColor}"><strong>Risco: ${data.risk_level}</strong></small>`;
                }

                appendMessage(answer, 'bot');
            }

        } catch (error) {
            console.error(error);
            const loadingEl = document.getElementById(loadingId);
            if (loadingEl) loadingEl.remove();
            appendMessage("Erro de conexão com o consultor.", 'bot');
        } finally {
            chatInput.disabled = false;
            chatInput.focus();
        }
    }

    sendBtn.addEventListener('click', sendMessage);
    chatInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendMessage();
    });

    function appendMessage(html, sender) {
        const div = document.createElement('div');
        div.className = `message ${sender}`;
        div.innerHTML = sender === 'user' ? `<p>${html}</p>` : `<p>${html}</p>`;
        const id = 'msg-' + Date.now();
        div.id = id;
        messagesContainer.appendChild(div);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        return id;
    }
}
