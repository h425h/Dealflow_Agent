# Progress Log

Read this after `README.md` at the start of every session. Update it before ending
one. Keep entries short — this is a log, not documentation. Newest entry on top.

---

## Current milestone

**Milestone 2: Add Tavily + GitHub connectors; wire both into Phase 1.**

`docs/phase-tests.md` is now the authoritative per-phase diligence test spec.
Read it alongside `docs/source-paper.md` before writing any phase logic or prompt.

---

## Milestone 2–4 roadmap

**M2 — Add Tavily + GitHub connectors, wire into Phase 1**
- `connectors/tavily_connector.py` — Tavily web search (feeds Phase 1 + 2 thesis tests
  for labor-replacement signal and vertical go-to-market on pricing pages / company sites)
- `connectors/github_connector.py` — GitHub public repo search (forward-deployed engineer
  hiring signal, open-source activity)
- Phase 1 updated to call arXiv + Tavily + GitHub and synthesize across all three

**M3 — Phases 2–4 + evals + memo**
- `connectors/edgar_connector.py` — SEC EDGAR (fund-fit / stage checks, public financials)
- `connectors/uspto_connector.py` — USPTO PatentsView (IP defensibility for Phase 4)
- Phase 2 (screening): pricing-model classifier, fund-fit/stage check, hiring-signal read
- Phase 3 (preliminary eval): Six Pensées, Seven Deadly Questions, operationalized
  labor-replacement test, Clone Test — pure reasoning, no new connectors
- Phase 4 (deep diligence): IP defensibility, scientific/technical moat, data-moat
  scoring, unit economics (when financials supplied), regulatory barriers
- `evals/connector_evals.py`, `evals/phase_evals.py`
- `memo/generator.py` — full IC-style memo with mandatory "cannot determine" section

**M4+ — LangGraph port (only when migration triggers in README are actually felt)**
- Port `orchestrator/agent.py` → `orchestrator/graph.py`; phases become nodes
- RAG meta-memory via ChromaDB (memo archive)
- Optional paid-data swap-in (Harmonic, PitchBook) via the same Connector interface

---

## Known limitations

- arXiv connector confidence is currently based on result count only, not actual
  relevance — revisit so high-count/low-relevance queries don't read as high confidence.
- Phase 1 confidence is miscalibrated on boundary cases — Abridge returns KILL/0.82
  2-of-3 runs and NEEDS-MORE-INFO/0.52 1-of-3, i.e. high confidence on a verdict that
  isn't stable. Abridge is a known boundary case (labor replacement vs. legally-required
  human attestation — the physician must sign off by law, not because the AI can't do
  the job). Revisit when building confidence calibration + the Phase 3 bull/bear debate,
  which is the right mechanism for boundary cases.

## Eval fixtures

Known companies with expected Phase 1 behavior, to be used when building evals:

| Company | Expected verdict | Expected confidence | Notes |
|---------|-----------------|---------------------|-------|
| Abridge | NEEDS-MORE-INFO or KILL/low | < 0.6 | Boundary case: replaces scribe but legally requires physician attestation. High-confidence KILL is a miscalibration failure. |

---

## Milestone checklist

Check items off as completed. Do not start a milestone before the previous one's
checked items are actually done (not "mostly done").

### Milestone 1 — From-scratch core
- [ ] `requirements.txt` — anthropic, arxiv, requests, python-dotenv only
- [ ] `config.py` — model name + shared constants
- [ ] `connectors/__init__.py`, `orchestrator/__init__.py` (empty)
- [ ] `connectors/base.py` — abstract `Connector` + `ConnectorResult`
- [ ] `connectors/arxiv_connector.py` — real arXiv API calls, mapped to `ConnectorResult`
- [ ] Stub files created for everything else in the tree (tavily/uspto/edgar/github
      connectors, graph.py, evals, memo/generator.py) — docstring + pass only
- [x] `orchestrator/prompts.py` — Phase 1 system prompt (one-minute test criteria)
- [ ] `orchestrator/phases.py` — phase → connector mapping (just phase 1 for now)
- [ ] `orchestrator/agent.py` — agentic loop: Claude + tool use + arXiv, returns verdict
- [ ] `cli/run.py` — runs Phase 1 against a real company name, prints verdict
- [ ] `tests/test_connectors.py` — real smoke test against the arXiv API
- [ ] Tested against at least 2 real companies, output looks sane

### Milestone 2 — Add Tavily + second connector
- [ ] `connectors/tavily_connector.py`
- [ ] Phase 1 uses both arXiv + Tavily
- [ ] `connectors/github_connector.py` (for SaaS-type companies)

### Milestone 3 — Phases 2–4 + evals
- [ ] `connectors/edgar_connector.py`
- [ ] `connectors/uspto_connector.py`
- [ ] Phase 2 (screening) implemented
- [ ] Phase 3 (preliminary eval — no connectors, pure reasoning) implemented
- [ ] Phase 4 (deep diligence) implemented
- [ ] Human-in-the-loop checkpoint between every phase in `cli/run.py`
- [ ] `evals/connector_evals.py` — at least one eval per connector
- [ ] `evals/phase_evals.py` — at least one eval per phase
- [ ] `memo/generator.py` — full run → IC-style memo, including "cannot determine" section

### Milestone 4 — LangGraph port (only if triggers in README are met)
- [ ] Trigger met: ____________________ (write which one, and why)
- [ ] `orchestrator/graph.py` built
- [ ] Old `orchestrator/agent.py` retired or kept for comparison

