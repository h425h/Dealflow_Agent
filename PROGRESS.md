# Progress Log

Read this after `README.md` at the start of every session. Update it before ending
one. Keep entries short — this is a log, not documentation. Newest entry on top.

---

## Current milestone

**Milestone 3: Phases 2–4 + evals + memo.** Eval harness (`evals/connector_evals.py`,
`evals/phase_evals.py`) is now built and passing — see Eval fixtures and Known
Limitations below. Phase 2 (screening) and Phase 3a (preliminary eval — structured
reasoning rubric) are built. Remaining M3 work: Phase 3b (bull/bear/synthesizer
debate), Phase 4 (deep diligence), EDGAR/USPTO connectors, `memo/generator.py`.

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
- Phase 3 (preliminary eval), split into two builds:
  - **3a (built)**: Six Pensées, Seven Deadly Questions, operationalized
    labor-replacement test, Clone Test — structured rubric, pure reasoning over
    Phase 1-2 findings, one optional gap-filling search, DATA-BLIND honesty rule.
  - **3b (not started)**: bull/bear/synthesizer debate wrapped around the 3a
    rubric — deliberately deferred until 3a's reasoning quality is verified.
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

- **arXiv confidence-by-count issue (still open, TODO).** arXiv connector confidence
  is based on result count only, not actual relevance. `evals/connector_evals.py` now
  has a live regression case for this (`arxiv / absence`): a nonsense query returns 5
  fully irrelevant papers (arXiv's full-text search does OR-matching on words like
  "Fictitious"/"Startup") and count-based scoring reads that as 0.9 confidence — a
  false-positive signal, not graceful absence. Marked XFAIL/known-issue so it's
  tracked and visible on every eval run without blocking the suite. Fix: switch
  confidence to something relevance-aware (e.g. weight by title/abstract keyword
  overlap with the query, not just `len(items)`).
- **Abridge boundary-case instability (still open, TODO).** Phase 1 confidence is
  miscalibrated on boundary cases. Historical runs (pre-eval-harness, sessions 1-3):
  KILL/0.82 2-of-3, NEEDS-MORE-INFO/0.52-0.62 1-of-3. **Fresh 5-run batch via the eval
  harness (2026-07-08, run against the current arXiv+Tavily+GitHub Phase 1):
  KILL 3/5 (confidence 0.72, 0.75, 0.78), NEEDS-MORE-INFO 2/5 (confidence 0.50, 0.52).**
  Reporting this honestly: the instability is NOT resolved — verdict still flips
  between two different searches finding slightly different framing language on
  Abridge's site/press (physician-review vs. autonomous-billing wording). Confidence
  is at least now consistently in the 0.5-0.8 range rather than spiking to 0.9+, which
  is an improvement, but the verdict itself is still a coin flip across identical runs.
  Abridge is a known boundary case (labor replacement vs. legally-required human
  attestation — the physician must sign off by law, not because the AI can't do the
  job). Revisit when building confidence calibration + the Phase 3 bull/bear debate,
  which is the right mechanism for boundary cases.
  **PREDICTION:** Abridge's verdict instability is expected to resolve via the
  Phase 3 bull/bear debate. Success criterion for that feature: the bull and bear
  agents genuinely disagree, the synthesizer fails to converge, and Abridge lands
  on NEEDS-MORE-INFO for structural reasons rather than sampling luck.
  **CONSISTENCY FINDING (2026-07-09, supports the prediction above):** Chatbase
  returned KILL/0.82 independently in both Phase 1 and Phase 2, via two entirely
  different tests (Phase 1: domain-boundary + belief scoring off arXiv/Tavily;
  Phase 2: pricing-model classifier + hiring-signal read off Tavily only).
  Independent phases converge tightly on unambiguous companies, while Abridge
  (a genuine thesis-boundary case) diverges across identical runs of the same
  phase. This suggests the verdict instability is specific to genuine
  thesis-boundary cases, not general system flakiness — which supports the
  prediction that Phase 3's bull/bear debate (built for exactly this kind of
  boundary disagreement) is the right structural fix, rather than a symptom of
  an unreliable pipeline that needs fixing elsewhere.
- **Eval gap: no fixture tests "github_search correctly included."** All 6 companies
  in the current Phase 1 fixture batch (Slang.ai, Chatbase, Glean, Rogo, Abridge,
  EvenUp) are closed-source enterprise SaaS, so the agent correctly skipped
  `github_search` in all 10 runs. `evals/phase_evals.py` checks the skip side of the
  "closed source = skip" rule but has zero coverage on the opposite case (an
  open-source-adjacent dev-tool company where `github_search` should fire). Add one
  such fixture when the batch is next regenerated.
