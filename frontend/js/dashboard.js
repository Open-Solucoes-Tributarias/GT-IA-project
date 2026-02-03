const API_URL = "http://localhost:8000";

document.addEventListener('DOMContentLoaded', () => {
    fetchDashboardData();
});

async function fetchDashboardData() {
    try {
        const response = await fetch(`${API_URL}/dashboard-data`);
        const data = await response.json();

        if (data.error) throw new Error(data.error);

        updateKPIs(data.kpis);
        renderCharts(data);
        renderTable(data.recent_audits);

    } catch (error) {
        console.error("Dashboard Load Error:", error);
        alert("Erro ao carregar dados do dashboard.");
    }
}

function updateKPIs(kpis) {
    document.getElementById('kpi-savings').textContent = formatCurrency(kpis.savings);
    document.getElementById('kpi-companies').textContent = kpis.companies;
    document.getElementById('kpi-risk').textContent = kpis.risk_high;
}

function renderTable(audits) {
    const tbody = document.getElementById('table-body');
    tbody.innerHTML = '';

    audits.forEach(a => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${a.company}</td>
            <td>${a.date}</td>
            <td>${formatCurrency(a.savings)}</td>
            <td><span class="tag ${a.risk}">${a.risk}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

function renderCharts(data) {
    // Risk Chart
    const ctxRisk = document.getElementById('riskChart').getContext('2d');
    new Chart(ctxRisk, {
        type: 'doughnut',
        data: {
            labels: ['Alto Risco', 'Baixo Risco'],
            datasets: [{
                data: [data.kpis.risk_high, data.kpis.risk_low],
                backgroundColor: ['#C62828', '#2E7D32']
            }]
        }
    });

    // Savings Chart (Mocking top companies from recent audits for visual)
    const ctxSavings = document.getElementById('savingsChart').getContext('2d');
    const labels = data.recent_audits.map(a => a.company);
    const values = data.recent_audits.map(a => a.savings);

    new Chart(ctxSavings, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Economia (R$)',
                data: values,
                backgroundColor: '#0066CC',
                borderRadius: 5
            }]
        },
        options: {
            scales: {
                y: { beginAtZero: true }
            }
        }
    });

}

function formatCurrency(value) {
    return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(value);
}
