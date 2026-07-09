import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from orchestrator.agent import run_phase


def print_verdict(verdict) -> None:
    u = verdict.usage
    total_cost = config.estimate_cost(u)

    print("=" * 60)
    print(f"PHASE:      {verdict.phase}")
    print(f"VERDICT:    {verdict.verdict.upper()}")
    print(f"CONFIDENCE: {verdict.confidence:.2f}")
    print(f"RUN ID:     {verdict.run_id}")
    print("-" * 60)
    print("RATIONALE:")
    print(verdict.rationale)
    if verdict.debate:
        d = verdict.debate
        print("-" * 60)
        print("DEBATE SYNTHESIS:")
        print(f"  converged:         {d['converged']}")
        if not d["converged"]:
            print(f"  resolving question: {d['resolving_question']}")
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


LAST_PHASE = 4   # highest phase currently implemented


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a deal-flow phase against a company.")
    parser.add_argument("company", help="Company name to evaluate")
    parser.add_argument(
        "--phase", type=int, default=1,
        help=(
            "Phase to start at (default: 1). Starting above 1 skips earlier "
            "checkpoints and does not pass earlier-phase context."
        ),
    )
    args = parser.parse_args()

    print(f"\nModel: {config.MODEL}")

    if args.phase != 1:
        print(f"Running Phase {args.phase} on: {args.company}\n")
        verdict = run_phase(args.phase, args.company)
        print_verdict(verdict)
        return

    prior_verdicts: list = []
    for phase in range(1, LAST_PHASE + 1):
        print(f"\nRunning Phase {phase} on: {args.company}\n")
        # Phase 3+ reasons over prior-phase findings instead of re-searching;
        # Phases 1-2 are independent research passes, so don't feed them prior context.
        verdict = run_phase(
            phase, args.company,
            prior_verdicts=prior_verdicts if phase >= 3 else None,
        )
        print_verdict(verdict)
        prior_verdicts.append(verdict)

        if phase == LAST_PHASE:
            break

        decision = checkpoint(args.company, verdict)
        if decision != "advance":
            print(f"\nHuman decision: {decision}. Stopping before Phase {phase + 1}.")
            return


if __name__ == "__main__":
    main()
