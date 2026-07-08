import os

from dotenv import load_dotenv
from tavily import TavilyClient

from connectors.base import Connector, ConnectorResult

load_dotenv()


class TavilyConnector(Connector):
    @property
    def name(self) -> str:
        return "tavily"

    def search(self, query: str, max_results: int = 10) -> ConnectorResult:
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            return ConnectorResult(
                source=self.name,
                query=query,
                items=[],
                confidence=0.0,
                error="TAVILY_API_KEY not set in environment",
            )

        try:
            client = TavilyClient(api_key=api_key)
            response = client.search(query=query, max_results=max_results)
        except Exception as exc:
            return ConnectorResult(
                source=self.name,
                query=query,
                items=[],
                confidence=0.0,
                error=str(exc),
            )

        raw_results = response.get("results", [])
        items = [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", "")[:500],
                "score": r.get("score", 0.0),
                "published_date": r.get("published_date"),
            }
            for r in raw_results
        ]

        if not items:
            confidence = 0.0
        else:
            scores = [it["score"] for it in items if it["score"]]
            confidence = (sum(scores) / len(scores)) if scores else (0.5 if len(items) < 4 else 0.9)

        return ConnectorResult(
            source=self.name,
            query=query,
            items=items,
            confidence=confidence,
        )