### Stretch — multi-agent bull/bear
- [ ] Not started

---

## Session log

Add a short entry each session. Format:

```
### YYYY-MM-DD
- What got built
- What broke / open questions
- What's next
```

### 2026-06-26 (session 3)
- Changed `github_connector.py` sort from `stars` to `updated` (recency harder to fake).
- Fixed `agent.py` tool descriptions to be per-connector (GitHub no longer says "research papers").
- Wired `GitHubConnector` into Phase 1 in `phases.py`.
- Updated Phase 1 prompt: added `github_search` tool guidance; flagged `recent_commits_4w`
  null behavior; CRITICAL note that absent GitHub presence is neutral, not negative;
  kept 4-search budget with GitHub as optional 3rd option within it.
- **Run `python3 cli/run.py "Abridge"` (run 489349ff) post-wiring:**
  - Verdict: NEEDS-MORE-INFO (confidence 0.55) — the more calibrated answer for this boundary case
  - Agent correctly skipped `github_search` for Abridge (enterprise healthcare, thin public GitHub)
  - 3 searches used (2 tavily + 1 arxiv + submit_verdict) — within 4-search cap
  - Cost: $0.046 | cache write=2,583 / read=5,166 ✓
- What's next: M2 checklist complete. Move to M3 (Phases 2–4, evals, memo).

### 2026-06-26 (session 2)
- Applied four cost optimizations to Phase 1 run:
  1. `config.py`: `MAX_RESULTS_PER_CONNECTOR` 10 → 5
  2. `connectors/arxiv_connector.py`: `summary` truncated to 500 chars
  3. `connectors/tavily_connector.py`: `content` truncated to 500 chars
  4. `orchestrator/prompts.py`: capped searches at 4 total (was running 6)
  5. `orchestrator/agent.py`: system prompt sent as cache_control block; usage accumulated per call; `usage` field added to `PhaseVerdict`
  6. `cli/run.py`: prints model name at startup + full token/cost breakdown
- **Re-run `python3 cli/run.py "Abridge"` (run 390d04f3)**:
  - Cost: **$0.047** (down from $0.20 — 4.2× reduction)
  - Cache: write=2,274 tokens on call 1; read=4,548 tokens across 2 subsequent calls ✓
  - Search count: 4 (2 tavily + 2 arXiv) — exactly at cap ✓
  - Verdict: KILL (confidence 0.82) — Abridge correctly flagged as augmentation copilot,
    not labor replacement. Strong vertical depth (Epic Pal, KLAS leader) but Belief A
    disqualifier applied cleanly.
- What's next: GitHub connector (pending user go-ahead per task scope)

### 2026-06-26
- Added retry-with-backoff to `orchestrator/agent.py`: catches `anthropic.RateLimitError`,
  sleeps 5s/10s/20s between attempts, re-raises after 4 total attempts.
- **First successful live Phase 1 run** — `python3 cli/run.py "Abridge"` (run 9b022666).
  - 7 tool calls: 4 Tavily + 2 arXiv + submit_verdict.
  - Verdict: NEEDS-MORE-INFO (confidence 0.62).
  - Core tension surfaced correctly: Abridge replaces the scribe role (labor replacement)
    but physician attestation is legally required (augmentation framing). Agent flagged this
    as a gray zone requiring human judgment — exactly the right behavior.
  - Tavily connector returning real signal; arXiv surfacing co-founder's early SOAP note paper.
- Open question: arXiv confidence is based on result count, not relevance — 10 results always
  scores 0.9, which is misleading (noted in Known Limitations).
- What's next: M2 — wire GitHub connector into Phase 1; confirm all three connectors
  (arXiv + Tavily + GitHub) fire in a single Phase 1 run.

### 2026-06-24
- Promoted to Milestone 2; added M2-4 roadmap section to PROGRESS.md.
- Added `docs/phase-tests.md` as authoritative per-phase diligence test spec.
- Built `connectors/tavily_connector.py`: full Connector implementation, TAVILY_API_KEY
  via python-dotenv, graceful error if key missing, results mapped to ConnectorResult.
- Added `tavily-python` to requirements.txt.
- Smoke-tested Tavily connector against a real company query; output confirmed clean.
- What's next: confirm Tavily data quality, then wire arXiv + Tavily into Phase 1;
  then build `connectors/github_connector.py`.

### 2026-06-23
- Built `orchestrator/prompts.py`: PHASE_PROMPTS[1] encoding the full investment thesis
  (labor-replacement vs. augmentation, vertical vs. horizontal, weighted scoring,
  disqualifiers, blind-spot/humility statement, confidence calibration for Phase 1).
- Verdict values use exact hyphenated strings matching submit_verdict enum in agent.py.
- What's next: `orchestrator/phases.py` (phase → connector mapping), then `orchestrator/agent.py` smoke test.

---

## Decisions log

Record any decision that deviates from or adds to the README, so it's not
re-litigated later. Format: decision, one-line reasoning, date.

- **From-scratch before LangGraph** — wanted to understand the agent loop before
  abstracting it; LangGraph only earns its complexity once specific pain is felt.
  (architecture decision, pre-build)
- **Human-in-the-loop always, no autonomous kill** — system should augment
  conviction-building, not replace judgment AI structurally can't make.
  (architecture decision, pre-build)
- **Real company examples, not hypothetical** — stronger demo/resume artifact than
  a hypothetical worked example. (project goal decision, pre-build)
