let chart;

document.getElementById('inventory-simulation-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    const button = e.target.querySelector('button');
    button.disabled = true;
    button.textContent = 'Simulating...';

    const formData = {
        initial_inventory: document.getElementById('initial_inventory').value,
        avg_daily_demand: document.getElementById('avg_daily_demand').value,
        demand_volatility: document.getElementById('demand_volatility').value,
        lead_time_days: document.getElementById('lead_time_days').value,
        num_days: document.getElementById('num_days').value,
        num_simulations: document.getElementById('num_simulations').value,
    };

    const response = await fetch('/simulate_inventory', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    });

    const data = await response.json();

    renderInventoryChart(data.inventory_simulations);
    displayInventorySummary(data);

    button.disabled = false;
    button.textContent = 'Run Inventory Simulation';
});

function renderInventoryChart(simulations) {
    const ctx = document.getElementById('inventory-chart').getContext('2d');

    if (chart) {
        chart.destroy();
    }

    const numSimulations = simulations[0].length;
    const numDays = simulations.length;
    const sampleSize = 20;

    const sampleDatasets = [];
    for (let i = 0; i < Math.min(numSimulations, sampleSize); i++) {
        sampleDatasets.push({
            label: `Simulation ${i + 1}`,
            data: simulations.map(s => s[i]),
            borderColor: 'rgba(255, 255, 255, 0.2)',
            borderWidth: 1,
            fill: false,
            pointRadius: 0,
            pointHoverRadius: 0,
        });
    }

    const averageSimulation = [];
    for (let i = 0; i < numDays; i++) {
        let sum = 0;
        for (let j = 0; j < numSimulations; j++) {
            sum += simulations[i][j];
        }
        averageSimulation.push(sum / numSimulations);
    }

    const averageDataset = {
        label: 'Average Inventory',
        data: averageSimulation,
        borderColor: '#00FF00',
        borderWidth: 2,
        fill: false,
        pointRadius: 0,
        tension: 0.1,
    };

    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array.from({ length: numDays }, (_, i) => i),
            datasets: [averageDataset, ...sampleDatasets]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { intersect: false, mode: 'index' },
            scales: {
                x: { title: { display: true, text: 'Days', color: 'white' }, ticks: { color: 'white' }, grid: { color: 'rgba(255, 255, 255, 0.1)' } },
                y: { title: { display: true, text: 'Inventory Level', color: 'white' }, ticks: { color: 'white' }, grid: { color: 'rgba(255, 255, 255, 0.1)' } }
            },
            plugins: {
                legend: { display: false },
                title: { display: true, text: 'Inventory Level Simulation', color: 'white', font: { size: 18 } },
                tooltip: { enabled: true }
            }
        }
    });
}

function displayInventorySummary(data) {
    const summaryContainer = document.getElementById('inventory-summary');
    summaryContainer.innerHTML = ''; // Clear previous results

    const metrics = {
        'Probability of Stockout': `${data.prob_of_stockout.toFixed(2)}%`,
        'Average Final Inventory': `${data.avg_final_inventory.toFixed(2)} units`,
        '90% Confidence Interval': `${data.confidence_interval_90.lower.toFixed(0)} - ${data.confidence_interval_90.upper.toFixed(0)} units`,
    };

    let delay = 0.5;
    for (const [key, value] of Object.entries(metrics)) {
        const card = document.createElement('div');
        card.className = 'card';
        card.style.animationDelay = `${delay}s`;
        card.innerHTML = `<h3>${key}</h3><p>${value}</p>`;
        summaryContainer.appendChild(card);
        delay += 0.5;
    }
}