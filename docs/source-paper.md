# Source Paper: Using Generative AI to Augment the Deal Flow Building Process in VC

Original: MGMT 2640, Wharton School, Spring 2026 (Harsh Mishra). This is the
foundational document for this project — the four-phase funnel, decision points,
and AI-tool mapping below are the actual design basis for the orchestrator's
phases and prompts. Read this before writing any phase logic or system prompts.

---

## 1. The VC Deal Flow Funnel

Deal flow is a sorting funnel: leads are continually filtered until very few
remain and get funded (Goldman Sachs Merchant Banking benchmark: ~2,000 leads →
300 meetings → 150 pursued → 20–50 funded, a 1–2% conversion rate).

Four phases, increasing commitment and analysis at each stage:

- **Phase I — Exogenous Pre-Qualifiers** ("one-minute test"): fund fit, stage,
  geography, sector, portfolio strategy. Factors *outside* the company itself.
  Most deals die here without the plan even being read closely.
- **Phase II — General Endogenous Qualifiers** ("ten-minute test"): company
  background, origin of technology, team, capital structure, business plan
  quality/completeness.
- **Phase III — Specific Merits** ("one-hour test and beyond"): management,
  technology, operations, finance, legal/IP — the intrinsic qualities of the
  firm and team.
- **Phase IV — Getting to Yes**: valuation negotiation, term sheet, milestones,
  budgets, closing.

Three structural problems run through the whole process:
1. **Information asymmetry** — the entrepreneur knows far more than the investor.
2. **Cognitive traps** — confirmation bias, escalation of commitment, recency
   bias, anchoring, story bias, similarity bias.
3. **Bandwidth limitations** — one VC juggling many boards/deals simultaneously.

Deal flow requires both **CONVICTION** (deep belief the business will succeed)
and **ANGLES** (unique advantages: connections, sector knowledge, research,
speed, a unique Value Creation Plan, seller preference, expertise).

## 2. Decision Points by Stage (five stages, mapped onto the four phases above)

**Stage 1 — Sourcing and Signal Detection.** Which sectors to monitor? Which
founders to watch? Is a researcher's defection from a major tech company a
signal of a new company forming? Key: thesis fit + timing.

**Stage 2 — Initial Screening.** One-minute and ten-minute tests. Fit to fund
vintage/size/check size/portfolio construction, sector, stage, geography. Is
the business plan complete and sophisticated — does the executive summary
provoke interest, is the customer described in detail, is competition seriously
analyzed?

**Stage 3 — Preliminary Evaluation.** The **Six Pensées**: Who are these
people? What is their business about? What are they truly selling? What
cannot be controlled? Will they reach the goal? Can we win? Plus the **Seven
Deadly Questions**: Who is your customer? Who are the competitors that worry
you most? How far and fast can you expand? How do you make money? How much
capital is needed and why? What's the business worth? Who have you consulted?

**Stage 4 — Deep Evaluation and Due Diligence.** Validate technology, check IP,
gauge market size, assess competition, evaluate management, stress-test
financials. Is the IP defensible? Is unit economics sound? Can the model
survive sensitivity testing? Real options framing: milestones = options to
invest further or pull out.

**Stage 5 — Conviction Building and IC.** Internal alignment. The investment
memo synthesizes all diligence into one story. The IC presentation must
address risk vs. uncertainty, name unacceptable binary risks, present the
Value Creation Plan, and answer: **does the price reflect the risk?**

## 3. AI Tools Mapped to Each Decision Point

