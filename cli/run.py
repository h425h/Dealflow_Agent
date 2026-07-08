import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from orchestrator.agent import run_phase


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a deal-flow phase against a company.")
    parser.add_argument("company", help="Company name to evaluate")
    parser.add_argument("--phase", type=int, default=1, help="Phase number (default: 1)")
    args = parser.parse_args()

    print(f"\nModel: {config.MODEL}")
    print(f"Running Phase {args.phase} on: {args.company}\n")
    verdict = run_phase(args.phase, args.company)

    u = verdict.usage
    input_cost = u["input_tokens"] * 3 / 1_000_000
    output_cost = u["output_tokens"] * 15 / 1_000_000
    cache_write_cost = u["cache_creation_input_tokens"] * 3.75 / 1_000_000
    cache_read_cost = u["cache_read_input_tokens"] * 0.30 / 1_000_000
    total_cost = input_cost + output_cost + cache_write_cost + cache_read_cost

    print("=" * 60)
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


if __name__ == "__main__":
    main()
