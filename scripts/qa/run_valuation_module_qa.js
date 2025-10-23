#!/usr/bin/env node

/**
 * Valuation Module QA Runner – Phase 1
 *
 * Quick verification that the Valuation Prescription charts initialise
 * and render the expected data payload.
 *
 * Tasks:
 *  - Load the dashboard (assumes local dev server is running on :8000)
 *  - Wait for Chart.js scatter + bar charts to mount
 *  - Capture dataset snapshots
 *  - Log counts + sample values for peer points and framework targets
 *
 * Target runtime: < 5 seconds.
 */

const path = require('path');
const fs = require('fs/promises');
const { chromium } = require('playwright');

const ROOT_DIR = path.resolve(__dirname, '..', '..');
const REPORT_DIR = path.join(ROOT_DIR, 'reports');
const ASSET_DIR = path.join(REPORT_DIR, 'valuation_module_assets');
const OUTPUT_PATH = path.join(ASSET_DIR, 'qa_phase1_snapshot.json');
const BASE_URL = 'http://127.0.0.1:8000/index.html';

async function ensureDir(dirPath) {
    await fs.mkdir(dirPath, { recursive: true });
}

async function waitForCharts(page) {
    await page.waitForFunction(() => {
        if (!window.Chart || typeof window.Chart.getChart !== 'function') {
            return false;
        }
        const scatter = window.Chart.getChart('valuation-peer-scatter');
        const bars = window.Chart.getChart('valuation-framework-bars');
        return Boolean(
            scatter &&
            bars &&
            Array.isArray(scatter.data?.datasets) &&
            scatter.data.datasets.length > 0 &&
            Array.isArray(bars.data?.datasets) &&
            bars.data.datasets.length > 0
        );
    }, { timeout: 10000 });
}

async function collectSnapshot(page) {
    return page.evaluate(() => {
        const scatter = window.Chart.getChart('valuation-peer-scatter');
        const bars = window.Chart.getChart('valuation-framework-bars');

        const peerDataset = scatter.data.datasets.find(dataset => dataset.id === 'peers');
        const catyDataset = scatter.data.datasets.find(dataset => dataset.id === 'caty');
        const regressionDataset = scatter.data.datasets.find(dataset => dataset.id === 'regression');

        const peers = (peerDataset?.data || []).map(point => ({
            ticker: point.ticker,
            rote: Number(point.x),
            ptbv: Number(point.y),
            predicted: Number(point.predicted?.toFixed(3)),
            residual: Number(point.residual?.toFixed(3))
        }));

        const caty = catyDataset?.data?.[0]
            ? {
                rote: Number(catyDataset.data[0].x),
                ptbv: Number(catyDataset.data[0].y),
                predicted: Number(catyDataset.data[0].predicted?.toFixed(3)),
                residual: Number(catyDataset.data[0].residual?.toFixed(3))
            }
            : null;

        const regressionVisible = Boolean(regressionDataset?.data?.length);

        const barDataset = bars.data.datasets[0];
        const frameworks = (barDataset?.data || []).map(entry => ({
            id: entry.id,
            label: entry.x,
            price: Number(entry.y?.toFixed(2)),
            delta: Number(entry.delta?.toFixed(2)),
            deltaPct: Number(entry.deltaPct?.toFixed(1)),
            category: entry.category ?? null,
            note: entry.note ?? null
        }));

        const regressionSummary = document.getElementById('regression-summary')?.textContent ?? '';
        const annotation = document.getElementById('caty-residual-annotation')?.textContent ?? '';

        return {
            peers,
            caty,
            regressionVisible,
            regressionSummary,
            annotation,
            frameworks
        };
    });
}

async function run() {
    await ensureDir(ASSET_DIR);

    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({
        viewport: { width: 1440, height: 900 }
    });
    const page = await context.newPage();

    const start = Date.now();
    await page.goto(BASE_URL, { waitUntil: 'networkidle' });
    await waitForCharts(page);
    const snapshot = await collectSnapshot(page);
    await browser.close();

    const elapsedMs = Date.now() - start;

    const peerSummary = {
        count: snapshot.peers.length,
        sample: snapshot.peers.slice(0, 3)
    };

    const frameworkSummary = {
        count: snapshot.frameworks.length,
        order: snapshot.frameworks.map(item => item.id),
        sample: snapshot.frameworks.slice(0, 3)
    };

    const output = {
        runtime_ms: elapsedMs,
        peerSummary,
        caty: snapshot.caty,
        regressionVisible: snapshot.regressionVisible,
        regressionSummary: snapshot.regressionSummary,
        annotation: snapshot.annotation,
        frameworkSummary
    };

    await fs.writeFile(OUTPUT_PATH, JSON.stringify(output, null, 2), 'utf8');
    console.log('Valuation QA Phase 1 complete:');
    console.log(JSON.stringify(output, null, 2));
}

run().catch((error) => {
    console.error('QA runner failed', error);
    process.exitCode = 1;
});
