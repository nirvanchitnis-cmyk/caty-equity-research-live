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

// Create vertical bar chart (for valuation comparison) - Cathay Brand Colors
function createValuationChart(canvasId, data) {
    const ctx = document.getElementById(canvasId);

    if (!ctx) {
        console.error(`Canvas element with ID '${canvasId}' not found`);
        return null;
    }

    // Cathay Brand Colors (NO gradients)
    const cathayRed = '#C41E3A';
    const cathayGold = '#D4AF37';
    const offBlack = '#1C1C1C';
    const offWhite = '#F8F8F6';
    const gridColor = '#E5E5E5';

    // Define colors for each bar
    const barColors = [
        offBlack,      // Current Price (off-black)
        cathayGold,    // Wilson 95% (Cathay Gold)
        cathayRed,     // IRC Blended (Cathay Red)
        cathayGold     // Regression (Cathay Gold)
    ];

    const chartConfig = {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Price Target ($)',
                data: data.values,
                backgroundColor: barColors,
                borderColor: barColors,
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: offWhite,
                    titleColor: offBlack,
                    bodyColor: offBlack,
                    borderColor: gridColor,
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            const value = context.parsed.y;
                            const currentPrice = data.values[0];
                            const returnPct = ((value - currentPrice) / currentPrice * 100).toFixed(1);
                            return `$${value.toFixed(2)} (${returnPct > 0 ? '+' : ''}${returnPct}%)`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: offBlack,
                        font: {
                            size: 12,
                            weight: '600'
                        }
                    },
                    grid: {
                        display: false
                    }
                },
                y: {
                    beginAtZero: false,
                    min: 35,
                    max: 60,
                    ticks: {
                        color: offBlack,
                        font: {
                            size: 12
                        },
                        callback: function(value) {
                            return '$' + value.toFixed(0);
                        }
                    },
                    grid: {
                        color: gridColor,
                        lineWidth: 1
                    },
                    title: {
                        display: true,
                        text: 'Target Price ($)',
                        color: offBlack,
                        font: {
                            size: 14,
                            weight: 'bold'
                        }
                    }
                }
            }
        }
    };

    return new Chart(ctx, chartConfig);
}

// Create line chart (for NCO trend) - Cathay Brand Colors
function createNCOTrendChart(canvasId, data) {
    const ctx = document.getElementById(canvasId);

    if (!ctx) {
        console.error(`Canvas element with ID '${canvasId}' not found`);
        return null;
    }

    // Cathay Brand Colors
    const cathayRed = '#C41E3A';
    const offBlack = '#1C1C1C';
    const offWhite = '#F8F8F6';
    const gridColor = '#E5E5E5';

    const chartConfig = {
        type: 'line',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'NCO Rate (bps)',
                data: data.values,
                borderColor: cathayRed,
                backgroundColor: cathayRed + '33', // 20% opacity
                tension: 0.3,
                fill: true,
                pointBackgroundColor: cathayRed,
                pointBorderColor: offWhite,
                pointBorderWidth: 2,
                pointRadius: 3,
                pointHoverRadius: 6,
                borderWidth: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: offWhite,
                    titleColor: offBlack,
                    bodyColor: offBlack,
                    borderColor: gridColor,
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            return context.parsed.y.toFixed(1) + ' bps';
                        }
                    }
                }
            },
            scales: {
                x: {
                    ticks: {
                        color: offBlack,
                        font: {
                            size: 10
                        },
                        maxRotation: 45,
                        minRotation: 45
                    },
                    grid: {
                        color: gridColor,
                        lineWidth: 0.5
                    }
                },
                y: {
                    beginAtZero: true,
                    ticks: {
                        color: offBlack,
                        font: {
                            size: 12
                        },
                        callback: function(value) {
                            return value.toFixed(0) + ' bps';
                        }
                    },
                    grid: {
                        color: gridColor,
                        lineWidth: 1
                    },
                    title: {
                        display: true,
                        text: 'Net Charge-Off Rate (bps)',
                        color: offBlack,
                        font: {
                            size: 14,
                            weight: 'bold'
                        }
                    }
                }
            }
        }
    };

    return new Chart(ctx, chartConfig);
}

