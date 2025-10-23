/* global Chart */
(function() {
    'use strict';

    const DATA_URL = 'data/caty14_monte_carlo.json';

    const SELECTORS = {
        canvas: 'mcDistributionChart',
        toggleCI: 'mcToggleCI',
        togglePercentiles: 'mcTogglePercentiles',
        toggleInterpretations: 'mcToggleInterpretations',
        exportPng: 'mcExportPng',
        exportCsv: 'mcExportCsv',
        tableBody: 'mcTableBody',
        interpretations: 'mcInterpretations',
        medianCell: 'mcMedianCell',
        meanCell: 'mcMeanCell',
        spotCell: 'mcSpotCell',
        status: 'mcToggleStatus'
    };

    const CONSTANTS = {
        pngWidth: 1200,
        pngHeight: 900,
        chartPaddingTop: 56,
        chartPaddingRight: 36,
        chartPaddingBottom: 24,
        chartPaddingLeft: 48
    };

    const state = {
        chart: null,
        bands: [],
        ranges: [],
        summary: null,
        showCI: true,
        showPercentiles: false,
        showInterpretations: false
    };

    const confidenceBandPlugin = {
        id: 'mcConfidenceBand',
        beforeDatasetsDraw(chart) {
            if (!state.showCI || !state.summary || !state.bands.length) {
                return;
            }

            const chartArea = chart.chartArea;
            if (!chartArea) {
                return;
            }

            const lowerValue = state.summary.percentile5;
            const upperValue = state.summary.percentile95;
            const lowerX = priceToPixelX(lowerValue, chart);
            const upperX = priceToPixelX(upperValue, chart);

            const ctx = chart.ctx;
            ctx.save();
            ctx.fillStyle = getCssVar('--mc-ci-fill') || 'rgba(122, 136, 147, 0.12)';
            ctx.fillRect(lowerX, chartArea.top, Math.max(0, upperX - lowerX), chartArea.bottom - chartArea.top);
            ctx.restore();
        }
    };

    const barLabelPlugin = {
        id: 'mcBarLabels',
        afterDatasetsDraw(chart) {
            if (!state.bands.length) {
                return;
            }

            const ctx = chart.ctx;
            const meta = chart.getDatasetMeta(0);
            if (!meta) {
                return;
            }

            ctx.save();
            ctx.font = '700 13px "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
            ctx.fillStyle = getCssVar('--text-primary') || '#14202D';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'bottom';

            state.bands.forEach((band, index) => {
                const element = meta.data[index];
                if (!element) {
                    return;
                }

                const { x, y } = element.getProps(['x', 'y'], true);
                ctx.fillText(band.probabilityLabel, x, y - 8);
            });

            ctx.restore();
        }
    };

    const referenceLinesPlugin = {
        id: 'mcReferenceLines',
        afterDatasetsDraw(chart) {
            if (!state.summary || !state.bands.length) {
                return;
            }

            const chartArea = chart.chartArea;
            if (!chartArea) {
                return;
            }

            const ctx = chart.ctx;
            const references = [
                {
                    key: 'median',
                    value: state.summary.median,
                    label: `Median $${formatPrice(state.summary.median)}`,
                    color: getCssVar('--mc-ref-median') || '#2F6690',
                    width: 2,
                    dash: [6, 6],
                    offsetX: -12,
                    align: 'right'
                },
                {
                    key: 'mean',
                    value: state.summary.mean,
                    label: `Mean $${formatPrice(state.summary.mean)}`,
                    color: getCssVar('--mc-ref-mean') || '#7A8893',
                    width: 1.5,
                    dash: [3, 4],
                    offsetX: 0,
                    align: 'center'
                },
                {
                    key: 'spot',
                    value: state.summary.spot,
                    label: `Spot $${formatPrice(state.summary.spot)}`,
                    color: getCssVar('--mc-ref-spot') || '#14202D',
                    width: 2,
                    dash: [],
                    offsetX: 12,
                    align: 'left'
                }
            ];

            if (state.showPercentiles) {
                references.unshift({
                    key: 'p5',
                    value: state.summary.percentile5,
                    label: `5th %ile $${formatPrice(state.summary.percentile5)}`,
                    color: getCssVar('--mc-ref-p5') || 'rgba(140, 30, 51, 0.6)',
                    width: 1,
                    dash: [4, 6],
                    offsetX: -14,
                    align: 'right'
                });
                references.push({
                    key: 'p95',
                    value: state.summary.percentile95,
                    label: `95th %ile $${formatPrice(state.summary.percentile95)}`,
                    color: getCssVar('--mc-ref-p95') || 'rgba(46, 111, 62, 0.6)',
                    width: 1,
                    dash: [4, 6],
                    offsetX: 14,
                    align: 'left'
                });
            }

            ctx.save();
            ctx.font = '600 12px "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif';
            ctx.textBaseline = 'bottom';

            references.forEach(reference => {
                const x = priceToPixelX(reference.value, chart);
                ctx.save();
                ctx.beginPath();
                ctx.setLineDash(reference.dash);
                ctx.lineWidth = reference.width;
                ctx.strokeStyle = reference.color;
                ctx.moveTo(x, chartArea.top);
                ctx.lineTo(x, chartArea.bottom);
                ctx.stroke();
                ctx.restore();

                ctx.save();
                ctx.fillStyle = reference.color;
                ctx.textAlign = reference.align;
                ctx.fillText(reference.label, x + reference.offsetX, chartArea.top - 8);
                ctx.restore();
            });

            ctx.restore();
        }
    };

    function getCssVar(varName) {
        return getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
    }

    function parseProbability(value) {
        if (typeof value !== 'string') {
            return 0;
        }
        const cleaned = value.replace('%', '').trim();
        const number = Number.parseFloat(cleaned);
        return Number.isFinite(number) ? number : 0;
    }

    function formatProbability(value) {
        if (!Number.isFinite(value)) {
            return '0.0%';
        }
        return `${value.toFixed(1)}%`;
    }

    function formatPrice(value) {
        if (!Number.isFinite(value)) {
            return '0.00';
        }
        return value.toFixed(2);
    }

    function priceToPixelX(price, chart) {
        const ranges = state.ranges;
        const chartArea = chart.chartArea;
        if (!ranges.length || !chartArea) {
            return chartArea ? chartArea.left : 0;
        }

        const binWidth = (chartArea.right - chartArea.left) / ranges.length;
        const minPrice = ranges[0].min;
        const maxPrice = ranges[ranges.length - 1].max;
        const clampedPrice = Math.min(Math.max(price, minPrice), maxPrice);

        let binIndex = ranges.length - 1;
        for (let i = 0; i < ranges.length; i += 1) {
            const range = ranges[i];
            if (clampedPrice <= range.max || i === ranges.length - 1) {
                binIndex = i;
                break;
            }
        }

        const range = ranges[binIndex];
        const span = Math.max(range.max - range.min, 0.0001);
        const fraction = (clampedPrice - range.min) / span;
        const binLeft = chartArea.left + binIndex * binWidth;
        return binLeft + fraction * binWidth;
    }

    function withOpacity(color, opacity) {
        if (!color) {
            return `rgba(46, 111, 62, ${opacity})`;
        }

        const trimmed = color.trim();
        if (trimmed.startsWith('#')) {
            const hex = trimmed.substring(1);
            const isShort = hex.length === 3;
            const r = Number.parseInt(isShort ? hex[0] + hex[0] : hex.slice(0, 2), 16);
            const g = Number.parseInt(isShort ? hex[1] + hex[1] : hex.slice(2, 4), 16);
            const b = Number.parseInt(isShort ? hex[2] + hex[2] : hex.slice(4, 6), 16);
            if ([r, g, b].some(component => Number.isNaN(component))) {
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

    function computeBandRanges(bands) {
        if (!state.summary) {
            return [];
        }

        const lowerBaseline = Math.max(0, state.summary.percentile5 - 10);
        const upperBaseline = state.summary.percentile95 + 10;

        return bands.map((band, index) => {
            const label = band.bandLabel.toLowerCase();

            if (label.startsWith('sub-$')) {
                const match = label.match(/sub-\$(\d+(?:\.\d+)?)/);
                const maxValue = match ? Number.parseFloat(match[1]) : 35;
                return {
                    min: lowerBaseline,
                    max: Number.isFinite(maxValue) ? maxValue : 35
                };
            }

            if (/\$\d+\s*-\s*\$\d+/.test(label)) {
                const match = label.match(/\$(\d+(?:\.\d+)?)\s*-\s*\$(\d+(?:\.\d+)?)/);
                if (match) {
                    return {
                        min: Number.parseFloat(match[1]),
                        max: Number.parseFloat(match[2])
                    };
                }
            }

            if (label.includes('+')) {
                const match = label.match(/\$(\d+(?:\.\d+)?)\+/);
                const minValue = match ? Number.parseFloat(match[1]) : 55;
                return {
                    min: Number.isFinite(minValue) ? minValue : 55,
                    max: Math.max(upperBaseline, (Number.isFinite(minValue) ? minValue : 55) + 20)
                };
            }

            const fallbackMin = 25 + index * 10;
            return {
                min: fallbackMin,
                max: fallbackMin + 10
            };
        });
    }

    function buildBandObjects(probabilityBands, summary) {
        const numRuns = Number(summary?.num_runs) || 0;
        if (!Array.isArray(probabilityBands)) {
            return [];
        }

        let cumulative = 0;

        return probabilityBands.map(band => {
            const probabilityValue = parseProbability(band.probability);
            cumulative += probabilityValue;
            const estimatedRuns = Math.round(numRuns * (probabilityValue / 100));
            return {
                bandLabel: band.band || '',
                probabilityValue,
                probabilityLabel: formatProbability(probabilityValue),
                estimatedRuns,
                estimatedRunsLabel: estimatedRuns.toLocaleString('en-US'),
                interpretation: band.interpretation || '',
                cumulativeValue: cumulative,
                cumulativeLabel: formatProbability(cumulative),
                midpoint: 0,
                isUpside: false
            };
        });
    }

    function assignBandMidpoints() {
        state.bands.forEach((band, index) => {
            const range = state.ranges[index];
            if (!range) {
                band.midpoint = 0;
                band.isUpside = false;
                return;
            }

            const midpoint = (range.min + range.max) / 2;
            band.midpoint = midpoint;
            band.isUpside = midpoint >= state.summary.spot;
        });
    }

    function getBarColors() {
        const downside = withOpacity(
            getCssVar('--mc-bar-downside') || '#B85C00',
            toNumber(getCssVar('--mc-bar-opacity'), 0.85)
        );
        const upside = withOpacity(
            getCssVar('--mc-bar-upside') || '#2E6F3E',
            toNumber(getCssVar('--mc-bar-opacity'), 0.85)
        );

        return state.bands.map(band => (band.isUpside ? upside : downside));
    }

    function buildChart() {
        const canvas = document.getElementById(SELECTORS.canvas);
        if (!canvas || typeof Chart === 'undefined') {
            return;
        }

        const data = {
            labels: state.bands.map(band => band.bandLabel),
            datasets: [
                {
                    label: 'Probability',
                    data: state.bands.map(band => band.probabilityValue),
                    backgroundColor: getBarColors(),
                    borderWidth: 0,
                    borderRadius: 14,
                    barPercentage: 0.75,
                    categoryPercentage: 0.6
                }
            ]
        };

        state.chart = new Chart(canvas, {
            type: 'bar',
            data,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                layout: {
                    padding: {
                        top: CONSTANTS.chartPaddingTop,
                        right: CONSTANTS.chartPaddingRight,
                        bottom: CONSTANTS.chartPaddingBottom,
                        left: CONSTANTS.chartPaddingLeft
                    }
                },
                animation: false,
                scales: {
                    x: {
                        grid: {
                            display: false
                        },
                        border: {
                            color: getCssVar('--border-color') || '#D6DADD'
                        },
                        ticks: {
                            color: getCssVar('--text-secondary') || '#4F5B67',
                            font: {
                                size: 12,
                                family: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
                            }
                        }
                    },
                    y: {
                        beginAtZero: true,
                        suggestedMax: 35,
                        title: {
                            display: true,
                            text: 'Probability (%)',
                            color: getCssVar('--text-secondary') || '#4F5B67',
                            font: {
                                weight: '600',
                                size: 12
                            }
                        },
                        ticks: {
                            callback(value) {
                                return `${value}%`;
                            },
                            color: getCssVar('--text-secondary') || '#4F5B67',
                            font: {
                                size: 12,
                                family: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
                            }
                        },
                        border: {
                            color: getCssVar('--border-color') || '#D6DADD'
                        },
                        grid: {
                            color: context => (context.tick.value === 0
                                ? getCssVar('--border-color') || '#D6DADD'
                                : `${getCssVar('--border-color') || '#D6DADD'}33`)
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
                                const band = state.bands[context[0].dataIndex];
                                return band ? band.bandLabel : '';
                            },
                            label(context) {
                                const band = state.bands[context.dataIndex];
                                if (!band) {
                                    return '';
                                }
                                return `Probability: ${band.probabilityLabel}`;
                            },
                            afterLabel(context) {
                                const band = state.bands[context.dataIndex];
                                if (!band || !state.summary) {
                                    return [];
                                }

                                const lines = [];
                                if (band.interpretation) {
                                    lines.push(band.interpretation);
                                }

                                lines.push(`Simulations: ~${band.estimatedRunsLabel} of ${state.summary.numRunsLabel}`);
                                lines.push(`Cumulative: ${band.cumulativeLabel}`);
                                return lines;
                            }
                        }
                    }
                }
            },
            plugins: [confidenceBandPlugin, barLabelPlugin, referenceLinesPlugin]
        });
    }

    function refreshChartTheme() {
        if (!state.chart) {
            return;
        }

        const chart = state.chart;
        const dataset = chart.data.datasets[0];
        if (dataset) {
            dataset.backgroundColor = getBarColors();
        }

        const axisColor = getCssVar('--text-secondary') || '#4F5B67';
        const borderColor = getCssVar('--border-color') || '#D6DADD';

        if (chart.options && chart.options.scales) {
            const { x, y } = chart.options.scales;
            if (x) {
                if (x.ticks) {
                    x.ticks.color = axisColor;
                }
                if (x.border) {
                    x.border.color = borderColor;
                }
            }
            if (y) {
                if (y.ticks) {
                    y.ticks.color = axisColor;
                }
                if (y.title) {
                    y.title.color = axisColor;
                }
                if (y.border) {
                    y.border.color = borderColor;
                }
                if (y.grid) {
                    y.grid.color = context => (context.tick.value === 0 ? borderColor : `${borderColor}33`);
                }
            }
        }

        chart.update('none');
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

    function bindToggle(button, stateKey, announcementLabel, onChange) {
        if (!button) {
            return;
        }

        button.addEventListener('click', () => {
            const current = button.getAttribute('aria-pressed') === 'true';
            const nextState = !current;
            button.setAttribute('aria-pressed', nextState ? 'true' : 'false');
            state[stateKey] = nextState;

            if (typeof onChange === 'function') {
                onChange(nextState);
            }

            announceToggle(`${announcementLabel} ${nextState ? 'shown' : 'hidden'}.`);
        });
    }

    function announceToggle(message) {
        const region = document.getElementById(SELECTORS.status);
        if (region) {
            region.textContent = message;
        }
    }

    function updateInterpretationsVisibility() {
        const container = document.getElementById(SELECTORS.interpretations);
        if (!container) {
            return;
        }

        if (state.showInterpretations) {
            container.hidden = false;
            container.setAttribute('aria-hidden', 'false');
        } else {
            container.hidden = true;
            container.setAttribute('aria-hidden', 'true');
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

        const link = document.createElement('a');
        link.href = chart.toBase64Image('image/png', 1);
        link.download = 'monte_carlo_distribution.png';
        link.click();

        chart.options.responsive = originalResponsive;
        chart.options.maintainAspectRatio = originalAspect;
        chart.resize(originalWidth, originalHeight);
        canvas.style.width = originalStyleWidth;
        canvas.style.height = originalStyleHeight;
        chart.update('none');
    }

    function exportCsv() {
        if (!state.bands.length || !state.summary) {
            return;
        }

        const rows = [
            ['Price_Band', 'Probability_Pct', 'Interpretation', 'Estimated_Runs', 'Cumulative_Probability']
        ];

        state.bands.forEach(band => {
            rows.push([
                band.bandLabel,
                Number(band.probabilityValue.toFixed(1)),
                band.interpretation,
                band.estimatedRuns,
                Number(band.cumulativeValue.toFixed(1))
            ]);
        });

        rows.push([]);
        rows.push(['# Metadata']);
        rows.push(['Simulation_Runs', state.summary.numRuns]);
        rows.push(['Median_Price', state.summary.median]);
        rows.push(['Mean_Price', state.summary.mean]);
        rows.push(['Spot_Price', state.summary.spot]);
        rows.push(['Loss_Probability_Pct', state.summary.lossProbability]);
        rows.push(['CI_95_Lower', state.summary.percentile5]);
        rows.push(['CI_95_Upper', state.summary.percentile95]);

        const csvContent = rows.map(row => row.map(escapeCsvValue).join(',')).join('\n');
        downloadBlob(csvContent, 'text/csv;charset=utf-8;', 'monte_carlo_distribution.csv');
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

    function populateTable() {
        const tbody = document.getElementById(SELECTORS.tableBody);
        if (!tbody) {
            return;
        }

        tbody.innerHTML = '';

        state.bands.forEach(band => {
            const row = document.createElement('tr');

            const priceCell = document.createElement('th');
            priceCell.setAttribute('scope', 'row');
            priceCell.textContent = band.bandLabel;

            const probabilityCell = document.createElement('td');
            probabilityCell.textContent = band.probabilityLabel;

            const interpretationCell = document.createElement('td');
            interpretationCell.textContent = band.interpretation;

            row.appendChild(priceCell);
            row.appendChild(probabilityCell);
            row.appendChild(interpretationCell);
            tbody.appendChild(row);
        });
    }

    function renderInterpretations() {
        const container = document.getElementById(SELECTORS.interpretations);
        if (!container) {
            return;
        }

        container.innerHTML = '';
        state.bands.forEach(band => {
            const paragraph = document.createElement('p');
            paragraph.className = 'mc-interpretation';

            const strong = document.createElement('strong');
            strong.textContent = `${band.bandLabel}:`;

            paragraph.appendChild(strong);
            paragraph.appendChild(document.createTextNode(` ${band.interpretation}`));

            container.appendChild(paragraph);
        });
    }

    function populateSummaryCells() {
        if (!state.summary) {
            return;
        }

        const medianCell = document.getElementById(SELECTORS.medianCell);
        if (medianCell) {
            medianCell.textContent = `$${formatPrice(state.summary.median)} (50th percentile)`;
        }

        const meanCell = document.getElementById(SELECTORS.meanCell);
        if (meanCell) {
            meanCell.textContent = `$${formatPrice(state.summary.mean)} (expected value)`;
        }

        const spotCell = document.getElementById(SELECTORS.spotCell);
        if (spotCell) {
            spotCell.textContent = `$${formatPrice(state.summary.spot)} (current market)`;
        }
    }

    function toNumber(value, fallback = 0) {
        const numeric = Number(value);
        return Number.isFinite(numeric) ? numeric : fallback;
    }

    async function loadData() {
        const response = await fetch(DATA_URL);
        if (!response.ok) {
            throw new Error(`Failed to load ${DATA_URL}: ${response.status}`);
        }

        const json = await response.json();
        const summary = json?.simulation_summary || {};
        const confidence = json?.confidence_interval || {};
        const probabilityBands = json?.tables?.probability_bands || [];

        state.summary = {
            numRuns: toNumber(summary.num_runs, 0),
            numRunsLabel: (Number(summary.num_runs) || 0).toLocaleString('en-US'),
            median: toNumber(summary.target_median, 0),
            mean: toNumber(summary.target_mean, 0),
            spot: toNumber(summary.spot_price, 0),
            lossProbability: toNumber(summary.loss_probability_pct, 0),
            percentile5: toNumber(confidence.lower_price, 0),
            percentile95: toNumber(confidence.upper_price, 0)
        };

        state.bands = buildBandObjects(probabilityBands, summary);
        state.ranges = computeBandRanges(state.bands);
        assignBandMidpoints();
    }

    async function init() {
        const canvas = document.getElementById(SELECTORS.canvas);
        if (!canvas) {
            return;
        }

        try {
            await loadData();
            renderInterpretations();
            updateInterpretationsVisibility();
            populateTable();
            populateSummaryCells();
            buildChart();
            bindToggle(
                document.getElementById(SELECTORS.toggleCI),
                'showCI',
                '95% confidence interval band',
                () => {
                    if (state.chart) {
                        state.chart.update('none');
                    }
                }
            );
            bindToggle(
                document.getElementById(SELECTORS.togglePercentiles),
                'showPercentiles',
                'Percentile reference lines',
                () => {
                    if (state.chart) {
                        state.chart.update('none');
                    }
                }
            );
            bindToggle(
                document.getElementById(SELECTORS.toggleInterpretations),
                'showInterpretations',
                'Scenario interpretations',
                () => {
                    updateInterpretationsVisibility();
                }
            );
            bindExports();
            refreshChartTheme();
            observeThemeChanges();
        } catch (error) {
            console.error('Failed to initialise Monte Carlo distribution module', error);
        }
    }

    document.addEventListener('DOMContentLoaded', init);
    window.refreshMonteCarloTheme = refreshChartTheme;
})();
