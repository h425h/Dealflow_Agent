# Per-Phase Diligence Test Specification

This is the authoritative spec for WHAT each funnel phase tests a company for. When
building or revising a phase's prompt (`orchestrator/prompts.py`), the tests below
are the rubric that phase must apply. Read this alongside `docs/source-paper.md`
(which has the underlying VC framework) and `CLAUDE.md` (the build rules).

Two important distinctions:

1. **Diligence tests vs. system evals.** This document covers *diligence tests* —
   the VC-judgment questions the agent applies to a company. It does NOT cover
   *system evals* (how we verify the agent itself works — connector accuracy,
   verdict validity, the LLM-as-judge harness). Those live in `evals/` and are
   tracked separately in PROGRESS.md.

2. **Tests get progressively more expensive and more thesis-specific deeper in the
   funnel.** Phase 1 is cheap, high-recall exclusion. Phase 4 is costly,
   evidence-heavy analysis. Only companies that survive earlier cuts reach the
   expensive tests. This mirrors the real funnel's economics.

The encoded thesis (see prompts.py) that all tests serve:
- AI startups only — AI is the core product, not a feature.
- Belief A: durable value comes from REPLACING labor end-to-end, not augmenting.
- Belief B: vertical/domain-specific AI beats horizontal — moat is proprietary
  data + distribution in one industry's workflow, not model quality.
- Scoring is WEIGHTED, not strict AND — strong on one belief + decent on the other
  can advance, with the weaker dimension flagged as a caveat.

**Structural humility note (thesis-level, applies system-wide):** This system
sources from PUBLIC signals, so it is structurally prone to surfacing CONSENSUS
deals — companies many investors can already see. Two related risks follow.
(1) Adverse selection: deals that reach a sourcing system easily may be ones
better-informed investors already passed on (MGMT 2640 Epilog). (2) The
non-consensus problem (from source-paper.md): the best venture returns come from
companies that did NOT fit the pattern when funded, which is exactly where a
pattern-matching system is weakest. The system should treat a clean thesis-fit as
necessary-but-not-sufficient and never mistake "everyone can see this is on-thesis"
for "this is a good investment." This is a reason the human-in-the-loop gates
exist, not a bug to engineer away.

---

## Phase 1 — Sourcing (the "one-minute test")

Cheap, high-recall exclusion. The job is to kill obvious non-fits fast, not to
analyze deeply. Verdicts are deliberately humble — thin public signal only.

Tests applied:
- **Domain-boundary test** — Is AI the core product, or a feature bolted onto a
  non-AI product? If the company would exist and generate revenue without AI →
  kill, with that as the sole rationale. (This is a hard gate, deliberately
  stricter than the weighted scoring elsewhere.)
- **Labor-replacement signal (first-pass)** — Any early indication the product
  does an end-to-end job a human was paid to do, vs. merely helping a human do it?
- **Vertical-vs-horizontal signal (first-pass)** — A specific industry wedge, or
  "AI for everyone / every team"?
- **Thesis-fit triage** — Given Beliefs A and B, does this company even belong in
  the funnel? Output: advance / kill / needs-more-info + humble rationale.

Connectors (current + planned): arXiv (live), Tavily web search (M2), GitHub (M2).

---

## Phase 2 — Screening (the "ten-minute test")

A few targeted API calls plus one real reasoning pass. Fund-fit and business-plan
sanity.

Tests applied:
- **Fund-fit / stage check** — Right stage and right kind of company for the
  thesis (adapted from the paper's Stage 2: vintage, sector, stage, geography).
- **Pricing-model classifier** — The single cleanest PUBLIC signal for the thesis.
  Outcome-based / per-task / per-resolution pricing → labor replacement. Per-seat
  pricing → augmentation. Classify the target's pricing page and language
  ("AI worker," "per outcome," "replaces," "ghost team" → replacement).
- **Business-plan completeness** — Does the company describe a real customer, a
  real workflow it enters, a real competitive context? (Paper's Stage 2: does the
  exec summary provoke interest, is the customer described in detail, is
  competition seriously analyzed?)
- **Hiring-signal read** — Job-post composition. Heavy on "forward-deployed /
  founding engineers," light on sales seats can signal a labor-replacement
  product. Explicit "we replaced our SDR team with agents" is a strong signal.

Connectors (planned): Tavily (M2), EDGAR (M3), GitHub (M2).

---

## Phase 3 — Preliminary Evaluation (the "one-hour test")

The reasoning core. Mostly no new connectors — structured reasoning over what
earlier phases gathered. Each question is a rubric field the agent must fill,
citing retrieved evidence or explicitly flagging "data-blind."

### The Six Pensées
- Who are these people? (founder pedigree; domain expertise BEYOND ML)
- What is their business about?
- What are they truly selling?
- What is beyond their control? (the risk surface)
- Will they reach the goal?
- Can we win?

### The Seven Deadly Questions
- Who is the customer?
- Which competitors keep you up at night?
- How far and how fast can they expand?
- How do they make money?
- How much capital is needed, and why?
- What is the business worth?
- Who have they consulted?

### Thesis-specific tests layered in at Phase 3
- **The Clone Test (Menlo Ventures)** — "If you cloned the founding team and
  codebase today and gave the clone access to current frontier models, why
  wouldn't it outcompete the original?" A company with no good answer has no moat.
- **Operationalized labor-replacement test** — "Could you literally remove the
  human from that role and route the output directly to the next step in the
  workflow?" If a human still reviews/corrects before it ships → augmentation.
- **Bull/bear/synthesizer debate** (M3+) — a bull-case agent and bear-case agent
  argue, then a synthesizer renders a view. Directly implements the paper's
  "AI as devil's advocate" point against confirmation bias and escalation of
  commitment. Must include a convergence check / round limit and a forced
  recommendation ("'it depends' is not acceptable").
- **Conjunction-fallacy check (bear-case tool)** — the central venture-math error:
  a plan that requires N independent ~90%-likely things to ALL happen is far less
  likely than it feels (seven 90% steps compound to ~48%). The bear agent must
  explicitly enumerate the company's required-to-succeed assumptions and reason
  about their JOINT probability, not each in isolation. For a labor-replacement AI
  company the chain is typically: the AI genuinely does the job end-to-end AND
  buyers trust it without a human checker AND the vertical's data moat holds AND
  incumbents don't bolt on a good-enough version AND the unit economics survive
  inference costs. Stacking these is where over-optimism hides. (From MGMT 2640
  Cognitive Traps supplement.)

Connectors: none required (pure reasoning); may re-query Tavily for a specific gap.

---

## Phase 4 — Deep Diligence (the "one-hour test and beyond")

The expensive, evidence-heavy phase. Free public registries do real work here.
Reached only by companies that survived Phases 1–3.

Tests applied:
- **AI-washing / capability-reality check** — THE most thesis-critical Phase 4
  test. A labor-replacement thesis has a specific failure mode: companies that
  *claim* to replace labor but are secretly humans-in-a-trenchcoat, or whose AI
  capability is materially overstated. The agent must look for evidence the
  claimed AI actually does what's claimed (technical papers, real product demos,
  third-party validation, customer outcomes) vs. red flags (vague capability
  claims, no technical detail, suspiciously human-paced "automation"). Pair with
  an earnings-quality lens (below). The Builder.ai collapse is the canonical case:
  ~$220M claimed 2024 revenue vs. ~$50M real, AI capabilities that did not exist,
  round-tripped revenue — investors never decomposed real vs. fabricated. For a
  thesis built on "AI replaces labor," verifying the AI is real is not optional.
