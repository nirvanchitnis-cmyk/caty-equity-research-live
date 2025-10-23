# An Open Letter to Dan Priest, U.S. Chief AI Officer, PwC

**From:** Nirvan Chitnis, Assurance Associate, PwC
**Date:** October 23, 2025
**Subject:** What I Built on $400/Month and 8GB of RAM — And What We Could Build with PwC's Full Stack

---

## Dear Dan,

I need to show you something. Not a pitch deck, not a concept document, but rather a production system I built in public over 60+ commits, with failures documented in Git history, validation gates passing on every deploy, and zero shortcuts taken. The repository is live at https://github.com/nirvanchitnis-cmyk/caty-equity-research-live, and the deployed site serves at https://nirvanchitnis-cmyk.github.io/caty-equity-research-live/. This is not clanker slop generated from a one-shot prompt. This was built brick by brick, with each commit representing real iteration, real failure, and real learning.

I built this project because I have been obsessed with a question you have been asking the market: "If everybody has intelligence, is intelligence really the differentiator… or are we just driving intelligence into our workflows to achieve the table stakes?" I would argue the answer is neither. The differentiator, I believe, is not whether you have intelligence or even whether you integrate it into workflows, but rather how deliberately and rigorously you structure that integration. And I built proof of concept to demonstrate what that looks like at audit-grade standards.

---

## What I Built (The Artifact)

The project is a fully automated equity research dashboard for Cathay General Bancorp (NASDAQ: CATY), built as my submission for the CFA Institute Research Challenge. The system fetches live data from SEC EDGAR APIs (including 10-Q, 10-K, and 8-K filings), FDIC Call Reports, and Yahoo Finance market data. It calculates three valuation models — specifically, a Wilson Confidence Interval target, a peer-normalized regression target, and a DDM-based target — and runs reconciliation guards to verify that published numbers match calculated outputs within a tolerance of ±$0.50. The system generates 17 interactive HTML modules with Chart.js visualizations, implements a canonical color palette with dark mode support, and tracks full provenance metadata for every number, including which SEC filing it came from, which line item, which API call, and which commit hash performed the calculation.

What makes this different from typical dashboard projects is that it is not a dashboard builder, not a BI tool, and not just a data pipeline. Rather, it is an audit-grade knowledge artifact with Git-tracked lineage for every fact published. This is not AI-generated slop where an LLM hallucinates outputs without verification. Every module follows a deterministic flow: structured data passes through a calculation script, populates an HTML template via autogen markers, and then passes through validation gates. If a number changes unexpectedly, the system breaks loudly, by design. This is not a prototype sitting in a development environment. It is live, it updates daily, it passes pre-commit validation hooks, and I can curl the live site and grep for specific facts with provenance URLs attached.

The repository contains 65+ commits with detailed messages documenting failures, iterations, and lessons learned. There are 31 autogen markers across the 17 HTML modules, ensuring deterministic templating rather than relying on LLM outputs. I implemented three validation scripts — a reconciliation guard, a disconfirmer monitor, and a stale timestamp detector — and the repository has zero force-pushes and zero "trust me bro" claims. Every assertion I make is independently testable by running the scripts against the live data.

The key architecture decision I made was to separate creative AI from execution AI. Claude handles strategy, architecture, and polish — the aspects that require judgment, taste, and contextual understanding. Codex handles grunt work, data wrangling, and systematic refactors — the mechanical tasks that benefit from deterministic execution. The human (me) holds accountability, runs the validation gates, and serves as the final check before anything deploys. This division of labor, I would argue, is the model PwC needs in order to deploy AI at scale while maintaining audit-grade quality controls.

---

## What I Learned (The Hard Way)

### Lesson 1: AI Without Governance Produces Vaporware

In the process of building this system, I committed work labeled as "complete" four separate times before it actually functioned as intended. Claude told me it was done, I believed the output, and then when I ran a test, the system failed within 30 seconds. The fix was to implement mandatory validation gates that block deployment unless tests pass. I documented every failure publicly — there is a file in the repository called `CLAUDE_ACCOUNTABILITY_OCT21.md` that catalogs each premature "all clear" claim and what broke when I actually tested it.

The translation to PwC is straightforward. Your $1 billion AI investment only compounds returns if you have validation gates at every layer of the system. Not post-hoc review conducted weeks later, but rather gates that block bad outputs before they reach clients. In the same way that we require reconciliations in audit before signing off on financial statements, AI systems should require validation before publishing outputs.

### Lesson 2: Provenance Matters More Than Performance

