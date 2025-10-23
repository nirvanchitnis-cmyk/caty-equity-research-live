# An Open Letter to Dan Priest, U.S. Chief AI Officer, PwC

**From:** Nirvan Chitnis, Assurance Associate, PwC
**Date:** October 23, 2025
**Subject:** What I Built on $400/Month and 8GB of RAM — And What We Could Build with PwC's Full Stack

---

## Dear Dan,

I need to show you something. Not a pitch deck. Not a concept. **A production system I built in public over 60+ commits, failures documented, validations passing, zero shortcuts.**

**Repository:** https://github.com/nirvanchitnis-cmyk/caty-equity-research-live
**Live Site:** https://nirvanchitnis-cmyk.github.io/caty-equity-research-live/

This is **not clanker slop.**
This is **not a one-shot prompt.**
This was **built brick by brick.**

And I built it because I'm obsessed with a question you've been asking the market: **"If everybody has intelligence, is intelligence really the differentiator… or are we just driving intelligence into our workflows to achieve the table stakes?"**

I think the answer is neither. **The differentiator is _how_ you drive intelligence into workflows.** And I built proof.

---

## What I Built (The Artifact)

### **Project:** Fully Automated, Audit-Grade Equity Research Dashboard for Cathay General Bancorp (CATY)

**What It Does:**
- Fetches live data from SEC EDGAR APIs (10-Q, 10-K, 8-K), FDIC Call Reports, Yahoo Finance market data
- Calculates three valuation models (Wilson Confidence Interval, peer-normalized regression, DDM-based targets)
- Runs reconciliation guards to verify published numbers match calculated outputs (±$0.50 tolerance)
- Generates 17 interactive HTML modules with Chart.js visualizations, canonical color palette, dark mode
- Tracks **full provenance metadata** for every number: which SEC filing, which line item, which API call, which commit

**What Makes It Different:**
- **Not a dashboard builder.** Not a BI tool. Not a data pipeline. It's an **audit-grade knowledge artifact** with Git-tracked lineage for every fact.
- **Not AI-generated slop.** Every module has structured data → calculation script → HTML template → validation gate. If a number changes, the system breaks loudly. By design.
- **Not a prototype.** It's live. It updates daily. It passes pre-commit validation hooks. I can curl the live site and grep for specific facts with provenance URLs.

**GitHub Stats:**
- 65+ commits with detailed messages documenting failures, iterations, and lessons learned
- 31 autogen markers across 17 HTML modules (deterministic templating, not LLM hallucination)
- 3 validation scripts (reconciliation guard, disconfirmer monitor, stale timestamp detector)
- Zero force-pushes, zero "trust me bro" claims — every assertion is testable

**Key Architecture Decision:**
I separated **creative AI (Claude)** from **execution AI (Codex)**. Claude does strategy, architecture, and polish. Codex does grunt work, data wrangling, and systematic refactors. Human (me) holds accountability and runs the validation gates.

**This is the model PwC needs.**

---

## What I Learned (The Hard Way)

### **Lesson 1: AI Without Governance = Vaporware**

I committed "complete" work **four times** before it actually worked. Claude told me it was done. I believed it. Then I ran a test and it failed in 30 seconds.

**The Fix:** Mandatory validation gates. No deploy without passing tests. Document every failure publicly (see: `CLAUDE_ACCOUNTABILITY_OCT21.md` in the repo).

**PwC Translation:** Your $1B AI investment only compounds if you have validation gates at every layer. Not post-hoc review. Gates that **block bad outputs before they reach clients.**

---

### **Lesson 2: Provenance > Performance**

I spent more time building provenance metadata than I did building calculations. Every number has:
- Source URL (SEC EDGAR accession number)
- Extraction method (regex, table parser, API call)
- Calculation logic (Git commit hash)
- Vintage timestamp (when was this data fetched?)

Why? Because when a client asks "Where did this number come from?", I can answer in **5 seconds** with a hyperlink to the exact SEC filing line item.

**PwC Translation:** In audit, provenance isn't nice-to-have. It's the product. AI that can't explain its work is a liability, not an asset.

---

### **Lesson 3: Partner Expertise ≠ Promptable Knowledge (Yet)**

I talked to experienced auditors about what makes a "good" risk assessment. The answers were:
- "You develop a feel for it"
- "Pattern recognition from seeing 100+ clients"
- "Knowing which questions to ask when the numbers look clean but _feel_ wrong"

**That's not in any LLM training set.** That's **muscle memory**. And it's PwC's competitive moat.

But here's the thing: **muscle memory can be canonicalized into heuristics.**

If we could capture how a senior manager triages 50 walkthrough requests, we could build a system that **augments junior staff** instead of replacing them. Not "AI does the audit." **"AI makes the 2nd-year think like a 5th-year."**

---

