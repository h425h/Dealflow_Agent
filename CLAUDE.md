# CLAUDE.md

You are working on **dealflow-agent**, an agentic VC deal-flow system. This file
is the operating contract for every Claude Code session on this repo. Read it
first, every session, before doing anything.

## Before you write any code, read these in order

1. **`README.md`** — the project front door: what this is, the thesis it
   encodes, and the findings from actually running it. Start here to understand
   *why* this exists before touching *how* it's built.
2. **`docs/BUILD_NOTES.md`** — the build operating contract: architecture, the
   four-phase funnel, the connector interface, migration triggers, and the full
   "what NOT to do" list. The file tree in its Architecture section is
   authoritative: every file is tagged with the milestone it belongs to.
3. **`PROGRESS.md`** — the current active milestone and a per-file checklist.
   This tells you exactly what to build *now* vs. later. Newest session log is
   at the top.
4. **`docs/source-paper.md`** — the VC domain knowledge this whole system is
   built on (the four phases, Six Pensées, Seven Deadly Questions, the
   question-template library, the reliability/confidence framing). Read this
   before writing any phase logic, prompt, or anything involving investment
   judgment. You do NOT need it for pure infrastructure work (connector
   boilerplate, argparse, etc.).

## Non-negotiable rules

These override any default instinct to be thorough or build ahead:

1. **Build only the current milestone.** `PROGRESS.md` names the active
   milestone. Build fully only the files tagged with that milestone in README's
   tree. **Every file tagged with a later milestone is a stub** — a module
   docstring naming its milestone, and `pass` (or a `NotImplementedError`). Do
   not implement ahead, even if a later file looks trivial.

2. **The current milestone is Milestone 1.** Until `PROGRESS.md` says otherwise,
   build fully: `requirements.txt`, `config.py`, `connectors/base.py`,
   `connectors/arxiv_connector.py`, `orchestrator/prompts.py` (Phase 1 only),
   `orchestrator/phases.py` (Phase 1 only), `orchestrator/agent.py`,
   `cli/run.py`, `tests/test_connectors.py`, and all `__init__.py` files.
   Everything else is a stub.

3. **No frameworks beyond Milestone 1's requirements.** Do not install or import
   LangGraph, LangChain, LangSmith, Tavily, ChromaDB, or any agent framework.
   The orchestrator is hand-written Python with the Anthropic SDK's native tool
   use. LangGraph comes later, and only when the migration triggers in README
   are actually met. `requirements.txt` contains ONLY: anthropic, arxiv,
   requests, python-dotenv.

4. **Connectors hold zero VC judgment.** A connector fetches from one data
   source and maps the result into a `ConnectorResult`. All reasoning,
   screening criteria, and investment logic live in `orchestrator/prompts.py`.
   If you find yourself writing an `if` statement about whether a company is a
   good investment inside a connector, stop — that belongs in a prompt.

5. **Ask before inventing investment criteria.** Before writing
   `orchestrator/prompts.py`, STOP and ask the human for their actual screening
   thesis (sectors, stage, check size, geography). `docs/source-paper.md` gives
   you the question *templates* and the funnel structure, but the specific
   thesis is the human's judgment to supply, not yours to fabricate.

6. **Update `PROGRESS.md` before ending a session.** Check off completed items,
   add a dated session-log entry at the top of the log, and note anything that
   broke or any open question. The next session depends on this being current.

## Architecture in one paragraph

A company name goes in. The orchestrator runs the VC funnel one phase at a time
(Phase 1 sourcing → 2 screening → 3 preliminary eval → 4 deep diligence). Each
phase is a Claude call with tool-use access scoped to only that phase's
connectors; the agent decides what to search, synthesizes findings, and returns
a verdict (advance / kill / needs-more-info + rationale). Between phases, a human
decides whether to proceed — the system never autonomously kills a deal, because
its whole design thesis is that AI augments diligence but cannot replace the
judgment calls (founder character, team chemistry, conviction) that close a
deal. State for each run is saved as JSON under `data/runs/`.

## Build order within a milestone

Even inside Milestone 1, go bottom-up so each piece is testable before the next
depends on it:
`base.py` → `arxiv_connector.py` → (smoke-test the connector against the real
API and confirm it returns a well-formed `ConnectorResult`) → `prompts.py` (ask
the human first) → `phases.py` → `agent.py` → `cli/run.py` → run end-to-end on
two real companies. Don't write `agent.py` before the connector it calls
actually works.