I spent considerably more time building provenance metadata than I spent building the actual calculations. Every number in the system has four pieces of metadata: the source URL (such as the SEC EDGAR accession number), the extraction method (whether it came from regex parsing, table extraction, or an API call), the calculation logic (referenced by Git commit hash), and the vintage timestamp indicating when the data was fetched.

The reason I prioritized this is because when a client asks "Where did this number come from?", I can answer in approximately five seconds with a hyperlink to the exact line item in the SEC filing. In audit, provenance is not a nice-to-have feature. It is the product. AI that cannot explain its work, that cannot trace its outputs back to authoritative sources, is a liability rather than an asset. This is particularly true in contexts where independence and professional skepticism are regulatory requirements, not just best practices.

### Lesson 3: Partner Expertise Is Not Yet Promptable Knowledge

I spoke with several experienced auditors about what makes a "good" risk assessment, and the answers I received were consistently qualitative rather than procedural. They described developing "a feel for it" based on pattern recognition from seeing 100+ clients over multiple years. They mentioned knowing which questions to ask when the numbers look clean on paper but something feels wrong. That tacit knowledge, that muscle memory from hundreds of engagements, is not in any LLM training set. It is PwC's competitive moat.

However, I would argue that muscle memory can be canonicalized into heuristics. If we could systematically capture how a senior manager triages 50 walkthrough requests, we could build a system that augments junior staff rather than replacing them. The goal would not be "AI does the audit" but rather "AI makes the second-year associate think like a fifth-year senior." The junior staff member still performs the work, still applies judgment, but they have access to the pattern recognition that normally takes years to develop.

---

## The Business Case (What I Want to Build at PwC)

### Concept: Partner-in-the-Loop AI Canonicalization System

The problem we face is one of knowledge transfer at scale. PwC employs more than 364,000 people globally, and only a fraction of those are partners. Partners possess decades of pattern recognition accumulated across hundreds of engagements, but that expertise does not transfer to new hires quickly enough. Although every audit engagement is bespoke and every client is different, the heuristics that partners use in order to navigate ambiguity are not bespoke. They are learned patterns that accumulate over time, and the learning process is inefficient.

What if we built a system where partners could record decision heuristics — not specific decisions tied to individual engagements, but rather generalizable patterns — as they perform their work? For example, a partner might encode the heuristic: "When revenue recognition policy changes mid-year, always check for restatement triggers in prior periods." Those heuristics would be structured, validated against historical engagements, and then integrated into an AI co-pilot that surfaces them contextually to junior staff during fieldwork.

This would not be a chatbot that answers questions in isolation, nor would it be a search engine over the PwC knowledge base, nor would it be an LLM that simply summarizes workpapers. Instead, the system would say: "Based on how Sarah (Senior Manager) handled 12 similar clients over the past three years, here are three specific things you should check next on this engagement." The system would be provenance-tracked, indicating which partner contributed each heuristic, which engagements validated it, and when it was last updated. There would be a feedback loop where junior staff indicate whether the heuristic was useful, whether it caught a risk, or whether it generated false positives that wasted time.

### Proof of Concept: What I Already Built

In the CATY project, I built valuation reconciliation guards that demonstrate this concept at a smaller scale. Every time a valuation script runs, the system performs four steps: it calculates the Wilson target, the regression target, and the normalized target; it extracts the published targets from README.md and index.html; it compares them within a tolerance of ±$0.50; and it fails the commit if the values do not match. This embodies a heuristic I learned from audit training: always reconcile calculated values against recorded values. Every time.

I did not write a 500-line Python script from scratch in order to implement this. Instead, I used AI to scaffold the initial implementation, then validated it against real data from the SEC filings, and finally integrated it into Git pre-commit hooks so that it runs automatically on every commit. The model is: partner defines the heuristic (in this case, "always reconcile calculated versus recorded"), AI scaffolds the implementation, human validates that the implementation matches the intent, and then the system enforces the heuristic going forward.

---

## What This Means for PwC's Bottom Line

### Efficiency Gains

The current state of knowledge transfer in Assurance is inefficient. Based on conversations with senior staff, junior associates spend approximately 40% of their time figuring out what to do next — asking seniors for guidance, reading prior-year memos, and searching through workpapers for relevant precedent. Senior staff, in turn, spend roughly 30% of their time answering "how do I…?" questions from junior associates. Partners spend approximately 20% of their review time identifying work that should not have been done in the first place, because the junior staff member did not know which procedures were actually necessary.