| Function | Tools | Notes |
|---|---|---|
| Sourcing / signal detection | Harmonic, Grata, Synaptic | Harmonic tracks 30M+ companies via public signal classification (LinkedIn updates, domain registration, hiring, founder departures) — detects company formation before any press release. Not free/accessible to us — see "What we can't replicate" below. |
| Relationship intelligence / CRM | Affinity | Finds warm intro paths automatically from email/calendar data. Not accessible to us — internal/proprietary by nature. |
| Competitive intelligence / market research | PitchBook, CB Insights | Funding data, predictive analytics, market sentiment. Paid/enterprise — not accessible to us. |
| Due diligence / memo writing | Claude, ChatGPT, Perplexity | **This is what we're building with.** LLMs synthesize market research, financial modeling, competitive analysis, bull/bear scenarios, memo drafts. |
| Alternative/demand-signal data | Sensor Tower, SimilarWeb, Bombora | App downloads, web traffic, B2B intent data. Paid — not accessible to us. |

### What we can and can't actually replicate

This matters for the project's honesty: Harmonic, Affinity, PitchBook, CB
Insights are enterprise tools costing tens of thousands of dollars a year. We
are **not** replicating them. We are building the **orchestration and reasoning
layer** — the part that decides what to ask, synthesizes findings, and flags
risk — using free/public data sources as a stand-in for what a real fund's paid
stack would feed in. The connector interface is deliberately designed so a real
Harmonic/PitchBook API key could later be swapped in without changing the
orchestrator.

**Free/public sources we use instead:**
- arXiv, Google Scholar, Semantic Scholar — academic signal, pre-commercialization research
- USPTO / EPO patent search — IP filings, claims, prior art
- SEC EDGAR — organizational structure, filings, fundraising history
- GitHub — open-source activity, team technical signal
- General web search (Tavily, agentic search) — news, hiring signals, domain registrations

## 4. Logical Question Sequences (the actual prompt patterns from the paper)

These are the field-tested question templates from the paper — use these as the
starting point for `orchestrator/prompts.py`, adapted per phase:

**Sourcing (→ arXiv/Tavily/GitHub connector queries):**
- "Name all firms founded within the last two years in [technology/industry]
  with founders who worked as executives at [relevant incumbents/research
  institutions]."
- "Name founders who recently left [key competitors] in the last three months
  and show signs of forming a business — domain registration, LinkedIn updates,
  hiring."

**Screening (→ EDGAR/Tavily, reasoning against fund criteria):**
- "How does the financing landscape look for [sector] startups? Funding by
  year, deal counts by round, median round size, leading institutional
  investors."
- "Draw a competitive map for [category]: companies with Series A+, their
  capabilities, investors, headcount trends."

**Preliminary evaluation (→ pure LLM reasoning, no connector — this is Phase 3):**
- "Analyze TAM for [product]. Name early adopters. What's the switching cost?"
- "Develop bull and bear cases for investing in [Company X] at [$_M] Series
  [_]. What assumptions get to a 10x return in 5 years? List three risk
  factors."
- "Evaluate the leadership team given these bios [insert]. What skill gaps
  exist relative to the business model's demands?"
- "What are the twelve most dangerous implicit assumptions in [Company X]'s
  business model?" (Discovery-Driven Planning framework, McGrath & MacMillan)

**Deep diligence (→ USPTO/arXiv/EDGAR connectors + synthesis):**
- "Search USPTO/EPO filings for [Company X] or its founders. Do patents
  provide strong protection? How broad are the claims? Does prior art exist
  that could invalidate novelty? Would core claims survive an Alice Corp. v.
  CLS Bank Section 101 challenge?"
- "Review the last 50 publications in [core tech area] on arXiv/Google
  Scholar. Who publishes most prolifically? What methodologies are gaining
  citation traction? Could any alternative approach make this technology
  obsolete?"
- "Determine unit economics given [ASP, COGS, CAC, LTV assumptions]. Compute
  LTV/CAC, payback period, contribution margin. Sensitivity test ±30% on each
  variable."

**Conviction-building (→ memo generator, end of pipeline):**
- "Write an investment memo for [Company X], raising [$_M] Series [_], based
  on these diligence findings: [...]. Include risks + mitigations, value
  inflection points, use of proceeds, competition, VC-method valuation."
- "Role-play an IC discussion. State the three best reasons to invest and
  three best reasons to pass. For each reason to pass, propose a structural
  fix (deal structure, milestone tranches, conditions precedent)."