- **Earnings-quality decomposition** — separate recurring from one-off revenue;
  flag non-market related-party transactions (round-tripping risk); ask whether
  reported growth is real or engineered. Reported revenue is an opinion until
  decomposed. (From MGMT 2640 Diligence Slide 21 + Builder.ai post-mortem.)
- **IP ownership acid test** — IP rights are EXCLUSIONARY, not affirmative: owning
  a patent is the right to sue others, NOT freedom to operate. Three questions
  (MGMT 2640 IP supplement): (1) Who really owns the core technology — is it
  ASSIGNED to the company (recorded) or merely LICENSED, and on what terms (field
  of use, termination, change-of-control)? Founders routinely "have" tech actually
  owned by a former employer, university, or departed co-founder. (2) Integrity of
  patents in hand/pending — what do the claims ACTUALLY cover (often far narrower
  than founders believe) vs. the sector's patent map? (3) Freedom to operate — do
  third-party patents block the product, and are they licensable and at what cost?
- **IP defensibility** — patents (USPTO), claim breadth, prior art. For
  algorithmic AI, the Alice Corp. v. CLS Bank §101 risk (see the DQC example in
  source-paper.md — algorithms on generic platforms can fail §101).
- **Scientific / technical moat** — arXiv + Semantic Scholar citation graph. Is
  the core method novel and defensible, or could an alternative approach make it
  obsolete? Who publishes most prolifically in the space?
- **Data-moat defensibility** — Menlo's defensive vs. generative moat scoring.
  Defensive (regulatory certification, human-sign-off requirements, compliance
  infrastructure) buys time; generative (compounding data, cross-customer signal,
  expanding workflow coverage) widens the gap over time. The best companies have
  both. This is the deep version of Belief B.
- **Unit economics** — LTV/CAC, payback period, contribution margin, ±30%
  sensitivity (paper's framework). Only when financials are supplied; otherwise
  flag data-blind.
- **Regulatory / compliance barriers** — what must clear before launch in target
  markets, with timelines and costs.
- **Team-gap analysis** — skills missing relative to the business model (e.g., the
  academic-founder-needs-a-commercial-CEO insight from the DQC example).

Connectors (planned): USPTO (M3), arXiv (live), EDGAR (M3), Semantic Scholar
(M2/M3).

---

## Phase 5 — Conviction / IC Synthesis (not a funnel filter — a consolidation gate)

The paper's Stage 5. Not new tests; it consolidates everything into a memo and a
recommendation. Implemented in `memo/generator.py` (M3).

Required outputs:
- **Value Creation Plan** — controllable vs. uncontrollable levers (paper: ~70% of
  value creation is within the investor's control).
- **"Does the price reflect the risk?"** — the central IC question.
- **MANDATORY "What this system cannot determine" section** — founder
  trustworthiness, co-founder chemistry, execution grit. Always present, by
  design. This is the honesty gate that keeps the system augmentative, not
  autonomous. It is a required output, never optional.

---

## Appendix — System evals (different axis, tracked in PROGRESS.md, not here)

For completeness, so the two are not confused. These test the AGENT, not the
company:
- **Component evals** (`evals/connector_evals.py`) — does each connector return
  accurate, relevant data for a known input?
- **Phase evals** (`evals/phase_evals.py`) — does each phase return a valid verdict
  (advance/kill/needs-more-info) with non-empty, grounded rationale?
- **End-to-end eval** — does a known company (the DQC worked example as golden-path
  regression fixture) flow through all phases producing sensible verdicts?
- **LLM-as-judge harness** — scores memo/verdict quality against a rubric, paired
  with machine-checkable rewards (valid structured verdict? real sources cited?).