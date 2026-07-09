from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-sonnet-4-6"

MAX_RESULTS_PER_CONNECTOR = 5

DATA_DIR = Path(__file__).parent / "data" / "runs"

# Per-million-token pricing for MODEL (claude-sonnet-4-6), used to estimate run cost.
_PRICE_PER_MILLION = {
    "input_tokens": 3.0,
    "output_tokens": 15.0,
    "cache_creation_input_tokens": 3.75,
    "cache_read_input_tokens": 0.30,
}


def estimate_cost(usage: dict) -> float:
    """Estimate USD cost from an accumulated usage dict (input/output/cache tokens)."""
    return sum(
        usage.get(key, 0) * price / 1_000_000
        for key, price in _PRICE_PER_MILLION.items()
    )
