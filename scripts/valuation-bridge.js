/* global Chart */
(function() {
    'use strict';

    const DATA_URL = 'data/valuation_outputs.json';

    const SELECTORS = {
        canvas: 'valuationBridgeChart',
        toggleDetails: 'bridgeToggleDetails',
        toggleTotal: 'bridgeToggleTotal',
        toggleOthers: 'bridgeToggleOthers',
        exportPng: 'bridgeExportPng',
        exportCsv: 'bridgeExportCsv',
        tableBody: 'bridgeTableBody',
        tableTotalTarget: 'bridgeTotalTargetCell',
        tableTotalDelta: 'bridgeTotalDeltaCell',
        status: 'bridgeToggleStatus'
    };

    const DATASET_IDS = {
        components: 'valuationBridgeComponents',
        total: 'valuationBridgeTotal'
    };

    const COMPONENT_ORDER = ['rim', 'ddm', 'regression'];

    const COMPONENT_META = {
        rim: {
            name: 'RIM',
            method: 'Residual Income Model',
            colorVar: '--bridge-rim',
            fallbackColor: '#2F6690'
        },
        ddm: {
            name: 'DDM',
            method: 'Dividend Discount Model',
            colorVar: '--bridge-ddm',
            fallbackColor: '#2E6F3E'
        },
        regression: {
            name: 'Regression',
            method: 'P/TBV vs ROTE Regression',
            colorVar: '--bridge-regression',
            fallbackColor: '#B85C00'
        }
    };

    const OTHER_FRAMEWORK_LINES = [
        {
            id: 'normalized',
            extract: data => toNumber(data?.methods?.normalized?.target_price),
            colorVar: '--bridge-other-normalized',
            fallbackColor: '#8C1E33',
            label: value => `Normalized $${value.toFixed(2)}`,
            dash: [6, 4]
        },
        {
            id: 'probability_weighted',
            extract: data => toNumber(data?.frameworks?.probability_weighted?.target_price),
            colorVar: '--bridge-other-probability',
            fallbackColor: '#6A3FA0',
            label: value => `Probability-Weighted $${value.toFixed(2)}`,
            dash: [4, 3]
        },
        {
            id: 'wilson_95',
            extract: data => toNumber(data?.frameworks?.wilson_95?.target_price),
            colorVar: '--bridge-other-wilson',
            fallbackColor: '#2F6690',
            label: value => `Wilson 95% $${value.toFixed(2)}`,
            dash: [2, 3]
        }
    ];

    const CONSTANTS = {
        pngWidth: 1400,
        pngHeight: 700,
        axisMax: 60
    };

    const state = {
        chart: null,
        components: [],
        componentsById: {},
        otherFrameworks: [],
        tooltipContext: {},
        totalTarget: Number.NaN,
        spotPrice: Number.NaN,
        returnPct: Number.NaN,
        coePct: Number.NaN,
        growthPct: Number.NaN,
        showDetails: false,
        showTotal: true,
        showOthers: false
    };

    const referenceLinesPlugin = {
        id: 'valuationBridgeReferenceLines',
        afterDatasetsDraw(chart) {
            const { ctx, chartArea, scales } = chart;
            const xScale = scales.x;
            if (!xScale || !Number.isFinite(state.spotPrice)) {
                return;
            }

            drawReferenceLine({
                ctx,
                chartArea,
                xScale,
                value: state.spotPrice,
                color: getCssVar('--bridge-spot') || '#14202D',
                label: `Spot $${state.spotPrice.toFixed(2)}`,
                dash: []
            });

            if (!state.showOthers || !state.otherFrameworks.length) {
                return;
            }

            state.otherFrameworks.forEach((frameworkLine, index) => {
                drawReferenceLine({
                    ctx,
                    chartArea,
                    xScale,
                    value: frameworkLine.value,
                    color: getCssVar(frameworkLine.colorVar) || frameworkLine.fallbackColor,
                    label: frameworkLine.label,
                    dash: frameworkLine.dash,
                    labelOffset: (index + 1) * 18
                });
            });
        }
    };

    const annotationPlugin = {
        id: 'valuationBridgeAnnotations',
        afterDatasetsDraw(chart) {
            if (!state.components.length) {
                return;
            }

            const componentsIndex = getDatasetIndex(DATASET_IDS.components);
            if (componentsIndex === -1) {
                return;
            }

            const componentsMeta = chart.getDatasetMeta(componentsIndex);
            const { ctx, chartArea } = chart;

            ctx.save();
            ctx.textAlign = 'right';
            ctx.textBaseline = 'bottom';

            state.components.forEach((component, index) => {
                const bar = componentsMeta.data[index];
                if (!bar) {
                    return;
                }

                const { x, y } = bar.getProps(['x', 'y'], true);
                const labelY = Math.max(y - 12, chartArea.top + 12);

                ctx.font = '700 13px "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
                ctx.fillStyle = getCssVar('--text-primary') || '#14202D';
                ctx.fillText(component.barLabel, x, labelY);

                if (state.showDetails) {
                    ctx.font = '500 11px "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
                    ctx.fillStyle = getCssVar('--bridge-annotation') || '#4F5B67';
                    const detailY = Math.max(labelY - 18, chartArea.top + 10);
                    ctx.fillText(component.detailLabel, x, detailY);
                }
            });

            if (state.showTotal) {
                const totalIndex = getDatasetIndex(DATASET_IDS.total);
                if (totalIndex > -1) {
                    const totalMeta = chart.getDatasetMeta(totalIndex);
                    const totalBar = totalMeta.data.find(Boolean);
                    if (totalBar) {
                        const { x, y } = totalBar.getProps(['x', 'y'], true);
                        const topLine = Math.max(y - 20, chartArea.top + 12);

                        ctx.font = '700 13px "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
                        ctx.fillStyle = getCssVar('--bridge-total') || '#8B7355';
                        ctx.fillText(`IRC Blended $${state.totalTarget.toFixed(2)}`, x, topLine);

                        ctx.font = '700 14px "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
                        const delta = state.totalTarget - state.spotPrice;
                        const deltaLabel = `${formatSignedCurrency(delta)} vs Spot (${formatSignedPercent(state.returnPct)} ${state.returnPct >= 0 ? 'upside' : 'downside'})`;
                        ctx.fillStyle = delta >= 0
                            ? (getCssVar('--success') || '#2E6F3E')
                            : (getCssVar('--danger') || '#8C1E33');
                        ctx.fillText(deltaLabel, x, Math.max(topLine - 22, chartArea.top + 12));
                    }
                }
            }

            ctx.restore();
        }
    };

    function drawReferenceLine({ ctx, chartArea, xScale, value, color, label, dash, labelOffset = 0 }) {
        if (!Number.isFinite(value)) {
            return;
        }

        const pixelX = xScale.getPixelForValue(value);
        if (!Number.isFinite(pixelX)) {
            return;
        }

        ctx.save();
        ctx.beginPath();
        ctx.setLineDash(dash || []);
        ctx.lineWidth = dash?.length ? 1.5 : 2;
        ctx.strokeStyle = color;
        ctx.moveTo(pixelX, chartArea.top);
        ctx.lineTo(pixelX, chartArea.bottom);
        ctx.stroke();
        ctx.setLineDash([]);

        ctx.font = '700 12px "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
        ctx.fillStyle = color;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'bottom';
        ctx.fillText(label, pixelX, chartArea.top - 8 - labelOffset);
        ctx.restore();
    }

    function buildChart() {
        const canvas = document.getElementById(SELECTORS.canvas);
        if (!canvas || typeof Chart === 'undefined') {
            return;
        }

        const componentValues = state.components.map(component => component.contribution);
        const componentBases = state.components.map(component => roundTo(component.cumulative - component.contribution, 2));
        const labels = [
            ...state.components.map(component => `${component.name} (${component.weightLabel})`),
            'IRC Blended Total'
        ];

        const chartConfig = {
            type: 'bar',
            data: {
                labels,
                datasets: [
                    {
                        id: DATASET_IDS.components,
                        label: 'IRC Bridge Components',
                        data: [...componentValues, null],
                        base: [...componentBases, null],
                        backgroundColor(context) {
                            return withOpacity(
                                getCssVar(state.components[context.dataIndex]?.colorVar) ||
                                    state.components[context.dataIndex]?.fallbackColor ||
                                    '#2F6690',
                                parseOpacity(getCssVar('--bridge-bar-opacity'), 0.85)
                            );
                        },
                        borderSkipped: false,
                        borderRadius(context) {
                            if (context.dataIndex >= state.components.length) {
                                return 0;
                            }
                            return {
                                topLeft: 0,
                                bottomLeft: 0,
                                topRight: 8,
                                bottomRight: 8
                            };
                        },
                        categoryPercentage: 0.8,
                        barPercentage: 0.9
                    },
                    {
                        id: DATASET_IDS.total,
                        label: 'IRC Blended Total',
                        data: [null, null, null, state.totalTarget],
                        base: [null, null, null, 0],
                        backgroundColor() {
                            return withOpacity(
                                getCssVar('--bridge-total') || '#8B7355',
                                Math.min(1, parseOpacity(getCssVar('--bridge-bar-opacity'), 0.85) + 0.05)
                            );
                        },
                        borderSkipped: false,
                        borderRadius: 10,
                        categoryPercentage: 0.8,
                        barPercentage: 0.6,
                        hidden: !state.showTotal
                    }
                ]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                layout: {
                    padding: {
                        top: 52,
                        right: 32,
                        bottom: 24,
                        left: 20
                    }
                },
                scales: {
                    x: {
                        min: 0,
                        max: CONSTANTS.axisMax,
                        grid: {
                            color: withOpacity(getCssVar('--border-color') || '#D6DADD', 0.35),
                            borderDash: [4, 2]
                        },
                        ticks: {
                            callback: value => `$${Number(value).toFixed(0)}`,
                            color: getCssVar('--text-secondary') || '#4F5B67',
                            font: {
                                family: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
                                size: 11
                            }
                        },
                        title: {
                            display: true,
                            text: 'Target Price ($)',
                            color: getCssVar('--text-secondary') || '#4F5B67',
                            font: {
                                family: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
                                weight: 600,
                                size: 13
                            }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: getCssVar('--text-secondary') || '#4F5B67',
                            font: {
                                family: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
                                size: 12
                            },
                            callback(value, index) {
                                if (index === state.components.length) {
                                    return 'IRC Blended Total';
                                }
                                return this.getLabelForValue(value);
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        usePointStyle: true,
                        backgroundColor: withOpacity('#14202D', 0.92),
                        padding: 12,
                        callbacks: {
                            title(context) {
                                const { dataset, dataIndex } = context[0];
                                if (dataset.id === DATASET_IDS.components) {
                                    const component = state.components[dataIndex];
                                    return component ? `${component.name} (${component.weightLabel})` : '';
                                }
                                if (dataset.id === DATASET_IDS.total) {
                                    return 'IRC Blended Target Price';
                                }
                                return '';
                            },
                            label(context) {
                                if (context.dataset.id === DATASET_IDS.components) {
                                    return getComponentTooltipLines(context.dataIndex);
                                }
                                if (context.dataset.id === DATASET_IDS.total) {
                                    return getTotalTooltipLines();
                                }
                                return '';
                            }
                        }
                    }
                }
            },
            plugins: [referenceLinesPlugin, annotationPlugin]
        };

        state.chart = new Chart(canvas.getContext('2d'), chartConfig);
    }

    function getComponentTooltipLines(index) {
        const component = state.components[index];
        if (!component) {
            return [];
        }

        const lines = [
            `Framework Target: ${formatCurrency(component.target)}`,
            `Weight: ${formatPercent(component.weight * 100, 1)}%`,
            `Contribution: ${formatCurrency(component.contribution)}`
        ];

        lines.push('');
        lines.push(`Method: ${component.method}`);

        const additional = getComponentAdditionalLines(component.id);
        if (additional.length) {
            lines.push('Key Inputs:');
            lines.push(...additional);
        }

        return lines;
    }

    function getComponentAdditionalLines(componentId) {
        const { normalizedInputs = {}, regression = {}, assumptions = {} } = state.tooltipContext;

        if (componentId === 'rim') {
            const rote = toNumber(normalizedInputs.rote);
            const coe = toNumber(normalizedInputs.coe);
            const growth = toNumber(normalizedInputs.g);
            return [
                `• ROTE: ${Number.isFinite(rote) ? `${rote.toFixed(2)}%` : 'n/a'}`,
                `• COE: ${Number.isFinite(coe) ? `${(coe * 100).toFixed(2)}%` : 'n/a'}`,
                `• Growth: ${Number.isFinite(growth) ? `${(growth * 100).toFixed(2)}%` : 'n/a'}`
            ];
        }

        if (componentId === 'ddm') {
            const payout = toNumber(assumptions.dividend_payout_pct);
            const growth = toNumber(assumptions.growth_rate_pct);
            return [
                `• Payout Ratio: ${Number.isFinite(payout) ? `${payout.toFixed(1)}%` : 'n/a'}`,
                `• Growth: ${Number.isFinite(growth) ? `${growth.toFixed(1)}%` : 'n/a'}`
            ];
        }

        if (componentId === 'regression') {
            const equation = typeof regression.equation === 'string'
                ? regression.equation
                : 'P/TBV = 0.058 × ROTE + 0.82';
            const rSquared = toNumber(regression.r_squared);
            const peerCount = Array.isArray(regression?.inputs?.peer_sample)
                ? regression.inputs.peer_sample.length
                : Number.NaN;
            return [
                `• Equation: ${equation}`,
                `• R^2: ${Number.isFinite(rSquared) ? `${(rSquared * 100).toFixed(0)}%` : 'n/a'}`,
                `• Sample: ${Number.isFinite(peerCount) ? `${peerCount} peers` : 'n/a'}`
            ];
        }

        return [];
    }

    function getTotalTooltipLines() {
        const lines = [
            `Target Price: ${formatCurrency(state.totalTarget)}`,
            `Spot Price: ${formatCurrency(state.spotPrice)}`,
            `${formatSignedCurrency(state.totalTarget - state.spotPrice)} (${formatSignedPercent(state.returnPct)} vs spot)`
        ];

        lines.push('');
        lines.push('Composition:');
        state.components.forEach(component => {
            lines.push(`• ${component.weightLabel} ${component.name}: ${formatCurrency(component.contribution)}`);
        });
        lines.push(`Total: ${formatCurrency(state.totalTarget)}`);
        return lines;
    }

    function bindControls() {
        bindToggle({
            buttonId: SELECTORS.toggleDetails,
            stateKey: 'showDetails',
            onToggle: () => {
                if (state.chart) {
                    state.chart.update('none');
                }
            },
            label: 'Component calculation details'
        });

        bindToggle({
            buttonId: SELECTORS.toggleTotal,
            stateKey: 'showTotal',
            onToggle: updateTotalVisibility,
            label: 'IRC blended total bar'
        });

        bindToggle({
            buttonId: SELECTORS.toggleOthers,
            stateKey: 'showOthers',
            onToggle: () => {
                if (state.chart) {
                    state.chart.update('none');
                }
            },
            label: 'Alternative framework lines'
        });

        updateTotalVisibility(state.showTotal);
    }

    function bindToggle({ buttonId, stateKey, onToggle, label }) {
        const button = document.getElementById(buttonId);
        if (!button) {
            return;
        }

        button.addEventListener('click', () => {
            const next = button.getAttribute('aria-pressed') !== 'true';
            button.setAttribute('aria-pressed', next ? 'true' : 'false');
            state[stateKey] = next;
            if (typeof onToggle === 'function') {
                onToggle(next);
            }
            announce(`${label} ${next ? 'shown' : 'hidden'}`);
        });
    }

    function updateTotalVisibility(visible) {
        const index = getDatasetIndex(DATASET_IDS.total);
        if (state.chart && index > -1) {
            state.chart.data.datasets[index].hidden = !visible;
        }
        state.showTotal = visible;
        updateTableFooter();
        if (state.chart) {
            state.chart.update('none');
        }
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

        const image = chart.toBase64Image('image/png', 1);
        const link = document.createElement('a');
        link.href = image;
        link.download = 'valuation_bridge.png';
        link.click();

        chart.options.responsive = originalResponsive;
        chart.options.maintainAspectRatio = originalAspect;
        chart.resize(originalWidth, originalHeight);
        canvas.style.width = originalStyleWidth;
        canvas.style.height = originalStyleHeight;
        chart.update('none');
    }

    function exportCsv() {
        if (!state.components.length) {
            return;
        }

        const rows = [
            ['Component', 'Framework_Target', 'Weight_Pct', 'Contribution_Dollar', 'Cumulative_Dollar', 'Method']
        ];

        state.components.forEach(component => {
            rows.push([
                component.name,
                component.target.toFixed(2),
                (component.weight * 100).toFixed(1),
                component.contribution.toFixed(2),
                component.cumulative.toFixed(2),
                component.method
            ]);
        });

        rows.push([
            'IRC_Blended',
            state.totalTarget.toFixed(2),
            '100.0',
            state.totalTarget.toFixed(2),
            state.totalTarget.toFixed(2),
            'Weighted Composite'
        ]);

        rows.push([]);
        rows.push(['# Metadata']);
        rows.push(['Spot_Price', state.spotPrice.toFixed(2)]);
        rows.push(['IRC_Target', state.totalTarget.toFixed(2)]);
        rows.push(['Upside_Dollar', (state.totalTarget - state.spotPrice).toFixed(2)]);
        rows.push(['Upside_Pct', state.returnPct.toFixed(1)]);
        if (Number.isFinite(state.coePct)) {
            rows.push(['COE_pct', state.coePct.toFixed(3)]);
        }
        if (Number.isFinite(state.growthPct)) {
            rows.push(['Growth_pct', state.growthPct.toFixed(1)]);
        }

        const csvContent = rows.map(row => row.map(escapeCsvValue).join(',')).join('\n');
        downloadBlob(csvContent, 'text/csv;charset=utf-8;', 'valuation_bridge.csv');
    }

    function populateTable() {
        const tbody = document.getElementById(SELECTORS.tableBody);
        if (!tbody) {
            return;
        }

        tbody.innerHTML = '';
        state.components.forEach(component => {
            const row = document.createElement('tr');

            const nameCell = document.createElement('th');
            nameCell.scope = 'row';
            nameCell.textContent = component.tableLabel;
            row.appendChild(nameCell);

            const targetCell = document.createElement('td');
            targetCell.textContent = formatCurrency(component.target);
            row.appendChild(targetCell);

            const weightCell = document.createElement('td');
            weightCell.textContent = `${(component.weight * 100).toFixed(1)}%`;
            row.appendChild(weightCell);

            const contributionCell = document.createElement('td');
            contributionCell.textContent = formatCurrency(component.contribution);
            row.appendChild(contributionCell);

            const cumulativeCell = document.createElement('td');
            cumulativeCell.textContent = formatCurrency(component.cumulative);
            row.appendChild(cumulativeCell);

            tbody.appendChild(row);
        });

        updateTableFooter();
    }

    function updateTableFooter() {
        const targetCell = document.getElementById(SELECTORS.tableTotalTarget);
        const deltaCell = document.getElementById(SELECTORS.tableTotalDelta);
        if (!targetCell || !deltaCell) {
            return;
        }

        const targetText = Number.isFinite(state.totalTarget) ? formatCurrency(state.totalTarget) : '—';
        targetCell.textContent = state.showTotal ? targetText : `${targetText} (hidden on chart)`;

        if (Number.isFinite(state.totalTarget) && Number.isFinite(state.spotPrice)) {
            const delta = state.totalTarget - state.spotPrice;
            deltaCell.textContent = `${formatSignedCurrency(delta)} vs Spot (${formatSignedPercent(state.returnPct)} ${state.returnPct >= 0 ? 'upside' : 'downside'})`;
        } else {
            deltaCell.textContent = '—';
        }
    }

    function announce(message) {
        const status = document.getElementById(SELECTORS.status);
        if (!status) {
            return;
        }
        status.textContent = message;
    }

    function getDatasetIndex(id, chartInstance = state.chart) {
        if (!chartInstance) {
            return -1;
        }
        return chartInstance.data.datasets.findIndex(dataset => dataset.id === id);
    }

    function parseOpacity(value, fallback) {
        const numeric = Number.parseFloat(value);
        if (Number.isFinite(numeric)) {
            return Math.min(1, Math.max(0, numeric));
        }
        return fallback;
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

    function formatCurrency(value) {
        if (!Number.isFinite(value)) {
            return '—';
        }
        const abs = Math.abs(value).toFixed(2);
        return `${value < 0 ? '-$' : '$'}${abs}`;
    }

    function formatSignedCurrency(value) {
        if (!Number.isFinite(value)) {
            return '—';
        }
        const abs = Math.abs(value).toFixed(2);
        return `${value >= 0 ? '+' : '-'}$${abs}`;
    }

    function formatPercent(value, decimals = 1) {
        if (!Number.isFinite(value)) {
            return '—';
        }
        return value.toFixed(decimals);
    }

    function formatSignedPercent(value, decimals = 1) {
        if (!Number.isFinite(value)) {
            return '—';
        }
        const abs = Math.abs(value).toFixed(decimals);
        return `${value >= 0 ? '+' : '-'}${abs}%`;
    }

    function formatWeight(weight) {
        if (!Number.isFinite(weight)) {
            return '';
        }
        return `${Math.round(weight * 100)}%`;
    }

    function roundTo(value, decimals = 2) {
        if (!Number.isFinite(value)) {
            return Number.NaN;
        }
        const factor = 10 ** decimals;
        return Math.round((value + Number.EPSILON) * factor) / factor;
    }

    function toNumber(value, fallback = Number.NaN) {
        const num = Number(value);
        return Number.isFinite(num) ? num : fallback;
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

    function refreshChartTheme() {
        if (!state.chart) {
            return;
        }

        const xScale = state.chart.options.scales.x;
        const yScale = state.chart.options.scales.y;

        xScale.grid.color = withOpacity(getCssVar('--border-color') || '#D6DADD', 0.35);
        xScale.ticks.color = getCssVar('--text-secondary') || '#4F5B67';
        xScale.title.color = getCssVar('--text-secondary') || '#4F5B67';
        yScale.ticks.color = getCssVar('--text-secondary') || '#4F5B67';

        state.chart.update('none');
    }

    function getCssVar(name) {
        return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    }

    async function loadData() {
        const response = await fetch(DATA_URL);
        if (!response.ok) {
            throw new Error(`Failed to load ${DATA_URL}: ${response.status}`);
        }

        const json = await response.json();
        const bridge = json?.frameworks?.irc_blended || json?.methods?.irc_blended;
        if (!bridge) {
            throw new Error('IRC blended framework not found in valuation outputs');
        }

        state.totalTarget = toNumber(bridge.target_price);
        state.returnPct = toNumber(bridge.return_pct);
        state.spotPrice = toNumber(json?.metadata?.price_used);
        state.coePct = toNumber(json?.assumptions?.cost_of_equity_pct);
        state.growthPct = toNumber(json?.assumptions?.growth_rate_pct);

        const weights = bridge.weights || {};
        const inputs = bridge.inputs || {};

        state.components = COMPONENT_ORDER.map(id => {
            const meta = COMPONENT_META[id];
            const weight = toNumber(weights[id]);
            const target = toNumber(inputs[`${id}_target`]);

            if (!meta || !Number.isFinite(weight) || !Number.isFinite(target)) {
                return null;
            }

            return {
                id,
                name: meta.name,
                method: meta.method,
                colorVar: meta.colorVar,
                fallbackColor: meta.fallbackColor,
                weight,
                target
            };
        }).filter(Boolean);

        state.components.forEach(component => {
            component.contribution = component.weight * component.target;
        });

        state.components.forEach(component => {
            component.contribution = roundTo(component.contribution, 2);
        });

        const contributionSum = state.components.reduce((sum, component) => sum + component.contribution, 0);
        const diff = roundTo(state.totalTarget - contributionSum, 2);
        if (state.components.length && Math.abs(diff) >= 0.01) {
            const lastComponent = state.components[state.components.length - 1];
            lastComponent.contribution = roundTo(lastComponent.contribution + diff, 2);
        }

        let running = 0;
        state.components.forEach(component => {
            running += component.contribution;
            component.cumulative = roundTo(running, 2);
            component.weightLabel = formatWeight(component.weight);
            component.barLabel = `${component.weightLabel} ${component.name} (${formatCurrency(component.contribution)})`;
            component.detailLabel = `${formatCurrency(component.target)} × ${component.weightLabel}`;
            component.tableLabel = `${component.name} (${component.weightLabel})`;
        });

        state.componentsById = Object.fromEntries(state.components.map(component => [component.id, component]));

        state.tooltipContext = {
            normalizedInputs: json?.methods?.normalized?.inputs || {},
            regression: json?.methods?.regression || {},
            assumptions: json?.assumptions || {}
        };

        state.otherFrameworks = OTHER_FRAMEWORK_LINES.map(config => {
            const value = config.extract(json);
            if (!Number.isFinite(value)) {
                return null;
            }
            const rounded = roundTo(value, 2);
            return {
                id: config.id,
                value: rounded,
                colorVar: config.colorVar,
                fallbackColor: config.fallbackColor,
                label: config.label(rounded),
                dash: config.dash
            };
        }).filter(Boolean);
    }

    async function init() {
        const canvas = document.getElementById(SELECTORS.canvas);
        if (!canvas) {
            return;
        }

        try {
            await loadData();
            if (!state.components.length || !Number.isFinite(state.totalTarget)) {
                return;
            }
            buildChart();
            bindControls();
            bindExports();
            populateTable();
            refreshChartTheme();
            observeThemeChanges();
        } catch (error) {
            console.error('Failed to initialise valuation bridge chart', error);
        }
    }

    document.addEventListener('DOMContentLoaded', init);
    window.refreshValuationBridgeTheme = refreshChartTheme;
})();
