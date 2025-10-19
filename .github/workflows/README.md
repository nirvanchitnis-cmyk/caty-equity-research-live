# GitHub Actions Workflows

## Overview

This directory contains CI/CD workflows for the CATY equity research repository.

---

## Workflows

### 1. Valuation Reconciliation Guard

**File:** `reconciliation-guard.yml`
**Purpose:** Validates that published valuation numbers match script outputs
**Status:** ✅ Required check (blocks merge on failure)

#### Triggers

- **Push to `main` or `q3-prep-oct19`** when modifying:
  - `README.md`
  - `index.html`
  - `CATY_12_valuation_model.html`
  - `analysis/valuation_bridge_final.py`
  - `analysis/probability_weighted_valuation.py`
  - `analysis/reconciliation_guard.py`

- **Pull requests to `main`** when modifying the same files

#### What It Does

1. Checks out the repository
2. Sets up Python 3.11
3. Installs dependencies (`numpy`, `scipy`)
4. Runs `python3 analysis/reconciliation_guard.py`
5. **Fails the build** if reconciliation check returns non-zero exit code

#### Validated Metrics

- Wilson 95% Target: **$51.74**
- IRC Blended Target: **$51.39**
- Regression Target: **$56.11**
- Normalized Target: **$39.32**

#### Tolerance

±$0.50 per metric (allows for rounding differences)

#### Success Case

```
✅ Valuation Numbers Validated

All published valuation numbers match script outputs within ±$0.50 tolerance.

Validated Metrics:
- Wilson 95% Target: $51.74
- IRC Blended Target: $51.39
- Regression Target: $56.11
- Normalized Target: $39.32
```

#### Failure Case

```
❌ Valuation Reconciliation Failed

Published numbers in README.md or index.html do not match script outputs.

Action Required:
1. Run `python3 analysis/reconciliation_guard.py` locally to see discrepancies
2. Rerun `python3 analysis/valuation_bridge_final.py` and `python3 analysis/probability_weighted_valuation.py`
3. Update README.md and index.html with correct values
4. Push corrected changes
```

#### Bypassing the Check

To skip CI validation (use sparingly, only for non-valuation changes):

```bash
git commit -m "Fix typo [skip ci]"
```

**Warning:** Bypassing CI means published numbers may drift. Use only for documentation fixes, typos, or unrelated changes.

---

## Local Development

### Running Reconciliation Guard Locally

Before pushing:

```bash
python3 analysis/reconciliation_guard.py
```

This runs the same validation that CI performs. Fix any discrepancies before committing.

### Pre-Commit Hook

A local pre-commit hook also runs the reconciliation guard. See `analysis/PRE_COMMIT_HOOK_GUIDE.md` for details.

**Relationship:**
- **Pre-commit hook:** Blocks local commits with wrong values
- **CI workflow:** Blocks remote pushes/merges with wrong values
- **Together:** Two-layer validation ensures published numbers stay accurate

---

## Workflow Management

### Viewing Workflow Runs

1. Go to **Actions** tab in GitHub repository
2. Select **Valuation Reconciliation Guard** workflow
3. View run history and logs

### Debugging Failures

If the workflow fails:

1. Click on the failed run
2. Expand the "Run reconciliation guard" step
3. Review the discrepancy output
4. Run locally: `python3 analysis/reconciliation_guard.py`
5. Fix and push corrected values

### Making the Workflow Optional (Not Recommended)

To temporarily disable required status:

1. Go to **Settings** → **Branches** → **Branch protection rules**
2. Edit `main` branch rule
3. Uncheck "Valuation Reconciliation Guard" from required status checks

**Warning:** This defeats the purpose of automated validation. Only use for emergency hotfixes.

---

## Future Workflows

Potential additional workflows:

- **Python Tests:** Run unit tests for valuation scripts
- **Link Checker:** Validate internal links in HTML files
- **ESG KPI Update:** Automated quarterly ESG data refresh
- **Peer Data Sync:** Fetch peer earnings data on release dates

---

**Maintained by:** Derek review desk
**Last Updated:** Oct 19, 2025
**Next Review:** Post-Q3 earnings (Oct 21, 2025)