With a Partner-in-the-Loop AI system, junior staff would receive contextual heuristics at the moment of confusion, rather than two hours later after waiting for a response on Slack. Senior staff would contribute heuristics asynchronously, spending five minutes to record a pattern rather than 30 minutes explaining it live during a call. Partners would review higher-signal work, because low-hanging procedural errors would be caught by validation gates before review even begins.

A conservative estimate of the efficiency gain would be approximately 10% across Assurance. Given that Assurance employs more than 36,000 people at PwC globally, a 10% efficiency gain translates to roughly 3,600 FTE-equivalent hours freed up annually. Those hours could be reallocated to deeper risk analysis, client relationship building, and complex judgments — the work that AI fundamentally cannot do because it requires human judgment and professional skepticism.

### Quality Gains

Audit quality issues, in many cases, trace back to situations where junior staff did not know to check a specific risk factor. The partner knew that the risk factor was relevant, but the partner was not in the room when the junior staff member made the decision about which procedures to perform. With a Partner-in-the-Loop AI system, heuristics would surface at the point of work rather than during review. This represents a shift from detective quality controls (catching errors after they happen) to preventive quality controls (blocking errors before they occur). The result would be fewer reperformance requests, fewer review notes, and fewer postmortem discussions about "why didn't we catch this during fieldwork?"

This is how you make AI intrinsic to audit workflows. Not by replacing auditors with AI, but rather by making every auditor think like the best auditor on the team.

---

## Why I'm Writing This (The Ask)

I do not want to simply perform audits at PwC for the next several years. I want to reimagine what is possible when you combine audit methodology with AI architecture. I built the CATY project on $400 per month in API costs (Claude plus Codex), 8GB of RAM on a 2019 MacBook Air, access to one terminal window, and 60+ commits of trial, error, and iteration.

Imagine what I could build with PwC's full stack. I would have access to anonymized audit data across more than 1,000 clients, partnership with experienced seniors, managers, and partners in order to extract heuristics from real engagements, PwC's AI infrastructure rather than my personal laptop, validation frameworks developed by PwC's methodology team, and legal and compliance guardrails to ensure that independence and confidentiality are maintained throughout.

I want to build the system I described above. Partner-in-the-Loop AI Canonicalization, starting with one service line (Assurance), one workflow (such as revenue testing), and one proof of concept. Not a pitch deck, not a prototype sitting in a demo environment, but rather a production system with Git-tracked provenance and validation gates that runs on live engagements.

---

## What Makes Me Qualified (Besides Obsession)

### Technical Competence

I wrote Python scripts that parse SEC EDGAR HTML filings, extract tables from semi-structured data, and validate outputs against XBRL feeds. I integrated Chart.js visualizations with a canonical design system, ensuring that the color palette is consistent across all 17 modules rather than relying on Tailwind defaults. I built Git pre-commit hooks that run reconciliation checks and fail loudly when thresholds are breached, preventing commits that contain unreconciled data. I architected a system where every number is traceable to a source document, an API call, or a calculation script, with full lineage documented in provenance metadata.

### Audit Mindset

I understand independence. Before building the CATY peer set, I extracted auditor information from DEF 14A proxy statements for all seven banks in the dataset. CATY is audited by KPMG, and the peer banks are audited by KPMG, Deloitte, and Crowe. There are zero PwC audit clients in the dataset, which means independence is maintained. I built this project outside of work hours, using only public data, on my own hardware.

I understand materiality. The reconciliation guards I built enforce a tolerance of ±$0.50, not "close enough" or "approximately." If the published Wilson target differs from the calculated Wilson target by more than 50 cents, the commit fails. This level of precision is arguably stricter than what would be required for equity research, but I implemented it because I believe that small tolerances compound into trust over time.

I understand professional skepticism. I documented every instance where Claude claimed the work was complete but testing revealed it was not. There is a public accountability document in the repository that catalogs each failure, because I believe that trust must be earned through transparency rather than assumed through authority.

### Humility

PwC is a repository of distilled expertise accumulated over decades. Partners have muscle memory from hundreds of audits, and I am a second-year associate who has seen a fraction of that experience. I do not claim to know what I do not know. However, I do know how to build systems that capture what partners know and make that knowledge scalable to junior staff who are still developing their judgment.

---

## The Gospel Anchor (Why I Care)

I am a Christian, and my faith shapes how I think about work. One of my guiding principles is taken from Luke 16:10: "Faithful in very little, faithful in much." In the CATY project, I applied this principle in several ways. Small numbers matter, which is why the reconciliation tolerance is ±$0.50 rather than ±$5. Small failures matter, which is why every premature "done" claim is documented in the Git history rather than deleted or hidden. Small habits compound, which is why I implemented validation gates, provenance metadata, and design system governance from the beginning rather than adding them as afterthoughts.

