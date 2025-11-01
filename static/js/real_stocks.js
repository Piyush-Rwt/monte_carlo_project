document.addEventListener('DOMContentLoaded', () => {
    const stockButtons = document.querySelectorAll('.btn-stock');
    const resultsSection = document.getElementById('results-section');
    let historicalChart;
    let simulationChart;

    stockButtons.forEach(button => {
        button.addEventListener('click', async () => {
            const symbol = button.dataset.symbol;
            resultsSection.style.display = 'block';

            // Fetch simulation data
            const response = await fetch(`/simulate_real_stock/${symbol}`);
            const data = await response.json();

            // Update UI
            document.getElementById('stock-name').textContent = button.textContent;
            document.getElementById('current-price').textContent = `$${data.current_price.toFixed(2)}`;
            document.getElementById('confidence-range').textContent = `$${data.confidence_range.lower.toFixed(2)} - $${data.confidence_range.upper.toFixed(2)}`;
            document.getElementById('prob-of-loss').textContent = `${data.prob_of_loss.toFixed(2)}%`;
            document.getElementById('risk-level').textContent = data.risk_level;

            // Render charts
            renderHistoricalChart(data.historical_data);
            renderSimulationChart(data.simulations);
        });
    });

    function renderHistoricalChart(historicalData) {
        const ctx = document.getElementById('historical-chart').getContext('2d');

        if (historicalChart) {
            historicalChart.destroy();
        }

        historicalChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: Array.from({ length: historicalData.length }, (_, i) => i),
                datasets: [{
                    label: 'Historical Price',
                    data: historicalData,
                    borderColor: '#007bff',
                    borderWidth: 2,
                    fill: false,
                    pointRadius: 0,
                }],
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
                        text: 'Historical Performance (6 Months)'
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

    function renderSimulationChart(simulations) {
        const ctx = document.getElementById('simulation-chart').getContext('2d');

        if (simulationChart) {
            simulationChart.destroy();
        }

        const datasets = simulations.map((simulation, index) => ({
            label: `Simulation ${index + 1}`,
            data: simulation,
            borderColor: `rgba(0, 123, 255, 0.1)`,
            borderWidth: 1,
            fill: false,
            pointRadius: 0,
        }));

        simulationChart = new Chart(ctx, {
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
                        text: 'Monte Carlo Simulation (30 Days)'
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
});
