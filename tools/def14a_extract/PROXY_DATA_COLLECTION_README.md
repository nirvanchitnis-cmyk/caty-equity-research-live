# DEF14A Proxy Data Collection - CFA IRC Team Workflow

**Date:** October 20, 2025
**Team Size:** 5 students
**Timeline:** 1 week
**Banks:** CATY, EWBC, CVBF, HAFC, COLB, BANC, HOPE (7 banks)

---

## Why Are We Doing This?

**You're building the governance/compensation foundation for a CFA Institute Research Challenge-winning equity research report.**

### The Big Picture:

**What We're Building:**
A fully automated, institutional-grade equity research dashboard for Cathay General Bancorp (CATY) that meets CFA IRC standards. Think Bloomberg Terminal quality, but built from scratch with 100% traceable data provenance.

**How Your Work Fits In:**

```
[SEC EDGAR] → [Automated Download] → [8 DEF14A Proxy Statements Downloaded]
                                              ↓
                            ┌─────────────────┴─────────────────┐
                            ↓                                   ↓
                [Automated Parser]                    [Human Collection (YOU)]
                    ↓                                           ↓
            Basic Facts:                          Complex Facts:
            - Board size                          - Compensation metrics & weights
            - CEO name                            - LTIP structure
            - Auditor                             - Top institutional holders
            - Pay ratio                           - Performance targets
            - Say-on-pay %
            - Audit fees
                            ↓                                   ↓
                            └─────────────────┬─────────────────┘
                                              ↓
                            [Merged Canonical JSON with Provenance]
                                              ↓
                            [HTML Modules: CATY_01, CATY_15]
                                              ↓
                            [CFA IRC Presentation: ESG/Governance Scoring]
```

**Why Can't Machines Do This?**

Some governance data is standardized (board size = always in a table). But compensation metrics? Every bank writes it differently:
- CATY: Clean table with percentages
- EWBC: Prose paragraphs ("70% financial metrics...")
- HOPE: Bullet points with special characters
- BANC: Everything on one minified HTML line

**Automated parsers fail on this variability.** But you can read the proxy, understand context, and extract the right data in 10 minutes per bank.

**What Happens to Your Data?**

1. **Week 1 (This Week):** You fill Excel template
2. **Week 2:** We convert Excel → JSON (automated script)
3. **Week 2:** Your data merges with automated extraction → canonical factbase
4. **Week 2:** Factbase populates HTML modules:
   - **CATY_01:** CEO compensation context (how aligned to ROTCE/credit quality?)
   - **CATY_15:** Governance scorecard (board independence, say-on-pay, compensation alignment)
5. **IRC Submission:** Your governance data becomes slides in the final presentation

**Why This Matters for IRC Scoring:**

**ESG/Governance Section (15 points):**
- Board independence %
- Say-on-pay shareholder approval
- Executive pay alignment to performance (ROTCE, efficiency, credit quality)
- Institutional ownership concentration
- Auditor independence

**Your data directly impacts 15% of the IRC score.** No governance data = weak ESG section = points lost.

---

## When You Get Stuck:

**"I can't find the compensation metrics table"**
→ Look for "Compensation Discussion & Analysis" section, search for CEO name, find nearest table/bullets

**"Weights don't add to 100%"**
→ Some banks round (38% + 32% + 30% = 100%). Close enough. If way off, flag it.

**"What's the difference between annual incentive and LTIP?"**
→ Annual = cash bonus (paid this year). LTIP = stock awards (vest over 3 years).

**"This bank doesn't disclose X"**
→ Mark "Not Disclosed" - that's valid data. Tells us they're less transparent.

**You're Not Alone:**
- 5 students, each assigned specific banks
- Nirvan + team available for questions
- 1 week timeline = ~2 hours per bank = manageable

---

## Objective

Manually extract complex governance/compensation facts from DEF14A proxy statements that are too variable for automated parsing. Data will integrate into canonical JSON schema with `human_collected` provenance.

---

## Data Collection Spreadsheet

**File:** `tools/def14a_extract/proxy_data_collection_template.xlsx`

**Structure:** 5 tabs (one per team member) + 1 validation tab

### Tab Assignment:

| Tab | Team Member | Banks Assigned | Fields to Extract |
|-----|-------------|----------------|-------------------|
| **Tab 1** | Student A | CATY, EWBC | Annual incentive metrics, LTIP structure |
| **Tab 2** | Student B | CVBF, HAFC | Annual incentive metrics, LTIP structure |
| **Tab 3** | Student C | COLB, BANC | Annual incentive metrics, LTIP structure |
| **Tab 4** | Student D | HOPE | Annual incentive metrics, LTIP structure |
| **Tab 5** | Student E | All banks | Top 5 institutional holders + ownership % |
| **Tab 6** | Validation | — | Automated checks (formulas) |

