# Pre-Commit Hook Guide - Reconciliation Guard

**Created:** Oct 19, 2025
**Purpose:** Automated validation of published valuation numbers
**Location:** `.git/hooks/pre-commit`

---

## What It Does

The pre-commit hook automatically runs `analysis/reconciliation_guard.py` before every commit that modifies valuation-related files. It ensures that published numbers in README.md and index.html match the outputs from:

- `analysis/valuation_bridge_final.py` (regression target $56.11, normalized target $39.32)
- `analysis/probability_weighted_valuation.py` (Wilson 95% target $51.74)

---

## Trigger Conditions

The hook runs **only** when committing changes to these files:

- `README.md`
- `index.html`
- `CATY_12_valuation_model.html`
- `analysis/valuation_bridge_final.py`
- `analysis/probability_weighted_valuation.py`

For all other files (e.g., Python scripts, evidence files, non-valuation HTML), the hook skips validation with:

```
[pre-commit] No valuation files changed, skipping reconciliation check.
```

---

## Success Case (Commit Allowed)

```bash
$ git commit -m "Update README with Q3 data"

[pre-commit] Relevant valuation files changed, running reconciliation guard...

CATY Valuation Reconciliation Guard
============================================================

Step 1: Running valuation scripts...
✓ Scripts executed successfully

Step 2: Extracting calculated values...
  Regression Target: $56.11
  Normalized Target: $39.32
  Wilson 95% Target: $51.74

Step 3: Extracting published values...
  README Wilson Target: $51.74
  index.html Wilson: $51.74
  index.html IRC Blended: $51.39

Step 4: Reconciliation checks...
  ✓ Wilson Target (README): $51.74 = $51.74
  ✓ Wilson Target (index.html): $51.74 = $51.74
  ✓ IRC Blended: $51.39 = $51.39

============================================================
✓ All reconciliation checks PASSED

✓ Reconciliation check passed - proceeding with commit.

[q3-prep-oct19 abc1234] Update README with Q3 data
 1 file changed, 2 insertions(+), 1 deletion(-)
```

---

## Failure Case (Commit Blocked)

```bash
$ git commit -m "Update valuation (WRONG NUMBER)"

[pre-commit] Relevant valuation files changed, running reconciliation guard...

CATY Valuation Reconciliation Guard
============================================================

Step 4: Reconciliation checks...
  ✗ Wilson Target (README): $53.50 (published) ≠ $51.74 (calculated) [Δ $1.76]

============================================================
✗ Reconciliation FAILED

✗ Reconciliation check FAILED

Commit blocked - published numbers do not match script outputs.

Options:
  1. Fix discrepancies in README.md/index.html
  2. Rerun valuation scripts if needed
  3. Run 'python3 analysis/reconciliation_guard.py' manually to debug
  4. Bypass (use only for non-valuation changes): git commit --no-verify
```

---

## Tolerance

The hook allows a **±$0.50 tolerance** for floating-point rounding differences. For example:

- **$51.74 vs $51.74** → ✓ Pass
- **$51.74 vs $52.00** → ✓ Pass (within tolerance)
- **$51.74 vs $52.50** → ✗ Fail (outside tolerance)

This prevents false positives from minor rounding differences while catching genuine discrepancies.

---

## Bypassing the Hook

**⚠️ Use sparingly and only for non-valuation changes!**

If you need to commit without validation (e.g., fixing a typo, updating unrelated sections), use:

```bash
git commit --no-verify -m "Fix typo in company overview"
```

**Warning:** Bypassing the hook means published numbers may drift out of sync with script outputs. Only use for changes that don't affect valuation numbers.

---

## Manual Validation

To run the reconciliation check manually (without committing):

```bash
python3 analysis/reconciliation_guard.py
```

This is useful for:
- Debugging discrepancies before committing
- Verifying published numbers after Q3 updates
- Pre-flight checks before pushing to GitHub

---

## Installation (Already Done)

The hook is already installed at `.git/hooks/pre-commit` (executable). No action required.

If the hook file is missing or you need to reinstall:

```bash
# Copy hook template to .git/hooks/
cp analysis/pre-commit-template .git/hooks/pre-commit

# Make executable
chmod +x .git/hooks/pre-commit
```

---

## Integration with Monitoring Runbook

The reconciliation guard is wired into the post-Q3 execution workflow at **Step 6**:

```
Step 6: Documentation
1. Update evidence/probability_dashboard.md
2. Add SHA256 hash to evidence/README.md
3. Update DEREK_EXECUTIVE_SUMMARY.md if rating changes
4. Update index.html rating badge if needed
5. **Run reconciliation guard: python3 analysis/reconciliation_guard.py**
   - Validates published numbers match script outputs
   - Must pass (exit code 0) before committing
   - If fails, fix discrepancies in README.md/index.html
6. Git commit with timestamp
7. Push to GitHub
```

---

## Troubleshooting

### Hook Not Running

Check if the hook file exists and is executable:

```bash
ls -l .git/hooks/pre-commit
# Should show: -rwxr-xr-x (executable permissions)
```

If missing, reinstall as above.

### Hook Running on Wrong Files

The hook should only run for valuation files. If it runs on every commit, check the `RELEVANT_FILES` array in `.git/hooks/pre-commit`:

```bash
RELEVANT_FILES=(
    "README.md"
    "index.html"
    "CATY_12_valuation_model.html"
    "analysis/valuation_bridge_final.py"
    "analysis/probability_weighted_valuation.py"
)
```

### Validation Failing Despite Correct Numbers

1. Run manually to see detailed output:
   ```bash
   python3 analysis/reconciliation_guard.py
   ```

2. Check if numbers are within ±$0.50 tolerance

3. Verify script outputs:
   ```bash
   python3 analysis/valuation_bridge_final.py
   python3 analysis/probability_weighted_valuation.py
   ```

4. If scripts produce different values, investigate data sources (FDIC CSV, peer snapshot)

---

## Best Practices

1. **Always let the hook run** - Don't bypass unless absolutely necessary
2. **Fix discrepancies immediately** - If validation fails, fix before retrying
3. **Run manual validation after Q3 updates** - Verify before committing
4. **Document bypasses** - If you use `--no-verify`, note why in the commit message

---

## Example Workflow (Post-Q3 Update)

```bash
# Step 1: Update valuation scripts with Q3 data
vim analysis/probability_weighted_valuation.py  # Update current_price
python3 analysis/nco_probability_analysis.py     # Rerun Wilson bounds

# Step 2: Update published numbers
vim README.md                                    # Update Wilson target
vim index.html                                   # Update scenario table

# Step 3: Manual validation
python3 analysis/reconciliation_guard.py
# ✓ All checks pass

# Step 4: Commit (hook runs automatically)
git add README.md index.html analysis/probability_weighted_valuation.py
git commit -m "Q3 update: Wilson 95% bounds recalculated"
# Hook validates → commit proceeds

# Step 5: Push
git push origin-live q3-prep-oct19:main
```

---

## Technical Details

**Hook Type:** Pre-commit (runs before commit is created)
**Language:** Bash
**Dependencies:** Python 3, `analysis/reconciliation_guard.py`
**Exit Codes:**
- 0 = Validation passed, commit allowed
- 1 = Validation failed, commit blocked
- (Non-zero from guard script) = Propagated to block commit

**Performance:** Adds ~2-3 seconds to commit time (script execution + validation)

---

**Maintained by:** Derek review desk
**Last Updated:** Oct 19, 2025
**Next Review:** Post-Q3 2025 (Oct 21)
