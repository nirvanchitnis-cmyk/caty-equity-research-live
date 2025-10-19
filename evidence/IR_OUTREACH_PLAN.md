# IR OUTREACH PLAN - CRE PROPERTY-TYPE DISCLOSURE REQUEST

**Date Created:** October 18, 2025
**Analyst:** Nirvan Chitnis
**Objective:** Obtain office, retail, multifamily, industrial breakdown of $10.4B CRE portfolio
**Status:** PENDING EXECUTION (awaiting Derek approval)

---

## EXECUTIVE SUMMARY

**Current State:** CRE concentration of 52.4% is confirmed from Q2'25 10-Q, but property-type composition is NOT DISCLOSED in public filings (10-Q, 10-K, 8-Ks).

**Data Gap Impact:** Unable to quantify tail risk from office sector stress without office exposure %.

**Next Step:** Formal IR outreach to request property-type breakdown.

---

## EMAIL DRAFT TO CATHAY IR

**To:** ir@cathaybank.com
**CC:** —
**Subject:** Data Request - CRE Property-Type Composition (Q2 2025)

---

Dear Cathay General Bancorp Investor Relations Team,

I am conducting equity research on Cathay General Bancorp (NASDAQ: CATY) and am requesting clarification on the commercial real estate portfolio composition as of Q2 2025.

**Data Request:**

