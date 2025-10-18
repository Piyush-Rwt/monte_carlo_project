let chart;
let simulationData = []; // Store simulation data globally

document.getElementById('simulation-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    // Show loading state
    const button = e.target.querySelector('button');
    button.disabled = true;
    button.textContent = 'Simulating...';

    const initial_price = document.getElementById('initial_price').value;
    const volatility = document.getElementById('volatility').value;
    const num_days = document.getElementById('num_days').value;
    const num_simulations = document.getElementById('num_simulations').value;
    const target_price = document.getElementById('target_price').value;

    const response = await fetch('/simulate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            initial_price,
            volatility,
            num_days,
            num_simulations,
            target_price
        })
    });

    const data = await response.json();
    simulationData = data.simulations; // Store the data

    renderChart(simulationData);
    displaySummary(data);
    displayRiskAnalysis(data);

    // Restore button state
    button.disabled = false;
    button.textContent = 'Run Simulation';
});

function renderChart(simulations) {
    const ctx = document.getElementById('simulation-chart').getContext('2d');

    if (chart) {
        chart.destroy();
    }

    const numSimulations = simulations[0].length;
    const numDays = simulations.length;
    const sampleSize = 20;

    // Plot a sample of simulations - disable interaction for performance
    const sampleDatasets = [];
    for (let i = 0; i < Math.min(numSimulations, sampleSize); i++) {
        sampleDatasets.push({
            label: `Simulation ${i + 1}`,
            data: simulations.map(s => s[i]),
            borderColor: 'rgba(255, 255, 255, 0.2)',
            borderWidth: 1,
            fill: false,
            pointRadius: 0,
            pointHoverRadius: 0, // Disable hover points
        });
    }
    
    // Calculate and plot the average simulation
    const averageSimulation = [];
    for (let i = 0; i < numDays; i++) {
        let sum = 0;
        for (let j = 0; j < numSimulations; j++) {
            sum += simulations[i][j];
        }
        averageSimulation.push(sum / numSimulations);
    }

    const averageDataset = {
        label: 'Average Simulation',
        data: averageSimulation,
        borderColor: '#00FF00',
        borderWidth: 2,
        fill: false,
        pointRadius: 0,
        tension: 0.1 // Slightly smooth the line
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
            interaction: {
                intersect: false,
                mode: 'index',
            },
            scales: {
                x: {
                    title: { display: true, text: 'Days', color: 'white' },
                    ticks: { color: 'white' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                },
                y: {
                    title: { display: true, text: 'Price', color: 'white' },
                    ticks: { color: 'white' },
                    grid: { color: 'rgba(255, 255, 255, 0.1)' }
                }
            },
            plugins: {
                legend: { display: false },
                title: {
                    display: true,
                    text: 'Monte Carlo Stock Price Simulation',
                    color: 'white',
                    font: { size: 18 }
                },
                tooltip: {
                    enabled: true
                }
            }
        }
    });
}

function displaySummary(data) {
    document.getElementById('avg-price').textContent = `$${data.avg_final_price.toFixed(2)}`;
    document.getElementById('min-price').textContent = `$${data.worst_case_price.toFixed(2)}`;
    document.getElementById('max-price').textContent = `$${data.best_case_price.toFixed(2)}`;

    const probCard = document.getElementById('prob-card');
    if (data.probability !== null) {
        document.getElementById('probability').textContent = `${data.probability.toFixed(2)}%`;
        probCard.style.display = 'block';
    } else {
        probCard.style.display = 'none';
    }

    document.querySelector('.summary-cards').style.opacity = 1;
}

function displayRiskAnalysis(data) {
    document.getElementById('loss-prob').textContent = `${data.prob_of_loss.toFixed(2)}%`;
    document.getElementById('ci-range').textContent = `$${data.confidence_interval_90.lower.toFixed(2)} - $${data.confidence_interval_90.upper.toFixed(2)}`;
    document.getElementById('var-value').textContent = `$${data.value_at_risk_95.toFixed(2)}`;
}

function displayRiskAnalysis(data) {
    document.getElementById('loss-prob').textContent = `${data.prob_of_loss.toFixed(2)}%`;
    document.getElementById('ci-range').textContent = `$${data.confidence_interval_90.lower.toFixed(2)} - $${data.confidence_interval_90.upper.toFixed(2)}`;
    document.getElementById('var-value').textContent = `$${data.value_at_risk_95.toFixed(2)}`;
}

document.getElementById('check-day-btn').addEventListener('click', () => {
    const dayInput = document.getElementById('day-input');
    const day = parseInt(dayInput.value, 10);
    const detailsDiv = document.getElementById('day-details');

    if (!simulationData || simulationData.length === 0) {
        detailsDiv.innerHTML = '<p class="error">Please run a simulation first.</p>';
        return;
    }

    if (isNaN(day) || day < 0 || day >= simulationData.length) {
        detailsDiv.innerHTML = `<p class="error">Invalid day. Please enter a number between 0 and ${simulationData.length - 1}.</p>`;
        return;
    }

    const pricesOnDay = simulationData[day];
    const avgPrice = pricesOnDay.reduce((a, b) => a + b, 0) / pricesOnDay.length;
    const minPrice = Math.min(...pricesOnDay);
    const maxPrice = Math.max(...pricesOnDay);

    detailsDiv.innerHTML = `
        <h4>Details for Day ${day}</h4>
        <p><strong>Average Price:</strong> $${avgPrice.toFixed(2)}</p>
        <p><strong>Minimum Price:</strong> $${minPrice.toFixed(2)}</p>
        <p><strong>Maximum Price:</strong> $${maxPrice.toFixed(2)}</p>
    `;
});