This is how I think about AI at PwC as well. If we are faithful in implementing small heuristics correctly (such as how to check revenue cut-off testing), then we can be faithful in deploying large-scale transformations (such as AI-augmented audit workflows across thousands of engagements). If we are faithful in validating small AI outputs (ensuring that LLM outputs match policy guidance), then we can be faithful in trusting large deployments (enterprise-scale AI co-pilots used across all service lines). If we are faithful in maintaining small acts of transparency (Git-tracked provenance for every calculation), then we can be faithful in earning large measures of trust (clients trusting our AI-augmented work product).

I want to build AI systems that honor this principle. Not "move fast and break things," but rather "move deliberately and build trust."

---

## What Happens Next (If You're Interested)

First, I would ask you to review the repository at https://github.com/nirvanchitnis-cmyk/caty-equity-research-live. Check the commit history to see 60+ commits documenting real iteration rather than vaporware. Run the validation scripts (located at `analysis/reconciliation_guard.py` and `analysis/disconfirmer_monitor.py`) to verify that the published numbers reconcile to the calculations. Curl the live site and grep for specific numbers to verify that every value includes provenance metadata linking back to the source.

Second, if the repository demonstrates sufficient rigor, I would propose that we discuss a pilot project. The pilot would target one service line (Assurance), one workflow (such as revenue testing, inventory observation, or IT general controls), and one proof of concept (partner-in-the-loop heuristic capture, integrated into an AI co-pilot, with validation gates to ensure quality). The timeline would be three months to deliver a production-ready MVP that could be tested on live engagements.

Third, if the pilot succeeds, we could scale the system to other service lines (Tax, Advisory, Consulting), other workflows (client onboarding, risk assessment, technical accounting research), and integrate it with PwC's existing AI stack. The goal would not be to replace PwC's current AI investments, but rather to augment them with audit-grade provenance and validation that ensures outputs are trustworthy.

---

## Why This Matters for PwC (The Big Picture)

You said in a recent interview: "AI is becoming intrinsic to every aspect of how companies operate." I agree with that statement, but I would add a qualification. Intrinsic does not mean invisible. Intrinsic means woven into the fabric of daily operations, but it should still be explicable and auditable.

At PwC, that means building AI systems that auditors trust because they understand how the systems work (provenance-tracked, validation-gated, deterministic outputs). It means building AI systems that partners contribute to because the systems capture their expertise rather than replacing them. It means building AI systems that clients value because the systems make our work more rigorous, not merely faster.

This is not about automation for the sake of cost reduction. It is about augmentation in order to elevate the quality of professional judgment across the entire organization. And I want to build it, working alongside you, at PwC.

---

## Closing Thought

I built the CATY project because I wanted to prove to myself that AI can be a tool for craft rather than simply a tool for speed. Every commit is documented in the Git history. Every failure is publicly acknowledged in the accountability files. Every number is traceable to its authoritative source with full provenance metadata.

This is not clanker slop. This is not a one-shot prompt. This was built brick by brick, with validation at every layer.

And if I can build this level of rigor on $400 per month and 8GB of RAM, imagine what we could build together with PwC's full stack.

We are at the precipice of something significant. I would be honored to build it alongside you.

---

**Nirvan Chitnis**
Assurance Associate, PwC
https://github.com/nirvanchitnis-cmyk

---

## P.S. — Independence Verification (Because I'm an Auditor)

Before building the CATY equity research project, I verified auditor independence for all companies in the dataset. The results are as follows:

| Company | Ticker | Auditor |
|---------|--------|---------|
| Cathay General Bancorp | CATY | KPMG LLP |
| East West Bancorp | EWBC | KPMG LLP |
| CVB Financial | CVBF | KPMG LLP |
| Hanmi Financial | HAFC | Crowe LLP |
| Columbia Banking System | COLB | Deloitte & Touche LLP |
| Banc of California | BANC | KPMG LLP |
| Hope Bancorp | HOPE | Crowe LLP |

There are zero PwC audit clients in the dataset. Independence has been maintained throughout the project. I built this outside of work hours, using public data exclusively, on my personal hardware.

The source of this verification is the DEF 14A proxy statements filed by each company in 2025. Auditor information was extracted via an automated parser that I built, with human validation to ensure accuracy. Full provenance is available in the repository at `data/proxy/*_DEF14A_extracted.json`.

This is how I approach professional work. Numbers matter. Sources matter. Independence matters.

I want to build AI systems at PwC that embody the same level of precision and accountability.
