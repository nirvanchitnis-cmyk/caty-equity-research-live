/* global Chart */
(function() {
    'use strict';

    const DATA_URL = 'data/caty12_calculated_tables.json';

    const SELECTORS = {
        canvas: 'scenarioWaterfallChart',
        toggleBaseline: 'scenarioToggleBaseline',
        toggleProvision: 'scenarioToggleProvision',
        toggleDetails: 'scenarioToggleDetails',
        exportPng: 'scenarioExportPng',
        exportCsv: 'scenarioExportCsv',
        tableBody: 'scenarioTableBody',
        status: 'scenarioToggleStatus'
    };

    const DATASET_IDS = {
        baseline: 'scenarioBaselineDataset',
        normalized: 'scenarioNormalizedDataset'
    };

    const CONSTANTS = {
        pngWidth: 1200,
        pngHeight: 800,
        spotPrice: 46.17
    };

    const SCENARIO_CONFIG = {
        bull: { label: 'Bull', heading: 'Bull Case', colorVar: '--scenario-bull' },
        base: { label: 'Base', heading: 'Base Case', colorVar: '--scenario-base' },
        bear: { label: 'Bear', heading: 'Bear Case', colorVar: '--scenario-bear' }
    };

    const SCENARIO_ORDER = ['bull', 'base', 'bear'];

    const state = {
        chart: null,
        scenarios: [],
        baselineValue: 0,
        ltmRote: 0,
        ltmNco: 0,
        throughCycleNco: 0,
        averageTce: 0,
        showBaseline: true,
        showProvision: false,
        showDetails: true
    };

    const root = document.documentElement;
    let cachedStyles = null;
    let cachedToken = '';

    function getThemeToken() {
        const theme = root ? root.getAttribute('data-theme') || 'light' : 'light';
        const motion = root ? root.getAttribute('data-reduces-motion') || 'false' : 'false';
        return `${theme}|${motion}`;
    }

    function getRootStyles() {
        if (!root) {
            return null;
        }
        const token = getThemeToken();
        if (!cachedStyles || cachedToken !== token) {
            cachedStyles = getComputedStyle(root);
            cachedToken = token;
        }
        return cachedStyles;
    }

    const baselinePlugin = {
        id: 'scenarioBaselineGuide',
        afterDatasetsDraw(chart) {
            if (!state.showBaseline || !Number.isFinite(state.baselineValue)) {
                return;
            }

            const { ctx, chartArea, scales } = chart;
            const yScale = scales.y;
            if (!yScale) {
                return;
            }

            const baselineY = yScale.getPixelForValue(state.baselineValue);
            if (!Number.isFinite(baselineY)) {
                return;
            }

            ctx.save();
            ctx.beginPath();
            ctx.setLineDash([6, 4]);
            ctx.lineWidth = 1.5;
            ctx.strokeStyle = getCssVar('--scenario-reference') || 'rgba(122, 136, 147, 0.6)';
            ctx.moveTo(chartArea.left, baselineY);
            ctx.lineTo(chartArea.right, baselineY);
            ctx.stroke();
            ctx.setLineDash([]);

            ctx.font = '600 11px "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
            ctx.fillStyle = getCssVar('--text-secondary') || '#4F5B67';
            ctx.textAlign = 'right';
            ctx.textBaseline = 'bottom';
            ctx.fillText(`LTM $${state.baselineValue.toFixed(1)}M`, chartArea.right - 8, baselineY - 6);
            ctx.restore();
        }
    };

    const annotationPlugin = {
        id: 'scenarioAnnotations',
        afterDatasetsDraw(chart) {
            if (!state.scenarios.length) {
                return;
            }

            const normalizedIndex = getDatasetIndex(DATASET_IDS.normalized, chart);
            if (normalizedIndex === -1) {
                return;
            }

            const baselineIndex = getDatasetIndex(DATASET_IDS.baseline, chart);
            const normalizedMeta = chart.getDatasetMeta(normalizedIndex);
            const baselineMeta = baselineIndex > -1 ? chart.getDatasetMeta(baselineIndex) : null;
            const { ctx, chartArea, scales } = chart;
            const yScale = scales.y;

            ctx.save();
            ctx.textAlign = 'center';

            state.scenarios.forEach((scenario, index) => {
                const bar = normalizedMeta.data[index];
                if (!bar || typeof bar.x !== 'number' || typeof bar.y !== 'number') {
                    return;
                }

                const color = getCssVar(scenario.colorVar) || '#2E6F3E';
                const targetLabel = scenario.targetLabel;
                const roteLabel = scenario.roteLabel;
                const ptbvLabel = scenario.ptbvLabel;

                const targetY = Math.max(bar.y - 14, chartArea.top + 16);
                const roteY = Math.max(targetY - 20, chartArea.top + 16);
                const ptbvY = Math.max(roteY - 16, chartArea.top + 16);

                ctx.textBaseline = 'bottom';
                ctx.font = '700 16px "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
                ctx.fillStyle = color;
                ctx.fillText(targetLabel, bar.x, targetY);

                ctx.font = '600 12px "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
                ctx.fillStyle = getCssVar('--text-primary') || '#14202D';
                ctx.fillText(roteLabel, bar.x, roteY);

                if (state.showDetails) {
                    ctx.font = '400 11px "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
                    ctx.fillStyle = getCssVar('--text-secondary') || '#4F5B67';
                    ctx.fillText(ptbvLabel, bar.x, ptbvY);
                }

                if (state.showProvision && yScale) {
                    const baselineY = yScale.getPixelForValue(state.baselineValue);
                    const baselineElement = baselineMeta?.data?.[index];
                    const baselineX = baselineElement && typeof baselineElement.x === 'number'
                        ? baselineElement.x
                        : bar.x - (bar.width || 24);
                    const midX = Number.isFinite(baselineX) ? (baselineX + bar.x) / 2 : bar.x;
                    const normalizedY = bar.y;
                    const midY = Number.isFinite(baselineY)
                        ? (baselineY + normalizedY) / 2
                        : normalizedY + (chartArea.bottom - normalizedY) * 0.25;

                    ctx.font = '600 11px "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
                    ctx.fillStyle = getCssVar('--scenario-annotation') || '#4F5B67';
                    ctx.textBaseline = 'middle';
                    ctx.fillText(scenario.netDeltaLabel, midX, midY);
                }
            });

            ctx.restore();
        }
    };

    function getCssVar(name) {
        const styles = getRootStyles();
        if (!styles) {
            return '';
        }
        return styles.getPropertyValue(name).trim();
    }

    function toNumber(value, fallback = 0) {
        const num = Number(value);
        return Number.isFinite(num) ? num : fallback;
    }

    function stripHtml(value) {
        if (typeof value !== 'string') {
            return '';
        }
        const div = document.createElement('div');
        div.innerHTML = value;
        return div.textContent || div.innerText || '';
    }

    function formatMillions(value, { includePlus = false } = {}) {
        if (!Number.isFinite(value)) {
            return 'n/a';
        }
        const sign = value < 0 ? '-' : (includePlus && value > 0 ? '+' : '');
        return `${sign}$${Math.abs(value).toFixed(1)}M`;
    }

    function formatPercent(value, decimals = 2) {
        if (!Number.isFinite(value)) {
            return 'n/a';
        }
        return `${value.toFixed(decimals)}%`;
    }

    function formatRatio(value, decimals = 3) {
        if (!Number.isFinite(value)) {
            return 'n/a';
        }
        return `${value.toFixed(decimals)}× P/TBV`;
    }

    function formatBps(value) {
        if (!Number.isFinite(value)) {
            return 'n/a';
        }
        const rounded = Number(value.toFixed(1));
        return `${Number.isInteger(rounded) ? rounded.toFixed(0) : rounded.toFixed(1)} bps`;
    }

    function formatDeltaBps(value) {
        if (!Number.isFinite(value)) {
            return 'n/a vs LTM';
        }
        const delta = Math.round(value * 100);
        if (delta === 0) {
            return '→0 bps vs LTM';
        }
        const arrow = delta > 0 ? '↑' : '↓';
        return `${arrow}${Math.abs(delta)} bps vs LTM`;
    }

    function withOpacity(color, opacity) {
        if (!color) {
            return `rgba(122, 136, 147, ${opacity})`;
        }

        const trimmed = color.trim();
        if (trimmed.startsWith('#')) {
            const hex = trimmed.substring(1);
            const isShort = hex.length === 3;
            const r = Number.parseInt(isShort ? hex[0] + hex[0] : hex.substring(0, 2), 16);
            const g = Number.parseInt(isShort ? hex[1] + hex[1] : hex.substring(2, 4), 16);
            const b = Number.parseInt(isShort ? hex[2] + hex[2] : hex.substring(4, 6), 16);

            if ([r, g, b].some(value => Number.isNaN(value))) {
                return `rgba(122, 136, 147, ${opacity})`;
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

        return `rgba(122, 136, 147, ${opacity})`;
    }

    function getScenarioKey(text) {
        const cleaned = stripHtml(text).toUpperCase();
        if (cleaned.includes('BULL')) {
            return 'bull';
        }
        if (cleaned.includes('BASE')) {
            return 'base';
        }
        if (cleaned.includes('BEAR')) {
            return 'bear';
        }
        return null;
    }

    function buildScenarioObjects(rawScenarios) {
        if (!Array.isArray(rawScenarios)) {
            return [];
        }

        const mapped = rawScenarios
            .map(entry => {
                const key = getScenarioKey(entry?.scenario_text);
                if (!key || !SCENARIO_CONFIG[key]) {
                    return null;
                }

                const config = SCENARIO_CONFIG[key];
                const normalizedNetIncome = toNumber(entry?.normalized_net_income_m);
                const targetPrice = toNumber(entry?.target_price, NaN);
                const rotePct = toNumber(entry?.rote_pct);
                const ncoBps = toNumber(entry?.nco_bps);
                const deltaProvision = toNumber(entry?.delta_provision_m);
                const taxEffect = toNumber(entry?.tax_effect_m);

                return {
                    key,
                    label: config.label,
                    heading: config.heading,
                    colorVar: config.colorVar,
                    ncoBps,
                    deltaProvision,
                    taxEffect,
                    normalizedNetIncome,
                    rotePct,
                    ptbv: toNumber(entry?.ptbv_multiple),
                    targetPrice: Number.isFinite(targetPrice) ? targetPrice : null
                };
            })
            .filter(Boolean);

        mapped.sort((a, b) => SCENARIO_ORDER.indexOf(a.key) - SCENARIO_ORDER.indexOf(b.key));
        return mapped;
    }

    function enrichScenarioData() {
        state.scenarios = state.scenarios.map(scenario => {
            const netDelta = scenario.normalizedNetIncome - state.baselineValue;
            const targetLabel = Number.isFinite(scenario.targetPrice)
                ? `$${scenario.targetPrice.toFixed(2)}`
                : 'Target n/a';

            return {
                ...scenario,
                netIncomeDelta: netDelta,
                netDeltaLabel: `ΔNI: ${formatMillions(netDelta, { includePlus: true })}`,
                roteLabel: `${formatPercent(scenario.rotePct)} (${formatDeltaBps(scenario.rotePct - state.ltmRote)})`,
                ptbvLabel: formatRatio(scenario.ptbv),
                targetLabel,
                tooltipName: `${scenario.heading} Normalized Earnings`,
                deltaVsSpot: Number.isFinite(scenario.targetPrice)
                    ? scenario.targetPrice - CONSTANTS.spotPrice
                    : null
            };
        });
    }

    function getDatasetIndex(id, chartInstance = state.chart) {
        if (!chartInstance) {
            return -1;
        }
        return chartInstance.data.datasets.findIndex(dataset => dataset.id === id);
    }

    function getDatasetColors() {
        const opacity = toNumber(getCssVar('--scenario-bar-opacity'), 0.85) || 0.85;
        const baselineColor = withOpacity(getCssVar('--scenario-ltm') || '#7A8893', opacity);
        const scenarioColors = state.scenarios.map(
            scenario => withOpacity(getCssVar(scenario.colorVar) || '#2E6F3E', opacity)
        );

        return { baselineColor, scenarioColors };
    }

    function buildChart() {
        const canvas = document.getElementById(SELECTORS.canvas);
        if (!canvas || typeof Chart === 'undefined') {
            return;
        }

        const labels = state.scenarios.map(scenario => [
            `${scenario.label}`,
            `(${formatBps(scenario.ncoBps)} NCO)`
        ]);
        const { baselineColor, scenarioColors } = getDatasetColors();

        state.chart = new Chart(canvas, {
            type: 'bar',
            data: {
                labels,
                datasets: [
                    {
                        id: DATASET_IDS.baseline,
                        label: 'LTM Net Income',
                        data: state.scenarios.map(() => state.baselineValue),
                        backgroundColor: baselineColor,
                        borderRadius: 12,
                        barPercentage: 0.55,
                        categoryPercentage: 0.6
                    },
                    {
                        id: DATASET_IDS.normalized,
                        label: 'Normalized Net Income',
                        data: state.scenarios.map(scenario => scenario.normalizedNetIncome),
                        backgroundColor: scenarioColors,
                        borderRadius: 12,
                        barPercentage: 0.55,
                        categoryPercentage: 0.6
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                layout: {
                    padding: {
                        top: 28,
                        right: 32,
                        bottom: 24,
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
                                return scenario ? scenario.tooltipName : '';
                            },
                            label(context) {
                                const scenario = state.scenarios[context.dataIndex];
                                if (!scenario) {
                                    return '';
                                }

                                if (context.dataset.id === DATASET_IDS.baseline) {
                                    return `$${state.baselineValue.toFixed(1)}M net income`;
                                }

                                return `$${scenario.normalizedNetIncome.toFixed(1)}M net income`;
                            },
                            afterLabel(context) {
                                const scenario = state.scenarios[context.dataIndex];
                                if (!scenario) {
                                    return [];
                                }

                                if (context.dataset.id === DATASET_IDS.baseline) {
                                    return [
                                        `ROTE: ${formatPercent(state.ltmRote)}`,
                                        `NCO: ${formatBps(state.ltmNco)}`
                                    ];
                                }

                                const deltaProvision = formatMillions(scenario.deltaProvision, { includePlus: true });
                                const taxEffect = formatMillions(scenario.taxEffect, { includePlus: true });
                                const deltaVsSpot = Number.isFinite(scenario.deltaVsSpot)
                                    ? `${scenario.deltaVsSpot > 0 ? '+' : ''}${scenario.deltaVsSpot.toFixed(2)} vs Spot`
                                    : 'n/a vs Spot';

                                return [
                                    `${formatPercent(scenario.rotePct, 2)} (${formatDeltaBps(scenario.rotePct - state.ltmRote)})`,
                                    'Credit Assumption:',
                                    `• NCO: ${formatBps(scenario.ncoBps)}`,
                                    `• Δ Provision: ${deltaProvision}`,
                                    `• After-tax impact: ${taxEffect}`,
                                    'Valuation:',
                                    `• ${formatRatio(scenario.ptbv)}`,
                                    `• Target Price: ${scenario.targetLabel} (${deltaVsSpot})`
                                ];
                            }
                        }
                    }
                },
                scales: {
                    x: {
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
                    },
                    y: {
                        min: 0,
                        max: 320,
                        border: {
                            color: getCssVar('--border-color') || '#D6DADD'
                        },
                        grid: {
                            color: `${getCssVar('--border-color') || '#D6DADD'}40`,
                            lineWidth: 1
                        },
                        ticks: {
                            color: getCssVar('--text-secondary') || '#4F5B67',
                            stepSize: 50,
                            callback(value) {
                                return `$${value}M`;
                            }
                        },
                        title: {
                            display: true,
                            text: 'Net Income ($ millions)',
                            color: getCssVar('--text-primary') || '#14202D',
                            font: {
                                weight: 'bold'
                            }
                        }
                    }
                }
            },
            plugins: [baselinePlugin, annotationPlugin]
        });
    }

    function refreshChartTheme() {
        if (!state.chart) {
            return;
        }

        const { data, options } = state.chart;
        const { baselineColor, scenarioColors } = getDatasetColors();

        const baselineIndex = getDatasetIndex(DATASET_IDS.baseline);
        if (baselineIndex > -1 && data.datasets[baselineIndex]) {
            data.datasets[baselineIndex].backgroundColor = baselineColor;
        }

        const normalizedIndex = getDatasetIndex(DATASET_IDS.normalized);
        if (normalizedIndex > -1 && data.datasets[normalizedIndex]) {
            data.datasets[normalizedIndex].backgroundColor = scenarioColors;
        }

        if (options.scales?.x) {
            options.scales.x.border.color = getCssVar('--border-color') || '#D6DADD';
            options.scales.x.ticks.color = getCssVar('--text-primary') || '#14202D';
        }

        if (options.scales?.y) {
            options.scales.y.border.color = getCssVar('--border-color') || '#D6DADD';
            options.scales.y.grid.color = `${getCssVar('--border-color') || '#D6DADD'}40`;
            options.scales.y.ticks.color = getCssVar('--text-secondary') || '#4F5B67';
            options.scales.y.title.color = getCssVar('--text-primary') || '#14202D';
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
            scenarioCell.textContent = scenario.label;
            row.appendChild(scenarioCell);

            const ncoCell = document.createElement('td');
            ncoCell.textContent = formatBps(scenario.ncoBps);
            row.appendChild(ncoCell);

            const ltmCell = document.createElement('td');
            ltmCell.textContent = formatMillions(state.baselineValue);
            row.appendChild(ltmCell);

            const deltaProvisionCell = document.createElement('td');
            deltaProvisionCell.textContent = formatMillions(scenario.deltaProvision, { includePlus: true });
            row.appendChild(deltaProvisionCell);

            const normalizedCell = document.createElement('td');
            normalizedCell.textContent = formatMillions(scenario.normalizedNetIncome);
            row.appendChild(normalizedCell);

            const roteCell = document.createElement('td');
            roteCell.textContent = formatPercent(scenario.rotePct);
            row.appendChild(roteCell);

            const targetCell = document.createElement('td');
            targetCell.textContent = Number.isFinite(scenario.targetPrice)
                ? `$${scenario.targetPrice.toFixed(2)}`
                : 'n/a';
            row.appendChild(targetCell);

            tbody.appendChild(row);
        });
    }

    function announce(message) {
        const status = document.getElementById(SELECTORS.status);
        if (!status) {
            return;
        }
        status.textContent = message;
    }

    function bindToggle({ buttonId, stateKey, onToggle, label }) {
        const button = document.getElementById(buttonId);
        if (!button) {
            return;
        }

        button.addEventListener('click', () => {
            const current = button.getAttribute('aria-pressed') === 'true';
            const next = !current;
            button.setAttribute('aria-pressed', next ? 'true' : 'false');
            state[stateKey] = next;
            if (typeof onToggle === 'function') {
                onToggle(next);
            }
            announce(`${label} ${next ? 'shown' : 'hidden'}`);
        });
    }

    function updateBaselineVisibility(visible) {
        if (!state.chart) {
            return;
        }
        const index = getDatasetIndex(DATASET_IDS.baseline);
        if (index === -1) {
            return;
        }
        state.chart.data.datasets[index].hidden = !visible;
        state.showBaseline = visible;
        state.chart.update('none');
    }

    function updateProvisionVisibility() {
        if (state.chart) {
            state.chart.update('none');
        }
    }

    function updateDetailsVisibility() {
        if (state.chart) {
            state.chart.update('none');
        }
    }

    function bindControls() {
        bindToggle({
            buttonId: SELECTORS.toggleBaseline,
            stateKey: 'showBaseline',
            onToggle: updateBaselineVisibility,
            label: 'LTM baseline'
        });

        bindToggle({
            buttonId: SELECTORS.toggleProvision,
            stateKey: 'showProvision',
            onToggle: updateProvisionVisibility,
            label: 'Provision impact'
        });

        bindToggle({
            buttonId: SELECTORS.toggleDetails,
            stateKey: 'showDetails',
            onToggle: updateDetailsVisibility,
            label: 'Valuation details'
        });

        // Ensure initial visibility state is respected
        updateBaselineVisibility(state.showBaseline);
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
        const { width: originalWidth, height: originalHeight } = canvas;
        const originalStyleWidth = canvas.style.width;
        const originalStyleHeight = canvas.style.height;

        chart.options.responsive = false;
        chart.options.maintainAspectRatio = false;
        chart.resize(CONSTANTS.pngWidth, CONSTANTS.pngHeight);
        chart.update('none');

        const link = document.createElement('a');
        link.href = chart.toBase64Image('image/png', 1);
        link.download = 'scenario_waterfall.png';
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
            ['Scenario', 'NCO_bps', 'LTM_NI_M', 'Delta_Provision_M', 'Tax_Effect_M', 'Normalized_NI_M', 'Normalized_ROTE_pct', 'P_TBV', 'Target_Price', 'Delta_vs_Spot']
        ];

        state.scenarios.forEach(scenario => {
            rows.push([
                scenario.label,
                Number.isFinite(scenario.ncoBps) ? scenario.ncoBps : '',
                Number.isFinite(state.baselineValue) ? Number(state.baselineValue.toFixed(1)) : '',
                Number.isFinite(scenario.deltaProvision) ? Number(scenario.deltaProvision.toFixed(1)) : '',
                Number.isFinite(scenario.taxEffect) ? Number(scenario.taxEffect.toFixed(1)) : '',
                Number.isFinite(scenario.normalizedNetIncome) ? Number(scenario.normalizedNetIncome.toFixed(1)) : '',
                Number.isFinite(scenario.rotePct) ? Number(scenario.rotePct.toFixed(2)) : '',
                Number.isFinite(scenario.ptbv) ? Number(scenario.ptbv.toFixed(3)) : '',
                Number.isFinite(scenario.targetPrice) ? Number(scenario.targetPrice.toFixed(2)) : '',
                Number.isFinite(scenario.deltaVsSpot) ? Number(scenario.deltaVsSpot.toFixed(2)) : ''
            ]);
        });

        rows.push([]);
        rows.push(['# Metadata']);
        rows.push(['LTM_NCO_bps', Number(state.ltmNco.toFixed(1))]);
        rows.push(['Through_Cycle_NCO_bps', Number(state.throughCycleNco.toFixed(1))]);
        rows.push(['Spot_Price', CONSTANTS.spotPrice.toFixed(2)]);
        rows.push(['LTM_ROTE_pct', Number(state.ltmRote.toFixed(2))]);
        rows.push(['Average_TCE_M', Number(state.averageTce.toFixed(1))]);

        const csvContent = rows.map(row => row.map(escapeCsvValue).join(',')).join('\n');
        downloadBlob(csvContent, 'text/csv;charset=utf-8;', 'scenario_waterfall.csv');
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
        state.baselineValue = toNumber(json?.normalization_inputs?.ltm_net_income_m);
        state.ltmRote = toNumber(json?.normalization_inputs?.ltm_rote_pct);
        state.ltmNco = toNumber(json?.normalization_inputs?.ltm_nco_bps);
        state.throughCycleNco = toNumber(json?.nco_sensitivity?.base_case_nco_bps);
        state.averageTce = toNumber(json?.normalization_inputs?.average_tce_m);

        state.scenarios = buildScenarioObjects(json?.nco_sensitivity?.scenarios);
        enrichScenarioData();
    }

    async function init() {
        const canvas = document.getElementById(SELECTORS.canvas);
        if (!canvas) {
            return;
        }

        try {
            await loadData();
            if (!state.scenarios.length) {
                return;
            }
            buildChart();
            bindControls();
            bindExports();
            populateTable();
            refreshChartTheme();
            observeThemeChanges();
        } catch (error) {
            console.error('Failed to initialise scenario waterfall chart', error);
        }
    }

    document.addEventListener('DOMContentLoaded', init);
    window.refreshScenarioWaterfallTheme = refreshChartTheme;
})();
