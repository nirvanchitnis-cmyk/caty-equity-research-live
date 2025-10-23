/* global Chart */
(function() {
    'use strict';

    const CREDIT_DATA_URL = 'data/caty07_credit_quality.json';
    const FDIC_HISTORY_URL = 'data/fdic_nco_history.json';
    const QUARTERS_TO_PLOT = ['2024-Q3', '2024-Q4', '2025-Q1', '2025-Q2'];

    const DATASET_IDS = {
        annual: 'annual',
        quarterly: 'quarterly',
        throughCycle: 'throughCycle',
        normalized: 'normalized',
        current: 'current'
    };

    const SELECTORS = {
        canvasId: 'ncoTimeSeriesChart',
        toggleQuarterly: 'ncoToggleQuarterly',
        toggleThroughCycle: 'ncoToggleThroughCycle',
        toggleNormalized: 'ncoToggleNormalized',
        toggleCurrent: 'ncoToggleCurrent',
        exportPng: 'ncoExportPng',
        exportCsv: 'ncoExportCsv',
        tableBody: 'ncoDataTableBody',
        currentPosition: 'ncoCurrentPosition',
        toggleStatus: 'ncoToggleStatus'
    };

    const CATEGORY_COLOR_VARS = {
        gfc: '--nco-bar-gfc',
        elevated: '--nco-bar-elevated',
        normalized: '--nco-bar-normalized',
        benign: '--nco-bar-benign',
        recovery: '--nco-bar-recovery'
    };

    const CATEGORY_LABELS = {
        gfc: 'Stress (>100 bps)',
        elevated: 'Elevated (40-100 bps)',
        normalized: 'Normalized (20-40 bps)',
        benign: 'Benign (0-20 bps)',
        recovery: 'Net recoveries (<0 bps)',
        default: 'Observed'
    };

    const state = {
        chart: null,
        annualData: [],
        quarterlyData: [],
        labels: [],
        references: {
            throughCycle: null,
            normalized: null,
            current: null,
            gfcPeak: null
        },
        indexMaps: {
            annual: new Map(),
            quarterly: new Map()
        },
        normalizedBand: {
            lower: 20,
            upper: 45
        },
        axisBounds: {
            min: 0,
            max: 250
        },
        gfcIndex: -1,
        recoveryIndices: []
    };

    function getCssVar(varName) {
        return getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
    }

    function toNumber(value, fallback = null) {
        const num = Number(value);
        return Number.isFinite(num) ? num : fallback;
    }

    function formatNumber(value, decimals = 1) {
        if (!Number.isFinite(value)) {
            return 'n/a';
        }
        return value.toFixed(decimals);
    }

    function formatBps(value, decimals = 1) {
        if (!Number.isFinite(value)) {
            return 'n/a';
        }
        return `${value.toFixed(decimals)} bps`;
    }

    function categorizeValue(value) {
        if (!Number.isFinite(value)) {
            return { category: 'normalized', label: CATEGORY_LABELS.default };
        }

        if (value < 0) {
            return { category: 'recovery', label: CATEGORY_LABELS.recovery };
        }

        if (value < 20) {
            return { category: 'benign', label: CATEGORY_LABELS.benign };
        }

        if (value < 40) {
            return { category: 'normalized', label: CATEGORY_LABELS.normalized };
        }

        if (value < 100) {
            return { category: 'elevated', label: CATEGORY_LABELS.elevated };
        }

        return { category: 'gfc', label: CATEGORY_LABELS.gfc };
    }

    function getColorForCategory(category) {
        const cssVar = CATEGORY_COLOR_VARS[category] || CATEGORY_COLOR_VARS.normalized;
        const color = getCssVar(cssVar);
        return color || '#7A8893';
    }

    function parseAnnualHistory(historyHtml) {
        if (!historyHtml) {
            return [];
        }

        const parser = new DOMParser();
        const doc = parser.parseFromString(`<table>${historyHtml}</table>`, 'text/html');
        const rows = Array.from(doc.querySelectorAll('tr'));
        const data = [];

        rows.forEach(row => {
            const cells = row.querySelectorAll('td');
            if (cells.length < 2) {
                return;
            }

            const period = cells[0].textContent.trim();
            if (!/^\d{4}$/.test(period)) {
                return;
            }

            const valueText = cells[1].textContent.replace(/[^0-9.\-]/g, '');
            const value = Number.parseFloat(valueText);
            if (!Number.isFinite(value)) {
                return;
            }

            const context = cells[2] ? cells[2].textContent.trim() : '';
            const { category, label } = categorizeValue(value);

            data.push({
                period,
                value,
                context,
                category,
                categoryLabel: label,
                emphasize: ['2009', '2010', '2011', '2024'].includes(period),
                isGfcPeak: period === '2009'
            });
        });

        return data;
    }

    function buildQuarterlySeries(fdicHistory) {
        const rawSeries = Array.isArray(fdicHistory.raw_data) ? fdicHistory.raw_data : [];
        const lookup = new Map(
            rawSeries.map(item => [item.date, toNumber(item.nco_bps)])
        );

        const series = [];

        QUARTERS_TO_PLOT.forEach(period => {
            const value = lookup.get(period);
            if (!Number.isFinite(value)) {
                console.warn(`NCO quarterly value missing for ${period}`);
                return;
            }

            const { category, label } = categorizeValue(value);
            series.push({
                period,
                value,
                category,
                categoryLabel: label,
                context: 'Quarterly annualized net charge-off rate'
            });
        });

        return series;
    }

    async function loadData() {
        const [creditResponse, fdicResponse] = await Promise.all([
            fetch(CREDIT_DATA_URL),
            fetch(FDIC_HISTORY_URL)
        ]);

        if (!creditResponse.ok) {
            throw new Error(`Failed to load ${CREDIT_DATA_URL} (${creditResponse.status})`);
        }

        if (!fdicResponse.ok) {
            throw new Error(`Failed to load ${FDIC_HISTORY_URL} (${fdicResponse.status})`);
        }

        const creditData = await creditResponse.json();
        const fdicHistory = await fdicResponse.json();

        state.references.throughCycle = toNumber(
            creditData?.through_cycle_nco?.guardrail_mean_bps,
            toNumber(creditData?.snapshot_metrics?.stress_guardrail_nco_bps, 42.8)
        );
        state.references.normalized = toNumber(
            creditData?.through_cycle_nco?.prob90_post2014_bps,
            toNumber(creditData?.snapshot_metrics?.through_cycle_nco_bps, 30.0)
        );
        state.references.current = toNumber(
            creditData?.snapshot_metrics?.nco_rate_ltm_bps,
            toNumber(creditData?.snapshot_metrics?.nco_rate_qtd_bps, 18.1)
        );
        state.references.gfcPeak = toNumber(
            creditData?.through_cycle_nco?.gfc_peak_bps,
            234.4
        );

        state.annualData = parseAnnualHistory(creditData?.through_cycle_nco?.history_rows_html);
        if (!state.annualData.length) {
            throw new Error('Annual NCO history not available in credit quality dataset.');
        }

        state.quarterlyData = buildQuarterlySeries(fdicHistory);
        state.gfcIndex = state.annualData.findIndex(item => item.isGfcPeak);
        state.recoveryIndices = state.annualData.reduce((accumulator, item, index) => {
            if (['2017', '2018', '2019'].includes(item.period)) {
                accumulator.push(index);
            }
            return accumulator;
        }, []);
    }

    function buildDatasets() {
        state.labels = [];
        state.indexMaps.annual.clear();
        state.indexMaps.quarterly.clear();

        state.annualData.forEach(item => {
            state.labels.push(item.period);
        });
        state.quarterlyData.forEach(item => {
            state.labels.push(item.period);
        });

        const totalLength = state.labels.length;
        const annualDataPoints = new Array(totalLength).fill(null);
        const annualBackground = new Array(totalLength).fill('transparent');
        const annualBorder = new Array(totalLength).fill('transparent');

        state.annualData.forEach((item, index) => {
            const color = getColorForCategory(item.category);
            annualDataPoints[index] = item.value;
            annualBackground[index] = color;
            annualBorder[index] = color;
            state.indexMaps.annual.set(index, item);
        });

        const quarterlyPoints = new Array(totalLength).fill(null);
        state.quarterlyData.forEach((item, offset) => {
            const index = state.annualData.length + offset;
            quarterlyPoints[index] = item.value;
            state.indexMaps.quarterly.set(index, item);
        });

        const referenceValues = [
            state.references.throughCycle,
            state.references.normalized,
            state.references.current,
            state.references.gfcPeak
        ].filter(Number.isFinite);

        const valueSet = [
            ...state.annualData.map(item => item.value),
            ...state.quarterlyData.map(item => item.value)
        ].filter(Number.isFinite);

        const minValue = valueSet.length ? Math.min(0, ...valueSet) : 0;
        const maxValue = [...valueSet, ...referenceValues].reduce(
            (accumulator, value) => Math.max(accumulator, value),
            0
        );

        state.axisBounds = {
            min: minValue < 0 ? Math.floor((minValue - 5) / 5) * 5 : 0,
            max: Math.max(250, Math.ceil((maxValue + 5) / 5) * 5)
        };

        const datasets = [
            {
                id: DATASET_IDS.annual,
                label: 'Annual NCO (bars)',
                type: 'bar',
                order: 1,
                data: annualDataPoints,
                backgroundColor: annualBackground,
                borderColor: annualBorder,
                borderWidth: 1.5,
                borderRadius: 6,
                maxBarThickness: 28,
                hoverBackgroundColor: annualBackground
            },
            {
                id: DATASET_IDS.quarterly,
                label: 'Quarterly trend (line)',
                type: 'line',
                order: 5,
                data: quarterlyPoints,
                borderColor: getCssVar('--nco-quarterly-line') || '#14202D',
                backgroundColor: getCssVar('--nco-quarterly-line') || '#14202D',
                pointBackgroundColor: getCssVar('--nco-quarterly-line') || '#14202D',
                pointBorderColor: getCssVar('--bg-secondary') || '#FFFFFF',
                pointBorderWidth: 2,
                pointRadius: 4,
                pointHoverRadius: 6,
                spanGaps: false,
                fill: false,
                tension: 0.25
            }
        ];

        const throughCycleDataset = createReferenceDataset(
            DATASET_IDS.throughCycle,
            `Through-cycle mean (${formatNumber(state.references.throughCycle)} bps)`,
            state.references.throughCycle,
            { colorVar: '--nco-ref-mean', borderDash: [6, 4], borderWidth: 2, order: 2 }
        );

        const normalizedDataset = createReferenceDataset(
            DATASET_IDS.normalized,
            `Post-2014 90th percentile (${formatNumber(state.references.normalized)} bps)`,
            state.references.normalized,
            { colorVar: '--nco-ref-normalized', borderDash: [4, 6], borderWidth: 1.5, order: 3 }
        );

        const currentDataset = createReferenceDataset(
            DATASET_IDS.current,
            `Current (Q3 2025: ${formatNumber(state.references.current)} bps)`,
            state.references.current,
            { colorVar: '--nco-ref-current', borderDash: [], borderWidth: 2.5, order: 4 }
        );

        if (throughCycleDataset) {
            datasets.push(throughCycleDataset);
        }
        if (normalizedDataset) {
            datasets.push(normalizedDataset);
        }
        if (currentDataset) {
            datasets.push(currentDataset);
        }

        return datasets;
    }

    function createReferenceDataset(id, label, value, options = {}) {
        if (!Number.isFinite(value)) {
            return null;
        }

        const color = getCssVar(options.colorVar || '--nco-ref-mean') || '#7A8893';

        return {
            id,
            label,
            type: 'line',
            order: options.order ?? 3,
            data: state.labels.map(() => value),
            borderColor: color,
            backgroundColor: color,
            borderWidth: options.borderWidth ?? 2,
            borderDash: options.borderDash ?? [],
            pointRadius: 0,
            pointHoverRadius: 0,
            fill: false
        };
    }

    function getDatasetIndex(id) {
        if (!state.chart) {
            return -1;
        }
        return state.chart.data.datasets.findIndex(dataset => dataset.id === id);
    }

    const normalizedBandPlugin = {
        id: 'ncoNormalizedBand',
        beforeDatasetsDraw(chart) {
            const { lower, upper } = state.normalizedBand;
            if (!Number.isFinite(lower) || !Number.isFinite(upper)) {
                return;
            }

            const { ctx, chartArea, scales } = chart;
            if (!chartArea || !scales?.y) {
                return;
            }

            const bandTop = scales.y.getPixelForValue(upper);
            const bandBottom = scales.y.getPixelForValue(lower);

            ctx.save();
            ctx.fillStyle = getCssVar('--nco-band-fill') || 'rgba(122, 136, 147, 0.18)';
            ctx.fillRect(
                chartArea.left,
                Math.min(bandTop, bandBottom),
                chartArea.right - chartArea.left,
                Math.abs(bandBottom - bandTop)
            );
            ctx.restore();
        }
    };

    const dataLabelPlugin = {
        id: 'ncoDataLabels',
        afterDatasetsDraw(chart) {
            const ctx = chart.ctx;
            const annualDatasetIndex = getDatasetIndex(DATASET_IDS.annual);

            if (annualDatasetIndex !== -1 && chart.isDatasetVisible(annualDatasetIndex)) {
                const annualMeta = chart.getDatasetMeta(annualDatasetIndex);

                ctx.save();
                ctx.font = '600 11px "Inter", "Segoe UI", sans-serif';
                ctx.textAlign = 'center';

                state.indexMaps.annual.forEach((item, index) => {
                    if (!item.emphasize) {
                        return;
                    }

                    const element = annualMeta.data[index];
                    if (!element || element.skip) {
                        return;
                    }

                    const value = item.value;
                    const position = element.tooltipPosition();
                    const offset = value >= 0 ? -8 : 16;

                    ctx.fillStyle = getCssVar('--text-primary') || '#14202D';
                    ctx.textBaseline = value >= 0 ? 'bottom' : 'top';
                    ctx.fillText(formatBps(value), position.x, position.y + offset);
                });

                ctx.restore();
            }

            const quarterlyDatasetIndex = getDatasetIndex(DATASET_IDS.quarterly);
            if (quarterlyDatasetIndex !== -1 && chart.isDatasetVisible(quarterlyDatasetIndex)) {
                const quarterlyMeta = chart.getDatasetMeta(quarterlyDatasetIndex);
                const quarterlyIndices = Array.from(state.indexMaps.quarterly.keys());

                if (quarterlyIndices.length) {
                    const lastIndex = quarterlyIndices[quarterlyIndices.length - 1];
                    const element = quarterlyMeta.data[lastIndex];
                    const dataPoint = state.indexMaps.quarterly.get(lastIndex);

                    if (element && !element.skip && dataPoint) {
                        const position = element.tooltipPosition();

                        ctx.save();
                        ctx.font = '600 11px "Inter", "Segoe UI", sans-serif';
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'bottom';
                        ctx.fillStyle = getCssVar('--nco-ref-current') || '#2F6690';
                        ctx.fillText(formatBps(dataPoint.value), position.x, position.y - 10);
                        ctx.restore();
                    }
                }
            }
        }
    };

    const gfcAnnotationPlugin = {
        id: 'ncoGfcAnnotation',
        afterDatasetsDraw(chart) {
            if (state.gfcIndex < 0 || !Number.isFinite(state.references.gfcPeak)) {
                return;
            }

            const datasetIndex = getDatasetIndex(DATASET_IDS.annual);
            if (datasetIndex === -1 || !chart.isDatasetVisible(datasetIndex)) {
                return;
            }

            const meta = chart.getDatasetMeta(datasetIndex);
            const element = meta.data[state.gfcIndex];
            if (!element || element.skip) {
                return;
            }

            const ctx = chart.ctx;
            const position = element.tooltipPosition();
            const topY = Math.min(position.y - 28, chart.chartArea.top + 16);

            ctx.save();
            ctx.strokeStyle = getCssVar('--nco-bar-gfc') || '#8C1E33';
            ctx.fillStyle = getCssVar('--nco-bar-gfc') || '#8C1E33';
            ctx.lineWidth = 1.5;

            ctx.beginPath();
            ctx.moveTo(position.x, topY + 4);
            ctx.lineTo(position.x, position.y - 12);
            ctx.stroke();

            ctx.beginPath();
            ctx.moveTo(position.x - 4, position.y - 16);
            ctx.lineTo(position.x + 4, position.y - 16);
            ctx.lineTo(position.x, position.y - 8);
            ctx.closePath();
            ctx.fill();

            ctx.font = '600 12px "Inter", "Segoe UI", sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'bottom';
            ctx.fillText(
                `GFC Peak: ${formatBps(state.references.gfcPeak)}`,
                position.x,
                topY
            );
            ctx.restore();
        }
    };

    const recoveryAnnotationPlugin = {
        id: 'ncoRecoveryAnnotation',
        afterDatasetsDraw(chart) {
            if (!state.recoveryIndices.length) {
                return;
            }

            const datasetIndex = getDatasetIndex(DATASET_IDS.annual);
            if (datasetIndex === -1 || !chart.isDatasetVisible(datasetIndex)) {
                return;
            }

            const meta = chart.getDatasetMeta(datasetIndex);
            const points = state.recoveryIndices
                .map(index => meta.data[index])
                .filter(point => point && !point.skip);

            if (!points.length) {
                return;
            }

            const first = points[0];
            const last = points[points.length - 1];
            const zeroY = chart.scales.y.getPixelForValue(0);

            const ctx = chart.ctx;
            ctx.save();
            ctx.font = '600 11px "Inter", "Segoe UI", sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'top';
            ctx.fillStyle = getCssVar('--info') || '#2F6690';
            ctx.fillText('Net recoveries', (first.x + last.x) / 2, zeroY + 8);
            ctx.restore();
        }
    };

    function buildChart() {
        const canvas = document.getElementById(SELECTORS.canvasId);
        if (!canvas) {
            console.error('NCO time series canvas not found.');
            return;
        }

        const datasets = buildDatasets();

        const chartConfig = {
            type: 'bar',
            data: {
                labels: state.labels,
                datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                layout: {
                    padding: {
                        top: 28,
                        right: 28,
                        bottom: 16,
                        left: 16
                    }
                },
                interaction: {
                    mode: 'index',
                    intersect: false
                },
                scales: {
                    x: {
                        type: 'category',
                        border: {
                            color: getCssVar('--border-color') || '#D6DADD'
                        },
                        grid: {
                            display: false
                        },
                        ticks: {
                            color: getCssVar('--text-secondary') || '#4F5B67',
                            maxRotation: 0,
                            autoSkip: false,
                            font: {
                                size: 11
                            }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        min: state.axisBounds.min,
                        max: state.axisBounds.max,
                        grace: '5%',
                        border: {
                            color: getCssVar('--border-color') || '#D6DADD'
                        },
                        grid: {
                            color: getCssVar('--border-color') || '#D6DADD',
                            lineWidth: 1
                        },
                        title: {
                            display: true,
                            text: 'Net Charge-Offs (bps)',
                            color: getCssVar('--text-primary') || '#14202D',
                            font: {
                                size: 13,
                                weight: 'bold'
                            }
                        },
                        ticks: {
                            stepSize: 25,
                            color: getCssVar('--text-secondary') || '#4F5B67',
                            callback: value => `${value} bps`
                        }
                    }
                },
                plugins: {
                    legend: {
                        align: 'start',
                        labels: {
                            color: getCssVar('--text-primary') || '#14202D',
                            usePointStyle: true,
                            boxWidth: 14,
                            boxHeight: 14
                        }
                    },
                    tooltip: {
                        backgroundColor: getCssVar('--bg-secondary') || '#F8FBF8',
                        borderColor: getCssVar('--border-color') || '#D6DADD',
                        borderWidth: 1,
                        titleColor: getCssVar('--text-primary') || '#14202D',
                        bodyColor: getCssVar('--text-secondary') || '#4F5B67',
                        padding: 12,
                        callbacks: {
                            title(tooltipItems) {
                                if (!tooltipItems.length) {
                                    return '';
                                }
                                return tooltipItems[0].label;
                            },
                            label(context) {
                                const datasetId = context.dataset.id;
                                const index = context.dataIndex;

                                if (datasetId === DATASET_IDS.annual) {
                                    const item = state.indexMaps.annual.get(index);
                                    if (!item) {
                                        return '';
                                    }
                                    return `${item.period}: ${formatBps(item.value)} • ${item.categoryLabel}`;
                                }

                                if (datasetId === DATASET_IDS.quarterly) {
                                    const item = state.indexMaps.quarterly.get(index);
                                    if (!item) {
                                        return '';
                                    }
                                    return `${item.period}: ${formatBps(item.value, 1)} • ${item.categoryLabel}`;
                                }

                                if (Number.isFinite(context.parsed.y)) {
                                    return context.dataset.label;
                                }

                                return '';
                            }
                        }
                    }
                }
            },
            plugins: [
                normalizedBandPlugin,
                dataLabelPlugin,
                gfcAnnotationPlugin,
                recoveryAnnotationPlugin
            ]
        };

        state.chart = new Chart(canvas, chartConfig);
    }

    function bindControls() {
        bindToggle(SELECTORS.toggleQuarterly, DATASET_IDS.quarterly, 'Quarterly overlay');
        bindToggle(SELECTORS.toggleThroughCycle, DATASET_IDS.throughCycle, 'Through-cycle reference');
        bindToggle(SELECTORS.toggleNormalized, DATASET_IDS.normalized, 'Post-2014 90th percentile reference');
        bindToggle(SELECTORS.toggleCurrent, DATASET_IDS.current, 'Current reference');
    }

    function bindToggle(elementId, datasetId, label) {
        const input = document.getElementById(elementId);
        if (!input) {
            return;
        }

        input.addEventListener('change', () => {
            setDatasetVisibility(datasetId, input.checked);
            announceVisibility(label, input.checked);
        });
    }

    function setDatasetVisibility(datasetId, isVisible) {
        if (!state.chart) {
            return;
        }

        const datasetIndex = getDatasetIndex(datasetId);
        if (datasetIndex === -1) {
            return;
        }

        state.chart.data.datasets[datasetIndex].hidden = !isVisible;
        state.chart.update();
    }

    function announceVisibility(label, visible) {
        const status = document.getElementById(SELECTORS.toggleStatus);
        if (!status) {
            return;
        }
        const visibility = visible ? 'shown' : 'hidden';
        status.textContent = `${label} ${visibility}.`;
    }

    function bindExports() {
        const pngButton = document.getElementById(SELECTORS.exportPng);
        if (pngButton) {
            pngButton.addEventListener('click', () => {
                if (!state.chart) {
                    return;
                }
                const link = document.createElement('a');
                link.href = state.chart.toBase64Image('image/png', 1);
                link.download = 'caty_nco_time_series.png';
                link.click();
            });
        }

        const csvButton = document.getElementById(SELECTORS.exportCsv);
        if (csvButton) {
            csvButton.addEventListener('click', exportCsv);
        }
    }

    function exportCsv() {
        const rows = [
            ['Period', 'Period Type', 'NCO (bps)', 'Color Category', 'Context']
        ];

        state.annualData.forEach(item => {
            rows.push([
                item.period,
                'Annual',
                formatNumber(item.value),
                item.categoryLabel,
                item.context || ''
            ]);
        });

        state.quarterlyData.forEach(item => {
            rows.push([
                item.period,
                'Quarterly',
                formatNumber(item.value),
                item.categoryLabel,
                item.context || ''
            ]);
        });

        const csvContent = rows
            .map(row => row.map(escapeCsvValue).join(','))
            .join('\n');

        downloadBlob(csvContent, 'text/csv;charset=utf-8;', 'caty_nco_time_series.csv');
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

    function updateDataTable() {
        const tbody = document.getElementById(SELECTORS.tableBody);
        if (!tbody) {
            return;
        }

        tbody.innerHTML = '';

        const allRows = [
            ...state.annualData.map(item => ({
                period: item.period,
                type: 'Annual',
                value: item.value,
                categoryLabel: item.categoryLabel,
                context: item.context || ''
            })),
            ...state.quarterlyData.map(item => ({
                period: item.period,
                type: 'Quarterly',
                value: item.value,
                categoryLabel: item.categoryLabel,
                context: item.context || ''
            }))
        ];

        allRows.forEach(row => {
            const tr = document.createElement('tr');

            const cells = [
                { text: row.period },
                { text: row.type },
                { text: formatNumber(row.value), align: 'right' },
                { text: row.categoryLabel },
                { text: row.context || '—' }
            ];

            cells.forEach(cell => {
                const td = document.createElement('td');
                td.textContent = cell.text;
                if (cell.align === 'right') {
                    td.style.textAlign = 'right';
                }
                tr.appendChild(td);
            });

            tbody.appendChild(tr);
        });
    }

    function updateCurrentPositionText() {
        const container = document.getElementById(SELECTORS.currentPosition);
        if (!container) {
            return;
        }

        const { current, normalized, throughCycle } = state.references;
        if (![current, normalized, throughCycle].every(Number.isFinite)) {
            container.textContent = '';
            return;
        }

        const normalizedGap = ((normalized - current) / normalized) * 100;
        const throughCycleGap = ((throughCycle - current) / throughCycle) * 100;

        container.textContent = `Current ${formatBps(current)} is ${normalizedGap.toFixed(1)}% below the ${formatBps(normalized)} normalized guardrail and ${throughCycleGap.toFixed(1)}% below the ${formatBps(throughCycle)} through-cycle mean.`;
    }

    function refreshChartTheme() {
        if (!state.chart) {
            return;
        }

        const annualDatasetIndex = getDatasetIndex(DATASET_IDS.annual);
        if (annualDatasetIndex !== -1) {
            const colors = new Array(state.labels.length).fill('transparent');
            const borderColors = new Array(state.labels.length).fill('transparent');

            state.annualData.forEach((item, index) => {
                const color = getColorForCategory(item.category);
                colors[index] = color;
                borderColors[index] = color;
            });

            const dataset = state.chart.data.datasets[annualDatasetIndex];
            dataset.backgroundColor = colors;
            dataset.borderColor = borderColors;
            dataset.hoverBackgroundColor = colors;
        }

        const quarterlyDatasetIndex = getDatasetIndex(DATASET_IDS.quarterly);
        if (quarterlyDatasetIndex !== -1) {
            const lineColor = getCssVar('--nco-quarterly-line') || '#14202D';
            const dataset = state.chart.data.datasets[quarterlyDatasetIndex];
            dataset.borderColor = lineColor;
            dataset.backgroundColor = lineColor;
            dataset.pointBackgroundColor = lineColor;
            dataset.pointBorderColor = getCssVar('--bg-secondary') || '#FFFFFF';
        }

        const throughCycleDatasetIndex = getDatasetIndex(DATASET_IDS.throughCycle);
        if (throughCycleDatasetIndex !== -1) {
            state.chart.data.datasets[throughCycleDatasetIndex].borderColor = getCssVar('--nco-ref-mean') || '#7A8893';
        }

        const normalizedDatasetIndex = getDatasetIndex(DATASET_IDS.normalized);
        if (normalizedDatasetIndex !== -1) {
            state.chart.data.datasets[normalizedDatasetIndex].borderColor = getCssVar('--nco-ref-normalized') || '#7A8893';
        }

        const currentDatasetIndex = getDatasetIndex(DATASET_IDS.current);
        if (currentDatasetIndex !== -1) {
            state.chart.data.datasets[currentDatasetIndex].borderColor = getCssVar('--nco-ref-current') || '#2F6690';
        }

        state.chart.options.scales.x.border.color = getCssVar('--border-color') || '#D6DADD';
        state.chart.options.scales.x.ticks.color = getCssVar('--text-secondary') || '#4F5B67';

        state.chart.options.scales.y.border.color = getCssVar('--border-color') || '#D6DADD';
        state.chart.options.scales.y.grid.color = getCssVar('--border-color') || '#D6DADD';
        state.chart.options.scales.y.ticks.color = getCssVar('--text-secondary') || '#4F5B67';
        state.chart.options.scales.y.title.color = getCssVar('--text-primary') || '#14202D';

        state.chart.options.plugins.legend.labels.color = getCssVar('--text-primary') || '#14202D';
        state.chart.options.plugins.tooltip.backgroundColor = getCssVar('--bg-secondary') || '#F8FBF8';
        state.chart.options.plugins.tooltip.borderColor = getCssVar('--border-color') || '#D6DADD';
        state.chart.options.plugins.tooltip.titleColor = getCssVar('--text-primary') || '#14202D';
        state.chart.options.plugins.tooltip.bodyColor = getCssVar('--text-secondary') || '#4F5B67';

        state.chart.update('none');
    }

    function observeThemeChanges() {
        const observer = new MutationObserver(mutations => {
            const themeChange = mutations.some(
                mutation => mutation.type === 'attributes' && mutation.attributeName === 'data-theme'
            );
            if (themeChange) {
                window.requestAnimationFrame(refreshChartTheme);
            }
        });

        observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });
    }

    async function init() {
        const canvas = document.getElementById(SELECTORS.canvasId);
        if (!canvas) {
            return;
        }

        try {
            await loadData();
            buildChart();
            bindControls();
            bindExports();
            updateDataTable();
            updateCurrentPositionText();
            refreshChartTheme();
            observeThemeChanges();
        } catch (error) {
            console.error('Failed to initialise NCO time series', error);
        }
    }

    document.addEventListener('DOMContentLoaded', init);
    window.refreshNcoTimeSeriesTheme = refreshChartTheme;
})();
