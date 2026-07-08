from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ConnectorResult:
    source: str
    query: str
    items: list[dict]
    confidence: float        # 0.0–1.0; always set, even on failure
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "source": self.source,
            "query": self.query,
            "items": self.items,
            "confidence": self.confidence,
            "error": self.error,
        }


class Connector(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        ...

    @abstractmethod
    def search(self, query: str, max_results: int = 10) -> ConnectorResult:
        ...
