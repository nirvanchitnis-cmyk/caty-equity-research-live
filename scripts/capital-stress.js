/* global Chart */
(function() {
    'use strict';

    const DATA_URL = 'data/caty09_capital_liquidity.json';

    const SELECTORS = {
        canvas: 'capitalStressChart',
        toggleDetails: 'capitalToggleDetails',
        toggleWellCap: 'capitalToggleWellCap',
        toggleBuffer: 'capitalToggleBuffer',
        exportPng: 'capitalExportPng',
        exportCsv: 'capitalExportCsv',
        tableBody: 'capitalTableBody',
        bufferFootnote: 'capitalBufferFootnote',
        status: 'capitalToggleStatus'
    };

    const DATASET_IDS = {
        series: 'capitalStressSeries'
    };

    const CONSTANTS = {
        pngWidth: 1400,
        pngHeight: 700,
        axisStep: 2.5
    };

    const state = {
        chart: null,
        series: [],
        startValue: Number.NaN,
        endValue: Number.NaN,
        regMin: Number.NaN,
        wellCap: Number.NaN,
        bufferReg: Number.NaN,
        bufferWell: Number.NaN,
        statusText: '',
        note: '',
        axisMax: 15,
        showDetails: false,
        showWellCap: true,
        showBuffer: true
    };

    const referenceLinesPlugin = {
        id: 'capitalStressReferenceLines',
        afterDatasetsDraw(chart) {
            const { ctx, chartArea, scales } = chart;
            const xScale = scales.x;
            if (!xScale) {
                return;
            }

            drawReferenceLine({
                ctx,
                chartArea,
                xScale,
                value: state.regMin,
                color: getCssVar('--capital-reg-min') || '#8C1E33',
                width: 2,
                label: () => `Reg Min ${formatPercent(state.regMin, 1)}`,
                dash: []
            });

            if (state.showWellCap) {
                drawReferenceLine({
                    ctx,
                    chartArea,
                    xScale,
                    value: state.wellCap,
                    color: getCssVar('--capital-well-cap') || '#B85C00',
                    width: 1.5,
                    label: () => `Well-Cap ${formatPercent(state.wellCap, 1)}`,
                    dash: [6, 4],
                    labelOffset: 18
                });
            }
        }
    };

    const annotationsPlugin = {
        id: 'capitalStressAnnotations',
        afterDatasetsDraw(chart) {
            const datasetIndex = getDatasetIndex(DATASET_IDS.series, chart);
            if (datasetIndex === -1) {
                return;
            }

            const datasetMeta = chart.getDatasetMeta(datasetIndex);
            const { ctx, chartArea } = chart;

            state.series.forEach((item, index) => {
                const bar = datasetMeta.data?.[index];
                if (!bar) {
                    return;
                }

                const { x, y } = bar.getProps(['x', 'y'], true);
                const rightPadding = 8;
                const topBound = chartArea.top + 14;

                ctx.save();
                ctx.textAlign = 'right';
                ctx.textBaseline = 'bottom';

                let labelY = Math.max(y - 8, topBound);
                ctx.font = '700 13px "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
                ctx.fillStyle = getCssVar('--text-primary') || '#14202D';
                ctx.fillText(item.displayLabel, x - rightPadding, labelY);

                if (item.showAfterLabel) {
                    labelY = Math.max(labelY - 16, topBound);
                    ctx.font = '500 11px "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
                    ctx.fillStyle = getCssVar('--text-secondary') || '#4F5B67';
                    ctx.fillText(item.afterLabel, x - rightPadding, labelY);
                }

                if (state.showDetails && item.assumptions && item.category !== 'baseline' && item.category !== 'result') {
                    ctx.textBaseline = 'top';
                    const detailY = Math.min(y + 10, chartArea.bottom - 18);
                    ctx.font = '500 11px "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
                    ctx.fillStyle = getCssVar('--capital-annotation') || '#4F5B67';
                    ctx.fillText(item.assumptions, x - rightPadding, detailY);
                }

                ctx.restore();
            });
        }
    };

    const bufferPlugin = {
        id: 'capitalStressBufferAnnotation',
        afterDatasetsDraw(chart) {
            if (!state.showBuffer) {
                return;
            }

            const datasetIndex = getDatasetIndex(DATASET_IDS.series, chart);
            if (datasetIndex === -1) {
                return;
            }

            const endingIndex = state.series.findIndex(item => item.category === 'result');
            if (endingIndex === -1) {
                return;
            }

            const endingBar = chart.getDatasetMeta(datasetIndex).data?.[endingIndex];
            if (!endingBar) {
                return;
            }

            const { ctx, chartArea, scales } = chart;
            const xScale = scales.x;
            const finalValue = state.series[endingIndex]?.afterValue;
            if (!Number.isFinite(finalValue) || !xScale) {
                return;
            }

            const finalX = xScale.getPixelForValue(finalValue);
            const baseY = endingBar.getProps(['y'], true).y;
            const lines = buildBufferLines();
            if (!lines.length) {
                return;
            }

            ctx.save();
            ctx.textAlign = 'right';
            ctx.textBaseline = 'bottom';
            const lineHeight = 16;
            const startY = Math.max(baseY - 18, chartArea.top + 24);
            const totalHeight = (lines.length - 1) * lineHeight;
            let currentY = startY - totalHeight;

            lines.forEach(line => {
                ctx.font = line.font;
                ctx.fillStyle = line.color;
                ctx.fillText(line.text, finalX - 8, currentY);
                currentY += lineHeight;
            });

            ctx.restore();
        }
    };

    document.addEventListener('DOMContentLoaded', init);

    async function init() {
        try {
            const data = await loadData();
            prepareState(data);
            buildChart();
            populateTable();
            bindControls();
            bindExports();
            observeThemeChanges();
        } catch (error) {
            console.error('Capital stress waterfall failed to initialize:', error);
            announce('Capital stress data unavailable');
        }
    }

    async function loadData() {
        const response = await fetch(DATA_URL);
        if (!response.ok) {
            throw new Error(`Failed to load ${DATA_URL}: ${response.status}`);
        }
        return response.json();
    }

    function prepareState(data) {
        const stress = data?.capital_stress_waterfall;
        if (!stress) {
            throw new Error('capital_stress_waterfall not found in data source');
        }

        state.regMin = toNumber(
            data?.regulatory_capital_q3_2025?.regulatory_minimum_cet1_pct,
            toNumber(stress.regulatory_minimum_cet1_pct, 7.0)
        );
        state.wellCap = toNumber(
            data?.regulatory_capital_q3_2025?.well_capitalized_cet1_pct,
            6.5
        );

        state.startValue = roundTo(toNumber(stress.starting_cet1_pct), 2);
        state.endValue = roundTo(toNumber(stress.ending_cet1_pct), 2);
        state.bufferReg = roundTo(toNumber(stress.buffer_vs_regulatory_ppts), 2);
        state.bufferWell = roundTo(toNumber(stress.buffer_vs_well_capitalized_ppts), 2);
        state.statusText = stress.status || '';
        state.note = stress.note || '';

        if (!Number.isFinite(state.startValue)) {
            throw new Error('Invalid starting CET1 value');
        }

        const components = Array.isArray(stress.components) ? stress.components : [];
        state.series = [];

        state.series.push({
            id: 'starting',
            label: 'Starting CET1',
            baseValue: 0,
            value: state.startValue,
            afterValue: state.startValue,
            category: 'baseline',
            assumptions: 'Q3 2025 actual CET1 ratio',
            displayLabel: `Starting CET1 ${formatPercent(state.startValue, 2)}`,
            afterLabel: `${formatPercent(state.startValue, 2)} CET1`,
            showAfterLabel: false,
            impact: 0
        });

        let cumulativeBefore = state.startValue;
        components.forEach((component, index) => {
            const impact = roundTo(toNumber(component?.impact_ppts), 2);
            if (!Number.isFinite(impact)) {
                return;
            }

            const afterValue = roundTo(cumulativeBefore + impact, 2);
            const label = component?.label || `Component ${index + 1}`;
            const category = component?.category === 'mitigant' ? 'mitigant' : 'loss';

            state.series.push({
                id: `component-${index}`,
                label,
                baseValue: cumulativeBefore,
                value: impact,
                afterValue,
                category,
                assumptions: component?.assumptions || '',
                displayLabel: `${label} (${formatSignedPpts(impact)})`,
                afterLabel: `After: ${formatPercent(afterValue, 2)} CET1`,
                showAfterLabel: true,
                impact
            });

            cumulativeBefore = afterValue;
        });

        if (!Number.isFinite(state.endValue)) {
            state.endValue = cumulativeBefore;
        }

        state.series.push({
            id: 'ending',
            label: 'Stressed CET1',
            baseValue: 0,
            value: state.endValue,
            afterValue: state.endValue,
            category: 'result',
            assumptions: state.statusText,
            displayLabel: `Stressed CET1 ${formatPercent(state.endValue, 2)}`,
            afterLabel: `${formatPercent(state.endValue, 2)} CET1`,
            showAfterLabel: false,
            impact: 0
        });

        const maxValue = Math.max(
            state.regMin,
            state.wellCap,
            ...state.series.map(item => {
                const start = item.baseValue;
                const end = item.baseValue + item.value;
                return Math.max(start, end, item.afterValue);
            })
        );

        const paddedMax = Math.ceil((maxValue + 1) / CONSTANTS.axisStep) * CONSTANTS.axisStep;
        state.axisMax = Math.max(15, paddedMax);
    }

    function buildChart() {
        const canvas = document.getElementById(SELECTORS.canvas);
        if (!canvas || typeof Chart === 'undefined') {
            return;
        }

        const labels = state.series.map(item => item.label);
        const dataValues = state.series.map(item => item.value);
        const baseValues = state.series.map(item => item.baseValue);

        state.chart = new Chart(canvas, {
            type: 'bar',
            data: {
                labels,
                datasets: [
                    {
                        id: DATASET_IDS.series,
                        label: 'CET1 Waterfall',
                        data: dataValues,
                        base: baseValues,
                        backgroundColor(context) {
                            const item = state.series[context.dataIndex];
                            const baseColor = getBarColor(item);
                            const opacity = parseOpacity(getCssVar('--capital-bar-opacity'), 0.85);
                            return withOpacity(baseColor, opacity);
                        },
                        borderSkipped: false,
                        borderRadius(context) {
                            const item = state.series[context.dataIndex];
                            if (!item) {
                                return 8;
                            }
                            if (item.category === 'baseline') {
                                return {
                                    topLeft: 0,
                                    bottomLeft: 0,
                                    topRight: 10,
                                    bottomRight: 10
                                };
                            }
                            if (item.category === 'result') {
                                return 10;
                            }
                            return 8;
                        },
                        categoryPercentage: 0.7,
                        barPercentage: 0.8
                    }
                ]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                layout: {
                    padding: {
                        top: 64,
                        right: 36,
                        bottom: 28,
                        left: 32
                    }
                },
                scales: {
                    x: {
                        min: 0,
                        max: state.axisMax,
                        grid: {
                            color: withOpacity(getCssVar('--border-color') || '#D6DADD', 0.35),
                            borderDash: [4, 2]
                        },
                        ticks: {
                            stepSize: CONSTANTS.axisStep,
                            color: getCssVar('--text-secondary') || '#4F5B67',
                            font: {
                                family: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
                                size: 11
                            },
                            callback: value => `${formatNumber(value)}%`
                        },
                        title: {
                            display: true,
                            text: 'CET1 Capital Ratio (%)',
                            color: getCssVar('--text-secondary') || '#4F5B67',
                            font: {
                                family: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
                                weight: '600',
                                size: 13
                            }
                        }
                    },
                    y: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: getCssVar('--text-secondary') || '#4F5B67',
                            font: {
                                family: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
                                size: 12
                            }
                        }
                    }
                },
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
                                const item = state.series[context[0].dataIndex];
                                return item ? item.label : '';
                            },
                            label(context) {
                                const item = state.series[context.dataIndex];
                                if (!item) {
                                    return '';
                                }
                                if (item.category === 'baseline' || item.category === 'result') {
                                    return `CET1: ${formatPercent(item.afterValue, 2)}`;
                                }
                                return `Impact: ${formatSignedPpts(item.value)}`;
                            },
                            afterLabel(context) {
                                const item = state.series[context.dataIndex];
                                if (!item) {
                                    return [];
                                }

                                const lines = [];
                                if (item.category !== 'baseline') {
                                    lines.push(`After: ${formatPercent(item.afterValue, 2)} CET1`);
                                }
                                if (item.assumptions && item.category !== 'baseline' && item.category !== 'result') {
                                    lines.push('');
                                    lines.push('Assumptions:');
                                    lines.push(`• ${item.assumptions}`);
                                }

                                if (item.category === 'result') {
                                    if (Number.isFinite(state.bufferReg) && Number.isFinite(state.regMin)) {
                                        lines.push(`Buffer vs ${formatPercent(state.regMin, 1)}%: ${formatSignedPpts(state.bufferReg, 2)}`);
                                    }
                                    if (Number.isFinite(state.bufferWell) && Number.isFinite(state.wellCap)) {
                                        lines.push(`Buffer vs ${formatPercent(state.wellCap, 1)}%: ${formatSignedPpts(state.bufferWell, 2)}`);
                                    }
                                    if (state.statusText) {
                                        lines.push(`Status: ${state.statusText}`);
                                    }
                                }

                                return lines;
                            }
                        }
                    }
                }
            },
            plugins: [referenceLinesPlugin, annotationsPlugin, bufferPlugin]
        });
    }

    function populateTable() {
        const tbody = document.getElementById(SELECTORS.tableBody);
        if (!tbody) {
            return;
        }

        tbody.innerHTML = '';

        state.series.forEach(item => {
            if (item.category === 'result') {
                return;
            }

            const row = document.createElement('tr');

            if (item.category === 'baseline') {
                row.classList.add('base-case');
            }

            const nameCell = document.createElement('th');
            nameCell.scope = 'row';
            nameCell.textContent = item.label;
            row.appendChild(nameCell);

            const impactCell = document.createElement('td');
            if (item.category === 'baseline') {
                impactCell.textContent = '—';
            } else {
                impactCell.textContent = formatSignedPpts(item.impact);
                if (item.category === 'loss') {
                    impactCell.classList.add('text-danger');
                } else if (item.category === 'mitigant') {
                    impactCell.classList.add('text-success');
                }
            }
            row.appendChild(impactCell);

            const afterCell = document.createElement('td');
            afterCell.textContent = formatPercent(item.afterValue, 2);
            row.appendChild(afterCell);

            const categoryCell = document.createElement('td');
            categoryCell.textContent = formatCategory(item.category);
            row.appendChild(categoryCell);

            tbody.appendChild(row);
        });

        const ending = state.series.find(item => item.category === 'result');
        if (ending) {
            const row = document.createElement('tr');
            row.classList.add('base-case');

            const nameCell = document.createElement('th');
            nameCell.scope = 'row';
            nameCell.textContent = ending.label;
            row.appendChild(nameCell);

            const impactCell = document.createElement('td');
            impactCell.textContent = '—';
            row.appendChild(impactCell);

            const afterCell = document.createElement('td');
            afterCell.textContent = formatPercent(ending.afterValue, 2);
            row.appendChild(afterCell);

            const categoryCell = document.createElement('td');
            categoryCell.textContent = 'Result';
            row.appendChild(categoryCell);

            tbody.appendChild(row);
        }

        updateBufferFootnote();
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
            description: 'Stress assumptions'
        });

        bindToggle({
            buttonId: SELECTORS.toggleWellCap,
            stateKey: 'showWellCap',
            onToggle: () => {
                if (state.chart) {
                    state.chart.update('none');
                }
            },
            description: 'Well-capitalized threshold'
        });

        bindToggle({
            buttonId: SELECTORS.toggleBuffer,
            stateKey: 'showBuffer',
            onToggle: () => {
                updateBufferFootnote();
                if (state.chart) {
                    state.chart.update('none');
                }
            },
            description: 'Capital buffer metrics'
        });
    }

    function bindToggle({ buttonId, stateKey, onToggle, description }) {
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
            announce(`${description} ${next ? 'shown' : 'hidden'}`);
        });
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

        const chart = state.chart;
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
        link.download = 'capital_stress_waterfall.png';
        link.click();

        chart.options.responsive = originalResponsive;
        chart.options.maintainAspectRatio = originalAspect;
        chart.resize(originalWidth, originalHeight);
        canvas.style.width = originalStyleWidth;
        canvas.style.height = originalStyleHeight;
        chart.update('none');
    }

    function exportCsv() {
        if (!state.series.length) {
            return;
        }

        const rows = [
            ['Component', 'Impact_ppts', 'Cumulative_CET1_pct', 'Category', 'Assumptions']
        ];

        state.series.forEach(item => {
            if (item.category === 'result') {
                return;
            }

            rows.push([
                formatCsvIdentifier(item.label),
                item.category === 'baseline' ? '' : item.impact.toFixed(2),
                Number.isFinite(item.afterValue) ? item.afterValue.toFixed(2) : '',
                formatCategory(item.category),
                item.assumptions || ''
            ]);
        });

        const ending = state.series.find(item => item.category === 'result');
        if (ending) {
            rows.push([
                'Ending_Stressed_CET1',
                '',
                Number.isFinite(ending.afterValue) ? ending.afterValue.toFixed(2) : '',
                'Result',
                ending.assumptions || ''
            ]);
        }

        rows.push([]);
        rows.push(['# Metadata']);
        if (Number.isFinite(state.regMin)) {
            rows.push(['Regulatory_Minimum_pct', state.regMin.toFixed(1)]);
        }
        if (Number.isFinite(state.wellCap)) {
            rows.push(['Well_Capitalized_pct', state.wellCap.toFixed(1)]);
        }
        if (Number.isFinite(state.bufferReg)) {
            rows.push(['Buffer_vs_RegMin_ppts', state.bufferReg.toFixed(2)]);
        }
        if (Number.isFinite(state.bufferWell)) {
            rows.push(['Buffer_vs_WellCap_ppts', state.bufferWell.toFixed(2)]);
        }
        if (state.statusText) {
            rows.push(['Status', state.statusText]);
        }
        if (state.note) {
            rows.push(['Scenario_Note', state.note]);
        }

        const csvContent = rows.map(row => row.map(escapeCsvValue).join(',')).join('\n');
        downloadBlob(csvContent, 'text/csv;charset=utf-8;', 'capital_stress_waterfall.csv');
    }

    function updateBufferFootnote() {
        const footCell = document.getElementById(SELECTORS.bufferFootnote);
        if (!footCell) {
            return;
        }

        if (!state.showBuffer) {
            footCell.textContent = 'Buffer metrics hidden; toggle to show';
            return;
        }

        const parts = [];
        if (Number.isFinite(state.bufferReg) && Number.isFinite(state.regMin)) {
            parts.push(`${formatSignedPpts(state.bufferReg, 2)} vs ${formatPercent(state.regMin, 1)}% regulatory minimum`);
        }
        if (Number.isFinite(state.bufferWell) && Number.isFinite(state.wellCap)) {
            parts.push(`${formatSignedPpts(state.bufferWell, 2)} vs ${formatPercent(state.wellCap, 1)}% well-capitalized`);
        }
        if (state.statusText) {
            parts.push(state.statusText);
        }
        if (state.note) {
            parts.push(state.note);
        }

        footCell.textContent = parts.length ? parts.join(' • ') : 'Buffer metrics unavailable';
    }

    function buildBufferLines() {
        const lines = [];
        if (Number.isFinite(state.bufferReg) && Number.isFinite(state.regMin)) {
            const positive = state.bufferReg >= 0;
            lines.push({
                text: `${formatSignedPpts(state.bufferReg, 2)} above ${formatPercent(state.regMin, 1)}% reg min`,
                color: (positive ? getCssVar('--success') : getCssVar('--danger')) || (positive ? '#2E6F3E' : '#8C1E33'),
                font: '700 13px "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
            });
        }
        if (Number.isFinite(state.bufferWell) && Number.isFinite(state.wellCap)) {
            const positive = state.bufferWell >= 0;
            lines.push({
                text: `${formatSignedPpts(state.bufferWell, 2)} above ${formatPercent(state.wellCap, 1)}% well-cap`,
                color: (positive ? getCssVar('--success') : getCssVar('--danger')) || (positive ? '#2E6F3E' : '#8C1E33'),
                font: '500 12px "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
            });
        }
        if (state.statusText) {
            lines.push({
                text: state.statusText,
                color: getCssVar('--text-primary') || '#14202D',
                font: '500 12px "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
            });
        }
        return lines;
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

    function getBarColor(item) {
        if (!item) {
            return getCssVar('--info') || '#2F6690';
        }
        switch (item.category) {
            case 'baseline':
                return getCssVar('--capital-base') || '#2E6F3E';
            case 'mitigant':
                return getCssVar('--capital-mitigant') || '#2E6F3E';
            case 'loss':
                return getCssVar('--capital-loss') || '#8C1E33';
            case 'result':
                return getCssVar('--capital-stressed') || '#8B7355';
            default:
                return getCssVar('--info') || '#2F6690';
        }
    }

    function drawReferenceLine({ ctx, chartArea, xScale, value, color, width, label, dash = [], labelOffset = 0 }) {
        if (!Number.isFinite(value)) {
            return;
        }

        const pixelX = xScale.getPixelForValue(value);
        if (pixelX < chartArea.left || pixelX > chartArea.right) {
            return;
        }

        ctx.save();
        ctx.beginPath();
        ctx.setLineDash(dash);
        ctx.lineWidth = width;
        ctx.strokeStyle = color;
        ctx.moveTo(pixelX, chartArea.top);
        ctx.lineTo(pixelX, chartArea.bottom);
        ctx.stroke();
        ctx.setLineDash([]);

        const labelText = typeof label === 'function' ? label() : label;
        if (labelText) {
            ctx.font = '700 12px "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
            ctx.fillStyle = color;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'bottom';
            ctx.fillText(labelText, pixelX, chartArea.top - 8 - labelOffset);
        }

        ctx.restore();
    }

    function getDatasetIndex(id, chartInstance = state.chart) {
        if (!chartInstance) {
            return -1;
        }
        return chartInstance.data.datasets.findIndex(dataset => dataset.id === id);
    }

    function formatPercent(value, decimals = 1) {
        if (!Number.isFinite(value)) {
            return '—';
        }
        return `${value.toFixed(decimals)}%`;
    }

    function formatNumber(value) {
        if (!Number.isFinite(value)) {
            return '';
        }
        return Number.isInteger(value) ? value.toFixed(0) : value.toFixed(1);
    }

    function formatSignedPpts(value, decimals = 1) {
        if (!Number.isFinite(value)) {
            return '—';
        }
        const abs = Math.abs(value).toFixed(decimals);
        return `${value >= 0 ? '+' : '-'}${abs} ppts`;
    }

    function formatCategory(category) {
        if (typeof category !== 'string') {
            return '';
        }
        if (category === 'baseline') {
            return 'Baseline';
        }
        if (category === 'result') {
            return 'Result';
        }
        return category.charAt(0).toUpperCase() + category.slice(1);
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

    function formatCsvIdentifier(label) {
        return String(label || '')
            .trim()
            .replace(/[^A-Za-z0-9]+/g, '_')
            .replace(/^_+|_+$/g, '') || 'Component';
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

    function getCssVar(name) {
        return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    }

    function announce(message) {
        const status = document.getElementById(SELECTORS.status);
        if (!status) {
            return;
        }
        status.textContent = message;
    }
})();
