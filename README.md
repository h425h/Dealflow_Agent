# Deal Flow Agent

An agentic system that augments the venture capital deal flow process — sourcing,
screening, preliminary evaluation, and deep diligence — built around the four-phase
funnel framework from MGMT 2640 (Wharton, Venture Capital and Entrepreneurial
Management).

This is a personal project, not a course submission. Goals, in order:
1. Genuinely understand agentic AI system design by building one for real.
2. Have a working, demoable artifact for VC internship conversations.
3. Build something architected well enough to plausibly extend into a real tool.

**Read this file at the start of every session.** Then read `PROGRESS.md` for current
state. Do not start building before reading both.

---

## Core design philosophy

- **Human-in-the-loop, always.** The agent never autonomously kills a deal. It runs
  a phase, presents findings + a recommendation, and a human decides whether to
  advance, kill, or dig deeper. This is a deliberate position, not a missing feature —
  see "Why human-in-the-loop" below.
- **Connectors are dumb and swappable.** Every data source (arXiv, USPTO, EDGAR,
  GitHub, Tavily, future paid APIs like Harmonic/PitchBook) implements the same
  interface. The orchestrator does not know or care which connector it's calling.
- **Build from scratch before reaching for a framework.** We are deliberately
  building the orchestrator as plain Python first, and porting to LangGraph later —
  see "Migration triggers" below. Do not install or use LangGraph until those
  triggers are met. This is intentional, not a TODO.
- **No phase should silently fail.** Every connector result includes a confidence
  rating. Every phase verdict includes explicit rationale. The memo's final section
  must always state what the system could *not* determine (founder character, team
  chemistry, execution grit) — this is a required output, not optional polish.

## Why human-in-the-loop

Full reasoning is in `docs/source-paper.md` — **read this before writing any
phase logic, prompts, or connector code.** It is the actual design basis for
the four phases, the decision points within each, the specific question
templates, and the reliability/confidence framing for connector results. The
short version: AI can compress the mechanical/factual parts of diligence —
market sizing, patent landscape, competitive mapping, financial sensitivity —
but cannot assess founder trustworthiness, team chemistry, or conviction.
Those require judgment. A system that pretends otherwise is dishonest about
what it's doing. Every phase checkpoint exists to keep a human making the
calls AI can't make.

## Architecture

```
dealflow-agent/
├── requirements.txt      # MILESTONE 1: anthropic, arxiv, requests, python-dotenv only
├── config.py             # MILESTONE 1: model name + shared constants
├── connectors/
│   ├── __init__.py
│   ├── base.py                  # MILESTONE 1 — build fully
│   ├── arxiv_connector.py       # MILESTONE 1 — build fully
│   ├── tavily_connector.py      # MILESTONE 2 — stub only (docstring + pass)
│   ├── uspto_connector.py       # MILESTONE 3 — stub only
│   ├── edgar_connector.py       # MILESTONE 3 — stub only
│   └── github_connector.py      # MILESTONE 2 — stub only
├── orchestrator/
│   ├── __init__.py
│   ├── agent.py           # MILESTONE 1 — build fully (from-scratch agentic loop)
│   ├── graph.py            # MILESTONE 4+ — stub only, do not build until migration triggers are met
│   ├── phases.py           # MILESTONE 1 — build fully, but only define Phase 1 for now
│   └── prompts.py          # MILESTONE 1 — build fully, but only Phase 1's prompt
├── evals/
│   ├── __init__.py
│   ├── connector_evals.py    # MILESTONE 3 — stub only
│   └── phase_evals.py         # MILESTONE 3 — stub only
├── memo/
│   ├── __init__.py
│   └── generator.py        # MILESTONE 3 — stub only
├── cli/
│   └── run.py               # MILESTONE 1 — build fully (argparse, takes a company name, runs Phase 1, prints verdict)
├── data/runs/              # saved JSON per company run — audit trail + eval fixtures
└── tests/
    └── test_connectors.py   # MILESTONE 1 — build fully (real smoke test against arXiv API)
```

**Rule for any session:** only build fully what's tagged with the current
milestone (see `PROGRESS.md` for which milestone is active). Everything tagged
with a later milestone gets a stub file only — a docstring naming the
milestone it belongs to, and `pass`. Do not implement ahead of the current
milestone even if it seems quick.

**The four phases** (mapped from the course funnel):

| Phase | Maps to | Connectors used | Output |
|---|---|---|---|
| 1. Sourcing | One-minute test, exogenous pre-qualifiers | arXiv, Tavily, GitHub | advance/kill + rationale |
| 2. Screening | Ten-minute test, fund fit | EDGAR, Tavily | advance/kill + rationale |
| 3. Preliminary evaluation | Six Pensées, Seven Deadly Questions, bull/bear case | none — pure reasoning | advance/kill + rationale |
| 4. Deep diligence | IP validity, unit economics, regulatory | USPTO, arXiv, EDGAR | advance/kill + rationale |

After any phase, output feeds `memo/generator.py` if the human stops here and wants
a summary memo of findings so far.

## Migration triggers — when to introduce LangGraph

Do **not** install LangGraph preemptively. Port `orchestrator/agent.py` to
`orchestrator/graph.py` only when at least two of these are actually being felt
during development (not anticipated — felt):

1. **Persistence pain** — losing progress because a run was interrupted and the
   JSON-per-phase save isn't enough to cleanly resume.
2. **Branching pain** — a phase needs to conditionally loop back (e.g. Phase 2
   says "not enough info, broaden Phase 1 search") and the `if/elif` control flow
   in `cli/run.py` is getting tangled.
3. **Interrupt pain** — wanting to pause mid-phase (not just between phases) for
   human input, and the hand-rolled `input()` checkpoint is too blunt for that.

When triggered: connectors do not change. Only the orchestration layer is rebuilt
as a `StateGraph`, phases become nodes, the JSON state dict becomes a typed graph
state, and `input()` becomes `interrupt()`.

## Stack

**In use now:**
- `anthropic` SDK (Claude, with tool use)
- `arxiv` (free API, no key)
- `requests` (USPTO PatentsView, SEC EDGAR full-text search — both free/keyless)
- `python-dotenv`

**Added later, on trigger — do not install early:**
- `tavily-python` — milestone 2 (agentic web search connector)
- `langgraph`, `langsmith` — milestone 4 (see migration triggers above)
- `chromadb` — only once a memo-archive RAG feature is actually being built

## What NOT to do

- Don't build all five connectors before Phase 1 logic works end-to-end on one.
- Don't add LangGraph, multi-agent patterns, or a web UI before the core
  single-agent-per-phase loop is proven with real data.
- Don't let connectors contain any VC reasoning/judgment — that belongs in
  `orchestrator/prompts.py` only. Connectors fetch and structure data, nothing more.
- Don't skip the "what this system cannot determine" section in memo output.

## Session workflow

1. Read this file.
2. Read `docs/source-paper.md` if working on phase logic, prompts, or anything
   involving VC reasoning/judgment (not needed for pure infra work like
   connector boilerplate).
3. Read `PROGRESS.md` for current milestone and last session's stopping point.
4. Work on the **next unchecked item only** — don't jump ahead.
5. Before ending a session, update `PROGRESS.md` (see that file for the format).