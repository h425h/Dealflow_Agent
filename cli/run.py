import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from orchestrator.agent import run_phase


def print_verdict(verdict) -> None:
    u = verdict.usage
    input_cost = u["input_tokens"] * 3 / 1_000_000
    output_cost = u["output_tokens"] * 15 / 1_000_000
    cache_write_cost = u["cache_creation_input_tokens"] * 3.75 / 1_000_000
    cache_read_cost = u["cache_read_input_tokens"] * 0.30 / 1_000_000
    total_cost = input_cost + output_cost + cache_write_cost + cache_read_cost

    print("=" * 60)
    print(f"PHASE:      {verdict.phase}")
    print(f"VERDICT:    {verdict.verdict.upper()}")
    print(f"CONFIDENCE: {verdict.confidence:.2f}")
    print(f"RUN ID:     {verdict.run_id}")
    print("-" * 60)
    print("RATIONALE:")
    print(verdict.rationale)
    print("-" * 60)
    print(f"TOOLS CALLED ({len(verdict.tool_calls)}):")
    for tc in verdict.tool_calls:
        if tc["tool"] == "submit_verdict":
            print(f"  submit_verdict")
        else:
            summary = tc.get("result_summary", {})
            print(
                f"  {tc['tool']}({tc['input']['query']!r})"
                f"  → {summary.get('item_count', '?')} results, "
                f"confidence={summary.get('confidence', '?')}"
            )
    print("-" * 60)
    print("TOKEN USAGE:")
    print(f"  input:        {u['input_tokens']:,}")
    print(f"  output:       {u['output_tokens']:,}")
    print(f"  cache write:  {u['cache_creation_input_tokens']:,}")
    print(f"  cache read:   {u['cache_read_input_tokens']:,}")
    print(f"  est. cost:    ${total_cost:.4f}")
    print("=" * 60)


def checkpoint(company: str, verdict) -> str:
    """Human-in-the-loop gate. Returns 'advance', 'kill', or 'dig-deeper'."""
    print(f"\nPhase {verdict.phase} complete for {company}: {verdict.verdict.upper()} "
          f"(confidence {verdict.confidence:.2f})")
    while True:
        choice = input("Human decision — advance / kill / dig-deeper: ").strip().lower()
        if choice in ("advance", "kill", "dig-deeper"):
            return choice
        print("Please type exactly one of: advance, kill, dig-deeper")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a deal-flow phase against a company.")
    parser.add_argument("company", help="Company name to evaluate")
    parser.add_argument(
        "--phase", type=int, default=1,
        help="Phase to start at (default: 1). Starting at 2 skips the Phase 1 checkpoint.",
    )
    args = parser.parse_args()

    print(f"\nModel: {config.MODEL}")

    if args.phase == 1:
        print(f"Running Phase 1 on: {args.company}\n")
        verdict = run_phase(1, args.company)
        print_verdict(verdict)

        decision = checkpoint(args.company, verdict)
        if decision != "advance":
            print(f"\nHuman decision: {decision}. Stopping before Phase 2.")
            return

        print(f"\nRunning Phase 2 on: {args.company}\n")
        verdict = run_phase(2, args.company)
        print_verdict(verdict)
    else:
        print(f"Running Phase {args.phase} on: {args.company}\n")
        verdict = run_phase(args.phase, args.company)
        print_verdict(verdict)


if __name__ == "__main__":
    main()