---

## Fields to Extract

### Section 1: Annual Incentive Metrics (Tabs 1-4)

**Source:** "Compensation Discussion & Analysis" section of DEF14A

**Data to Collect:**

| Column | Description | Example |
|--------|-------------|---------|
| Ticker | Bank ticker | CATY |
| Metric Name | Performance metric | ROTCE, Efficiency Ratio, Credit Quality |
| Weight % | % of bonus tied to metric | 40, 30, 20 |
| Target Value | Target performance level (if disclosed) | 11.5%, 47%, <30 bps |
| Result | Actual 2024 performance | 11.95%, 46.9%, 18 bps |
| Payout % | Actual payout as % of target | 125% |

**Search Tips:**
- Look for table titled "Annual Incentive Metrics" or "STI Performance"
- CEO-specific metrics (not other NEOs)
- Weights must sum to 100%
- If not disclosed, leave blank

**Example (CATY):**
- ROTCE: 56% weight
- ROA: 24% weight
- Individual Performance: 20% weight

---

### Section 2: LTIP Structure (Tabs 1-4)

**Source:** "Long-Term Incentive Plan" section

**Data to Collect:**

| Column | Description | Example |
|--------|-------------|---------|
| Ticker | Bank ticker | CATY |
| Metric Name | Long-term metric | Relative TSR, EPS CAGR, ROTCE |
| Weight % | % of LTIP tied to metric | 50, 25, 25 |
| Relative to Peers? | Is metric compared to peer group? | Yes/No |
| Vesting Period | Years until vesting | 3 years |
| Vehicle | RSU, PSU, Options, Cash | PSU, RSU |

**Search Tips:**
- Look for "Performance Stock Units" or "Long-Term Incentive"
- Check if TSR is "relative" or "absolute"
- Vehicles: RSU (time-based), PSU (performance-based)

---

### Section 3: Institutional Ownership (Tab 5)

**Source:** "Security Ownership of Certain Beneficial Owners" table

**Data to Collect (Top 5 Holders):**

| Column | Description | Example |
|--------|-------------|---------|
| Ticker | Bank ticker | CATY |
| Rank | 1-5 (largest to smallest) | 1 |
| Holder Name | Institution name | BlackRock Inc. |
| Ownership % | % of shares outstanding | 15.22% |
| Shares Owned | Number of shares (if disclosed) | 10,546,789 |

**Search Tips:**
- Look for table: "Principal Stockholders" or ">5% Beneficial Owners"
- Exclude directors/management (those are insiders, not institutions)
- Take top 5 by ownership %
- Stop at director section (don't mix institution/individual data)

---

## Quality Control Checklist

Before submitting:
- [ ] All weights sum to 100% (annual incentive, LTIP)
- [ ] Ownership % verified against source table
- [ ] Bank ticker matches assignment
- [ ] No blank required fields (mark "Not Disclosed" if truly missing)
- [ ] Page numbers referenced for each fact

---

## Integration Workflow (Post-Collection)

### Step 1: Export to JSON

After 1 week, run:
```bash
python3 tools/def14a_extract/excel_to_json.py \
  --excel tools/def14a_extract/proxy_data_collection_template.xlsx \
  --output data/proxy/human_collected/
```

**Output:** JSON files with human-collected data + provenance

### Step 2: Merge with Automated Data

```bash
python3 tools/def14a_extract/merge_automated_and_human.py \
  --automated data/proxy/*_extracted.json \
  --human data/proxy/human_collected/*.json \
  --output data/proxy/*_FINAL.json
```

**Result:** Complete governance factbase with mixed provenance

---

## Provenance Example (Human Collected)

```json
{
  "section": "compensation.annual_incentive.metrics",
  "method": "human_collected",
  "locators": ["DEF14A page 42", "table: Annual Incentive Metrics"],
  "text_snippet": null,
  "confidence_pct": 100,
  "source_url": "https://www.sec.gov/Archives/...",
  "sha256": null,
  "collected_by": "Student A",
  "collection_date": "2025-10-27"
}
```

---

## Timeline

| Date | Milestone |
|------|-----------|
| Oct 20 | Template created, team briefed |
| Oct 21-27 | Team collects data (1 week) |
| Oct 28 | Data validated, exported to JSON |
| Oct 28 | Merged with automated extraction |
| Oct 29 | Integrated into CATY_01 + CATY_15 modules |

---

**Template Location:** `tools/def14a_extract/proxy_data_collection_template.xlsx`
**Questions:** Contact Nirvan Chitnis
