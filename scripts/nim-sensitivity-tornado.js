/* global Chart */
(function() {
    'use strict';

    const DATA_URL = 'data/caty05_calculated_tables.json';

    const SELECTORS = {
        canvas: 'nimTornadoChart',
        toggleRote: 'nimToggleRote',
        toggleValuation: 'nimToggleValuation',
        exportPng: 'nimExportPng',
        exportCsv: 'nimExportCsv',
        tableBody: 'nimTornadoTableBody',
        status: 'nimToggleStatus'
    };

    const DATASET_IDS = {
        low: 'nimLowDataset',
        high: 'nimHighDataset'
    };

    const CONSTANTS = {
        rotePerBps: 0.015,
        valuationPerBps: 0.25,
        pngWidth: 1200,
        pngHeight: 800,
        tooltipLineHeight: 16
    };

    const state = {
        chart: null,
        scenarios: [],
        showRote: false,
        showValuation: false
    };

    const midpointLabelPlugin = {
        id: 'nimMidpointLabels',
        afterDatasetsDraw(chart) {
            if (!state.chart || !state.scenarios.length) {
                return;
            }

            const { ctx, scales } = chart;
            const xScale = scales.x;
            const yScale = scales.y;
            const lowMeta = chart.getDatasetMeta(getDatasetIndex(DATASET_IDS.low, chart));
            const highMeta = chart.getDatasetMeta(getDatasetIndex(DATASET_IDS.high, chart));
            const midpointColor = getCssVar('--nim-tornado-midpoint-label') || '#14202D';
            const annotationColor = getCssVar('--text-secondary') || '#4F5B67';
            const lineHeight = CONSTANTS.tooltipLineHeight;

            ctx.save();
            ctx.font = '600 12px "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
            ctx.textBaseline = 'middle';
            ctx.fillStyle = midpointColor;

            state.scenarios.forEach((scenario, index) => {
                const refElement = (highMeta.data[index] && typeof highMeta.data[index].y === 'number')
                    ? highMeta.data[index]
                    : lowMeta.data[index];

                if (!refElement) {
                    return;
                }

                const centerY = refElement.y;
                const midpointX = xScale.getPixelForValue(scenario.midpoint);

                ctx.textAlign = 'center';
                ctx.fillStyle = midpointColor;
                ctx.fillText(scenario.midpointLabel, midpointX, centerY);

                const annotationLines = [];
                if (state.showRote) {
                    annotationLines.push(scenario.roteLabel);
                }
                if (state.showValuation) {
                    annotationLines.push(scenario.valuationLabel);
                }

                if (!annotationLines.length) {
                    return;
                }

                const isCompression = scenario.isCompression;
                const anchorValue = isCompression
                    ? -Math.abs(scenario.nimLow)
                    : Math.max(scenario.nimHigh, 0);
                const anchorX = xScale.getPixelForValue(anchorValue) + (isCompression ? -12 : 12);

                ctx.fillStyle = annotationColor;
                ctx.textAlign = isCompression ? 'right' : 'left';

                const totalHeight = (annotationLines.length - 1) * lineHeight;
                const startY = centerY - totalHeight / 2;

                annotationLines.forEach((text, lineIndex) => {
                    ctx.fillText(text, anchorX, startY + lineIndex * lineHeight);
                });
            });

            ctx.restore();
        }
    };

    const zeroLinePlugin = {
        id: 'nimZeroBaseline',
        afterDraw(chart) {
            if (!state.chart) {
                return;
            }

            const { ctx, chartArea, scales } = chart;
            const xScale = scales.x;
            const zeroX = xScale.getPixelForValue(0);

            ctx.save();
            ctx.beginPath();
            ctx.moveTo(zeroX, chartArea.top);
            ctx.lineTo(zeroX, chartArea.bottom);
            ctx.lineWidth = 2;
            ctx.strokeStyle = getCssVar('--border-color') || '#D6DADD';
            ctx.stroke();
            ctx.restore();
        }
    };

    function getCssVar(varName) {
        return getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
    }

    function toNumber(value, fallback = 0) {
        const num = Number(value);
        return Number.isFinite(num) ? num : fallback;
    }

    function sanitizeMinus(value) {
        return typeof value === 'string'
            ? value.replace(/\u2212/g, '-')
            : value;
    }

    function parseNimRange(text) {
        if (typeof text !== 'string') {
            return { low: 0, high: 0 };
        }

        const normalised = sanitizeMinus(text);
        const match = normalised.match(/([+\-]?\d+(?:\.\d*)?)\s*to\s*([+\-]?\d+(?:\.\d*)?)\s*bps/i);

        if (!match) {
            return { low: 0, high: 0 };
        }

        const low = Number.parseFloat(match[1]);
        const high = Number.parseFloat(match[2]);

        if (!Number.isFinite(low) || !Number.isFinite(high)) {
            return { low: 0, high: 0 };
        }

        return low <= high ? { low, high } : { low: high, high: low };
    }

    function formatSigned(value, decimals = 0, suffix = '', { includePlus = true } = {}) {
        if (!Number.isFinite(value)) {
            return 'n/a';
        }

        const rounded = value.toFixed(decimals);
        const needsPlus = includePlus && value > 0;
        return `${needsPlus ? '+' : ''}${rounded}${suffix}`;
    }

    function formatCurrency(value) {
        if (!Number.isFinite(value)) {
            return 'n/a';
        }

        return `${value >= 0 ? '+' : '-'}$${Math.abs(value).toFixed(2)}`;
    }

    function buildKeyLabel(name, fedCut, scenarioKey) {
        const stickySuffix = scenarioKey === 'sticky' ? ', 40% β' : '';
        return `${name} (${formatSigned(fedCut, 0, ' bps')}${stickySuffix})`;
    }

    function buildScenarioObjects(rawScenarios) {
        if (!rawScenarios || typeof rawScenarios !== 'object') {
            return [];
        }

        const entries = Object.entries(rawScenarios).map(([key, value]) => {
            const { low, high } = parseNimRange(value.nim_impact_text || '');
            const fedCut = toNumber(value.fed_cut_bps, 0);
            const depositDelta = toNumber(value.deposit_cost_delta_bps, 0);
            const midpoint = (low + high) / 2;

            const roteImpact = midpoint * CONSTANTS.rotePerBps;
            const valuationImpact = midpoint * CONSTANTS.valuationPerBps;

            return {
                key,
                name: value.name || key,
                assumptions: value.assumptions || '',
                fedCut,
                depositDelta,
                nimLow: low,
                nimHigh: high,
                midpoint,
                midpointLabel: formatSigned(midpoint, 0, ' bps'),
                roteImpact,
                roteLabel: `${formatSigned(roteImpact, 2, '% ROTE')}`,
                valuationImpact,
                valuationLabel: `${formatCurrency(valuationImpact)}/sh`,
                label: buildKeyLabel(value.name || key, fedCut, key),
                isCompression: high <= 0
            };
        });

        return entries.sort((a, b) => Math.abs(b.midpoint) - Math.abs(a.midpoint));
    }

    function getDatasetIndex(id, chartInstance = state.chart) {
        if (!chartInstance) {
            return -1;
        }

        return chartInstance.data.datasets.findIndex(dataset => dataset.id === id);
    }

    function getDatasetColors() {
        const expansion = withOpacity(
            getCssVar('--nim-tornado-expansion') || '#2E6F3E',
            toNumber(getCssVar('--nim-tornado-bar-opacity'), 0.85) || 0.85
        );
        const compression = withOpacity(
            getCssVar('--nim-tornado-compression') || '#8C1E33',
            toNumber(getCssVar('--nim-tornado-bar-opacity'), 0.85) || 0.85
        );

        const lowColors = [];
        const highColors = [];

        state.scenarios.forEach(scenario => {
            const color = scenario.isCompression ? compression : expansion;
            lowColors.push(color);
            highColors.push(color);
        });

        return { lowColors, highColors };
    }

    function withOpacity(color, opacity) {
        if (!color) {
            return `rgba(46, 111, 62, ${opacity})`;
        }

        const trimmed = color.trim();

        if (trimmed.startsWith('#')) {
            const hex = trimmed.substring(1);
            const isShort = hex.length === 3;
            const r = Number.parseInt(isShort ? hex[0] + hex[0] : hex.substring(0, 2), 16);
            const g = Number.parseInt(isShort ? hex[1] + hex[1] : hex.substring(2, 4), 16);
            const b = Number.parseInt(isShort ? hex[2] + hex[2] : hex.substring(4, 6), 16);
            if ([r, g, b].some(num => Number.isNaN(num))) {
                return `rgba(46, 111, 62, ${opacity})`;
            }
            return `rgba(${r}, ${g}, ${b}, ${opacity})`;
        }

        if (trimmed.startsWith('rgb')) {
            return trimmed.replace(/rgba?\(([^)]+)\)/, (_, rgbValues) => {
                const parts = rgbValues.split(',').map(part => part.trim());
                const base = parts.slice(0, 3).join(', ');
                return `rgba(${base}, ${opacity})`;
            });
        }

        return `rgba(46, 111, 62, ${opacity})`;
    }

    function buildChart() {
        const canvas = document.getElementById(SELECTORS.canvas);
        if (!canvas || typeof Chart === 'undefined') {
            return;
        }

        const { lowColors, highColors } = getDatasetColors();
        const labels = state.scenarios.map(scenario => scenario.label);

        const data = {
            labels,
            datasets: [
                {
                    id: DATASET_IDS.low,
                    label: 'Low bound',
                    data: state.scenarios.map(scenario => {
                        const value = scenario.nimLow;
                        if (value === 0) {
                            return 0;
                        }
                        return value > 0 ? -Math.abs(value) : value;
                    }),
                    backgroundColor: lowColors,
                    borderWidth: 0,
                    borderRadius: 12,
                    barPercentage: 0.75,
                    categoryPercentage: 0.65,
                    stack: 'nimRange'
                },
                {
                    id: DATASET_IDS.high,
                    label: 'High bound',
                    data: state.scenarios.map(scenario => scenario.nimHigh),
                    backgroundColor: highColors,
                    borderWidth: 0,
                    borderRadius: 12,
                    barPercentage: 0.75,
                    categoryPercentage: 0.65,
                    stack: 'nimRange'
                }
            ]
        };

        state.chart = new Chart(canvas, {
            type: 'bar',
            data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                indexAxis: 'y',
                layout: {
                    padding: {
                        top: 16,
                        right: 32,
                        bottom: 16,
                        left: 24
                    }
                },
                animation: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: getCssVar('--bg-secondary') || '#F8FBF8',
                        borderColor: getCssVar('--border-color') || '#D6DADD',
                        borderWidth: 1,
                        titleColor: getCssVar('--text-primary') || '#14202D',
                        bodyColor: getCssVar('--text-secondary') || '#4F5B67',
                        padding: 12,
                        callbacks: {
                            title(context) {
                                if (!context.length) {
                                    return '';
                                }
                                const scenario = state.scenarios[context[0].dataIndex];
                                return scenario ? scenario.name : '';
                            },
                            label(context) {
                                const scenario = state.scenarios[context.dataIndex];
                                if (!scenario) {
                                    return '';
                                }

                                const low = formatSigned(scenario.nimLow, 0, ' bps');
                                const high = formatSigned(scenario.nimHigh, 0, ' bps');
                                return `NIM Impact: ${low} to ${high} (mid ${scenario.midpointLabel})`;
                            },
                            afterLabel(context) {
                                const scenario = state.scenarios[context.dataIndex];
                                if (!scenario) {
                                    return [];
                                }

                                const fedCut = `Fed Cut: ${formatSigned(scenario.fedCut, 0, ' bps')}`;
                                const deposit = `Deposit Δ: ${formatSigned(scenario.depositDelta, 0, ' bps')}`;
                                return [fedCut, deposit, scenario.assumptions];
                            }
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    intersect: false
                },
                scales: {
                    x: {
                        min: -5,
                        max: 45,
                        border: {
                            color: getCssVar('--border-color') || '#D6DADD'
                        },
                        grid: {
                            color: value => (value.tick.value === 0
                                ? getCssVar('--border-color') || '#D6DADD'
                                : `${getCssVar('--border-color') || '#D6DADD'}33`),
                            lineWidth: value => (value.tick.value === 0 ? 0 : 1)
                        },
                        ticks: {
                            color: getCssVar('--text-secondary') || '#4F5B67',
                            callback: value => `${value} bps`,
                            stepSize: 10
                        },
                        title: {
                            display: true,
                            text: 'NIM Impact (bps)',
                            color: getCssVar('--text-primary') || '#14202D',
                            font: {
                                weight: 'bold'
                            }
                        }
                    },
                    y: {
                        border: {
                            color: getCssVar('--border-color') || '#D6DADD'
                        },
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: getCssVar('--text-primary') || '#14202D',
                            font: {
                                weight: 600
                            }
                        }
                    }
                }
            },
            plugins: [zeroLinePlugin, midpointLabelPlugin]
        });
    }

    function refreshChartTheme() {
        if (!state.chart) {
            return;
        }

        const { lowColors, highColors } = getDatasetColors();
        const { options, data } = state.chart;

        if (data.datasets[0]) {
            data.datasets[0].backgroundColor = lowColors;
        }
        if (data.datasets[1]) {
            data.datasets[1].backgroundColor = highColors;
        }

        if (options.scales?.x) {
            options.scales.x.border.color = getCssVar('--border-color') || '#D6DADD';
            options.scales.x.grid.color = value => (value.tick.value === 0
                ? getCssVar('--border-color') || '#D6DADD'
                : `${getCssVar('--border-color') || '#D6DADD'}33`);
            options.scales.x.ticks.color = getCssVar('--text-secondary') || '#4F5B67';
            options.scales.x.title.color = getCssVar('--text-primary') || '#14202D';
        }

        if (options.scales?.y) {
            options.scales.y.border.color = getCssVar('--border-color') || '#D6DADD';
            options.scales.y.ticks.color = getCssVar('--text-primary') || '#14202D';
        }

        if (options.plugins?.tooltip) {
            const tooltip = options.plugins.tooltip;
            tooltip.backgroundColor = getCssVar('--bg-secondary') || '#F8FBF8';
            tooltip.borderColor = getCssVar('--border-color') || '#D6DADD';
            tooltip.titleColor = getCssVar('--text-primary') || '#14202D';
            tooltip.bodyColor = getCssVar('--text-secondary') || '#4F5B67';
        }

        state.chart.update('none');
    }

    function populateTable() {
        const tbody = document.getElementById(SELECTORS.tableBody);
        if (!tbody) {
            return;
        }

        tbody.innerHTML = '';

        state.scenarios.forEach(scenario => {
            const row = document.createElement('tr');

            const scenarioCell = document.createElement('th');
            scenarioCell.scope = 'row';
            scenarioCell.textContent = scenario.name;
            row.appendChild(scenarioCell);

            const fedCell = document.createElement('td');
            fedCell.textContent = formatSigned(scenario.fedCut, 0, ' bps');
            row.appendChild(fedCell);

            const depositCell = document.createElement('td');
            depositCell.textContent = formatSigned(scenario.depositDelta, 0, ' bps');
            row.appendChild(depositCell);

            const lowCell = document.createElement('td');
            lowCell.textContent = formatSigned(scenario.nimLow, 0, ' bps');
            row.appendChild(lowCell);

            const highCell = document.createElement('td');
            highCell.textContent = formatSigned(scenario.nimHigh, 0, ' bps');
            row.appendChild(highCell);

            const midCell = document.createElement('td');
            midCell.textContent = scenario.midpointLabel;
            row.appendChild(midCell);

            const assumptionsCell = document.createElement('td');
            assumptionsCell.textContent = scenario.assumptions;
            row.appendChild(assumptionsCell);

            tbody.appendChild(row);
        });
    }

    function bindToggle(button, stateKey, announcementLabel) {
        if (!button) {
            return;
        }

        button.addEventListener('click', () => {
            const isPressed = button.getAttribute('aria-pressed') === 'true';
            const nextState = !isPressed;
            button.setAttribute('aria-pressed', nextState ? 'true' : 'false');
            state[stateKey] = nextState;
            announceToggle(`${announcementLabel} ${nextState ? 'shown' : 'hidden'}.`);

            if (state.chart) {
                state.chart.update('none');
            }
        });
    }

    function announceToggle(message) {
        const region = document.getElementById(SELECTORS.status);
        if (!region) {
            return;
        }
        region.textContent = message;
    }

    function bindExports() {
        const pngButton = document.getElementById(SELECTORS.exportPng);
        if (pngButton) {
            pngButton.addEventListener('click', exportPng);
        }

        const csvButton = document.getElementById(SELECTORS.exportCsv);
        if (csvButton) {
            csvButton.addEventListener('click', exportCsv);
        }
    }

    function exportPng() {
        if (!state.chart) {
            return;
        }

        const { chart } = state;
        const canvas = chart.canvas;
        const originalResponsive = chart.options.responsive;
        const originalAspect = chart.options.maintainAspectRatio;
        const originalWidth = canvas.width;
        const originalHeight = canvas.height;
        const originalStyleWidth = canvas.style.width;
        const originalStyleHeight = canvas.style.height;

        chart.options.responsive = false;
        chart.options.maintainAspectRatio = false;
        chart.resize(CONSTANTS.pngWidth, CONSTANTS.pngHeight);
        chart.update('none');

        const link = document.createElement('a');
        link.href = chart.toBase64Image('image/png', 1);
        link.download = 'nim_sensitivity_tornado.png';
        link.click();

        chart.options.responsive = originalResponsive;
        chart.options.maintainAspectRatio = originalAspect;
        chart.resize(originalWidth, originalHeight);
        canvas.style.width = originalStyleWidth;
        canvas.style.height = originalStyleHeight;
        chart.update('none');
    }

    function exportCsv() {
        if (!state.scenarios.length) {
            return;
        }

        const rows = [
            ['Scenario', 'Fed_Cut_bps', 'Deposit_Delta_bps', 'NIM_Low_bps', 'NIM_High_bps', 'Midpoint_bps', 'Assumptions']
        ];

        state.scenarios.forEach(scenario => {
            rows.push([
                scenario.name,
                scenario.fedCut,
                scenario.depositDelta,
                scenario.nimLow,
                scenario.nimHigh,
                Number(scenario.midpoint.toFixed(2)),
                scenario.assumptions
            ]);
        });

        const csvContent = rows.map(row => row.map(escapeCsvValue).join(',')).join('\n');
        downloadBlob(csvContent, 'text/csv;charset=utf-8;', 'nim_sensitivity_tornado.csv');
    }

    function escapeCsvValue(value) {
        const stringValue = String(value ?? '');
        if (/[",\n]/.test(stringValue)) {
            return `"${stringValue.replace(/"/g, '""')}"`;
        }
        return stringValue;
    }

    function downloadBlob(content, mimeType, filename) {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        link.click();
        URL.revokeObjectURL(url);
    }

    function observeThemeChanges() {
        const observer = new MutationObserver(mutations => {
            const themeChanged = mutations.some(
                mutation => mutation.type === 'attributes' && mutation.attributeName === 'data-theme'
            );

            if (themeChanged) {
                window.requestAnimationFrame(refreshChartTheme);
            }
        });

        observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    }

    async function loadData() {
        const response = await fetch(DATA_URL);
        if (!response.ok) {
            throw new Error(`Failed to load ${DATA_URL}: ${response.status}`);
        }

        const json = await response.json();
        const scenariosNode = json?.down_cycle?.scenarios;
        state.scenarios = buildScenarioObjects(scenariosNode);
    }

    async function init() {
        const canvas = document.getElementById(SELECTORS.canvas);
        if (!canvas) {
            return;
        }

        try {
            await loadData();
            buildChart();
            bindToggle(document.getElementById(SELECTORS.toggleRote), 'showRote', 'ROTE impact annotation');
            bindToggle(document.getElementById(SELECTORS.toggleValuation), 'showValuation', 'Valuation impact annotation');
            bindExports();
            populateTable();
            refreshChartTheme();
            observeThemeChanges();
        } catch (error) {
            console.error('Failed to initialise NIM sensitivity tornado', error);
        }
    }

    document.addEventListener('DOMContentLoaded', init);
    window.refreshNimSensitivityTheme = refreshChartTheme;
})();
