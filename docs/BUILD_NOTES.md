# Build Notes

Internal build log and operating contract for working on this codebase. This is
the "how it was built and how to keep building it" doc — for what it *is* and
what it *found*, see `README.md`. For per-session history, see `PROGRESS.md`.

**Read this before writing any code in this repo.** Then read `PROGRESS.md` for
current state.

---

## Core design philosophy

- **Human-in-the-loop, always.** The agent never autonomously kills a deal. It runs
  a phase, presents findings + a recommendation, and a human decides whether to
  advance, kill, or dig deeper. This is a deliberate position, not a missing feature —
  see "Why human-in-the-loop" below.
- **Connectors are dumb and swappable.** Every data source (arXiv, USPTO, EDGAR,
  GitHub, Tavily, future paid APIs like Harmonic/PitchBook) implements the same
  interface. The orchestrator does not know or care which connector it's calling.
- **Build from scratch before reaching for a framework.** The orchestrator was
  deliberately built as plain Python first, with a LangGraph port only if the
  migration triggers below are actually felt — see "Migration triggers." As of
  the current state, no trigger has fired, and no framework was introduced.
- **No phase should silently fail.** Every connector result includes a confidence
  rating. Every phase verdict includes explicit rationale. The memo's final section
  always states what the system could *not* determine (founder character, team
  chemistry, execution grit) — this is a required output, not optional polish.

## Why human-in-the-loop

Full reasoning is in `docs/source-paper.md` — read this before writing any
phase logic, prompts, or connector code. It is the actual design basis for
the four phases, the decision points within each, the specific question
templates, and the reliability/confidence framing for connector results. The
short version: AI can compress the mechanical/factual parts of diligence —
market sizing, patent landscape, competitive mapping, financial sensitivity —
but cannot assess founder trustworthiness, team chemistry, or conviction.
Those require judgment. A system that pretends otherwise is dishonest about
what it's doing. Every phase checkpoint exists to keep a human making the
calls AI can't make.

## Architecture (file tree, tagged by milestone)

```
dealflow-agent/
├── requirements.txt      # M1: anthropic, arxiv, requests, python-dotenv, tavily-python
├── config.py             # M1: model name + shared constants + cost estimator
├── connectors/
│   ├── __init__.py
│   ├── base.py                  # M1 — Connector + ConnectorResult
│   ├── arxiv_connector.py       # M1 — arXiv API
│   ├── tavily_connector.py      # M2 — Tavily web search
│   ├── github_connector.py      # M2 — GitHub public repo search
│   ├── uspto_connector.py       # M3 — USPTO Open Data Portal (patent search)
│   └── edgar_connector.py       # M3 — stub only; SEC EDGAR full-text search, not yet built
├── orchestrator/
│   ├── __init__.py
│   ├── agent.py            # M1 — agentic loop (Claude + tool use)
│   ├── debate.py            # M3b — bull/bear/synthesizer debate
│   ├── graph.py             # M4+ — stub only, do not build until migration triggers are met
│   ├── phases.py            # M1–M3 — phase → connector mapping, all 4 phases
│   └── prompts.py           # M1–M3 — all phase system prompts + debate prompts + memo prompt
├── evals/
│   ├── __init__.py
│   ├── connector_evals.py    # M3 — real-API evals per connector
│   └── phase_evals.py         # M3 — fixture-based evals per phase
├── memo/
│   ├── __init__.py
│   └── generator.py        # M3 — IC-style memo synthesizer
├── cli/
│   └── run.py               # M1 — argparse entrypoint, human-in-the-loop gates
├── scripts/
│   └── render_memo.py       # presentation layer — renders memo markdown to standalone HTML
├── data/
│   ├── runs/                # saved JSON per phase per company — audit trail + eval fixtures (gitignored, local evidence only)
│   └── memos/                # generated IC memos (markdown + rendered HTML)
└── tests/
    └── test_connectors.py   # M1 — real smoke test against the arXiv API
```

**The four phases** (mapped from the MGMT 2640 / Wharton VC course funnel):

| Phase | Maps to | Connectors used | Output |
|---|---|---|---|
| 1. Sourcing | One-minute test, exogenous pre-qualifiers | arXiv, Tavily, GitHub | advance/kill/needs-more-info + rationale |
| 2. Screening | Ten-minute test, fund fit | Tavily, arXiv, GitHub | advance/kill/needs-more-info + rationale |
| 3. Preliminary evaluation | Six Pensées, Seven Deadly Questions, Clone Test, bull/bear debate | Tavily (1 optional search) | advance/kill/needs-more-info + rationale |
| 4. Deep diligence | AI-washing check, IP acid test, data-moat scoring, unit economics | USPTO, arXiv, Tavily | advance/kill/needs-more-info + rationale |

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

As of the current state, no trigger has fired across four full phases and 9
sessions of development — the hand-rolled state passing has been sufficient.

When triggered: connectors do not change. Only the orchestration layer is rebuilt
as a `StateGraph`, phases become nodes, the JSON state dict becomes a typed graph
state, and `input()` becomes `interrupt()`.

## Stack

**In use:**
- `anthropic` SDK (Claude, with tool use + prompt caching)
- `arxiv` (free API, no key)
- `requests` (USPTO Open Data Portal, SEC EDGAR full-text search — both free/keyless)
- `tavily-python` (agentic web search)
- `python-dotenv`

**Deliberately not added, on the anti-preemption principle:**
- `langgraph`, `langsmith` — no migration trigger above has fired
- `chromadb` — would back a memo-archive RAG feature that doesn't exist yet;
  needs an archive of memos to retrieve over first
- Paid data connectors (Harmonic, PitchBook, etc.) — the `Connector` interface
  is designed for swap-in, but the free-data version is what proves the
  orchestration layer works at all

## What NOT to do

- Don't build all five connectors before Phase 1 logic works end-to-end on one.
- Don't add LangGraph, multi-agent patterns, or a web UI before the core
  single-agent-per-phase loop is proven with real data.
- Don't let connectors contain any VC reasoning/judgment — that belongs in
  `orchestrator/prompts.py` only. Connectors fetch and structure data, nothing more.
- Don't skip the "what this system cannot determine" section in memo output.
- Don't build ahead of the milestone named as current in `PROGRESS.md`, even if
  a later file looks trivial — stub it (docstring + `pass`) instead.

## Session workflow

1. Read `README.md`, then this file.
2. Read `docs/source-paper.md` if working on phase logic, prompts, or anything
   involving VC reasoning/judgment (not needed for pure infra work like
   connector boilerplate).
3. Read `PROGRESS.md` for current milestone and last session's stopping point.
4. Work on the **next unchecked item only** — don't jump ahead.
5. Before ending a session, update `PROGRESS.md`: check off completed items,
   add a dated session-log entry at the top of the log, note anything that
   broke or any open question.
