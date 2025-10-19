/**
 * Shared Chart.js Utilities
 * Provides theme-aware chart configuration and helpers
 * All charts read CSS variables to respect light/dark modes
 */

// Get CSS variable value
function getCSSVar(varName) {
    return getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
}

// Get theme colors from CSS variables
function getThemeColors() {
    return {
        cathayRed: getCSSVar('--cathay-red'),
        cathayGold: getCSSVar('--cathay-gold'),
        cathayBlack: getCSSVar('--cathay-black'),
        textPrimary: getCSSVar('--text-primary'),
        textSecondary: getCSSVar('--text-secondary'),
        bgPrimary: getCSSVar('--bg-primary'),
        bgSecondary: getCSSVar('--bg-secondary'),
        borderColor: getCSSVar('--border-color'),
        success: getCSSVar('--success'),
        warning: getCSSVar('--warning'),
        danger: getCSSVar('--danger'),
        info: getCSSVar('--info')
    };
}

// Default Chart.js configuration (theme-aware)
function getDefaultChartConfig() {
    const colors = getThemeColors();

    return {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: {
                labels: {
                    color: colors.textPrimary,
                    font: {
                        family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                        size: 12
                    }
                }
            },
            tooltip: {
                backgroundColor: colors.bgSecondary,
                titleColor: colors.textPrimary,
                bodyColor: colors.textSecondary,
                borderColor: colors.borderColor,
                borderWidth: 1,
                padding: 12,
                displayColors: true,
                callbacks: {}
            }
        },
        scales: {
            x: {
                ticks: {
                    color: colors.textSecondary
                },
                grid: {
                    color: colors.borderColor
                }
            },
            y: {
                ticks: {
                    color: colors.textSecondary
                },
                grid: {
                    color: colors.borderColor
                }
            }
        }
    };
}

// Create horizontal bar chart (for valuation comparison)
function createValuationChart(canvasId, data) {
    const colors = getThemeColors();
    const ctx = document.getElementById(canvasId);

    if (!ctx) {
        console.error(`Canvas element with ID '${canvasId}' not found`);
        return null;
    }

    // Define colors for each bar
    const barColors = [
        colors.textSecondary,    // Current Price (gray)
        colors.cathayGold,       // Wilson 95% (gold)
        colors.info,             // IRC Blended (blue)
        colors.success           // Regression (green)
    ];

    const config = getDefaultChartConfig();

    const chartConfig = {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Price Target ($)',
                data: data.values,
                backgroundColor: barColors,
                borderColor: barColors,
                borderWidth: 1
            }]
        },
        options: {
            ...config,
            indexAxis: 'y', // Horizontal bars
            plugins: {
                ...config.plugins,
                legend: {
                    display: false // Hide legend for single dataset
                },
                tooltip: {
                    ...config.plugins.tooltip,
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed.x;
                            const currentPrice = data.values[0];
                            const returnPct = ((value - currentPrice) / currentPrice * 100).toFixed(1);
                            return `$${value.toFixed(2)} (${returnPct > 0 ? '+' : ''}${returnPct}%)`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    ...config.scales.x,
                    beginAtZero: false,
                    min: Math.floor(Math.min(...data.values) * 0.9),
                    max: Math.ceil(Math.max(...data.values) * 1.05),
                    ticks: {
                        ...config.scales.x.ticks,
                        callback: function(value) {
                            return '$' + value.toFixed(0);
                        }
                    }
                },
                y: {
                    ...config.scales.y
                }
            }
        }
    };

    return new Chart(ctx, chartConfig);
}

// Create line chart (for NCO trend)
function createNCOTrendChart(canvasId, data) {
    const colors = getThemeColors();
    const ctx = document.getElementById(canvasId);

    if (!ctx) {
        console.error(`Canvas element with ID '${canvasId}' not found`);
        return null;
    }

    const config = getDefaultChartConfig();

    const chartConfig = {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'NCO Rate (bps)',
                data: data.values,
                borderColor: colors.cathayRed,
                backgroundColor: colors.cathayRed + '20', // 20% opacity
                tension: 0.1,
                fill: true,
                pointBackgroundColor: colors.cathayRed,
                pointBorderColor: colors.bgSecondary,
                pointBorderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6
            }]
        },
        options: {
            ...config,
            plugins: {
                ...config.plugins,
                legend: {
                    display: false
                },
                tooltip: {
                    ...config.plugins.tooltip,
                    callbacks: {
                        label: function(context) {
                            return context.parsed.y.toFixed(1) + ' bps';
                        }
                    }
                }
            },
            scales: {
                x: {
                    ...config.scales.x
                },
                y: {
                    ...config.scales.y,
                    beginAtZero: true,
                    ticks: {
                        ...config.scales.y.ticks,
                        callback: function(value) {
                            return value.toFixed(0) + ' bps';
                        }
                    }
                }
            }
        }
    };

    return new Chart(ctx, chartConfig);
}

// Update all charts when theme changes
function updateChartsOnThemeChange(chartInstances) {
    chartInstances.forEach(chart => {
        if (chart) {
            const colors = getThemeColors();

            // Update chart colors
            chart.options.plugins.legend.labels.color = colors.textPrimary;
            chart.options.plugins.tooltip.backgroundColor = colors.bgSecondary;
            chart.options.plugins.tooltip.titleColor = colors.textPrimary;
            chart.options.plugins.tooltip.bodyColor = colors.textSecondary;
            chart.options.plugins.tooltip.borderColor = colors.borderColor;

            if (chart.options.scales.x) {
                chart.options.scales.x.ticks.color = colors.textSecondary;
                chart.options.scales.x.grid.color = colors.borderColor;
            }

            if (chart.options.scales.y) {
                chart.options.scales.y.ticks.color = colors.textSecondary;
                chart.options.scales.y.grid.color = colors.borderColor;
            }

            chart.update();
        }
    });
}

// Fetch market data from JSON
async function fetchMarketData() {
    try {
        const response = await fetch('data/market_data_current.json');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching market data:', error);
        return null;
    }
}

// Initialize valuation comparison chart from market data
async function initValuationChart(canvasId) {
    const marketData = await fetchMarketData();

    if (!marketData) {
        console.error('Failed to load market data');
        return null;
    }

    const chartData = {
        labels: [
            'Current Price',
            'Wilson 95%',
            'IRC Blended',
            'Regression'
        ],
        values: [
            marketData.price,
            marketData.calculated_metrics.target_wilson_95,
            marketData.calculated_metrics.target_irc_blended,
            marketData.calculated_metrics.target_regression
        ]
    };

    return createValuationChart(canvasId, chartData);
}

// Fetch NCO history from JSON
async function fetchNCOHistory() {
    try {
        const response = await fetch('data/fdic_nco_history.json');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching NCO history:', error);
        return null;
    }
}

// Initialize NCO trend chart from FDIC history
async function initNCOChart(canvasId) {
    const ncoHistory = await fetchNCOHistory();

    if (!ncoHistory) {
        console.error('Failed to load NCO history');
        return null;
    }

    const chartData = {
        labels: ncoHistory.labels,
        values: ncoHistory.values
    };

    return createNCOTrendChart(canvasId, chartData);
}
