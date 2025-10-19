# Rapid-Turnaround Memo Workflow - Oct 21 EWBC → CATY (60-Minute Window)

**Timeline:** Tuesday, Oct 21, 2025
**EWBC Call:** 2:00-3:00 PM PT
**CATY Call:** 3:00 PM PT
**Window:** **60 minutes** (5:00-6:00 PM ET / 2:00-3:00 PM PT)
**Objective:** Extract EWBC red flags and prep CATY questions in 1 hour

---

## ⏱️ Minute-by-Minute Timeline

### 2:00-3:00 PM PT (EWBC Call)
- Listen live OR
- Wait for 8-K filing (usually within 15 min of call start)

### 3:00-3:10 PM PT (10 min) - Data Extraction
**Action:** Download EWBC 8-K and extract headline metrics

```bash
# Monitor SEC filings
python3 analysis/fetch_peer_filings.py EWBC --cutoff 2025-10-20

# Download 8-K from link provided
curl -o evidence/raw/EWBC_Q3_2025_earnings_8K.pdf [SEC_LINK]

# Hash for evidence trail
shasum -a 256 evidence/raw/EWBC_Q3_2025_earnings_8K.pdf
```

**OR use web search:**
```bash
# Instant results from financial news
web_search: "EWBC Q3 2025 earnings results NCO NIM"
```

**Extract These 5 Metrics ONLY:**
1. NCO rate (bps)
2. NIM (%)
3. Deposit QoQ change (%)
4. ALLL coverage (%)
5. Management tone (1 sentence)

---

### 3:10-3:30 PM PT (20 min) - Red Flag Triage

**Fill out this checklist (30 seconds each):**

| Red Flag | Threshold | EWBC Q3 | Triggered? |
|----------|-----------|---------|------------|
| NCO Spike | >50 bps | [__] bps | ☐ YES ☐ NO |
| NIM Collapse | -15 bps QoQ | [__] bps | ☐ YES ☐ NO |
| Deposit Outflow | -3% QoQ | [__]% | ☐ YES ☐ NO |
| Provision Build | +20 bps | [__] bps | ☐ YES ☐ NO |
| Mgmt Tone | Cautious | [__] | ☐ CAUTION ☐ NEUTRAL |

**Total Red Flags:** [__] / 5

**If 0-1 red flags:**
→ **NO CATY RECALIBRATION NEEDED**
→ Proceed with baseline Wilson 74/26, HOLD rating

**If 2+ red flags:**
→ **URGENT RECALIBRATION**
→ Jump to Section 4 (CATY Adjustments)

---

### 3:30-3:50 PM PT (20 min) - CATY Question Prep

**If red flags triggered, draft 2-3 targeted questions:**

**Example (NCO spike red flag):**
> "EWBC just reported NCO of [55] bps, up from [32] bps last quarter, driven by office CRE. Can you comment on your CRE office performance in Q3? Are you seeing similar migration to criticized status?"

**Example (NIM collapse red flag):**
> "EWBC's NIM compressed [18] bps this quarter due to deposit repricing. Your deposit beta is historically lower at 0.35. How did your cost of deposits trend in Q3, and are you seeing any acceleration?"

**Example (Deposit outflow red flag):**
> "EWBC lost [4%] of deposits this quarter. Given your Asian-American customer overlap, are you seeing similar pressure? What is your deposit retention rate for core customers?"

**Template:**
```
CATY Call Question #1 (based on EWBC [METRIC]):
"[Direct question referencing EWBC data point and asking for CATY comparison]"

CATY Call Question #2:
"[Follow-up question]"

CATY Call Question #3 (if needed):
"[Third question if multiple red flags]"
```

---

### 3:50-4:00 PM PT (10 min) - Buffer/Review
- Review questions for clarity
- Check CATY baseline assumptions (NCO 18 bps current, 42.8 bps normalized)
- Prep comparison talking points

---

### 4:00 PM PT (CATY Call Starts)
- ✅ **Armed with EWBC signals**
- ✅ **Red flags triaged**
- ✅ **Questions drafted**

---

## Section 4: CATY Assumption Adjustments (If Red Flags Triggered)

### 4.1 Wilson Upper Bound Adjustment

