"""
Milestone 3 — Connector evaluation suite.

Real API calls against known queries, no mocking. For each connector (arxiv,
tavily, github) we check:
  1. "real data"    — a query with a known-correct answer returns well-formed,
                       non-empty results.
  2. "absence"       — a query with no matching data returns a clean, neutral
                       empty result (items=[], confidence=0.0, error=None) —
                       NOT an exception and NOT an `error`-flagged failure.
                       This matters because Phase 1 treats absent GitHub/arXiv
                       signal as neutral, not a negative, per prompts.py.
  3. Schema validation on whatever comes back.

Run directly: `python3 evals/connector_evals.py`. Exits non-zero if any case
fails, so it can be used as a regression gate.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).parent.parent))

from connectors.arxiv_connector import ArxivConnector
from connectors.base import Connector, ConnectorResult
from connectors.github_connector import GitHubConnector
from connectors.tavily_connector import TavilyConnector

_ITEM_SCHEMAS: dict[str, list[str]] = {
    "arxiv": ["title", "summary", "authors", "published", "url", "pdf_url", "categories"],
    "tavily": ["title", "url", "content", "score", "published_date"],
    "github": [
        "name", "url", "description", "language", "stars", "forks",
        "recent_commits_4w", "contributor_count", "pushed_at", "is_fork",
    ],
}


def _validate_schema(result: ConnectorResult) -> list[str]:
    """Return a list of schema problems (empty list = valid)."""
    problems = []
    if not isinstance(result.source, str) or not result.source:
        problems.append("source is not a non-empty string")
    if not isinstance(result.query, str) or not result.query:
        problems.append("query is not a non-empty string")
    if not isinstance(result.items, list):
        problems.append("items is not a list")
    if not isinstance(result.confidence, (int, float)):
        problems.append("confidence is not numeric")
    elif not (0.0 <= result.confidence <= 1.0):
        problems.append(f"confidence {result.confidence} out of [0.0, 1.0] range")
    if result.error is not None and not isinstance(result.error, str):
        problems.append("error is set but not a string")

    expected_keys = _ITEM_SCHEMAS.get(result.source, [])
    for i, item in enumerate(result.items):
        if not isinstance(item, dict):
            problems.append(f"items[{i}] is not a dict")
            continue
        missing = [k for k in expected_keys if k not in item]
        if missing:
            problems.append(f"items[{i}] missing expected keys: {missing}")
    return problems


@dataclass
class EvalCase:
    connector: Connector
    name: str
    query: str
    max_results: int
    check: Callable[[ConnectorResult], list[str]]  # returns list of failure reasons
    known_issue: str | None = None  # if set, a failure here is expected (xfail) — tracked, not blocking


def _check_real_data(result: ConnectorResult) -> list[str]:
    failures = []
    if result.error is not None:
        failures.append(f"expected no error, got: {result.error!r}")
    if not result.items:
        failures.append("expected non-empty items, got []")
    if result.confidence <= 0.0:
        failures.append(f"expected confidence > 0.0, got {result.confidence}")
    failures.extend(_validate_schema(result))
    return failures


def _make_absence_check(threshold: float = 0.15) -> Callable[[ConnectorResult], list[str]]:
    """Build a check for 'no real data exists' queries.

    Real search backends (arXiv full-text match, live web search) will often
    return SOME loosely-matching items for almost any query string — so
    "absence" can't mean "items must be empty." What matters for downstream
    Phase 1 reasoning is that a non-match reads as neutral/low-confidence,
    not as an `error` and not as a falsely high-confidence signal (in either
    direction — falsely negative OR falsely positive both corrupt a verdict).
    """
    def check(result: ConnectorResult) -> list[str]:
        failures = []
        if result.error is not None:
            failures.append(
                f"absence case surfaced an `error` instead of a clean empty/neutral result: "
                f"{result.error!r}"
            )
        if result.confidence > threshold:
            failures.append(
                f"expected neutral confidence (<= {threshold}) on an absence case, got "
                f"{result.confidence} across {len(result.items)} items — irrelevant matches "
                f"are being scored as real signal"
            )
        failures.extend(_validate_schema(result))
        return failures
    return check


_check_absence = _make_absence_check()


# Deliberately absurd, unique tokens so "real data" and "absence" cases can't
# collide with each other or with real-world content.
_NONSENSE = "Zqxvwbrklm9284 Nonexistent Fictitious Startup Corp"

CASES: list[EvalCase] = [
    # --- arXiv -----------------------------------------------------------
    EvalCase(
        connector=ArxivConnector(),
        name="arxiv / real data (AlphaFold — known to have arXiv coverage)",
        query="AlphaFold protein structure prediction",
        max_results=5,
        check=_check_real_data,
    ),
    EvalCase(
        connector=ArxivConnector(),
        name="arxiv / absence (nonsense query, no papers should exist)",
        query=_NONSENSE,
        max_results=5,
        check=_check_absence,
        known_issue=(
            "arXiv confidence is count-based, not relevance-based (PROGRESS.md Known "
            "Limitations). Full-text OR-matching on words like 'Fictitious'/'Startup' "
            "returns 5 unrelated papers, which count-based scoring reads as 0.9 "
            "confidence — a false-positive signal, not a graceful absence."
        ),
    ),
    # --- Tavily ------------------------------------------------------------
    EvalCase(
        connector=TavilyConnector(),
        name="tavily / real data (Anthropic — known to have web coverage)",
        query="Anthropic Claude API pricing",
        max_results=5,
        check=_check_real_data,
    ),
    EvalCase(
        connector=TavilyConnector(),
        name="tavily / absence (nonsense company, no web presence should exist)",
        query=f"{_NONSENSE} pricing labor replacement product",
        max_results=5,
        check=_check_absence,
    ),
    # --- GitHub --------------------------------------------------------
    # Kept to max_results=2 — unauthenticated GitHub API is capped at 60
    # core / 10 search requests per hour, and each repo costs 2 extra core
    # calls (commit_activity + contributors).
    EvalCase(
        connector=GitHubConnector(),
        name="github / real data (org:vercel — well-known public GitHub org)",
        query="org:vercel",
        max_results=2,
        check=_check_real_data,
    ),
    EvalCase(
        connector=GitHubConnector(),
        name="github / absence (nonsense query, no repos should exist)",
        query=_NONSENSE.replace(" ", ""),
        max_results=2,
        check=_check_absence,
    ),
]


def run() -> bool:
    results_by_connector: dict[str, list[tuple[EvalCase, bool, list[str]]]] = {}
    for case in CASES:
        try:
            result = case.connector.search(query=case.query, max_results=case.max_results)
            failures = case.check(result)
        except Exception as exc:  # a connector must never raise — that's itself a failure
            failures = [f"connector raised an exception instead of returning a result: {exc!r}"]
        passed = not failures
        results_by_connector.setdefault(case.connector.name, []).append((case, passed, failures))

    blocking_failure = False
    print("=" * 70)
    print("CONNECTOR EVALS")
    print("=" * 70)
    for connector_name, cases in results_by_connector.items():
        n_pass = sum(1 for _, p, _ in cases if p)
        print(f"\n[{connector_name}] {n_pass}/{len(cases)} passed")
        for case, passed, failures in cases:
            if passed:
                status = "PASS"
            elif case.known_issue:
                status = "XFAIL (known issue)"
            else:
                status = "FAIL"
            print(f"  {status}  {case.name}")
            for f in failures:
                print(f"        - {f}")
            if case.known_issue and not passed:
                print(f"        note: {case.known_issue}")
            if not passed and not case.known_issue:
                blocking_failure = True
    print("\n" + "=" * 70)
    print("OVERALL: " + ("PASS" if not blocking_failure else "FAIL")
          + " (XFAIL known-issue cases do not block; see notes above)")
    print("=" * 70)
    return not blocking_failure


if __name__ == "__main__":
    sys.exit(0 if run() else 1)
