# Progress Log

Read this after `README.md` at the start of every session. Update it before ending
one. Keep entries short — this is a log, not documentation. Newest entry on top.

---

## Current milestone

**Milestone 1: Phase 1 (sourcing) working end-to-end with arXiv connector only.**

Not started yet.

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
- [ ] `orchestrator/prompts.py` — Phase 1 system prompt (one-minute test criteria)
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

(No sessions yet — this is the first one.)

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