- **EvenUp is not a clean fixture, kept as an unasserted bonus.** Picked as a
  "should ADVANCE" candidate but the live run surfaced real public evidence that
  EvenUp "relies on a mix of AI and human drafters" — a genuine Belief-A ambiguity,
  not a system bug. Landed NEEDS-MORE-INFO (confidence 0.50), which is actually the
  well-reasoned answer. Saved as `evals/fixtures/evenup.json` but not used in the
  verdict-direction assertions; Slang.ai replaced it as the asserted "clear advance"
  vertical-labor-replacement fixture.

## Eval fixtures

Phase 1 fixture batch generated 2026-07-08 via the live agent (arXiv + Tavily +
GitHub), saved to `evals/fixtures/`, loaded by `evals/phase_evals.py`:

| Company | Verdict | Confidence | Asserted? | Notes |
|---------|---------|-----------|-----------|-------|
| Slang.ai | ADVANCE | 0.72 | yes (expect advance) | Vertical (restaurants), full phone-answering automation, no human review before output ships. |
| Chatbase | KILL | 0.85 | yes (expect kill) | Horizontal GPT wrapper, no vertical moat. |
| Glean | KILL | 0.85 | yes (expect kill) | Horizontal enterprise search/assistant, explicit "AI coworker" augmentation framing. |
| Rogo | ADVANCE | 0.78 | yes (expect advance) | Vertical (investment banking), explicit junior-analyst-replacement framing. |
| Abridge | KILL 3/5, NEEDS-MORE-INFO 2/5 | 0.72-0.78 (KILL) / 0.50-0.52 (NMI) | no — distribution reported, not a single verdict | Boundary case, see Known Limitations above. |
| EvenUp | NEEDS-MORE-INFO | 0.50 | no — bonus/unasserted | See Known Limitations above; kept because it's a legitimately interesting ambiguous case. |

---

## Milestone checklist

Check items off as completed. Do not start a milestone before the previous one's
checked items are actually done (not "mostly done").

### Milestone 1 — From-scratch core
- [x] `requirements.txt` — anthropic, arxiv, requests, python-dotenv only
- [x] `config.py` — model name + shared constants
- [x] `connectors/__init__.py`, `orchestrator/__init__.py` (empty)
- [x] `connectors/base.py` — abstract `Connector` + `ConnectorResult`
- [x] `connectors/arxiv_connector.py` — real arXiv API calls, mapped to `ConnectorResult`
- [x] Stub files created for everything else in the tree (tavily/uspto/edgar/github
      connectors, graph.py, evals, memo/generator.py) — docstring + pass only
- [x] `orchestrator/prompts.py` — Phase 1 system prompt (one-minute test criteria)
- [x] `orchestrator/phases.py` — phase → connector mapping (just phase 1 for now)
- [x] `orchestrator/agent.py` — agentic loop: Claude + tool use + arXiv, returns verdict
- [x] `cli/run.py` — runs Phase 1 against a real company name, prints verdict
- [x] `tests/test_connectors.py` — real smoke test against the arXiv API
- [x] Tested against at least 2 real companies, output looks sane

### Milestone 2 — Add Tavily + second connector
- [x] `connectors/tavily_connector.py`
- [x] Phase 1 uses both arXiv + Tavily
- [x] `connectors/github_connector.py` (for SaaS-type companies)

### Milestone 3 — Phases 2–4 + evals
- [ ] `connectors/edgar_connector.py`
- [ ] `connectors/uspto_connector.py`
- [x] Phase 2 (screening) implemented
- [x] Phase 3a (preliminary eval — structured reasoning rubric) implemented
- [ ] Phase 3b (bull/bear/synthesizer debate) implemented
- [ ] Phase 4 (deep diligence) implemented
- [x] Human-in-the-loop checkpoint between every phase in `cli/run.py` (Phase 1 →
      2 → 3 gates built; will extend as Phase 4 lands)
- [x] `evals/connector_evals.py` — at least one eval per connector
- [x] `evals/phase_evals.py` — at least one eval per phase
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

