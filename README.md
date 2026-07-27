# Deal Flow Agent

An agentic VC deal-flow system that runs a company through a four-phase diligence
funnel — sourcing, screening, preliminary evaluation, and deep diligence — the
way a real investment committee process is structured (mapped from MGMT 2640,
Wharton's Venture Capital and Entrepreneurial Management course). Each phase is
a Claude agent with tool-use access to a scoped set of connectors (arXiv,
Tavily web search, GitHub); it decides what to search, synthesizes what
it finds, and returns a verdict with a confidence score and explicit rationale.
Between every phase, a human decides whether to advance, kill, or dig deeper —
the system never autonomously kills a deal. State from every run is saved as
JSON, so any verdict is fully auditable back to the searches that produced it.

This is a personal project built to learn agentic system design for real and
to have a working artifact for VC internship conversations — not a course
submission, and not a production tool.

---

## The thesis it encodes

The system screens against one specific, falsifiable investment thesis — not a
generic "is this a good company" rubric. Two beliefs, weighted, not strict:

- **Belief A — Labor replacement, not augmentation.** Durable AI value comes
  from replacing an end-to-end job a human was paid to do, not from making a
  human faster. The test: could you remove the human from this role entirely
  and route the output straight to the next step? If a human still reviews,
  approves, or corrects it before it ships, that's augmentation — and this
  thesis passes on augmentation, however well-executed.
- **Belief B — Vertical depth, not horizontal breadth.** The moat is not model
  quality — it's proprietary data and distribution locked inside one
  industry's workflow. A horizontal tool has to win on model quality, a race
  it will lose to frontier labs.

**Weighted, not strict:** a company exceptional on one belief and credible on
the other can still advance, with the weaker dimension carried forward as an
explicit caveat — not papered over, not silently dropped. A company weak on
both is a clean kill.

The system is also explicit about what this thesis is *not* built to catch —
see Findings, below.

## Architecture

```
company name
     │
     ▼
Phase 1 — Sourcing        (arXiv, Tavily, GitHub)     → advance / kill / needs-more-info
     │  human checkpoint
     ▼
Phase 2 — Screening       (Tavily, arXiv, GitHub)      → pricing model, fund-fit, hiring signal
     │  human checkpoint
     ▼
Phase 3 — Preliminary eval (pure reasoning + 1 search) → Six Pensées, Seven Deadly Questions,
     │  human checkpoint                                  Clone Test, then a bull/bear/synthesizer debate
     ▼
Phase 4 — Deep diligence  (arXiv, Tavily)              → AI-washing check, IP acid test, data-moat score
     │  human checkpoint
     ▼
memo/generator.py  →  IC-style memo, mandatory "what this system cannot determine" section
```

Three connectors (arXiv, Tavily, GitHub), one hand-rolled agentic loop
(no LangGraph — see below), one memo synthesizer.

The GitHub connector is scoped, not a general signal source: it's only
meaningful for companies with a public dev surface (open-source cores, public
SDKs, dev-tool components). For the median target here (closed vertical B2B
SaaS), thin or neutral results are the normal case, not the exception, and
absence of a GitHub presence is never scored as a negative.

Phase 4's IP analysis runs on arXiv + Tavily reasoning only — there is no
patent-database connector. A USPTO connector existed but its live-data path
was never verified against a real authenticated query (a key requires
personal ID.me identity verification), so it was removed rather than left in
as unverified machinery. The IP-ownership and Alice §101 rubric fields
therefore come back DATA-BLIND far more often than not; that is the honest,
structurally correct answer, not a gap to paper over.

## Findings

This is the part that matters — what happened when the thesis met real
companies, reported honestly, including where a pre-registered prediction
turned out to be wrong.

**The thesis discriminates.** Run against contrasting real companies, the
funnel produced different verdicts for traceable, specific reasons — not vibes.
[Slang.ai](data/memos/slang.ai_memo.md) (restaurant phone-answering AI, no
human review before a reservation ships) landed **ADVANCE, with an explicit
stage-fit caveat** — full four-phase pass on both beliefs, undercut only by a
Series B entry price that may not fit an early-stage mandate.
[Chatbase](data/memos/chatbase_memo.md) (GPT-wrapper chatbot builder) landed
**KILL** — both beliefs failed independently: per-seat pricing and a ~20%
human-escalation rate are augmentation, not replacement, and a policy of Zero
Data Retention structurally forecloses any vertical data moat. Same funnel, same
rubric, opposite verdicts, each one traceable to a specific test (pricing-model
classifier, vertical-wedge check, data-moat score).

**A falsified prediction, reported honestly.** I pre-registered that the Phase
3 bull/bear debate would resolve a verdict-instability problem discovered on
Abridge (Phase 1 flipped between KILL and NEEDS-MORE-INFO across identical
runs) by structurally failing to converge — bull and bear would genuinely
disagree, and the system would land on NEEDS-MORE-INFO for real reasons. It
didn't happen that way. All 3 independent debate runs on Abridge converged on
KILL (confidence 0.92 / 0.85 / 0.82), and the control company (Chatbase) also
converged — confirming the debate mechanism isn't just hedging by default; it
converges when the evidence warrants it. **Diagnosis:** Phase 3's structured
rubric, by forcing the operationalized labor-replacement test to reason
explicitly through the workflow step by step, resolved Abridge's core ambiguity
(the physician's sign-off is legally *required*, not a product choice Abridge
could remove) *before* the debate ever started. There was nothing substantive
left for bull and bear to disagree about. The Phase 1 instability turned out to
be a symptom of thin, unsynthesized search results forcing a snap judgment —
not a genuinely irreducible thesis tension. The fix landed one phase earlier
than predicted, and the mechanism was shown to converge for the right reason
(the Chatbase control also converged, decisively, ruling out "hedges by
default" as the explanation) — but as of the most recent session, no run
against any company has yet produced a genuine `converged=false` with a named
resolving question. That true-positive test remains open, not solved: finding
a company whose Phase 3a rubric holds real residual tension is still on the
list.

**Confidence didn't climb with more evidence — it round-tripped.** Slang.ai's
confidence moved 0.68 (Phase 1) → 0.75 (Phase 2) → 0.72 (Phase 3) → 0.68
(Phase 4) → 0.70 (final memo). It peaked early and gave back most of that gain
as deeper diligence added qualifications: Phase 3's Clone Test flagged the
data moat behind the company's strongest bull argument as never publicly
substantiated, and Phase 4 added a co-founder identity gap and escalating
regulatory exposure on top. Four phases of diligence on the one company that
passed every phase ended almost exactly where it started, not higher — more
scrutiny bought more named caveats, not more conviction.

**Where public-data AI stops working.** DATA-BLIND flags cluster
predictably on valuation, capital needs, unit economics, cap table, and
advisor relationships — real gaps, but ones a data room closes. A second
category doesn't close with more data at all: founder trustworthiness,
co-founder chemistry, and execution grit under pressure. Every memo this
system produces ends with a two-part "what this system cannot determine"
section for exactly this reason — DATA-ACCESS LIMITS (resolvable with a data
room) versus STRUCTURAL LIMITS (resolvable only by a human in the room). This
split is why the human-in-the-loop checkpoints exist between every phase, not
a UX nicety layered on top.

## Cost

Individual phases run $0.03–$0.19 depending on phase and whether Phase 3's
bull/bear debate fires; Phase 4 (the evidence-heavy deep-diligence phase) and
Phase 3-with-debate are the most expensive. A full four-phase run plus memo
lands around **$0.40–$0.55 end to end** (Slang.ai: $0.0428 + $0.0393 + $0.0752
+ $0.1493 + $0.1011 = $0.4077; Chatbase: $0.0337 + $0.0297 + $0.1914 + $0.1819
+ $0.0958 = $0.5325 — Chatbase's Phase 3 included a full 3-round bull/bear
debate, Slang.ai's did not). Kept this low by prompt caching on every system
prompt and a hard per-phase search cap (4 searches for Phases 1–2, 1 for Phase
3, 5 for Phase 4).

## What's deliberately not built, and why

- **No LangGraph.** The orchestrator is hand-rolled Python with the Anthropic
  SDK's native tool use. A port only happens once at least two of three
  migration triggers are actually *felt*, not anticipated: **persistence
  pain** (a run is interrupted and the JSON-per-phase saves aren't enough to
  cleanly resume), **branching pain** (a phase needs to conditionally loop
  back and the `if/elif` control flow in `cli/run.py` gets tangled), and
  **interrupt pain** (wanting to pause mid-phase, not just between phases, and
  the `input()` checkpoint is too blunt). None has fired across all four
  phases — hand-rolled state passing has been enough. When they do, connectors
  don't change: only the orchestration layer becomes a `StateGraph`, phases
  become nodes, and `input()` becomes `interrupt()`.
- **No paid data connectors.** Harmonic, PitchBook, and similar sit behind the
  same `Connector` interface every free connector implements, so swapping one
  in is additive, not a rewrite — but the free-data version is what actually
  proves the orchestration layer works, so that's what got built first.
- **No RAG meta-memory.** A memo-archive retrieval layer (ChromaDB) needs an
  archive of memos to retrieve over, and this system has produced exactly two.
  Building retrieval before there's anything to retrieve would be building
  ahead of the evidence.

## Read more

- Full memos: [`data/memos/slang.ai_memo.md`](data/memos/slang.ai_memo.md)
  (advance) · [`data/memos/chatbase_memo.md`](data/memos/chatbase_memo.md)
  (kill) — or the rendered HTML versions in the same folder.
- [`docs/source-paper.md`](docs/source-paper.md) — the VC domain knowledge
  (Six Pensées, Seven Deadly Questions, the phase framework) this whole system
  is built on.
- [`docs/phase-tests.md`](docs/phase-tests.md) — the per-phase diligence test
  spec: exactly what each funnel phase tests a company for, and why.

## License

MIT — see [`LICENSE`](LICENSE).