Could you please provide the breakdown of the $10.4 billion CRE portfolio (52.4% of total loans, per Q2'25 10-Q) by property type:

1. **Office CRE** (% and $M)
2. **Retail CRE** (% and $M)
3. **Multifamily Residential CRE** (% and $M)
4. **Industrial/Warehouse CRE** (% and $M)
5. **Other CRE** (% and $M, if applicable)

**Context:**

The Q2 2025 10-Q discloses total CRE loans of $10,363 million (line 4068-4070 of HTML filing, accession 0001437749-25-025772), but does not provide granular property-type composition. This breakdown would help assess exposure to specific property sectors experiencing valuation pressure (e.g., office sector stress from persistent remote work trends).

**Additional Information (if available):**

- Average loan-to-value (LTV) ratios by property type
- Geographic concentration within CRE (% in California, New York, Texas)
- Maturity profile of CRE loans (% maturing 2025-2027)

**Timeline:**

I would greatly appreciate a response within **3-5 business days** if possible. If this data is not publicly disclosed but available to institutional investors, please let me know the appropriate channel for requesting it.

Thank you for your assistance. Please feel free to contact me if you need any clarification on this request.

Best regards,
Nirvan Chitnis
Equity Research Analyst

---

## FALLBACK OPTIONS IF IR DECLINES

### Option A: FDIC Call Report (Regulatory Data)
**Source:** FR Y-9C Schedule HC-C (Bank Holding Company quarterly report)
**Fields:**
- RCON1415: Construction, land development, and other land loans
- RCON1417: Secured by nonfarm nonresidential properties
- RCON1460: Secured by multifamily (5 or more) residential properties

**Limitation:** Owner-occupied vs non-owner-occupied mapping is imperfect proxy for office exposure. Field RCON1417 includes office, retail, industrial, warehouse, healthcare, etc.

**Status:** API query pending; see evidence/README.md for command execution

---

### Option B: Earnings Call Transcript Search
**Source:** Seeking Alpha, Bloomberg, S&P Capital IQ
**Target:** Q2 2025 earnings call (August 7, 2025)
**Search terms:** "office", "property type", "CRE breakdown", "CRE composition"

**Expected yield:** Management commentary may provide qualitative color ("office exposure is modest") but unlikely to give precise %.

---

### Option C: Third-Party Data Vendors
**Sources:**
- **Trepp:** CMBS loan-level data (may include Cathay-originated loans)
- **CoStar:** Property market analytics (cap rates, occupancy by property type)
- **S&P Global Market Intelligence:** Bank loan composition estimates

**Cost:** $500-$2,000 per data pull
**Accuracy:** Estimates only; not primary source

---

### Option D: Analyst Conference Calls / NDR
**Approach:** Request non-deal roadshow (NDR) meeting with Cathay CFO/Treasurer
**Ask:** Direct question on office % during Q&A
**Timeline:** 1-2 weeks lead time typical

---

## DECISION TREE

```
IR Outreach Email Sent
    ├─ IR Responds with Data → ✅ INTEGRATE INTO THESIS (update CATY_08, index.html, capital stress worksheet)
    ├─ IR Declines (not disclosed) → Use Option A (FDIC proxy) + annotate as "regulatory data proxy"
    ├─ IR No Response (5 business days) → Escalate to Option B (earnings call) + Option A (FDIC)
    └─ IR Refers to Public Filings → Document search attempt, flag as "unavailable via public disclosure"
```

---

## TIMELINE

| Date | Milestone | Status |
|------|-----------|--------|
| Oct 18, 2025 | IR outreach plan created | ✅ DONE |
| Oct 18, 2025 | Derek approval to send email | ⏳ PENDING |
| Oct 18, 2025 | Email sent to IR | ⏳ PENDING APPROVAL |
| Oct 21-23, 2025 | IR response expected | ⏳ TBD |
| Oct 24, 2025 | Fallback to FDIC if no response | ⏳ TBD |
| Oct 25, 2025 | Finalize property-type data source | ⏳ TBD |

---

## RISK ASSESSMENT

### Risk 1: IR Declines to Disclose
**Probability:** Medium (30-40%)
**Mitigation:** Use FDIC regulatory data as proxy with explicit caveats

### Risk 2: IR Requires Institutional Investor Verification
**Probability:** Low (10-15%)
**Mitigation:** Provide professional credentials; escalate to Derek if needed

### Risk 3: Data Exists but Only in Earnings Deck (Not Filed)
**Probability:** Medium (25-35%)
**Mitigation:** Request link to investor presentation on IR website

### Risk 4: Office % is Immaterial (<10%)
**Probability:** Low (15-20%)
**Implication:** If office % is low, SELL thesis weakens on office-specific stress but remains valid on total CRE concentration

---

## INTEGRATION INTO THESIS

**If Office % < 15%:**
- Downweight office stress scenario in CATY_08
- Emphasize total CRE concentration (52.4%) + refinancing risk
- Maintain SELL rating based on through-cycle NCO normalization alone

**If Office % = 15-25%:**
- Moderate office tail risk (current base case assumption)
- Maintain SELL thesis with office stress as supporting factor

**If Office % > 25%:**
- Elevate office stress to primary risk driver
- Tighten target price to $38-40 range (vs current $40.32)
- Consider adding Bear Case scenario with higher loss severity

---

## DOCUMENTATION REQUIREMENTS

**Once data received:**
1. Update CATY_08_cre_exposure.html with sourced figures
2. Update index.html risk section with property-type breakdown
3. Update capital stress worksheet with office-specific scenarios
4. Add citation to evidence/README.md with IR correspondence date
5. Create evidence/IR_RESPONSE_[DATE].txt with full email chain
6. Update DEREK_EXECUTIVE_SUMMARY.md with confirmed office %

---

## CONTACTS

**Cathay General Bancorp Investor Relations**
Email: ir@cathaybank.com
Phone: (626) 279-3286
Website: https://investor.cathaybank.com
Address: 777 North Broadway, Los Angeles, CA 90012

---

## APPROVAL CHECKPOINT

**Derek:** This plan is ready for execution pending your approval. Key decision points:

1. **Approve email send?** (Yes / No / Modify)
2. **Approve fallback to FDIC proxy if IR declines?** (Yes / No)
3. **Timeline acceptable?** (3-5 business day turnaround)

**Next Action:** Awaiting Derek's GO/NO-GO on email dispatch.