### 2026-07-09 (session 6)
- Built Phase 3a (preliminary evaluation, structured reasoning rubric only —
  the bull/bear/synthesizer debate is Phase 3b, deliberately deferred to a
  separate task so reasoning quality could be verified before wrapping
  multi-agent orchestration around it).
- `orchestrator/phases.py` PHASE_DEFINITIONS[3]: connectors=[TavilyConnector()]
  only — no new connector types, matching the spec's "pure reasoning" framing.
  One Tavily connector is wired in solely to allow a single optional
  gap-filling search (enforced via prompt instruction, same pattern as the
  Phase 1/2 search caps).
- **Infrastructure change required and made:** Phase 3 needs to reason over
  "what Phases 1-2 gathered," but `run_phase()` previously started every phase
  from a blank slate (just the company name) — there was no mechanism to pass
  earlier verdicts forward. Added `prior_verdicts` param to `run_phase()` and
  `orchestrator/agent.py::_initial_message()`, which folds prior phases'
  verdict/confidence/rationale/search-history into the first user message.
  Scoped narrowly: only Phase 3+ receives prior context (`cli/run.py` only
  passes `prior_verdicts` when `phase >= 3`), so Phase 1/2 behavior and
  existing eval fixtures are unaffected.
- `orchestrator/prompts.py` PHASE_PROMPTS[3]: full rubric — Six Pensées, Seven
  Deadly Questions, Clone Test, operationalized labor-replacement test. Hard
  honesty rule: every field must cite evidence or say exactly "DATA-BLIND:
  cannot determine from public sources"; explicitly forbids inventing capital
  figures, valuations, TAM, or named advisors without a direct public source.
  Same verdict enum/humility statement/weighted scoring as Phases 1-2; capped
  at 1 optional tavily_search (vs. 4 for Phases 1-2) since this phase reasons,
  it doesn't gather.
- `cli/run.py`: generalized the phase loop (`LAST_PHASE = 3`) instead of
  hand-writing each phase transition; added the Phase 2 → Phase 3 checkpoint
  on the same input()-based advance/kill/dig-deeper pattern.
- **Ran the full Phase 1 → 2 → 3 pipeline on Slang.ai:** ADVANCE (0.68) →
  advance → ADVANCE (0.75) → advance → ADVANCE (0.72). Phase 3 used exactly 1
  search (founder background) + submit_verdict — respected the cap. Correctly
  flagged DATA-BLIND on capital needed, valuation, and advisors/consultants
  (no public source for any of them). Clone Test answer was appropriately
  qualified ("credible but fragile" — integration lock-in + accumulated call
  data, but OpenTable/SevenRooms could build native competition). Labor-
  replacement test resolved cleanly to "yes, for the phone-answering/
  reservationist role specifically." Verdict surfaced a genuine new finding
  Phases 1-2 missed: Slang.ai is at Series B (~$68M raised), which is a stage
  mismatch for an early-stage thesis — flagged as a fund-mandate-dependent
  caveat rather than papered over. Cost: $0.0428 (P1) + $0.0393 (P2) + $0.0752
  (P3) = $0.1573 total. Full trace: `data/runs/slang.ai_phase3_b3ee319e.json`.
- What's next: Phase 3b (bull/bear/synthesizer debate) once reasoning quality
  above is judged sufficient; then Phase 4 (deep diligence) and EDGAR/USPTO.

### 2026-07-09 (session 5)
- Added a testable prediction to the Abridge Known Limitations entry: the
  Phase 3 bull/bear debate should be the mechanism that resolves the
  verdict-instability boundary case, with an explicit success criterion
  (genuine disagreement, non-convergence, structural NEEDS-MORE-INFO).
- Built Phase 2 (screening): `orchestrator/phases.py` PHASE_DEFINITIONS[2]
  reuses the Tavily/arXiv/GitHub connector set (Phase 2 differs by reasoning,
  not data source); EDGAR deliberately deferred since Phase 2's tests
  (pricing pages, careers pages, news) all run off Tavily and EDGAR is
  near-empty for private startups.
- `orchestrator/prompts.py` PHASE_PROMPTS[2]: pricing-model classifier as
  centerpiece (outcome/per-resolution → labor replacement vs. per-seat →
  augmentation), fund-fit/stage check, business-plan completeness, hiring-
  signal read (forward-deployed-engineer-heavy vs. sales-heavy job posts).
  Same verdict enum, humility statement, weighted scoring posture, and
  4-search cap as Phase 1; system prompt cached the same way.
