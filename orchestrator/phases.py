from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from connectors.base import Connector
from connectors.arxiv_connector import ArxivConnector
from connectors.github_connector import GitHubConnector
from connectors.tavily_connector import TavilyConnector


@dataclass
class PhaseDefinition:
    number: int
    name: str
    connectors: List[Connector]


PHASE_DEFINITIONS: dict[int, PhaseDefinition] = {
    1: PhaseDefinition(
        number=1,
        name="sourcing",
        connectors=[ArxivConnector(), TavilyConnector(), GitHubConnector()],
    ),
    2: PhaseDefinition(
        number=2,
        name="screening",
        # Same connector set as Phase 1 — Phase 2 differs by REASONING (pricing-model
        # classifier, fund-fit, hiring signal), not by data source. EDGAR was removed
        # entirely: it indexes public-company filings only, and every company in this
        # thesis's target universe is private; every Phase 2 test in docs/phase-tests.md
        # runs off Tavily (pricing pages, careers pages, news) instead.
        connectors=[TavilyConnector(), ArxivConnector(), GitHubConnector()],
    ),
    3: PhaseDefinition(
        number=3,
        name="preliminary_evaluation",
        # Per docs/phase-tests.md, Phase 3 is PURE REASONING over what Phases 1-2
        # already gathered — no new connector types. One Tavily connector is wired
        # in only to allow a single optional gap-filling search (capped at 1 in the
        # Phase 3 prompt); it is not a research phase.
        connectors=[TavilyConnector()],
    ),
    4: PhaseDefinition(
        number=4,
        name="deep_diligence",
        # Expensive, evidence-heavy phase. USPTO was removed entirely: its
        # live-data path was never verified against a real authenticated query
        # (a key requires personal ID.me identity verification, never pursued),
        # so IP defensibility / Alice Sec. 101 risk now run on arXiv + Tavily
        # reasoning only, with DATA-BLIND expected on patent-specific fields
        # far more often than not. Tavily + arXiv also cover AI-washing
        # capability verification and scientific/technical moat checks.
        connectors=[ArxivConnector(), TavilyConnector()],
    ),
}