**Current:** 74/26 (26% tail probability)

**Decision Tree:**

| EWBC NCO | EWBC NIM | EWBC Deposits | Recommended Tail | Wilson Target | Rating |
|----------|----------|---------------|------------------|---------------|--------|
| <30 bps | >-10 bps | >-2% | **Keep 26%** | $51.74 | **HOLD** |
| 30-50 bps | -10 to -15 bps | -2% to -3% | **Increase to 30%** | ~$50.50 | **HOLD** |
| >50 bps | <-15 bps | <-3% | **Increase to 35%** | ~$49.00 | **HOLD/SELL** |

**Action:**
```python
# Update analysis/probability_weighted_valuation.py
upper_prob_current = 0.74  # OLD
upper_prob_current = 0.70  # NEW (if increasing tail to 30%)
upper_prob_current = 0.65  # NEW (if increasing tail to 35%)

# Rerun
python3 analysis/probability_weighted_valuation.py
```

---

### 4.2 NCO Normalization Adjustment

**Current:** 42.8 bps through-cycle

**If EWBC NCO > 50 bps:**
```python
# Increase CRE climate buffer
through_cycle_nco_bps = 42.8  # OLD
through_cycle_nco_bps = 45.8  # NEW (+3.0 bps CRE stress)

# Update analysis/valuation_bridge_final.py line 31
```

---

### 4.3 Q3 NIM Estimate (for CATY)

**Current CATY NIM (Q2):** 3.27%

**If EWBC NIM compresses >10 bps:**
```python
# Estimate CATY Q3 NIM
caty_nim_q2 = 3.27
ewbc_nim_compression = [__]  # bps from EWBC
caty_nim_q3_estimate = caty_nim_q2 - (ewbc_nim_compression * 0.80)  # CATY moat = 20% cushion

# Use for ROTE forecast validation
```

---

## Section 5: Deliverables & Distribution

### 5.1 Memo Output (≤2 Hours Post-EWBC)

**File:** `evidence/EWBC_Q3_2025_rapid_memo_[TIMESTAMP].md`

**Contents (1-page max):**
```markdown
# EWBC Q3 Rapid Memo - Oct 21, 2025

## Red Flags: [__] / 5
- NCO: [__] bps ([RED FLAG if >50])
- NIM: [__]% ([RED FLAG if -15 bps])
- Deposits: [__]% QoQ ([RED FLAG if -3%])

## CATY Calibration:
- Wilson tail: [Keep 26% / Increase to __%]
- CATY Questions: [List 2-3 questions]

## Source:
- 8-K: [SEC link]
- SHA256: [hash]

Memo completed: [Timestamp]
```

---

### 5.2 Distribution Checklist

**Within 2 Hours of EWBC Call:**
- [ ] Populate monitoring template with EWBC data
- [ ] Create rapid memo (1-page)
- [ ] Hash and archive 8-K to evidence/raw/
- [ ] Update peer_preearnings_questionbank.md with answers
- [ ] Distribute to Derek (Slack/email)
- [ ] Stage CATY call questions

**Post-CATY (Oct 21 evening):**
- [ ] Populate CATY section of monitoring template
- [ ] Compare CATY vs EWBC on critical metrics
- [ ] Update Wilson bounds if needed
- [ ] Commit changes (reconciliation guard validates)

**Post-COLB (Oct 30):**
- [ ] Full COLB analysis (no time pressure)
- [ ] Triangulate CATY vs EWBC vs COLB
- [ ] Validate rating or reconvene committee

---

## Section 6: Tools & Commands

### 6.1 SEC Filing Monitor
```bash
# Check for EWBC 8-K (run every 15 min starting 2:00 PM PT)
python3 analysis/fetch_peer_filings.py EWBC --cutoff 2025-10-20

# Check for COLB 8-K (run Oct 30 starting 2:00 PM PT)
python3 analysis/fetch_peer_filings.py COLB --cutoff 2025-10-29
```

### 6.2 Web Search for Instant Results
```bash
# Use when 8-K not yet filed or for speed
web_search: "EWBC Q3 2025 earnings results"
web_search: "EWBC Q3 NCO provision NIM"
web_search: "COLB Q3 2025 earnings results"
```

