document.getElementById('simulation-form').addEventListener('submit', function(event) {
    event.preventDefault();

    const initialPrice = parseFloat(document.getElementById('initial-price').value);
    const volatility = parseFloat(document.getElementById('volatility').value);
    const numDays = parseInt(document.getElementById('num-days').value);
    const numSimulations = parseInt(document.getElementById('num-simulations').value);
    const targetPrice = document.getElementById('target-price').value ? parseFloat(document.getElementById('target-price').value) : null;

    fetch('/simulate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            initial_price: initialPrice,
            volatility: volatility,
            num_days: numDays,
            num_simulations: numSimulations,
            target_price: targetPrice
        })
    })
    .then(response => response.json())
    .then(data => {
        displaySummary(initialPrice, volatility, numDays, numSimulations, targetPrice, data.avg_final_price, data.best_case_price, data.worst_case_price, data.probability);
        displayChart(data.simulations);
    });
});

function displaySummary(initialPrice, volatility, numDays, numSimulations, targetPrice, avgFinalPrice, bestCase, worstCase, probability) {
    const summaryContent = document.getElementById('summary-content');
    summaryContent.innerHTML = `
        <p><strong>Initial Price:</strong> $${initialPrice.toFixed(2)}</p>
        <p><strong>Daily Volatility:</strong> ${volatility.toFixed(2)}%</p>
        <p><strong>Simulation Days:</strong> ${numDays}</p>
        <p><strong>Number of Simulations:</strong> ${numSimulations}</p>
        ${targetPrice ? `<p><strong>Target Price:</strong> $${targetPrice.toFixed(2)}</p>` : ''}
        <hr>
        <p><strong>Average Final Price:</strong> $${avgFinalPrice.toFixed(2)}</p>
        <p><strong>Best-Case Final Price:</strong> $${bestCase.toFixed(2)}</p>
        <p><strong>Worst-Case Final Price:</strong> $${worstCase.toFixed(2)}</p>
        ${probability !== null ? `<p><strong>Probability of reaching target:</strong> ${probability.toFixed(2)}%</p>` : ''}
    `;
}

let chart;
function displayChart(simulations) {
    const ctx = document.getElementById('simulation-chart').getContext('2d');

    if (chart) {
        chart.destroy();
    }

    const datasets = simulations.map((simulation, index) => ({
        label: `Simulation ${index + 1}`,
        data: simulation,
        borderColor: `rgba(${Math.random() * 255}, ${Math.random() * 255}, ${Math.random() * 255}, 0.5)`,
        borderWidth: 1,
        fill: false,
        pointRadius: 0,
    }));

    chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array.from({ length: simulations[0].length }, (_, i) => i),
            datasets: datasets,
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: 'Monte Carlo Stock Price Simulation'
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Days'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Price'
                    }
                }
            }
        }
    });
}
