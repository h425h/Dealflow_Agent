from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-sonnet-4-6"

MAX_RESULTS_PER_CONNECTOR = 5

DATA_DIR = Path(__file__).parent / "data" / "runs"