- `cli/run.py`: added the first human-in-the-loop checkpoint. After Phase 1,
  prints the verdict and blocks on `input()` for advance / kill / dig-deeper;
  only "advance" proceeds to Phase 2. `--phase 2` still allows jumping
  straight into Phase 2 for testing, bypassing the gate intentionally.
- **Ran the full Phase 1 → checkpoint → Phase 2 flow on two fixtures:**
  - **Slang.ai** (clear vertical labor-replacer): Phase 1 ADVANCE (0.75) →
    human "advance" → Phase 2 ADVANCE (0.78). Phase 2 pricing classifier read
    Slang.ai's flat-subscription tiers as a mild augmentation-leaning signal
    but end-to-end call handling (no human review before a reservation ships)
    and deep OpenTable/SevenRooms/Yelp integration carried both beliefs.
    Correctly surfaced Series B stage as a fund-fit caveat and a sales-heavy
    hiring mix as a secondary flag — both genuine diligence questions, not
    thesis failures. Cost: $0.0443 (P1) + $0.0401 (P2).
  - **Chatbase** (thin GPT-wrapper): Phase 1 KILL (0.82) → forced "advance"
    at the checkpoint anyway to demonstrate Phase 2 end-to-end → Phase 2 KILL
    (0.82), same verdict via independent reasoning. Pricing classifier
    correctly read message-credit SaaS tiers as tooling/augmentation, not
    outcome-based. Hiring signal was a clean corroborating counter-signal:
    3 open roles, all GTM, zero engineering — confirms a sold tool, not a
    company still building labor-replacing automation. Cost: $0.0337 (P1) +
    $0.0297 (P2).
  - All 4 runs well under the $0.10/run cost ceiling; total for the demo:
    $0.1478. Full traces saved under `data/runs/`.
- What's next: Phase 3 (preliminary eval — Six Pensées, Seven Deadly
  Questions, Clone Test, operationalized labor-replacement test; pure
  reasoning, no new connectors) is the next M3 item, per `docs/phase-tests.md`.

### 2026-07-08 (session 4)
- Built the eval harness: `evals/connector_evals.py` (real API calls, no mocking)
  and `evals/phase_evals.py` (fixture-based, no API calls).
- `connector_evals.py`: 2 cases per connector (real-data + absence) + schema
  validation. Discovered the arXiv absence case is a live regression of the
  known confidence-by-count issue (nonsense query → 5 irrelevant papers → 0.9
  confidence); marked XFAIL/known-issue rather than silently loosened or left
  blocking. Tavily's absence case needed a design fix: live web search almost
  never returns literally zero items for any query, so "neutral" is defined as
  low-confidence (<=0.15), not empty items — Tavily's own relevance scoring
  already gets this right (0.03 avg on a nonsense query).
- Generated a fresh Phase 1 fixture batch (10 real runs, ~$0.37 total) against
  the CURRENT arXiv+Tavily+GitHub agent: Slang.ai/Chatbase/Glean/Rogo (1 run
  each) + Abridge (5 runs) + EvenUp (1 run, became a bonus/unasserted fixture
  — see below). Saved to `evals/fixtures/`.
- EvenUp was picked as a "should ADVANCE" fixture but the live run surfaced
  real evidence EvenUp "relies on a mix of AI and human drafters" — landed
  NEEDS-MORE-INFO, and that's actually the right call, not a bug. Swapped in
  Slang.ai (restaurant AI phone-answering, no human review before the
  reservation ships) as the asserted advance fixture instead; kept EvenUp's
  result as an unasserted bonus fixture since it's a genuinely informative case.
- `phase_evals.py` result: 4/4 directional assertions pass (Slang.ai advance,
  Rogo advance, Chatbase kill, Glean kill). Abridge 5-run distribution: KILL
  3/5 (conf 0.72-0.78), NEEDS-MORE-INFO 2/5 (conf 0.50-0.52) — reported
  honestly, not resolved. All 10 runs under the $0.10/run cost ceiling.
  github_search correctly skipped in all 10 runs (all fixture companies are
  closed-vertical enterprise SaaS) — flagged as an eval coverage gap: no
  fixture yet tests the "github_search correctly included" side of the rule.
- Checked off Milestone 1 and 2 checklist items retroactively — both were
  already fully built per prior sessions' logs but the checkboxes were stale.
- What's next: Phase 2 (screening) is the next M3 item — pricing-model
  classifier, fund-fit/stage check, hiring-signal read per `docs/phase-tests.md`.

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