// Create scatter plot (for peer regression) - Cathay Brand Colors
function createPeerScatterChart(canvasId, peerData, regressionData) {
    const ctx = document.getElementById(canvasId);

    if (!ctx) {
        console.error(`Canvas element with ID '${canvasId}' not found`);
        return null;
    }

    // Cathay Brand Colors
    const cathayRed = '#C41E3A';
    const cathayGold = '#D4AF37';
    const offBlack = '#1C1C1C';
    const offWhite = '#F8F8F6';
    const gridColor = '#E5E5E5';

    const chartConfig = {
        type: 'scatter',
        data: {
            datasets: [
                // Peers (red dots)
                {
                    label: 'Peers',
                    data: peerData.peers,
                    backgroundColor: cathayRed,
                    borderColor: cathayRed,
                    pointRadius: 8,
                    pointHoverRadius: 10
                },
                // CATY (gold dot with red border)
                {
                    label: 'CATY',
                    data: [peerData.caty],
                    backgroundColor: cathayGold,
                    borderColor: cathayRed,
                    pointRadius: 12,
                    pointHoverRadius: 14,
                    borderWidth: 2
                },
                // Regression line (off-black dashed)
                {
                    label: 'Regression Line',
                    data: regressionData,
                    type: 'line',
                    borderColor: offBlack,
                    borderWidth: 2,
                    borderDash: [8, 4],
                    fill: false,
                    pointRadius: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        color: offBlack,
                        font: {
                            size: 12,
                            weight: '600'
                        },
                        usePointStyle: true
                    }
                },
                tooltip: {
                    backgroundColor: offWhite,
                    titleColor: offBlack,
                    bodyColor: offBlack,
                    borderColor: gridColor,
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            if (context.dataset.type === 'line') return null;
                            return `ROTE: ${context.parsed.x.toFixed(2)}%, P/TBV: ${context.parsed.y.toFixed(3)}x`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    type: 'linear',
                    min: 7,
                    max: 18,
                    ticks: {
                        color: offBlack,
                        font: {
                            size: 12
                        },
                        callback: function(value) {
                            return value.toFixed(0) + '%';
                        }
                    },
                    grid: {
                        color: gridColor,
                        lineWidth: 1
                    },
                    title: {
                        display: true,
                        text: 'ROTE (%)',
                        color: offBlack,
                        font: {
                            size: 14,
                            weight: 'bold'
                        }
                    }
                },
                y: {
                    min: 0.5,
                    max: 2.0,
                    ticks: {
                        color: offBlack,
                        font: {
                            size: 12
                        },
                        callback: function(value) {
                            return value.toFixed(1) + 'x';
                        }
                    },
                    grid: {
                        color: gridColor,
                        lineWidth: 1
                    },
                    title: {
                        display: true,
                        text: 'P/TBV (x)',
                        color: offBlack,
                        font: {
                            size: 14,
                            weight: 'bold'
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

// Initialize peer scatter plot (ROTE vs P/TBV)
function initPeerScatterChart(canvasId) {
    // Peer data from CATY_11 (n=4 clean cohort)
    const peerData = {
        peers: [
            { x: 8.65, y: 0.930, label: 'HAFC' },
            { x: 14.10, y: 1.730, label: 'CVBF' },
            { x: 16.38, y: 1.830, label: 'EWBC' }
        ],
        caty: { x: 11.95, y: 1.269, label: 'CATY' }
    };

    // Regression line: P/TBV = -0.1483 + 0.1244*ROTE
    // Calculate two points for the line
    const regressionData = [
        { x: 8, y: -0.1483 + 0.1244 * 8 },    // Left edge
        { x: 17, y: -0.1483 + 0.1244 * 17 }   // Right edge
    ];

    return createPeerScatterChart(canvasId, peerData, regressionData);
}
