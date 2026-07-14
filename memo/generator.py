"""
Milestone 3e — IC-style memo generator.

Loads a single company's accumulated phase verdicts (Phases 1-4, whichever are
present in data/runs/) and makes one Claude call, with prompt caching on the
system prompt, to synthesize an investment-committee memo. Pure synthesis: no
tools, no new searches — everything the memo says must already be in the phase
record it was given. The final section, "WHAT THIS SYSTEM CANNOT DETERMINE," is
a required output, not optional polish — see MEMO_SYSTEM_PROMPT.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import anthropic

import config
from orchestrator.prompts import MEMO_SYSTEM_PROMPT

_BACKOFF = [5, 10, 20]


@dataclass
class MemoResult:
    company: str
    memo_markdown: str
    phases_included: list
    usage: dict
    run_id: str
    timestamp: str
    path: Path


def _company_slug(company: str) -> str:
    return company.lower().replace(" ", "_").replace("/", "_")


def _load_phase_records(company: str) -> dict:
    """Load the latest saved JSON run per phase (1-4) for a company from
    data/runs/. Phase 3 has two files per run_phase(3, ...) call — a
    rubric-only save (debate=None) and the final combined save (debate set) —
    so Phase 3 prefers files with a debate present."""
    slug = _company_slug(company)
    records: dict = {}
    for phase in range(1, 5):
        candidates = sorted(config.DATA_DIR.glob(f"{slug}_phase{phase}_*.json"))
        parsed = [json.loads(p.read_text()) for p in candidates]
        if not parsed:
            continue
        if phase == 3:
            with_debate = [r for r in parsed if r.get("debate") is not None]
            pool = with_debate or parsed
        else:
            pool = parsed
        pool.sort(key=lambda r: r["timestamp"])
        records[phase] = pool[-1]
    return records


def _build_memo_user_message(company: str, records: dict) -> str:
    if not records:
        return f"Company: {company}\n\nNo phase records found for this company."

    lines = [f"Company: {company}"]
    for phase in sorted(records):
        r = records[phase]
        lines.append("")
        lines.append("=" * 70)
        lines.append(f"PHASE {phase}")
        lines.append("=" * 70)
        lines.append(f"Verdict: {r['verdict']} (confidence {r['confidence']:.2f})")
        lines.append("")
        lines.append(r["rationale"])
        if r.get("debate"):
            d = r["debate"]
            lines.append("")
            lines.append("--- Phase 3 debate structured fields ---")
            lines.append(f"Converged: {d['converged']}")
            lines.append(f"Convergence summary: {d['convergence_summary']}")
            if not d["converged"]:
                lines.append(f"Resolving question: {d['resolving_question']}")
    return "\n".join(lines)


def _call_with_backoff(sdk_client, **kwargs):
    for attempt, wait in enumerate([0] + _BACKOFF):
        if wait:
            time.sleep(wait)
        try:
            return sdk_client.messages.create(**kwargs)
        except anthropic.RateLimitError:
            if attempt == len(_BACKOFF):
                raise


def generate_memo(company_name: str) -> MemoResult:
    records = _load_phase_records(company_name)
    if not records:
        raise ValueError(
            f"No phase records found for {company_name!r} in {config.DATA_DIR}"
        )

    sdk_client = anthropic.Anthropic()
    system_block = [
        {"type": "text", "text": MEMO_SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}
    ]
    user_message = _build_memo_user_message(company_name, records)

    response = _call_with_backoff(
        sdk_client,
        model=config.MODEL,
        max_tokens=8192,
        system=system_block,
        messages=[{"role": "user", "content": user_message}],
    )
    memo_text = "\n".join(block.text for block in response.content if hasattr(block, "text"))

    u = response.usage
    usage = {
        "input_tokens": u.input_tokens,
        "output_tokens": u.output_tokens,
        "cache_creation_input_tokens": getattr(u, "cache_creation_input_tokens", 0) or 0,
        "cache_read_input_tokens": getattr(u, "cache_read_input_tokens", 0) or 0,
    }

    config.MEMO_DIR.mkdir(parents=True, exist_ok=True)
    path = config.MEMO_DIR / f"{_company_slug(company_name)}_memo.md"
    path.write_text(memo_text)

    return MemoResult(
        company=company_name,
        memo_markdown=memo_text,
        phases_included=sorted(records),
        usage=usage,
        run_id=str(uuid.uuid4())[:8],
        timestamp=datetime.now(timezone.utc).isoformat(),
        path=path,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an IC memo for a company.")
    parser.add_argument("company", help="Company name (must have saved phase runs in data/runs/)")
    args = parser.parse_args()

    print(f"\nModel: {config.MODEL}")
    print(f"Generating memo for: {args.company}\n")

    result = generate_memo(args.company)
    total_cost = config.estimate_cost(result.usage)

    print(result.memo_markdown)
    print("\n" + "=" * 60)
    print(f"Phases included: {result.phases_included}")
    print(f"Saved to: {result.path}")
    print("-" * 60)
    print("TOKEN USAGE:")
    print(f"  input:        {result.usage['input_tokens']:,}")
    print(f"  output:       {result.usage['output_tokens']:,}")
    print(f"  cache write:  {result.usage['cache_creation_input_tokens']:,}")
    print(f"  cache read:   {result.usage['cache_read_input_tokens']:,}")
    print(f"  est. cost:    ${total_cost:.4f}")
    print("=" * 60)


if __name__ == "__main__":
    main()