### 6.3 Evidence Archiving
```bash
# Download earnings materials
curl -o evidence/raw/EWBC_Q3_2025_earnings_8K.pdf [SEC_LINK]
curl -o evidence/raw/EWBC_Q3_2025_earnings_deck.pdf [DECK_LINK]

# Hash for integrity
shasum -a 256 evidence/raw/EWBC_Q3_2025_earnings_8K.pdf >> evidence/README.md
```

### 6.4 Valuation Recalibration
```bash
# If red flags triggered
vim analysis/probability_weighted_valuation.py  # Update upper_prob_current
python3 analysis/probability_weighted_valuation.py  # Rerun Wilson

# Validate
python3 analysis/reconciliation_guard.py
```

---

## Section 7: Workflow Diagram

```
Oct 21, 2025 Timeline
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2:00 PM PT │ EWBC Call Starts
    ↓      │
3:00 PM PT │ EWBC Call Ends
    ↓      │
    │      ├─ [10 min] Download 8-K, extract 5 metrics
    │      │
3:10 PM PT ├─ [20 min] Red flag triage (NCO, NIM, deposits)
    │      │
3:30 PM PT ├─ [20 min] Draft CATY questions (if red flags)
    │      │
3:50 PM PT ├─ [10 min] Review buffer
    ↓      │
4:00 PM PT │ CATY Call Starts ✅ ARMED WITH EWBC SIGNALS
    ↓      │
5:00 PM PT │ CATY Call Ends
    ↓      │
    │      ├─ [2 hours] Complete EWBC memo + CATY analysis
    ↓      │
7:00 PM PT │ Distribute memo, commit updates ✅
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Oct 30, 2025 (Post-CATY Validation)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2:00 PM PT │ COLB Call (no time pressure, CATY already reported)
    ↓      │
    │      ├─ Full analysis (use complete template)
    │      ├─ Triangulate CATY vs EWBC vs COLB
    ↓      │
    │      ├─ Validate CATY assumptions post-facto
    │      ├─ Reconvene rating committee if divergences
    ↓      │
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Section 8: Contingency Plans

### 8.1 If EWBC 8-K Delayed (Not Filed by 3:05 PM PT)
- Skip SEC filing, use web search for press release
- Rely on headline metrics from financial news sites
- Complete full analysis post-CATY (not time-critical)

### 8.2 If Multiple Red Flags (3+)
- Escalate to Derek immediately
- Consider postponing CATY rating update (wait for COLB Oct 30)
- Flag "Rating Under Review" if uncertainty too high

### 8.3 If CATY Pre-Empts EWBC (Unlikely)
- Reverse workflow: Use CATY → EWBC comparison
- Adjust EWBC expectations based on CATY results

---

## Section 9: Success Criteria

**Minimum Viable Memo (30 minutes):**
- ✅ 5 metrics extracted (NCO, NIM, Deposits, ALLL, Tone)
- ✅ Red flag count (0-5)
- ✅ CATY action (Yes/No recalibration)

**Full Memo (60 minutes):**
- ✅ Above +
- ✅ 2-3 CATY questions drafted
- ✅ Comparison table populated
- ✅ 8-K archived and hashed

**Ideal Memo (2 hours, post-CATY):**
- ✅ Above +
- ✅ Full monitoring template populated
- ✅ Valuation scripts rerun (if needed)
- ✅ Memo distributed to team
- ✅ Commits pushed with reconciliation guard validation

---

## Section 10: Lessons Learned (Post-Mortem Template)

**After Oct 21, answer:**
1. Did the 60-minute window work? Too tight?
2. Which metrics were most valuable (NCO, NIM, deposits)?
3. Did EWBC signals improve CATY call prep?
4. Should we adjust workflow for future quarters?

**Update this file with:**
- Actual timeline executed
- Bottlenecks encountered
- Process improvements for Q4 2025

---

**Template Status:** ✅ READY FOR OCT 21 EXECUTION
**Owner:** Derek + Claude
**Next Use:** Tuesday, October 21, 2025, 2:00 PM PT
**Fallback:** COLB Oct 30 (no time pressure, full analysis)
