import arxiv

from connectors.base import Connector, ConnectorResult


class ArxivConnector(Connector):
    @property
    def name(self) -> str:
        return "arxiv"

    def search(self, query: str, max_results: int = 10) -> ConnectorResult:
        try:
            client = arxiv.Client()
            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance,
            )
            papers = list(client.results(search))
        except Exception as exc:
            return ConnectorResult(
                source=self.name,
                query=query,
                items=[],
                confidence=0.0,
                error=str(exc),
            )

        items = [
            {
                "title": p.title,
                "summary": p.summary[:500],
                "authors": [a.name for a in p.authors],
                "published": p.published.date().isoformat() if p.published else None,
                "url": p.entry_id,
                "pdf_url": p.pdf_url,
                "categories": p.categories,
            }
            for p in papers
        ]

        confidence = 0.0 if not items else (0.5 if len(items) < 4 else 0.9)

        return ConnectorResult(
            source=self.name,
            query=query,
            items=items,
            confidence=confidence,
        )