## The Business Case (What I Want to Build at PwC)

### **Concept:** Partner-in-the-Loop AI Canonicalization System

**Problem:**
- PwC has 364,000+ people. A fraction are partners. Partners have decades of pattern recognition that doesn't transfer to new hires fast enough.
- Audits are bespoke. Every client is different. But the _heuristics_ partners use to navigate ambiguity are **not** bespoke. They're learned. And learning is slow.

**What If:**
- We built a system where partners could **record decision heuristics** (not decisions, heuristics) as they work.
- Example: "When revenue recognition policy changes mid-year, always check for restatement triggers in prior periods."
- Those heuristics get structured, validated, and integrated into an **AI co-pilot** that surfaces them contextually to junior staff during fieldwork.

**Not:**
- ❌ A chatbot that answers questions
- ❌ A search engine over PwC knowledge base
- ❌ An LLM that "summarizes" workpapers

**Instead:**
- ✅ A system that says: "Based on how Sarah (Senior Manager) handled 12 similar clients, here are 3 things to check next."
- ✅ Provenance-tracked: Which partner contributed this heuristic? Which engagements validated it? When was it last updated?
- ✅ Feedback loop: Did the junior staff find this heuristic useful? Did it catch a risk? Did it create false positives?

---

### **Proof of Concept (What I Already Built):**

In the CATY project, I built **valuation reconciliation guards**. Every time a valuation script runs, it:
1. Calculates Wilson target, regression target, normalized target
2. Extracts published targets from README.md and index.html
3. Compares them within ±$0.50 tolerance
4. **Fails the commit if they don't match**

This is a **heuristic I learned from audit**: reconcile calculated vs. recorded. Every time.

I didn't write a 500-line Python script from scratch. I used **AI to scaffold it**, then I **validated it against real data**, then I **integrated it into Git hooks** so it runs automatically.

**That's the model.** Partner defines the heuristic ("always reconcile calculated vs. recorded"). AI scaffolds the implementation. Human validates. System enforces.

---

## What This Means for PwC's Bottom Line

### **Efficiency Gains:**

**Current State:**
- Junior staff spends 40% of time on "figure out what to do next" (asking seniors, reading memos, searching prior-year workpapers)
- Senior staff spends 30% of time answering "how do I…?" questions
- Partners spend 20% of time reviewing work that shouldn't have been done in the first place

**With Partner-in-the-Loop AI:**
- Junior staff gets **contextual heuristics** at the moment of confusion (not 2 hours later after Slack ping)
- Senior staff **contributes heuristics asynchronously** (5 minutes to record a pattern vs. 30 minutes explaining it live)
- Partners review **higher-signal work** because low-hanging errors are caught by validation gates

