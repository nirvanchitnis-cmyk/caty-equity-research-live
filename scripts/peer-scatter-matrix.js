/* global Chart */
(function() {
    'use strict';

    const DATA_URL = 'data/caty11_peers_normalized.json';

    const SELECTORS = {
        canvas: 'peerScatterChart',
        xAxis: 'peerXAxisSelect',
        yAxis: 'peerYAxisSelect',
        toggleRegression: 'peerToggleRegression',
        toggleLabels: 'peerToggleLabels',
        toggleMedians: 'peerToggleMedians',
        toggleHope: 'peerToggleHope',
        exportPng: 'peerScatterExportPng',
        exportCsv: 'peerScatterExportCsv',
        tableBody: 'peerScatterTableBody',
        status: 'peerToggleStatus'
    };

    const CONSTANTS = {
        pngWidth: 1200,
        pngHeight: 900,
        minRadius: 6,
        maxRadius: 20,
        regressionAxes: { x: 'rote_pct', y: 'p_tbv' },
        axisPadding: 0.02
    };

    const AXIS_CONFIG = {
        rote_pct: {
            key: 'rote_pct',
            label: 'Return on Tangible Equity (%)',
            shortLabel: 'ROTE',
            min: 0,
            max: 18,
            stepSize: 2,
            formatTick: value => `${value}%`,
            formatTooltip: value => `${toFixed(value, 2)}%`,
            formatLabel: value => `${toFixed(value, 2)}%`
        },
        p_tbv: {
            key: 'p_tbv',
            label: 'Price / Tangible Book Value (×)',
            shortLabel: 'P/TBV',
            min: 0.6,
            max: 2.0,
            stepSize: 0.2,
            formatTick: value => `${toFixed(value, 1)}×`,
            formatTooltip: value => `${toFixed(value, 3)}×`,
            formatLabel: value => `${toFixed(value, 3)}×`
        },
        cre_pct: {
            key: 'cre_pct',
            label: 'Commercial Real Estate Exposure (%)',
            shortLabel: 'CRE',
            min: 0,
            max: 85,
            stepSize: 15,
            formatTick: value => `${value}%`,
            formatTooltip: value => `${toFixed(value, 1)}%`,
            formatLabel: value => `${toFixed(value, 1)}%`
        },
        mkt_cap: {
            key: 'mkt_cap',
            label: 'Market Capitalization ($ billions)',
            shortLabel: 'MarketCap',
            min: 0,
            max: 16,
            stepSize: 4,
            formatTick: value => `$${toFixed(value, 0)}B`,
            formatTooltip: value => `$${toFixed(value, 2)}B`,
            formatLabel: value => `$${toFixed(value, 2)}B`
        }
    };

    const state = {
        chart: null,
        peers: [],
        visiblePeers: [],
        regressionPeers: new Set(),
        excludedPeers: new Set(),
        xAxis: CONSTANTS.regressionAxes.x,
        yAxis: CONSTANTS.regressionAxes.y,
        showRegression: true,
        regressionPreference: true,
        showAllLabels: false,
        showMedians: false,
        includeHope: false,
        medians: {},
        regression: {
            intercept: 0,
            slope: 0,
            rSquared: 0,
            sampleSize: 0,
            equation: '',
            summary: ''
        },
        residualStd: 0,
        marketCapRange: { min: Number.POSITIVE_INFINITY, max: Number.NEGATIVE_INFINITY }
    };

    const peerRegressionPlugin = {
        id: 'peerRegressionPlugin',
        afterDatasetsDraw(chart) {
            if (!state.showRegression) {
                return;
            }

            if (state.xAxis !== CONSTANTS.regressionAxes.x || state.yAxis !== CONSTANTS.regressionAxes.y) {
                return;
            }

            if (!state.chart || !Number.isFinite(state.regression.slope) || !Number.isFinite(state.regression.intercept)) {
                return;
            }

            const { ctx, chartArea, scales } = chart;
            const xScale = scales.x;
            const yScale = scales.y;

            if (!xScale || !yScale) {
                return;
            }

            const xMin = xScale.min;
            const xMax = xScale.max;
            const intercept = state.regression.intercept;
            const slope = state.regression.slope;

            const lineColor = getCssVar('--peer-regression') || '#2F6690';
            const bandColor = getCssVar('--peer-confidence') || 'rgba(122, 136, 147, 0.12)';

            if (Number.isFinite(state.residualStd) && state.residualStd > 0) {
                const upperPoints = [];
                const lowerPoints = [];
                const steps = 40;
                for (let index = 0; index <= steps; index += 1) {
                    const ratio = index / steps;
                    const xValue = xMin + (xMax - xMin) * ratio;
                    const fitted = intercept + slope * xValue;
                    const upper = yScale.getPixelForValue(fitted + state.residualStd);
                    const lower = yScale.getPixelForValue(fitted - state.residualStd);

                    upperPoints.push({ x: xScale.getPixelForValue(xValue), y: upper });
                    lowerPoints.push({ x: xScale.getPixelForValue(xValue), y: lower });
                }

                ctx.save();
                ctx.beginPath();
                upperPoints.forEach((point, index) => {
                    if (index === 0) {
                        ctx.moveTo(point.x, point.y);
                    } else {
                        ctx.lineTo(point.x, point.y);
                    }
                });

                for (let index = lowerPoints.length - 1; index >= 0; index -= 1) {
                    const point = lowerPoints[index];
                    ctx.lineTo(point.x, point.y);
                }

                ctx.closePath();
                ctx.fillStyle = bandColor;
                ctx.fill();
                ctx.restore();
            }

            const start = {
                x: xScale.getPixelForValue(xMin),
                y: yScale.getPixelForValue(intercept + slope * xMin)
            };
            const end = {
                x: xScale.getPixelForValue(xMax),
                y: yScale.getPixelForValue(intercept + slope * xMax)
            };

            ctx.save();
            ctx.beginPath();
            ctx.strokeStyle = lineColor;
            ctx.lineWidth = 2;
            ctx.moveTo(start.x, start.y);
            ctx.lineTo(end.x, end.y);
            ctx.stroke();
            ctx.restore();

            const textColor = getCssVar('--text-secondary') || '#4F5B67';
            const summary = [
                state.regression.equation || `P/TBV = ${toFixed(intercept, 3)} + ${toFixed(slope, 3)} × ROTE`,
                `R² = ${toFixed(state.regression.rSquared, 3)}`,
                `n = ${state.regression.sampleSize}`
            ];

            ctx.save();
            ctx.fillStyle = textColor;
            ctx.font = '600 11px "Inter", "Helvetica Neue", Arial, sans-serif';
            ctx.textAlign = 'right';
            ctx.textBaseline = 'bottom';

            const padding = 8;
            let textY = chartArea.top + 12;
            summary.forEach(line => {
                ctx.fillText(line, chartArea.right - padding, textY);
                textY += 14;
            });
            ctx.restore();
        }
    };

    const peerLabelsPlugin = {
        id: 'peerLabelsPlugin',
        afterDatasetsDraw(chart) {
            const dataset = chart.data.datasets[0];
            const meta = chart.getDatasetMeta(0);

            if (!dataset || !meta) {
                return;
            }

            const ctx = chart.ctx;
            ctx.save();

            meta.data.forEach((element, index) => {
                if (!element || element.skip) {
                    return;
                }

                const dataPoint = dataset.data[index];
                if (!dataPoint || !dataPoint.peer) {
                    return;
                }

                const { peer } = dataPoint;
                const alwaysShow = peer.ticker === 'CATY';
                if (!alwaysShow && !state.showAllLabels) {
                    return;
                }

                const { x, y } = element.tooltipPosition();
                const offset = peer.ticker === 'CATY' ? 12 : 10;
                ctx.font = peer.ticker === 'CATY'
                    ? '700 12px "Inter", "Helvetica Neue", Arial, sans-serif'
                    : '600 10px "Inter", "Helvetica Neue", Arial, sans-serif';
                ctx.textAlign = 'center';
                ctx.textBaseline = 'top';
                ctx.fillStyle = peer.ticker === 'CATY'
                    ? (getCssVar('--peer-caty-border') || '#8B7355')
                    : (getCssVar('--text-primary') || '#14202D');

                ctx.fillText(peer.ticker, x, y + offset);
            });

            ctx.restore();
        }
    };

    const peerReferenceLinesPlugin = {
        id: 'peerReferenceLinesPlugin',
        afterDatasetsDraw(chart) {
            const { showMedians } = state;
            const { ctx, chartArea, scales } = chart;
            const xScale = scales.x;
            const yScale = scales.y;

            if (!xScale || !yScale) {
                return;
            }

            const medianColor = getCssVar('--peer-median') || 'rgba(122, 136, 147, 0.5)';
            const labelColor = getCssVar('--text-secondary') || '#4F5B67';

            ctx.save();
            ctx.lineWidth = 1;
            ctx.setLineDash([6, 4]);

            if (showMedians) {
                const xMedian = getMedianValue(state.xAxis);
                if (Number.isFinite(xMedian) && xMedian >= xScale.min && xMedian <= xScale.max) {
                    const pixel = xScale.getPixelForValue(xMedian);
                    ctx.beginPath();
                    ctx.strokeStyle = medianColor;
                    ctx.moveTo(pixel, chartArea.top);
                    ctx.lineTo(pixel, chartArea.bottom);
                    ctx.stroke();

                    ctx.font = '600 11px "Inter", "Helvetica Neue", Arial, sans-serif';
                    ctx.fillStyle = labelColor;
                    ctx.textBaseline = 'top';
                    ctx.textAlign = pixel > (chartArea.left + chartArea.width / 2) ? 'right' : 'left';
                    const label = `Median ${AXIS_CONFIG[state.xAxis].shortLabel}: ${AXIS_CONFIG[state.xAxis].formatLabel(xMedian)}`;
                    const labelOffset = ctx.textAlign === 'right' ? -8 : 8;
                    ctx.fillText(label, pixel + labelOffset, chartArea.top + 6);
                }

                const yMedian = getMedianValue(state.yAxis);
                if (Number.isFinite(yMedian) && yMedian >= yScale.min && yMedian <= yScale.max) {
                    const pixel = yScale.getPixelForValue(yMedian);
                    ctx.beginPath();
                    ctx.strokeStyle = medianColor;
                    ctx.moveTo(chartArea.left, pixel);
                    ctx.lineTo(chartArea.right, pixel);
                    ctx.stroke();

                    ctx.font = '600 11px "Inter", "Helvetica Neue", Arial, sans-serif';
                    ctx.fillStyle = labelColor;
                    ctx.textBaseline = pixel < (chartArea.top + chartArea.height / 2) ? 'top' : 'bottom';
                    ctx.textAlign = 'left';
                    const label = `Median ${AXIS_CONFIG[state.yAxis].shortLabel}: ${AXIS_CONFIG[state.yAxis].formatLabel(yMedian)}`;
                    const yOffset = ctx.textBaseline === 'top' ? 6 : -6;
                    ctx.fillText(label, chartArea.left + 8, pixel + yOffset);
                }
            }

            ctx.restore();
        }
    };

    async function initPeerScatterMatrix() {
        const canvas = document.getElementById(SELECTORS.canvas);
        if (!canvas || typeof Chart === 'undefined') {
            return;
        }

        try {
            const data = await loadData();
            prepareState(data);
            bindAxisControls();
            bindToggleControls();
            bindExports();
            createChart(canvas);
            applyURLState();
            updateRegressionAvailability();
            updateTable();
            observeThemeChanges();
        } catch (error) {
            console.error('Peer scatter matrix failed to initialise', error);
        }
    }

    async function loadData() {
        const response = await fetch(DATA_URL, { cache: 'no-store' });
        if (!response.ok) {
            throw new Error(`Failed to load peer data (${response.status})`);
        }
        return response.json();
    }

    function prepareState(payload) {
        const peerData = payload.peer_data || {};
        const regressionUniverse = payload.regression_universe || {};
        const regressionPeers = new Set(regressionUniverse.regression_peers || []);
        const excludedPeers = new Set(Object.keys(regressionUniverse.excluded_peers || {}));
        const members = payload.summary?.peer_universe_members || [];

        state.regressionPeers = regressionPeers;
        state.excludedPeers = excludedPeers;

        const ordering = ['CATY']
            .concat(Array.from(regressionPeers))
            .concat(members)
            .filter((ticker, index, array) => array.indexOf(ticker) === index);

        state.peers = ordering
            .map(ticker => {
                const info = peerData[ticker];
                if (!info) {
                    return null;
                }

                const marketCap = Number(info.mkt_cap_millions);
                if (Number.isFinite(marketCap) && marketCap > 0) {
                    state.marketCapRange.min = Math.min(state.marketCapRange.min, marketCap);
                    state.marketCapRange.max = Math.max(state.marketCapRange.max, marketCap);
                }

                return {
                    ticker,
                    name: info.name || ticker,
                    rote_pct: toNumber(info.rote_pct),
                    p_tbv: toNumber(info.p_tbv),
                    cre_pct: toNumber(info.cre_pct),
                    mkt_cap_millions: toNumber(info.mkt_cap_millions),
                    price: toNumber(info.price),
                    tbvps: toNumber(info.tbvps),
                    fitted_p_tbv: toNumber(info.fitted_p_tbv),
                    residual: toNumber(info.residual),
                    cooks_d: toNumber(info.cooks_d),
                    note: info.note || '',
                    status: determineStatus(ticker, regressionPeers, excludedPeers),
                    isTarget: ticker === 'CATY',
                    isRegressionPeer: regressionPeers.has(ticker),
                    isExcluded: excludedPeers.has(ticker)
                };
            })
            .filter(Boolean);

        state.regression = {
            intercept: toNumber(payload.regression_stats?.intercept),
            slope: toNumber(payload.regression_stats?.slope),
            rSquared: toNumber(payload.regression_stats?.r_squared),
            sampleSize: toNumber(payload.regression_stats?.sample_size),
            equation: payload.regression_stats?.equation || '',
            summary: payload.regression_stats?.scatter_summary_html || ''
        };

        state.medians = {
            rote_pct: toNumber(payload.distribution_analysis?.rote_pct?.median),
            p_tbv: toNumber(payload.distribution_analysis?.p_tbv?.median),
            cre_pct: toNumber(payload.distribution_analysis?.cre_pct?.median),
            mkt_cap: toNumber(payload.distribution_analysis?.mkt_cap_millions?.median) / 1000
        };

        state.residualStd = computeResidualStd();

        if (!Number.isFinite(state.marketCapRange.min) || !Number.isFinite(state.marketCapRange.max)) {
            state.marketCapRange.min = 200;
            state.marketCapRange.max = 15000;
        }
    }

    function determineStatus(ticker, regressionPeers, excludedPeers) {
        if (ticker === 'CATY') {
            return 'Target';
        }
        if (excludedPeers.has(ticker)) {
            return 'Excluded';
        }
        if (regressionPeers.has(ticker)) {
            return 'Peer (Regression)';
        }
        return 'Peer';
    }

    function computeResidualStd() {
        const residuals = state.peers
            .filter(peer => peer.ticker !== 'CATY' && peer.isRegressionPeer && Number.isFinite(peer.residual))
            .map(peer => peer.residual);

        if (residuals.length <= 2) {
            return 0;
        }

        const sumSquares = residuals.reduce((total, value) => total + (value * value), 0);
        const variance = sumSquares / (residuals.length - 2);
        return Math.sqrt(Math.max(variance, 0));
    }

    function createChart(canvas) {
        const ctx = canvas.getContext('2d');

        const dataset = {
            label: 'Peers',
            data: buildDatasetData(),
            parsing: false,
            pointBackgroundColor: context => {
                const peer = context.raw?.peer;
                if (!peer) {
                    return getCssVar('--peer-excluded') || '#7A8893';
                }
                const baseColor = getCreColor(peer.cre_pct);
                const alpha = peer.ticker === 'CATY' ? 0.9 : 0.75;
                return applyOpacity(baseColor, alpha);
            },
            pointBorderColor: context => {
                const peer = context.raw?.peer;
                if (!peer) {
                    return getCssVar('--border-color') || '#D6DADD';
                }

                if (peer.ticker === 'CATY') {
                    return getCssVar('--peer-caty-border') || '#8B7355';
                }

                if (peer.isExcluded) {
                    return getCssVar('--peer-excluded') || '#7A8893';
                }

                return getCssVar('--border-color') || '#D6DADD';
            },
            pointBorderWidth: context => {
                const peer = context.raw?.peer;
                if (!peer) {
                    return 1;
                }
                if (peer.ticker === 'CATY') {
                    return 3;
                }
                if (peer.isExcluded) {
                    return 2;
                }
                return 1.5;
            },
            pointBorderDash: context => {
                const peer = context.raw?.peer;
                if (peer && peer.isExcluded) {
                    return [6, 4];
                }
                return undefined;
            },
            pointStyle: context => (context.raw?.peer?.ticker === 'CATY' ? 'rectRot' : 'circle'),
            hoverRadius: context => {
                const radius = context.raw?.r;
                return Number.isFinite(radius) ? radius + 4 : 8;
            },
            clip: false
        };

        state.chart = new Chart(ctx, {
            type: 'bubble',
            data: {
                datasets: [dataset]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                parsing: false,
                normalized: true,
                animation: false,
                layout: {
                    padding: {
                        top: 32,
                        right: 36,
                        bottom: 36,
                        left: 48
                    }
                },
                scales: {
                    x: buildScaleOptions('x', state.xAxis),
                    y: buildScaleOptions('y', state.yAxis)
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        enabled: true,
                        displayColors: false,
                        padding: 12,
                        callbacks: {
                            title: items => formatTooltipTitle(items),
                            label: context => buildTooltipLines(context)
                        }
                    }
                }
            },
            plugins: [peerRegressionPlugin, peerLabelsPlugin, peerReferenceLinesPlugin]
        });
    }

    function buildDatasetData() {
        const includeHope = state.includeHope;
        const data = [];
        const visible = [];

        state.peers.forEach(peer => {
            if (peer.ticker === 'HOPE' && !includeHope) {
                return;
            }

            const xValue = getAxisValue(peer, state.xAxis);
            const yValue = getAxisValue(peer, state.yAxis);

            if (!Number.isFinite(xValue) || !Number.isFinite(yValue)) {
                return;
            }

            const radius = getBubbleRadius(peer.mkt_cap_millions);
            data.push({
                x: xValue,
                y: yValue,
                r: radius,
                peer
            });
            visible.push(peer);
        });

        state.visiblePeers = visible;
        return data;
    }

    function buildScaleOptions(axisId, axisKey) {
        const config = AXIS_CONFIG[axisKey];
        const isXAxis = axisId === 'x';
        const color = getCssVar('--text-secondary') || '#4F5B67';
        const borderColor = getCssVar('--border-color') || '#D6DADD';

        return {
            type: 'linear',
            position: isXAxis ? 'bottom' : 'left',
            min: config.min,
            max: config.max,
            grid: {
                color: withOpacity(borderColor, 0.35),
                lineWidth: 1
            },
            ticks: {
                stepSize: config.stepSize,
                color,
                padding: 10,
                callback: value => config.formatTick(Number(value))
            },
            title: {
                display: true,
                text: config.label,
                color,
                font: {
                    weight: '600',
                    size: 13
                }
            }
        };
    }

    function updateChart() {
        if (!state.chart) {
            return;
        }

        const dataset = state.chart.data.datasets[0];
        dataset.data = buildDatasetData();

        state.chart.options.scales.x = buildScaleOptions('x', state.xAxis);
        state.chart.options.scales.y = buildScaleOptions('y', state.yAxis);

        state.chart.update('none');
        updateTable();
        updateURL();
    }

    function applyURLState() {
        const params = new URLSearchParams(window.location.search);
        const xa = params.get('x');
        const ya = params.get('y');
        if (AXIS_CONFIG[xa]) {
            state.xAxis = xa;
        }
        if (AXIS_CONFIG[ya]) {
            state.yAxis = ya;
        }
        state.showRegression = params.get('reg') === '1' ? true : state.regressionPreference;
        state.showAllLabels = params.get('lab') === '1';
        state.showMedians = params.get('med') === '1';
        state.includeHope = params.get('hope') === '1';
    }

    function updateURL() {
        const params = new URLSearchParams(window.location.search);
        params.set('x', state.xAxis);
        params.set('y', state.yAxis);
        params.set('reg', state.showRegression ? '1' : '0');
        params.set('lab', state.showAllLabels ? '1' : '0');
        params.set('med', state.showMedians ? '1' : '0');
        params.set('hope', state.includeHope ? '1' : '0');
        history.replaceState(null, '', `${location.pathname}?${params.toString()}`);
    }

    function bindAxisControls() {
        const xSelect = document.getElementById(SELECTORS.xAxis);
        const ySelect = document.getElementById(SELECTORS.yAxis);

        if (xSelect) {
            xSelect.value = state.xAxis;
            xSelect.addEventListener('change', event => {
                const nextValue = event.target.value;
                if (!AXIS_CONFIG[nextValue]) {
                    return;
                }
                state.xAxis = nextValue;
                updateRegressionAvailability();
                updateChart();
            });
        }

        if (ySelect) {
            ySelect.value = state.yAxis;
            ySelect.addEventListener('change', event => {
                const nextValue = event.target.value;
                if (!AXIS_CONFIG[nextValue]) {
                    return;
                }
                state.yAxis = nextValue;
                updateRegressionAvailability();
                updateChart();
            });
        }
    }

    function bindToggleControls() {
        const regressionButton = document.getElementById(SELECTORS.toggleRegression);
        const labelsButton = document.getElementById(SELECTORS.toggleLabels);
        const mediansButton = document.getElementById(SELECTORS.toggleMedians);
        const hopeButton = document.getElementById(SELECTORS.toggleHope);

        if (regressionButton) {
            regressionButton.addEventListener('click', () => {
                if (regressionButton.hasAttribute('disabled')) {
                    return;
                }
                const next = regressionButton.getAttribute('aria-pressed') !== 'true';
                regressionButton.setAttribute('aria-pressed', next ? 'true' : 'false');
                state.showRegression = next;
                state.regressionPreference = next;
                announce(`Regression line ${next ? 'shown' : 'hidden'}.`);
                updateChart();
            });
        }

        if (labelsButton) {
            labelsButton.addEventListener('click', () => {
                const next = labelsButton.getAttribute('aria-pressed') !== 'true';
                labelsButton.setAttribute('aria-pressed', next ? 'true' : 'false');
                state.showAllLabels = next;
                announce(`All peer labels ${next ? 'shown' : 'hidden'}.`);
                updateChart();
            });
        }

        if (mediansButton) {
            mediansButton.addEventListener('click', () => {
                const next = mediansButton.getAttribute('aria-pressed') !== 'true';
                mediansButton.setAttribute('aria-pressed', next ? 'true' : 'false');
                state.showMedians = next;
                announce(`Median reference lines ${next ? 'shown' : 'hidden'}.`);
                updateChart();
            });
        }

        if (hopeButton) {
            hopeButton.addEventListener('click', () => {
                const next = hopeButton.getAttribute('aria-pressed') !== 'true';
                hopeButton.setAttribute('aria-pressed', next ? 'true' : 'false');
                state.includeHope = next;
                announce(`HOPE Bancorp ${next ? 'included' : 'excluded'} from view.`);
                updateChart();
            });
        }
    }

    function updateRegressionAvailability() {
        const regressionButton = document.getElementById(SELECTORS.toggleRegression);
        if (!regressionButton) {
            return;
        }

        const isDefaultAxes = state.xAxis === CONSTANTS.regressionAxes.x && state.yAxis === CONSTANTS.regressionAxes.y;

        if (!isDefaultAxes) {
            state.showRegression = false;
            regressionButton.setAttribute('aria-pressed', 'false');
            regressionButton.setAttribute('disabled', 'true');
        } else {
            state.showRegression = state.regressionPreference;
            regressionButton.removeAttribute('disabled');
            regressionButton.setAttribute('aria-pressed', state.showRegression ? 'true' : 'false');
        }
    }

    function bindExports() {
        const pngButton = document.getElementById(SELECTORS.exportPng);
        const csvButton = document.getElementById(SELECTORS.exportCsv);

        if (pngButton) {
            pngButton.addEventListener('click', exportPng);
        }

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
        const { width, height } = canvas;
        const originalResponsive = chart.options.responsive;
        const originalAspect = chart.options.maintainAspectRatio;
        const originalDisplayWidth = canvas.style.width;
        const originalDisplayHeight = canvas.style.height;

        chart.options.responsive = false;
        chart.options.maintainAspectRatio = false;
        chart.resize(CONSTANTS.pngWidth, CONSTANTS.pngHeight);
        chart.update('none');

        const xLabel = AXIS_CONFIG[state.xAxis].shortLabel;
        const yLabel = AXIS_CONFIG[state.yAxis].shortLabel;
        const filename = `peer_scatter_matrix_${xLabel}_${yLabel}.png`;

        const imageData = canvas.toDataURL('image/png', 1.0);
        const link = document.createElement('a');
        link.href = imageData;
        link.download = filename;
        link.click();

        chart.options.responsive = originalResponsive;
        chart.options.maintainAspectRatio = originalAspect;
        chart.resize(width, height);
        canvas.style.width = originalDisplayWidth;
        canvas.style.height = originalDisplayHeight;
        chart.update('none');
    }

    function exportCsv() {
        const rows = [
            ['Ticker', 'Name', 'ROTE_pct', 'P_TBV', 'CRE_pct', 'Mkt_Cap_M', 'Price', 'TBVPS', 'Fitted_P_TBV', 'Residual', 'Cooks_D', 'Status']
        ];

        const exportPeers = state.peers.filter(peer => peer.ticker !== 'HOPE' || state.includeHope);

        exportPeers.forEach(peer => {
            rows.push([
                peer.ticker,
                peer.name,
                Number.isFinite(peer.rote_pct) ? toFixed(peer.rote_pct, 2) : '',
                Number.isFinite(peer.p_tbv) ? toFixed(peer.p_tbv, 3) : '',
                Number.isFinite(peer.cre_pct) ? toFixed(peer.cre_pct, 1) : '',
                Number.isFinite(peer.mkt_cap_millions) ? toFixed(peer.mkt_cap_millions, 1) : '',
                Number.isFinite(peer.price) ? toFixed(peer.price, 2) : '',
                Number.isFinite(peer.tbvps) ? toFixed(peer.tbvps, 2) : '',
                Number.isFinite(peer.fitted_p_tbv) ? toFixed(peer.fitted_p_tbv, 3) : '',
                Number.isFinite(peer.residual) ? toFixed(peer.residual, 3) : '',
                Number.isFinite(peer.cooks_d) ? toFixed(peer.cooks_d, 3) : '',
                peer.status
            ]);
        });

        rows.push([]);
        rows.push(['# Metadata']);
        rows.push(['Regression_Equation', state.regression.equation || `P/TBV = ${toFixed(state.regression.intercept, 3)} + ${toFixed(state.regression.slope, 3)} × ROTE`]);
        rows.push(['R_Squared', Number.isFinite(state.regression.rSquared) ? toFixed(state.regression.rSquared, 3) : '']);
        rows.push(['Sample_Size', state.regression.sampleSize || '']);
        rows.push(['Median_ROTE', Number.isFinite(state.medians.rote_pct) ? toFixed(state.medians.rote_pct, 2) : '']);
        rows.push(['Median_P_TBV', Number.isFinite(state.medians.p_tbv) ? toFixed(state.medians.p_tbv, 3) : '']);
        rows.push(['Median_CRE', Number.isFinite(state.medians.cre_pct) ? toFixed(state.medians.cre_pct, 1) : '']);

        const csvContent = rows.map(columns => columns.map(escapeCsvValue).join(',')).join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'peer_scatter_matrix.csv');
        link.click();
        URL.revokeObjectURL(url);
    }

    function updateTable() {
        const tbody = document.getElementById(SELECTORS.tableBody);
        if (!tbody) {
            return;
        }

        tbody.innerHTML = '';
        const fragment = document.createDocumentFragment();

        state.visiblePeers.forEach(peer => {
            const row = document.createElement('tr');

            const tickerCell = document.createElement('th');
            tickerCell.scope = 'row';
            tickerCell.textContent = peer.ticker;
            row.appendChild(tickerCell);

            const nameCell = document.createElement('td');
            nameCell.textContent = peer.name;
            row.appendChild(nameCell);

            row.appendChild(createTableCell(Number.isFinite(peer.rote_pct) ? `${toFixed(peer.rote_pct, 2)}%` : 'n/a'));
            row.appendChild(createTableCell(Number.isFinite(peer.p_tbv) ? `${toFixed(peer.p_tbv, 3)}×` : 'n/a'));
            row.appendChild(createTableCell(Number.isFinite(peer.cre_pct) ? `${toFixed(peer.cre_pct, 1)}%` : 'n/a'));
            row.appendChild(createTableCell(Number.isFinite(peer.mkt_cap_millions) ? `$${toFixed(peer.mkt_cap_millions / 1000, 2)}B` : 'n/a'));
            row.appendChild(createTableCell(peer.status));

            fragment.appendChild(row);
        });

        tbody.appendChild(fragment);
    }

    function createTableCell(value) {
        const cell = document.createElement('td');
        cell.textContent = value;
        return cell;
    }

    function getAxisValue(peer, axisKey) {
        switch (axisKey) {
            case 'rote_pct':
                return peer.rote_pct;
            case 'p_tbv':
                return peer.p_tbv;
            case 'cre_pct':
                return peer.cre_pct;
            case 'mkt_cap':
                return Number.isFinite(peer.mkt_cap_millions) ? peer.mkt_cap_millions / 1000 : Number.NaN;
            default:
                return Number.NaN;
        }
    }

    function getMedianValue(axisKey) {
        if (!(axisKey in state.medians)) {
            return Number.NaN;
        }
        return state.medians[axisKey];
    }

    function getBubbleRadius(marketCapMillions) {
        if (!Number.isFinite(marketCapMillions) || marketCapMillions <= 0) {
            return CONSTANTS.minRadius;
        }

        const { min, max } = state.marketCapRange;
        if (!Number.isFinite(min) || !Number.isFinite(max) || min <= 0 || max <= min) {
            return CONSTANTS.minRadius;
        }

        const logMin = Math.log(min);
        const logMax = Math.log(max);
        const logValue = Math.log(marketCapMillions);
        const ratio = clamp((logValue - logMin) / (logMax - logMin), 0, 1);
        return CONSTANTS.minRadius + ratio * (CONSTANTS.maxRadius - CONSTANTS.minRadius);
    }

    function getCreColor(crePercent) {
        if (!Number.isFinite(crePercent)) {
            return getCssVar('--peer-excluded') || '#7A8893';
        }

        const low = getCssVar('--peer-cre-low') || '#2E6F3E';
        const mid = getCssVar('--peer-cre-mid') || '#B85C00';
        const high = getCssVar('--peer-cre-high') || '#8C1E33';

        if (crePercent <= 20) {
            return low;
        }
        if (crePercent >= 50) {
            return high;
        }

        if (crePercent <= 35) {
            const t = (crePercent - 20) / 15;
            return interpolateColor(low, mid, t);
        }

        const t = (crePercent - 35) / 15;
        return interpolateColor(mid, high, t);
    }

    function formatTooltipTitle(items) {
        if (!items || !items.length) {
            return '';
        }
        const item = items[0];
        const peer = item.raw?.peer;
        if (!peer) {
            return '';
        }
        return `${peer.name} (${peer.ticker})`;
    }

    function buildTooltipLines(context) {
        const peer = context.raw?.peer;
        if (!peer) {
            return [];
        }

        const lines = [
            `Profitability: ${Number.isFinite(peer.rote_pct) ? `${toFixed(peer.rote_pct, 2)}% ROTE` : 'n/a'}`,
            `Valuation: ${Number.isFinite(peer.p_tbv) ? `${toFixed(peer.p_tbv, 3)}× P/TBV` : 'n/a'}`,
            `Risk: ${Number.isFinite(peer.cre_pct) ? `${toFixed(peer.cre_pct, 1)}% CRE exposure` : 'n/a'}`,
            `Size: ${Number.isFinite(peer.mkt_cap_millions) ? `$${toFixed(peer.mkt_cap_millions / 1000, 2)}B market cap` : 'n/a'}`
        ];

        const residualLines = [];
        if (Number.isFinite(peer.fitted_p_tbv)) {
            residualLines.push(`• Fitted P/TBV: ${toFixed(peer.fitted_p_tbv, 3)}×`);
        }

        if (Number.isFinite(peer.residual)) {
            const pct = Number.isFinite(peer.fitted_p_tbv) && peer.fitted_p_tbv !== 0
                ? ` (${formatResidualPercent(peer.residual, peer.fitted_p_tbv)})`
                : '';
            residualLines.push(`• Residual: ${toFixed(peer.residual, 3)}×${pct}`);
        } else {
            residualLines.push('• Residual: n/a');
        }

        if (Number.isFinite(peer.cooks_d)) {
            residualLines.push(`• Cook's D: ${toFixed(peer.cooks_d, 3)}`);
        } else if (peer.status === 'Excluded') {
            residualLines.push('• Cook\'s D: > 0.5 (excluded)');
        }

        lines.push('');
        lines.push('Regression:');
        lines.push(...residualLines);
        lines.push('');
        lines.push(`Status: ${peer.status}`);

        return lines;
    }

    function formatResidualPercent(residual, fitted) {
        if (!Number.isFinite(fitted) || fitted === 0) {
            return 'n/a';
        }
        const pct = (residual / fitted) * 100;
        return `${pct >= 0 ? '+' : ''}${toFixed(pct, 1)}%`;
    }

    function observeThemeChanges() {
        const observer = new MutationObserver(mutations => {
            const themeChanged = mutations.some(mutation => mutation.type === 'attributes' && mutation.attributeName === 'data-theme');
            if (themeChanged) {
                refreshChartTheme();
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
        const borderColor = getCssVar('--border-color') || '#D6DADD';
        const tickColor = getCssVar('--text-secondary') || '#4F5B67';

        xScale.grid.color = withOpacity(borderColor, 0.35);
        yScale.grid.color = withOpacity(borderColor, 0.35);
        xScale.ticks.color = tickColor;
        yScale.ticks.color = tickColor;
        xScale.title.color = tickColor;
        yScale.title.color = tickColor;

        state.chart.update('none');
    }

    function announce(message) {
        const region = document.getElementById(SELECTORS.status);
        if (!region) {
            return;
        }
        region.textContent = message;
    }

    function getCssVar(name) {
        return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
    }

    function toFixed(value, decimals) {
        if (!Number.isFinite(value)) {
            return '0';
        }
        const factor = Math.pow(10, decimals);
        return (Math.round((value + Number.EPSILON) * factor) / factor).toFixed(decimals);
    }

    function toNumber(value, fallback = Number.NaN) {
        const numeric = Number(value);
        return Number.isFinite(numeric) ? numeric : fallback;
    }

    function clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
    }

    function applyOpacity(color, alpha) {
        const parsed = parseColor(color);
        if (!parsed) {
            return color;
        }
        return `rgba(${parsed.r}, ${parsed.g}, ${parsed.b}, ${alpha})`;
    }

    function withOpacity(color, opacity) {
        return applyOpacity(color, opacity);
    }

    function interpolateColor(colorA, colorB, t) {
        const start = parseColor(colorA);
        const end = parseColor(colorB);
        if (!start || !end) {
            return colorB;
        }

        const ratio = clamp(t, 0, 1);
        const r = Math.round(start.r + (end.r - start.r) * ratio);
        const g = Math.round(start.g + (end.g - start.g) * ratio);
        const b = Math.round(start.b + (end.b - start.b) * ratio);

        return `rgb(${r}, ${g}, ${b})`;
    }

    function parseColor(color) {
        if (!color) {
            return null;
        }

        const trimmed = color.trim();

        if (trimmed.startsWith('#')) {
            const hex = trimmed.replace('#', '');
            if (hex.length === 3) {
                const r = parseInt(hex[0] + hex[0], 16);
                const g = parseInt(hex[1] + hex[1], 16);
                const b = parseInt(hex[2] + hex[2], 16);
                return { r, g, b };
            }
            if (hex.length === 6) {
                const r = parseInt(hex.slice(0, 2), 16);
                const g = parseInt(hex.slice(2, 4), 16);
                const b = parseInt(hex.slice(4, 6), 16);
                return { r, g, b };
            }
        }

        const rgbaMatch = trimmed.match(/rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)(?:\s*,\s*([\d.]+))?\s*\)/i);
        if (rgbaMatch) {
            return {
                r: Number(rgbaMatch[1]),
                g: Number(rgbaMatch[2]),
                b: Number(rgbaMatch[3])
            };
        }

        return null;
    }

    function escapeCsvValue(value) {
        const stringValue = String(value ?? '');
        if (/[",\n]/.test(stringValue)) {
            return `"${stringValue.replace(/"/g, '""')}"`;
        }
        return stringValue;
    }

    window.initPeerScatterMatrix = initPeerScatterMatrix;
})();
