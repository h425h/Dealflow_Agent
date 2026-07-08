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
    # Phases 2–4 added in Milestones 2–3.
}