**Conservative Estimate:**
- 10% efficiency gain across Assurance = **36,000+ people × 10% = 3,600 FTE-equivalent** hours freed up
- Those hours go to: deeper risk analysis, client relationship building, complex judgments (the work AI can't do)

---

### **Quality Gains:**

**Current State:**
- Audit quality issues often trace back to "junior staff didn't know to check X"
- X was obvious to the partner. But the partner wasn't in the room when the decision was made.

**With Partner-in-the-Loop AI:**
- Heuristics surface at the point of work (not during review)
- **Preventive quality** vs. detective quality
- Fewer reperformance requests, fewer review notes, fewer "why didn't we catch this?" postmortems

**This is how you make AI intrinsic to audit workflows.** Not by replacing auditors. By **making every auditor think like the best auditor on the team.**

---

## Why I'm Writing This (The Ask)

I don't want to just do audit at PwC. I want to **reimagine what's possible.**

I built the CATY project on:
- $400/month (Claude + Codex API costs)
- 8GB of RAM (a 2019 MacBook Air)
- One terminal
- 60+ commits of trial, error, and iteration

**Imagine what I could build with PwC's full stack:**
- Access to anonymized audit data across 1000+ clients
- Partnership with experienced seniors/managers/partners to extract heuristics
- PwC's AI infrastructure (not my laptop)
- Validation frameworks from PwC's methodology team
- Legal/compliance guardrails to ensure independence and confidentiality

**I want to build the system I described above.** Partner-in-the-Loop AI Canonicalization. Starting with one service line (Assurance), one workflow (revenue testing), one proof of concept.

Not a deck. Not a prototype. **A production system with Git-tracked provenance and validation gates.**

---

## What Makes Me Qualified (Besides Obsession)

### **Technical Chops:**
- I wrote Python scripts to parse SEC EDGAR HTML, extract tables, validate against XBRL feeds
- I integrated Chart.js visualizations with canonical design systems (not Tailwind defaults slapped on)
- I built Git pre-commit hooks that run reconciliation checks and fail loudly when thresholds are breached
- I architected a system where **every number is traceable** to a source document, API call, or calculation script

### **Audit Mindset:**
- I understand independence. **I checked auditor conflicts before building the CATY peer set.** (See: DEF14A extraction — CATY uses KPMG, peers use KPMG/Deloitte/Crowe. **Zero PwC clients in the dataset.**)
- I understand materiality. I built ±$0.50 tolerance into reconciliation guards (not "close enough," not "approximately," **±$0.50**).
- I understand skepticism. I documented every Claude failure publicly because **trust must be earned, not assumed.**

### **Humility:**
- PwC is a **repository of pure distilled genius.** Partners have muscle memory from hundreds of audits. I'm a 2nd-year.
- I don't know what I don't know. But I know **how to build systems that capture what partners know** and make it scalable.

---

## The Gospel Anchor (Why I Care)

I'm a Christian. My faith shapes how I think about work.

One of my design principles is: **"Faithful in very little, faithful in much" (Luke 16:10).**

In the CATY project, I applied this as:
- Small numbers matter (reconciliation within ±$0.50, not ±$5)
- Small failures documented (every premature "done" claim is in Git history)
- Small habits compound (validation gates, provenance metadata, design system governance)

**This is how I think about AI at PwC:**
- If we're faithful in **small heuristics** (how to check revenue cut-off), we can be faithful in **large transformations** (AI-augmented audit workflows)
- If we're faithful in **small validations** (does this LLM output match policy?), we can be faithful in **large deployments** (enterprise-scale AI co-pilots)
- If we're faithful in **small transparency** (Git-tracked provenance), we can be faithful in **large trust** (clients trust our AI-augmented work product)

**I want to build AI systems that honor this principle.** Not "move fast and break things." **Move deliberately and build trust.**

---

## What Happens Next (If You're Interested)

1. **Review the repo:** https://github.com/nirvanchitnis-cmyk/caty-equity-research-live
   - Check the commit history (60+ commits documenting real iteration, not vaporware)
   - Run the validation scripts (`scripts/reconciliation_guard.py`, `scripts/disconfirmer_monitor.py`)
   - Curl the live site and verify every number has provenance metadata

2. **Let's talk about a pilot:**
   - One service line (Assurance)
   - One workflow (e.g., revenue testing, inventory observation, IT general controls)
   - One proof of concept (partner-in-the-loop heuristic capture → AI co-pilot → validation gates)
   - Three months to production-ready MVP

3. **If it works, scale it:**
   - Other service lines (Tax, Advisory, Consulting)
   - Other workflows (client onboarding, risk assessment, technical accounting research)
   - Integrate with PwC's existing AI stack (not replace it, **augment** it)

---

## Why This Matters for PwC (The Big Picture)

You said: **"AI is becoming intrinsic to every aspect of how companies operate."**

I agree. But **intrinsic ≠ invisible.** Intrinsic means **woven into the fabric**, not hidden under the hood.

**At PwC, that means:**
- AI that auditors **trust** because they understand how it works (provenance-tracked, validation-gated)
- AI that partners **contribute to** because it captures their expertise (not replaces it)
- AI that clients **value** because it makes our work **more rigorous**, not just faster

**This is not about automation. It's about augmentation.**

And I want to build it. With you. At PwC.

---

## Closing Thought

I built the CATY project because I wanted to prove to myself that **AI can be a tool for craft, not just speed.**

Every commit is documented. Every failure is public. Every number is traceable.

**This is not clanker slop.**
**This is not a one-shot prompt.**
**This was built brick by brick.**

And if I can do this on $400/month and 8GB of RAM, **imagine what we can do with PwC's full stack.**

We're at the precipice of something amazing. Let's build it together.

---

**Nirvan Chitnis**
Assurance Associate, PwC
📧 nirvan.chitnis@pwc.com
🔗 https://github.com/nirvanchitnis-cmyk
📍 San Jose, California

---

**P.S. — Independence Verification (Because I'm an Auditor)**

Before building the CATY equity research project, I verified auditor independence for all companies in scope:

| Company | Ticker | Auditor |
|---------|--------|---------|
| Cathay General Bancorp | CATY | KPMG LLP |
| East West Bancorp | EWBC | KPMG LLP |
| CVB Financial | CVBF | KPMG LLP |
| Hanmi Financial | HAFC | Crowe LLP |
| Columbia Banking System | COLB | Deloitte & Touche LLP |
| Banc of California | BANC | KPMG LLP |
| Hope Bancorp | HOPE | Crowe LLP |

**Zero PwC audit clients.** Independence maintained. I built this outside of work, with public data, on my own hardware.

**Source:** DEF 14A proxy statements for each company (2025 filings). Auditor information extracted via automated parser with human validation. See: `data/proxy/*_DEF14A_extracted.json` for full provenance.

This is how I think. Numbers matter. Sources matter. Independence matters.

Let's build AI that thinks the same way.
