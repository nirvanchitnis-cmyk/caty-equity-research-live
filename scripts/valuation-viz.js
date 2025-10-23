/* global Chart, getCSSVar, getThemeColors, fetchJsonResource, updateThemeToggleState */
/**
 * Valuation Decision Module
 * Builds peer scatter (ROTE vs P/TBV) + framework bar comparison with interactive controls.
 * Fulfils board prescription for maintaining CATY HOLD decision.
 */
(function () {
    'use strict';

    const DEFAULT_CONFIG = {
        scatterCanvasId: 'valuation-peer-scatter',
        barCanvasId: 'valuation-framework-bars',
        peerTableId: 'peer-data-table',
        frameworkTableId: 'framework-data-table',
        catyAnnotationId: 'caty-residual-annotation',
        regressionSummaryId: 'regression-summary',
        peerCountLabelId: 'peer-count-label',
        shareFeedbackId: 'share-feedback'
    };

    const LEGEND_ORDER = {
        CATY: 0,
        Peers: 1,
        'Regression line': 2
    };

    const DEFAULT_FRAMEWORK_ORDER = ['regression', 'irc_blended', 'wilson_95', 'probability_weighted', 'normalized'];

    /**
     * Scatter data label plugin - renders labels for CATY and residual leaders.
     */
    const scatterLabelPlugin = {
        id: 'scatterLabelPlugin',
        afterDatasetsDraw(chart, args, opts) {
            const labels = (opts && Array.isArray(opts.labels)) ? opts.labels : [];
            if (!labels.length) {
                return;
            }

            const ctx = chart.ctx;
            ctx.save();
            ctx.font = '12px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'bottom';
            const textColor = (opts && opts.color) || getCSSVar('--text-primary') || '#14202D';
            ctx.fillStyle = textColor;

            labels.forEach((entry) => {
                const { datasetIndex, datasetId, index, label } = entry;
                const actualDatasetIndex = typeof datasetIndex === 'number'
                    ? datasetIndex
                    : chart.data.datasets.findIndex(ds => ds && ds.id === datasetId);

                if (actualDatasetIndex < 0) {
                    return;
                }

                const meta = chart.getDatasetMeta(actualDatasetIndex);
                if (!meta || !meta.data || !meta.data[index]) {
                    return;
                }

                const point = meta.data[index];
                if (!point || point.hidden) {
                    return;
                }

                const position = point.tooltipPosition();
                const yOffset = entry.yOffset || 8;
                ctx.fillText(label, position.x, position.y - yOffset);
            });

            ctx.restore();
        }
    };

    /**
     * Bar chart reference line plugin - draws horizontal line at Spot price.
     */
    const barReferenceLinePlugin = {
        id: 'barReferenceLine',
        afterDatasetsDraw(chart, args, options) {
            if (!options || typeof options.value !== 'number') {
                return;
            }

            const yScale = chart.scales[chart.getDatasetMeta(0).yAxisID];
            if (!yScale) {
                return;
            }

            const lineY = yScale.getPixelForValue(options.value);
            const { left, right } = chart.chartArea;
            const ctx = chart.ctx;
            ctx.save();
            ctx.strokeStyle = options.color || getCSSVar('--bar-neutral') || '#4F5B67';
            ctx.lineWidth = 1.5;
            ctx.setLineDash([6, 4]);
            ctx.beginPath();
            ctx.moveTo(left, lineY);
            ctx.lineTo(right, lineY);
            ctx.stroke();

            if (options.label) {
                ctx.font = '12px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
                ctx.fillStyle = ctx.strokeStyle;
                ctx.textBaseline = 'bottom';
                ctx.textAlign = 'right';
                ctx.fillText(options.label, right, lineY - 6);
            }

            ctx.restore();
        }
    };

    if (typeof Chart !== 'undefined' && Chart.register) {
        Chart.register(scatterLabelPlugin, barReferenceLinePlugin);
    }

    function loadJson(path) {
        if (typeof fetchJsonResource === 'function') {
            return fetchJsonResource(path);
        }
        return fetch(path).then((response) => {
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status} for ${path}`);
            }
            return response.json();
        });
    }

    function formatPercent(value, decimals = 1) {
        return `${Number(value).toFixed(decimals)}%`;
    }

    function formatMultiple(value, decimals = 3) {
        return `${Number(value).toFixed(decimals)}x`;
    }

    function formatDollar(value, decimals = 2) {
        return `$${Number(value).toFixed(decimals)}`;
    }

    function formatSigned(value, decimals = 3, suffix = 'x') {
        const num = Number(value);
        const sign = num >= 0 ? '+' : '';
        return `${sign}${num.toFixed(decimals)}${suffix}`;
    }

    function formatSignedPercent(value, decimals = 1) {
        const num = Number(value);
        const sign = num >= 0 ? '+' : '';
        return `${sign}${num.toFixed(decimals)}%`;
    }

    function clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
    }

    function computeRegression(points) {
        if (!Array.isArray(points) || points.length < 2) {
            return null;
        }

        const n = points.length;
        const sums = points.reduce((acc, point) => {
            const x = Number(point.x);
            const y = Number(point.y);
            acc.sumX += x;
            acc.sumY += y;
            acc.sumXY += x * y;
            acc.sumX2 += x * x;
            acc.sumY2 += y * y;
            return acc;
        }, { sumX: 0, sumY: 0, sumXY: 0, sumX2: 0, sumY2: 0 });

        const denominator = (n * sums.sumX2) - (sums.sumX * sums.sumX);
        if (denominator === 0) {
            return null;
        }

        const slope = ((n * sums.sumXY) - (sums.sumX * sums.sumY)) / denominator;
        const intercept = (sums.sumY - slope * sums.sumX) / n;

        const meanY = sums.sumY / n;
        let ssTot = 0;
        let ssRes = 0;
        points.forEach(({ x, y }) => {
            const predicted = intercept + slope * x;
            ssTot += Math.pow(y - meanY, 2);
            ssRes += Math.pow(y - predicted, 2);
        });

        const rSquared = ssTot === 0 ? null : (1 - (ssRes / ssTot));

        return {
            slope,
            intercept,
            rSquared: rSquared !== null ? clamp(rSquared, 0, 1) : null,
            n
        };
    }

    function computeLinePoints(coefficients, xMin = 0, xMax = 18) {
        if (!coefficients) {
            return [];
        }
        const start = { x: xMin, y: coefficients.intercept + coefficients.slope * xMin };
        const end = { x: xMax, y: coefficients.intercept + coefficients.slope * xMax };
        return [start, end];
    }

    function getModuleColors() {
        return {
            peer: getCSSVar('--peer-marker') || '#7A8893',
            peerHover: getCSSVar('--peer-marker') || '#7A8893',
            catyFill: getCSSVar('--caty-marker-fill') || '#14202D',
            catyOutline: getCSSVar('--caty-marker-outline') || '#F5F7FA',
            regression: getCSSVar('--regression-line') || '#2F6690',
            up: getCSSVar('--success') || '#2E6F3E',
            down: getCSSVar('--danger') || '#8C1E33',
            neutral: getCSSVar('--bar-neutral') || '#4F5B67',
            textPrimary: getCSSVar('--text-primary') || '#14202D',
            textSecondary: getCSSVar('--text-secondary') || '#4F5B67',
            grid: getCSSVar('--border-color') || '#D6DADD',
            panel: getCSSVar('--bg-primary') || '#F8FBF8'
        };
    }

    function buildFrameworkCollection(valuationData) {
        const frameworks = [];
        const spot = Number(valuationData.metadata?.price_used ?? valuationData.methods?.regression?.inputs?.price ?? 0);

        frameworks.push({
            id: 'regression',
            label: 'Regression',
            price: Number(valuationData.methods?.regression?.target_price ?? 0),
            category: 'Model-derived'
        });
        frameworks.push({
            id: 'irc_blended',
            label: 'IRC Blended',
            price: Number(valuationData.methods?.irc_blended?.target_price ?? 0),
            category: 'Model-derived'
        });
        frameworks.push({
            id: 'wilson_95',
            label: 'Wilson 95%',
            price: Number(valuationData.methods?.wilson_95?.target_price ?? 0),
            category: 'Model-derived',
            simulated: true
        });
        frameworks.push({
            id: 'probability_weighted',
            label: 'Probability-Weighted',
            price: Number(valuationData.frameworks?.probability_weighted?.target_price ?? 0),
            category: 'Scenario-weighted'
        });
        frameworks.push({
            id: 'normalized',
            label: 'Normalized (Gordon)',
            price: Number(valuationData.methods?.normalized?.target_price ?? 0),
            category: 'Gordon Growth'
        });
        frameworks.push({
            id: 'spot',
            label: 'Spot',
            price: spot,
            category: 'Reference'
        });

        return frameworks;
    }

    function updateLabelState(labelEl, { checked, disabled }) {
        if (!labelEl) {
            return;
        }
        labelEl.classList.toggle('is-disabled', !!disabled);
        labelEl.classList.toggle('is-checked', !!checked);
    }

    function toggleCheckboxDisabled(input, label, disabled) {
        input.disabled = disabled;
        updateLabelState(label, { checked: input.checked, disabled });
        if (disabled) {
            input.setAttribute('aria-disabled', 'true');
        } else {
            input.removeAttribute('aria-disabled');
        }
    }

    function applyLegendSort(options) {
        if (!options || !options.plugins || !options.plugins.legend) {
            return;
        }

        if (!options.plugins.legend.labels) {
            options.plugins.legend.labels = {};
        }

        options.plugins.legend.labels.sort = (a, b) => {
            const orderA = LEGEND_ORDER[a.text] ?? Number.MAX_SAFE_INTEGER;
            const orderB = LEGEND_ORDER[b.text] ?? Number.MAX_SAFE_INTEGER;
            return orderA - orderB;
        };
    }

    function formatFrameworkLabel(framework) {
        if (!framework || !framework.category) {
            return framework.label;
        }
        if (framework.category === 'Reference') {
            return framework.label;
        }
        const suffix = framework.simulated ? `${framework.category}; Simulated` : framework.category;
        return `${framework.label} (${suffix})`;
    }

    async function initValuationDecisionModule(userConfig = {}) {
        const config = { ...DEFAULT_CONFIG, ...userConfig };
        const scatterCanvas = document.getElementById(config.scatterCanvasId);
        const barCanvas = document.getElementById(config.barCanvasId);
        const peerTable = document.getElementById(config.peerTableId);
        const frameworkTable = document.getElementById(config.frameworkTableId);
        const catyAnnotation = document.getElementById(config.catyAnnotationId);
        const regressionSummary = document.getElementById(config.regressionSummaryId);
        const peerCountLabel = document.getElementById(config.peerCountLabelId);
        const shareFeedback = document.getElementById(config.shareFeedbackId);

        const refitToggle = document.getElementById('refit-regression-toggle');
        const peerCheckboxGrid = document.getElementById('peer-checkbox-grid');
        const frameworkCheckboxGrid = document.getElementById('framework-checkbox-grid');
        const resetButton = document.getElementById('reset-valuation-viz');
        const exportPngButton = document.getElementById('export-valuation-png');
        const exportCsvButton = document.getElementById('export-valuation-csv');
        const shareButton = document.getElementById('share-valuation-state');

        if (!scatterCanvas || !barCanvas || !peerTable || !frameworkTable || !catyAnnotation || !regressionSummary
            || !peerCountLabel || !shareFeedback || !refitToggle || !peerCheckboxGrid || !frameworkCheckboxGrid
            || !resetButton || !exportPngButton || !exportCsvButton || !shareButton) {
            console.warn('Valuation decision module: required DOM nodes missing.');
            return null;
        }

        let peerComparables;
        let valuationOutputs;
        try {
            [peerComparables, valuationOutputs] = await Promise.all([
                loadJson('data/peer_comparables.json'),
                loadJson('data/valuation_outputs.json')
            ]);
        } catch (error) {
            console.error('Failed to load valuation datasets', error);
            return null;
        }

        if (!peerComparables || !valuationOutputs) {
            return null;
        }

        const regressionInputs = valuationOutputs.methods?.regression?.inputs || {};
        const peerSampleList = Array.isArray(regressionInputs.peer_sample) ? regressionInputs.peer_sample : [];
        const peerMetricsByTicker = new Map();
        peerComparables.metrics.forEach((metric) => {
            peerMetricsByTicker.set(metric.ticker, metric);
        });

        const peers = peerSampleList.map((ticker) => {
            const metric = peerMetricsByTicker.get(ticker);
            if (!metric) {
                return null;
            }
            return {
                ticker,
                rote: Number(metric.rote_pct),
                ptbv: Number(metric.p_tbv),
                price: Number(metric.price)
            };
        }).filter(Boolean);

        const catyMetric = peerMetricsByTicker.get('CATY');
        if (!catyMetric) {
            console.warn('CATY metrics missing from peer_comparables.json');
            return null;
        }

        const fixedCoefficients = {
            slope: Number(regressionInputs.coefficients?.slope ?? valuationOutputs.methods?.regression?.coefficients?.slope ?? 0.058),
            intercept: Number(regressionInputs.coefficients?.intercept ?? valuationOutputs.methods?.regression?.coefficients?.intercept ?? 0.82),
            rSquared: Number(valuationOutputs.methods?.regression?.r_squared ?? 0.68),
            n: peerSampleList.length
        };

        const frameworks = buildFrameworkCollection(valuationOutputs);
        const selectableFrameworkIds = frameworks.filter(item => item.id !== 'spot').map(item => item.id);

        const state = {
            peers,
            caty: {
                ticker: 'CATY',
                rote: Number(catyMetric.rote_pct),
                ptbv: Number(catyMetric.p_tbv),
                price: Number(catyMetric.price)
            },
            fixedCoefficients,
            selectedPeers: new Set(peers.map((peer) => peer.ticker)),
            refit: false,
            frameworks,
            selectedFrameworks: new Set(selectableFrameworkIds),
            spotPrice: Number(valuationOutputs.metadata?.price_used ?? catyMetric.price),
            currentCoefficients: fixedCoefficients,
            coefficientsSource: 'fixed',
            shareFeedbackTimeout: null
        };

        const peerCheckboxRefs = new Map();
        const frameworkCheckboxRefs = new Map();

        function buildPeerControls() {
            peerCheckboxGrid.innerHTML = '';
            peers.forEach((peer) => {
                const label = document.createElement('label');
                label.setAttribute('data-peer', peer.ticker);

                const input = document.createElement('input');
                input.type = 'checkbox';
                input.value = peer.ticker;
                input.checked = state.selectedPeers.has(peer.ticker);
                input.disabled = !state.refit;
                input.setAttribute('aria-label', `${peer.ticker} peer inclusion`);

                const span = document.createElement('span');
                span.textContent = `${peer.ticker} · ${formatPercent(peer.rote)} / ${formatMultiple(peer.ptbv)}`;

                label.appendChild(input);
                label.appendChild(span);
                updateLabelState(label, { checked: input.checked, disabled: input.disabled });

                input.addEventListener('change', () => {
                    if (!state.refit) {
                        input.checked = state.selectedPeers.has(peer.ticker);
                        return;
                    }
                    if (input.checked) {
                        state.selectedPeers.add(peer.ticker);
                    } else {
                        state.selectedPeers.delete(peer.ticker);
                    }
                    updateLabelState(label, { checked: input.checked, disabled: input.disabled });
                    render();
                    updateURL();
                });

                peerCheckboxGrid.appendChild(label);
                peerCheckboxRefs.set(peer.ticker, { input, label });
            });
        }

        function buildFrameworkControls() {
            frameworkCheckboxGrid.innerHTML = '';
            frameworks.forEach((framework) => {
                if (framework.id === 'spot') {
                    return;
                }
                const label = document.createElement('label');
                label.setAttribute('data-framework', framework.id);

                const input = document.createElement('input');
                input.type = 'checkbox';
                input.value = framework.id;
                input.checked = state.selectedFrameworks.has(framework.id);
                input.setAttribute('aria-label', `${framework.label} framework inclusion`);

                const span = document.createElement('span');
                span.textContent = `${framework.label} · ${formatDollar(framework.price)}`;

                label.appendChild(input);
                label.appendChild(span);
                updateLabelState(label, { checked: input.checked, disabled: input.disabled });

                input.addEventListener('change', () => {
                    if (input.checked) {
                        state.selectedFrameworks.add(framework.id);
                    } else {
                        state.selectedFrameworks.delete(framework.id);
                    }
                    updateLabelState(label, { checked: input.checked, disabled: input.disabled });
                    render();
                    updateURL();
                });

                frameworkCheckboxGrid.appendChild(label);
                frameworkCheckboxRefs.set(framework.id, { input, label });
            });
        }

        function applyURLState() {
            const params = new URLSearchParams(window.location.search);
            const refitParam = params.get('refit');
            if (refitParam !== null) {
                state.refit = refitParam === 'true';
            }

            const peersParam = params.get('peers');
            if (state.refit && peersParam) {
                const tokens = peersParam.split(',').map(token => token.trim()).filter(Boolean);
                const validPeers = tokens.filter(token => peerCheckboxRefs.has(token));
                if (validPeers.length >= 2) {
                    state.selectedPeers = new Set(validPeers);
                }
            }

            const frameworksParam = params.get('frameworks');
            if (frameworksParam !== null) {
                if (frameworksParam.trim() === '' || frameworksParam === 'none') {
                    state.selectedFrameworks.clear();
                } else {
                    const selected = frameworksParam.split(',').map(token => token.trim()).filter(Boolean);
                    const valid = selected.filter(token => frameworkCheckboxRefs.has(token));
                    state.selectedFrameworks = new Set(valid);
                }
            }

            const themeParam = params.get('theme');
            if (themeParam && (themeParam === 'light' || themeParam === 'dark')) {
                document.documentElement.setAttribute('data-theme', themeParam);
                localStorage.setItem('theme', themeParam);
                if (typeof updateThemeToggleState === 'function') {
                    updateThemeToggleState(themeParam === 'dark');
                }
            }
        }

        function syncControlState() {
            refitToggle.checked = state.refit;
            peerCheckboxRefs.forEach(({ input, label }, ticker) => {
                const shouldBeChecked = state.selectedPeers.has(ticker);
                if (input.checked !== shouldBeChecked) {
                    input.checked = shouldBeChecked;
                }
                toggleCheckboxDisabled(input, label, !state.refit);
            });
            frameworkCheckboxRefs.forEach(({ input, label }, id) => {
                const shouldBeChecked = state.selectedFrameworks.has(id);
                if (input.checked !== shouldBeChecked) {
                    input.checked = shouldBeChecked;
                }
                updateLabelState(label, { checked: shouldBeChecked, disabled: false });
            });
        }

        function getSelectedPeerData() {
            return peers
                .filter(peer => state.selectedPeers.has(peer.ticker))
                .map(peer => ({ x: peer.rote, y: peer.ptbv, ticker: peer.ticker }));
        }

        function getScatterDatasets() {
            return {
                caty: {
                    id: 'caty',
                    label: 'CATY',
                    type: 'scatter',
                    parsing: false,
                    data: [],
                    pointRadius: 9,
                    pointHoverRadius: 11,
                    pointStyle: 'rectRot',
                    borderWidth: 2,
                    order: 3
                },
                peers: {
                    id: 'peers',
                    label: 'Peers',
                    type: 'scatter',
                    parsing: false,
                    data: [],
                    pointRadius: 7,
                    pointHoverRadius: 9,
                    pointStyle: 'circle',
                    borderWidth: 1.5,
                    order: 1
                },
                regression: {
                    id: 'regression',
                    label: 'Regression line',
                    type: 'line',
                    parsing: false,
                    data: [],
                    borderDash: [6, 4],
                    borderWidth: 2,
                    fill: false,
                    pointRadius: 0,
                    tension: 0,
                    order: 2
                }
            };
        }

        function getBarDatasets() {
            return [{
                id: 'framework-bars',
                label: 'Price ($)',
                parsing: false,
                data: [],
                borderRadius: 6,
                borderWidth: 1.5,
                maxBarThickness: 48
            }];
        }

        const colors = getModuleColors();

        const scatterChart = new Chart(scatterCanvas.getContext('2d'), {
            type: 'scatter',
            data: {
                datasets: Object.values(getScatterDatasets())
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                parsing: false,
                animation: { duration: 0 },
                interaction: {
                    mode: 'nearest',
                    intersect: false
                },
                scales: {
                    x: {
                        type: 'linear',
                        min: 0,
                        max: 18,
                        ticks: {
                            stepSize: 2,
                            callback: (value) => formatPercent(value, 0),
                            color: colors.textSecondary,
                            font: {
                                family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                                size: 12
                            }
                        },
                        title: {
                            display: true,
                            text: 'ROTE (%)',
                            color: colors.textPrimary,
                            font: {
                                size: 13,
                                weight: '600'
                            }
                        },
                        grid: {
                            color: colors.grid,
                            lineWidth: 1
                        }
                    },
                    y: {
                        min: 0.7,
                        max: 2.0,
                        ticks: {
                            stepSize: 0.2,
                            callback: (value) => `${value.toFixed(2)}x`,
                            color: colors.textSecondary,
                            font: {
                                family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                                size: 12
                            }
                        },
                        title: {
                            display: true,
                            text: 'P/TBV (x)',
                            color: colors.textPrimary,
                            font: {
                                size: 13,
                                weight: '600'
                            }
                        },
                        grid: {
                            color: colors.grid,
                            lineWidth: 1
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: {
                            color: colors.textPrimary,
                            font: {
                                family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                                size: 12
                            }
                        }
                    },
                    tooltip: {
                        usePointStyle: true,
                        callbacks: {
                            label(context) {
                                const raw = context.raw || {};
                                if (context.dataset.label === 'Regression line') {
                                    return `Fit ${formatMultiple(context.parsed.y, 3)}`;
                                }
                                const ticker = raw.ticker || context.dataset.label;
                                const rote = raw.x ?? context.parsed.x;
                                const ptbv = raw.y ?? context.parsed.y;
                                const predicted = raw.predicted;
                                const residual = raw.residual;
                                const residualPct = raw.residualPct;
                                const lines = [
                                    `${ticker}`,
                                    `ROTE ${formatPercent(rote)}`,
                                    `P/TBV ${formatMultiple(ptbv)}`
                                ];

                                if (typeof predicted === 'number') {
                                    lines.push(`Fit ${formatMultiple(predicted)}`);
                                }
                                if (typeof residual === 'number') {
                                    lines.push(`Residual ${formatSigned(residual)}`);
                                }
                                if (typeof residualPct === 'number') {
                                    lines.push(`${formatSignedPercent(residualPct)}`);
                                }
                                return lines;
                            }
                        }
                    },
                    scatterLabelPlugin: {
                        labels: []
                    }
                }
            }
        });

        applyLegendSort(scatterChart.options);

        const barChart = new Chart(barCanvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: [],
                datasets: getBarDatasets()
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                parsing: false,
                animation: { duration: 0 },
                scales: {
                    x: {
                        ticks: {
                            color: colors.textSecondary,
                            font: {
                                family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                                size: 12
                            }
                        },
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: true,
                        min: 0,
                        max: 60,
                        ticks: {
                            stepSize: 5,
                            callback: (value) => formatDollar(value, 0),
                            color: colors.textSecondary,
                            font: {
                                family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                                size: 12
                            }
                        },
                        grid: {
                            color: colors.grid,
                            lineWidth: 1
                        },
                        title: {
                            display: true,
                            text: 'Price ($)',
                            color: colors.textPrimary,
                            font: {
                                size: 13,
                                weight: '600'
                            }
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label(context) {
                                const raw = context.raw || {};
                                const value = context.parsed.y;
                                const delta = raw.delta ?? (value - state.spotPrice);
                                const deltaPct = raw.deltaPct ?? ((delta / state.spotPrice) * 100);
                                const note = raw.category || raw.note;
                                const lines = [
                                    `${formatDollar(value)}`
                                ];
                                lines.push(`Δ ${formatSigned(delta, 2, '$')} (${formatSignedPercent(deltaPct)})`);
                                if (note) {
                                    lines.push(note);
                                }
                                return lines;
                            }
                        }
                    },
                    barReferenceLine: {
                        value: state.spotPrice,
                        color: colors.neutral,
                        label: `Spot ${formatDollar(state.spotPrice)}`
                    }
                }
            }
        });

        function applyThemeStyles() {
            const themeColors = getModuleColors();

            // Scatter chart
            const peerDataset = scatterChart.data.datasets.find(dataset => dataset.id === 'peers');
            const catyDataset = scatterChart.data.datasets.find(dataset => dataset.id === 'caty');
            const regressionDataset = scatterChart.data.datasets.find(dataset => dataset.id === 'regression');

            if (peerDataset) {
                peerDataset.backgroundColor = themeColors.peer;
                peerDataset.borderColor = themeColors.peer;
            }
            if (catyDataset) {
                catyDataset.backgroundColor = themeColors.catyFill;
                catyDataset.borderColor = themeColors.catyOutline;
            }
            if (regressionDataset) {
                regressionDataset.borderColor = themeColors.regression;
            }

            if (scatterChart.options.scales?.x) {
                scatterChart.options.scales.x.ticks.color = themeColors.textSecondary;
                scatterChart.options.scales.x.grid.color = themeColors.grid;
                scatterChart.options.scales.x.title.color = themeColors.textPrimary;
            }
            if (scatterChart.options.scales?.y) {
                scatterChart.options.scales.y.ticks.color = themeColors.textSecondary;
                scatterChart.options.scales.y.grid.color = themeColors.grid;
                scatterChart.options.scales.y.title.color = themeColors.textPrimary;
            }
            if (scatterChart.options.plugins?.legend?.labels) {
                scatterChart.options.plugins.legend.labels.color = themeColors.textPrimary;
            }
            if (scatterChart.options.plugins?.tooltip) {
                scatterChart.options.plugins.tooltip.backgroundColor = themeColors.panel;
                scatterChart.options.plugins.tooltip.titleColor = themeColors.textPrimary;
                scatterChart.options.plugins.tooltip.bodyColor = themeColors.textSecondary;
                scatterChart.options.plugins.tooltip.borderColor = themeColors.grid;
            }
            if (scatterChart.options.plugins?.scatterLabelPlugin) {
                scatterChart.options.plugins.scatterLabelPlugin.color = themeColors.textPrimary;
            }

            // Bar chart
            const barDataset = barChart.data.datasets[0];
            if (barDataset && Array.isArray(barDataset.backgroundColor)) {
                barDataset.backgroundColor = barDataset.backgroundColor.map((color, index) => {
                    const raw = barDataset.data[index];
                    if (raw && raw.id === 'spot') {
                        return themeColors.neutral;
                    }
                    const delta = raw ? raw.delta : 0;
                    if (delta > 0.0001) {
                        return themeColors.up;
                    }
                    if (delta < -0.0001) {
                        return themeColors.down;
                    }
                    return themeColors.neutral;
                });
                barDataset.borderColor = barDataset.backgroundColor;
            }

            if (barChart.options.scales?.x) {
                barChart.options.scales.x.ticks.color = themeColors.textSecondary;
            }
            if (barChart.options.scales?.y) {
                barChart.options.scales.y.ticks.color = themeColors.textSecondary;
                barChart.options.scales.y.grid.color = themeColors.grid;
                barChart.options.scales.y.title.color = themeColors.textPrimary;
            }
            if (barChart.options.plugins?.tooltip) {
                barChart.options.plugins.tooltip.backgroundColor = themeColors.panel;
                barChart.options.plugins.tooltip.titleColor = themeColors.textPrimary;
                barChart.options.plugins.tooltip.bodyColor = themeColors.textSecondary;
                barChart.options.plugins.tooltip.borderColor = themeColors.grid;
            }
            if (barChart.options.plugins?.barReferenceLine) {
                barChart.options.plugins.barReferenceLine.color = themeColors.neutral;
            }
        }

        function updateScatterChart(coefficients, usingFixedFallback) {
            const selectedPeers = peers.filter(peer => state.selectedPeers.has(peer.ticker));
            const peerDataset = scatterChart.data.datasets.find(dataset => dataset.id === 'peers');
            const catyDataset = scatterChart.data.datasets.find(dataset => dataset.id === 'caty');
            const regressionDataset = scatterChart.data.datasets.find(dataset => dataset.id === 'regression');

            const peerPoints = selectedPeers.map((peer) => {
                const predicted = coefficients.intercept + coefficients.slope * peer.rote;
                const residual = peer.ptbv - predicted;
                const residualPct = predicted !== 0 ? (residual / predicted) * 100 : null;
                return {
                    x: peer.rote,
                    y: peer.ptbv,
                    ticker: peer.ticker,
                    predicted,
                    residual,
                    residualPct
                };
            });

            const catyPredicted = coefficients.intercept + coefficients.slope * state.caty.rote;
            const catyResidual = state.caty.ptbv - catyPredicted;
            const catyResidualPct = catyPredicted !== 0 ? (catyResidual / catyPredicted) * 100 : null;

            if (peerDataset) {
                peerDataset.data = peerPoints;
            }
            if (catyDataset) {
                catyDataset.data = [{
                    x: state.caty.rote,
                    y: state.caty.ptbv,
                    ticker: 'CATY',
                    predicted: catyPredicted,
                    residual: catyResidual,
                    residualPct: catyResidualPct
                }];
            }
            if (regressionDataset) {
                regressionDataset.data = usingFixedFallback ? [] : computeLinePoints(coefficients, 0, 18);
            }

            const topResidual = peerPoints.reduce((acc, point, index) => {
                if (acc === null || point.residual > acc.value) {
                    return { value: point.residual, index };
                }
                return acc;
            }, null);

            const bottomResidual = peerPoints.reduce((acc, point, index) => {
                if (acc === null || point.residual < acc.value) {
                    return { value: point.residual, index };
                }
                return acc;
            }, null);

            const labels = [];
            if (catyDataset && catyDataset.data.length) {
                labels.push({
                    datasetId: 'caty',
                    index: 0,
                    label: 'CATY'
                });
            }
            if (peerDataset && peerDataset.data.length && topResidual) {
                const point = peerDataset.data[topResidual.index];
                labels.push({
                    datasetId: 'peers',
                    index: topResidual.index,
                    label: `${point.ticker} ${formatSigned(point.residual)}`
                });
            }
            if (peerDataset && peerDataset.data.length && bottomResidual && topResidual && bottomResidual.index !== topResidual.index) {
                const point = peerDataset.data[bottomResidual.index];
                labels.push({
                    datasetId: 'peers',
                    index: bottomResidual.index,
                    label: `${point.ticker} ${formatSigned(point.residual)}`
                });
            }

            scatterChart.options.plugins.scatterLabelPlugin.labels = labels;
            applyThemeStyles();
            scatterChart.update('none');

            updateAnnotation(catyPredicted, catyResidual, catyResidualPct);
        }

        function computeFrameworkOrder() {
            const included = state.frameworks
                .filter(item => item.id === 'spot' || state.selectedFrameworks.has(item.id));

            const spotItem = included.find(item => item.id === 'spot');

            const nonSpot = included.filter(item => item.id !== 'spot');
            const sorted = nonSpot.map((item) => {
                const delta = item.price - state.spotPrice;
                const deltaPct = state.spotPrice !== 0 ? (delta / state.spotPrice) * 100 : 0;
                return {
                    ...item,
                    delta,
                    deltaPct
                };
            }).sort((a, b) => {
                const absA = Math.abs(a.delta);
                const absB = Math.abs(b.delta);
                if (absA !== absB) {
                    return absB - absA;
                }
                const orderA = DEFAULT_FRAMEWORK_ORDER.indexOf(a.id);
                const orderB = DEFAULT_FRAMEWORK_ORDER.indexOf(b.id);
                return orderA - orderB;
            });

            if (spotItem) {
                sorted.push({
                    ...spotItem,
                    delta: 0,
                    deltaPct: 0
                });
            }

            return sorted;
        }

        function chooseBarColor(delta) {
            const themeColors = getModuleColors();
            if (Math.abs(delta) < 0.0001) {
                return themeColors.neutral;
            }
            if (delta > 0) {
                return themeColors.up;
            }
            return themeColors.down;
        }

        function updateBarChart() {
            const orderedFrameworks = computeFrameworkOrder();
            const barDataset = barChart.data.datasets[0];
            const labels = orderedFrameworks.map(item => item.label);

            barChart.data.labels = labels;
            barDataset.data = orderedFrameworks.map((item) => ({
                x: item.label,
                y: item.price,
                delta: item.delta,
                deltaPct: item.deltaPct,
                id: item.id,
                category: item.category,
                note: item.simulated ? 'Simulated' : null
            }));

            barDataset.backgroundColor = orderedFrameworks.map((item) => {
                if (item.id === 'spot') {
                    return getModuleColors().neutral;
                }
                return chooseBarColor(item.delta);
            });
            barDataset.borderColor = barDataset.backgroundColor.slice();

            const maxPrice = orderedFrameworks.reduce((acc, item) => Math.max(acc, item.price), state.spotPrice);
            const paddedMax = Math.max(60, Math.ceil((maxPrice + 2) / 5) * 5);
            if (barChart.options.scales?.y) {
                barChart.options.scales.y.max = paddedMax;
            }

            if (barChart.options.plugins?.barReferenceLine) {
                barChart.options.plugins.barReferenceLine.value = state.spotPrice;
                barChart.options.plugins.barReferenceLine.label = `Spot ${formatDollar(state.spotPrice)}`;
            }

            applyThemeStyles();
            barChart.update('none');
        }

        function updateAnnotation(predicted, residual, residualPct) {
            const predictedEl = catyAnnotation.querySelector('.annotation-predicted');
            if (predictedEl) {
                predictedEl.textContent = formatMultiple(predicted);
            }
            const residualPctText = typeof residualPct === 'number' ? formatSignedPercent(residualPct) : '';
            catyAnnotation.innerHTML = `CATY actual ${formatMultiple(state.caty.ptbv)} vs fit <span class="annotation-predicted">${formatMultiple(predicted)}</span> → residual ${formatSigned(residual)} (${residualPctText}).`;
        }

        function updateTables() {
            const peerTbody = peerTable.querySelector('tbody');
            peerTbody.innerHTML = '';

            peers.forEach((peer) => {
                const included = state.selectedPeers.has(peer.ticker);
                const predicted = state.currentCoefficients.intercept + state.currentCoefficients.slope * peer.rote;
                const residual = peer.ptbv - predicted;
                const row = document.createElement('tr');
                if (!included) {
                    row.classList.add('is-excluded');
                }

                row.innerHTML = `
                    <td>${peer.ticker}</td>
                    <td data-align="right">${formatPercent(peer.rote)}</td>
                    <td data-align="right">${formatMultiple(peer.ptbv)}</td>
                    <td data-align="right">${formatMultiple(predicted)}</td>
                    <td data-align="right">${formatSigned(residual)}</td>
                    <td>${included ? 'Yes' : 'No'}</td>
                `;

                peerTbody.appendChild(row);
            });

            const catyRow = document.createElement('tr');
            const predicted = state.currentCoefficients.intercept + state.currentCoefficients.slope * state.caty.rote;
            const residual = state.caty.ptbv - predicted;
            catyRow.innerHTML = `
                <td>CATY</td>
                <td data-align="right">${formatPercent(state.caty.rote)}</td>
                <td data-align="right">${formatMultiple(state.caty.ptbv)}</td>
                <td data-align="right">${formatMultiple(predicted)}</td>
                <td data-align="right">${formatSigned(residual)}</td>
                <td>Overlay</td>
            `;
            peerTbody.appendChild(catyRow);

            const frameworkTbody = frameworkTable.querySelector('tbody');
            frameworkTbody.innerHTML = '';

            const orderedForTable = [
                ...computeFrameworkOrder(),
                ...state.frameworks.filter(item => item.id !== 'spot' && !state.selectedFrameworks.has(item.id))
            ];

            orderedForTable.forEach((framework) => {
                const included = framework.id === 'spot' || state.selectedFrameworks.has(framework.id);
                const delta = framework.price - state.spotPrice;
                const deltaPct = state.spotPrice !== 0 ? (delta / state.spotPrice) * 100 : 0;
                const row = document.createElement('tr');
                if (!included) {
                    row.classList.add('is-excluded');
                }
                row.innerHTML = `
                    <td>${formatFrameworkLabel(framework)}</td>
                    <td data-align="right">${formatDollar(framework.price)}</td>
                    <td data-align="right">${formatSigned(delta, 2, '$')}</td>
                    <td data-align="right">${formatSignedPercent(deltaPct)}</td>
                    <td>${included ? 'Yes' : 'No'}</td>
                `;

                frameworkTbody.appendChild(row);
            });
        }

        function updateRegressionSummary(usingFixedFallback) {
            const coeffs = state.currentCoefficients;
            const peersIncluded = state.selectedPeers.size;
            const slopeText = coeffs ? coeffs.slope.toFixed(3) : 'n/a';
            const interceptText = coeffs ? coeffs.intercept.toFixed(2) : 'n/a';
            const rSquaredText = coeffs && typeof coeffs.rSquared === 'number'
                ? coeffs.rSquared.toFixed(2)
                : (state.refit ? 'n/a' : fixedCoefficients.rSquared.toFixed(2));

            let summary = `y = ${slopeText} × ROTE + ${interceptText} (R² = ${rSquaredText}; n = ${peersIncluded})`;
            const details = [];

            if (state.refit && !usingFixedFallback) {
                details.push('Refit on current selection');
            } else if (usingFixedFallback) {
                details.push('Refit unavailable (<2 peers); showing fixed coefficients');
            } else {
                details.push('Fixed coefficients');
            }

            regressionSummary.textContent = `${summary}; ${details.join(' • ')}`;
            regressionSummary.classList.toggle('text-danger', usingFixedFallback);
        }

        function updatePeerCountLabel() {
            peerCountLabel.textContent = state.selectedPeers.size;
        }

        function updateURL() {
            const params = new URLSearchParams(window.location.search);
            if (state.refit) {
                params.set('refit', 'true');
                params.set('peers', Array.from(state.selectedPeers).join(','));
            } else {
                params.delete('refit');
                params.delete('peers');
            }

            if (state.selectedFrameworks.size === selectableFrameworkIds.length) {
                params.delete('frameworks');
            } else if (state.selectedFrameworks.size === 0) {
                params.set('frameworks', 'none');
            } else {
                params.set('frameworks', Array.from(state.selectedFrameworks).join(','));
            }

            const theme = document.documentElement.getAttribute('data-theme');
            if (theme) {
                params.set('theme', theme);
            }

            const query = params.toString();
            const newUrl = `${window.location.pathname}${query ? `?${query}` : ''}${window.location.hash}`;
            window.history.replaceState(null, '', newUrl);
        }

        function clearShareFeedback() {
            if (state.shareFeedbackTimeout) {
                window.clearTimeout(state.shareFeedbackTimeout);
            }
            shareFeedback.textContent = '';
        }

        async function handleExportPNG() {
            try {
                const scatterCanvas = scatterChart.canvas;
                const barCanvas = barChart.canvas;
                const padding = 40;
                const gap = 40;
                const width = scatterCanvas.width + barCanvas.width + gap + padding * 2;
                const height = Math.max(scatterCanvas.height, barCanvas.height) + padding * 2;

                const exportCanvas = document.createElement('canvas');
                exportCanvas.width = width;
                exportCanvas.height = height;
                const ctx = exportCanvas.getContext('2d');
                const themeColors = getModuleColors();
                ctx.fillStyle = themeColors.panel;
                ctx.fillRect(0, 0, width, height);
                ctx.fillStyle = themeColors.textPrimary;
                ctx.font = '18px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
                ctx.fillText('CATY Valuation vs Profitability and Framework Targets', padding, padding - 12);

                const scatterImage = new Image();
                scatterImage.src = scatterCanvas.toDataURL('image/png');
                const barImage = new Image();
                barImage.src = barCanvas.toDataURL('image/png');

                await Promise.all([
                    scatterImage.decode ? scatterImage.decode().catch(() => null) : null,
                    barImage.decode ? barImage.decode().catch(() => null) : null
                ]);

                ctx.drawImage(scatterImage, padding, padding);
                ctx.drawImage(barImage, padding + scatterCanvas.width + gap, padding);

                const link = document.createElement('a');
                link.href = exportCanvas.toDataURL('image/png');
                link.download = 'caty-valuation-decision.png';
                link.click();
            } catch (error) {
                console.error('PNG export failed', error);
            }
        }

        function handleExportCSV() {
            const lines = [];
            const coeffs = state.currentCoefficients;

            lines.push('"Peer Scatter"');
            lines.push('"Ticker","ROTE (%)","P/TBV (x)","Predicted P/TBV (x)","Residual (x)","Included"');
            peers.forEach((peer) => {
                const predicted = coeffs.intercept + coeffs.slope * peer.rote;
                const residual = peer.ptbv - predicted;
                const included = state.selectedPeers.has(peer.ticker) ? 'Yes' : 'No';
                lines.push(`"${peer.ticker}","${peer.rote.toFixed(2)}","${peer.ptbv.toFixed(3)}","${predicted.toFixed(3)}","${residual.toFixed(3)}","${included}"`);
            });
            const catyPredicted = coeffs.intercept + coeffs.slope * state.caty.rote;
            const catyResidual = state.caty.ptbv - catyPredicted;
            lines.push(`"CATY","${state.caty.rote.toFixed(2)}","${state.caty.ptbv.toFixed(3)}","${catyPredicted.toFixed(3)}","${catyResidual.toFixed(3)}","Overlay"`);
            lines.push('');
            lines.push('"Regression Summary","Slope","Intercept","R^2","Peers","Source"');
            const sourceLabel = state.coefficientsSource === 'refit'
                ? 'Refit'
                : (state.coefficientsSource === 'refit-fallback' ? 'Fixed fallback (<2 peers)' : 'Fixed');
            lines.push(`"Coefficients","${coeffs.slope.toFixed(3)}","${coeffs.intercept.toFixed(2)}","${(coeffs.rSquared ?? fixedCoefficients.rSquared).toFixed(2)}","${state.selectedPeers.size}","${sourceLabel}"`);
            lines.push('');
            lines.push('"Framework Bars"');
            lines.push('"Framework","Price ($)","Δ vs Spot ($)","Δ vs Spot (%)","Included","Notes"');
            state.frameworks.forEach((framework) => {
                const delta = framework.price - state.spotPrice;
                const deltaPct = state.spotPrice !== 0 ? (delta / state.spotPrice) * 100 : 0;
                const included = framework.id === 'spot' || state.selectedFrameworks.has(framework.id) ? 'Yes' : 'No';
                const noteParts = [];
                if (framework.category && framework.category !== 'Reference') {
                    noteParts.push(framework.category);
                }
                if (framework.simulated) {
                    noteParts.push('Simulated');
                }
                lines.push(`"${framework.label}","${framework.price.toFixed(2)}","${delta.toFixed(2)}","${deltaPct.toFixed(1)}","${included}","${noteParts.join(' ')}"`);
            });

            const blob = new Blob([lines.join('\n')], { type: 'text/csv;charset=utf-8;' });
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = 'caty-valuation-decision.csv';
            link.click();
            URL.revokeObjectURL(link.href);
        }

        async function handleShareLink() {
            updateURL();
            const url = window.location.href;
            try {
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    await navigator.clipboard.writeText(url);
                    shareFeedback.textContent = 'Link copied to clipboard.';
                } else {
                    throw new Error('Clipboard API unavailable');
                }
            } catch (error) {
                console.warn('Clipboard copy failed, fallback to prompt', error);
                window.prompt('Copy this link:', url); // eslint-disable-line no-alert
                shareFeedback.textContent = 'Link ready – copied manually.';
            }

            if (state.shareFeedbackTimeout) {
                window.clearTimeout(state.shareFeedbackTimeout);
            }
            state.shareFeedbackTimeout = window.setTimeout(() => {
                shareFeedback.textContent = '';
            }, 4000);
        }

        function handleReset() {
            clearShareFeedback();
            state.refit = false;
            state.selectedPeers = new Set(peers.map(peer => peer.ticker));
            state.selectedFrameworks = new Set(selectableFrameworkIds);
            state.currentCoefficients = state.fixedCoefficients;
            state.coefficientsSource = 'fixed';
            syncControlState();
            render();
            updateURL();
        }

        function render() {
            clearShareFeedback();

            if (!state.refit) {
                state.selectedPeers = new Set(peers.map(peer => peer.ticker));
                syncControlState();
            } else {
                peerCheckboxRefs.forEach(({ input, label }, ticker) => {
                    toggleCheckboxDisabled(input, label, false);
                    input.checked = state.selectedPeers.has(ticker);
                    updateLabelState(label, { checked: input.checked, disabled: false });
                });
            }

            const selectedPeerData = getSelectedPeerData();
            let coefficients = state.fixedCoefficients;
            let usingFixedFallback = false;

            if (state.refit) {
                const regression = computeRegression(selectedPeerData);
                if (regression) {
                    coefficients = regression;
                    state.coefficientsSource = 'refit';
                } else {
                    coefficients = state.fixedCoefficients;
                    state.coefficientsSource = 'refit-fallback';
                    usingFixedFallback = true;
                }
            } else {
                state.coefficientsSource = 'fixed';
            }

            state.currentCoefficients = coefficients;

            updateScatterChart(coefficients, usingFixedFallback);
            updateBarChart();
            updateTables();
            updateRegressionSummary(usingFixedFallback && state.refit);
            updatePeerCountLabel();
        }

        // Initialise controls and state
        buildPeerControls();
        buildFrameworkControls();
        applyURLState();
        syncControlState();
        render();
        applyThemeStyles();

        refitToggle.addEventListener('change', () => {
            state.refit = refitToggle.checked;
            if (!state.refit) {
                state.selectedPeers = new Set(peers.map(peer => peer.ticker));
            }
            syncControlState();
            render();
            updateURL();
        });

        resetButton.addEventListener('click', handleReset);
        exportPngButton.addEventListener('click', handleExportPNG);
        exportCsvButton.addEventListener('click', handleExportCSV);
        shareButton.addEventListener('click', handleShareLink);

        window.refreshValuationModuleTheme = () => {
            applyThemeStyles();
            scatterChart.update('none');
            barChart.update('none');
        };

        return [scatterChart, barChart];
    }

    window.initValuationDecisionModule = initValuationDecisionModule;
})();