- "Which cognitive bias — confirmation, escalation of commitment, anchoring,
  similarity bias — is most likely influencing this deal team's analysis of
  [Company X], based on the diligence report?"

## 5. Worked Example in the Paper: Democritus Quantum Computers (DQC)

A hypothetical Delaware C-corp, founder Dr. T.B. Franklin (academic, "Franklin
Algorithms" for quantum noise reduction), raising $25M Series A, pre-revenue,
patents pending, IBM as prospective investor.

Key findings from the paper's walkthrough (useful as a sanity check for our
system's own output later — if our real-company runs produce reasoning this
sharp, we're on track):

- **Sourcing**: Harmonic-style signal detection would catch incorporation +
  early quantum-physicist hiring + domain registration as a compound signal.
- **IP risk**: Algorithms alone are unpatentable under *Alice Corp. v. CLS Bank*
  (2014) Section 101 two-step test — but running on a quantum computing
  platform plausibly avoids this per *Ex parte Yudong Cao* (USPTO PTAB, Feb
  2025). Patents pending (not granted) + weak international protection (EPO,
  most Asian offices) = real risk, correctly flagged as a binary risk to
  resolve, not necessarily a kill.
- **Valuation (VC method)**: $25M raise, 50% target IRR, 5-year horizon, $500M
  terminal value → ~$65.8M discounted terminal value → ~79% required ownership
  today (accounting for future dilution) → ~$6.5M pre-money. Notably *lower*
  than what a company with IBM co-investment and patents pending would expect
  — a classic negotiation friction point AI can surface fast by running many
  input combinations.
- **What AI could not determine**: Dr. Franklin's trustworthiness as a
  collaborator, IBM's actual commitment level, whether the team can pivot
  under pressure. These remain explicitly human judgment calls.

## 6. Database Reliability Assessment (this is where `confidence` in
`ConnectorResult` comes from)

- Commercial databases (PitchBook/Crunchbase) are strong on funded companies,
  blind to pre-seed/bootstrapped ones.
- Harmonic-style signal inference introduces noise — a "high momentum" signal
  might just mean a well-funded services company, not a real tech venture.
- Patent databases are reliable on filed content but blind to trade secrets,
  know-how, and prosecution likelihood — claim wording assessment still needs
  a human/domain expert.
- Academic databases (arXiv) front-run breakthroughs well but require domain
  knowledge to interpret — partially, not fully, covered by an LLM.
- **The most reliable information is the information AI cannot access at
  all**: CRM history, IC minutes, back-channel reputation. This is structural,
  not a tooling gap — proprietary firm memory will never be in a public API.

## 7. Recommendations from the Paper (these became this project's design principles)

1. AI-native sourcing should augment, not replace, relationship-based deal flow.
2. Proprietary datasets (CRM, IC archives) are the real moat — connecting them
   to AI is higher-value than adding more external sourcing tools.
3. Cognitive bias should be explicitly countered by AI — devil's advocate,
   bear-case generation, assumption-testing. **(This is the stretch-goal
   multi-agent bull/bear pattern in our README.)**
4. AI-powered sourcing has real equity/bias risks — training data overrepresents
   founders from prestigious networks and historically funded demographics.
5. **The non-consensus problem**: the best investments (Google, Airbnb,
   SpaceX) didn't fit historical patterns when funded. An AI trained on past
   success will be weakest exactly where the best returns live. This is a
   genuine, unsolved limitation of pattern-matching approaches — not something
   our system should claim to solve.

## 8. Why this project is human-in-the-loop by design

From the paper's own reflection: *"Diligence involves making eye contact."* No
model can replace reading founder character, gauging co-founder chemistry, or
assessing grit under pressure. AI expands the *scope* of rigor in diligence —
it does not replace judgment. This is the explicit design thesis behind every
phase checkpoint in this system: the agent presents findings, a human decides.
