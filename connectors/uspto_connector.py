"""
Milestone 3 — USPTO connector.

Fetches patent data from the USPTO Open Data Portal (ODP) Patent File Wrapper
API. Used in Phase 4 deep diligence (IP defensibility, Alice Sec. 101 risk).

NOTE (built 2026-07): the classic PatentsView REST API that this connector was
originally scoped against (api.patentsview.org / search.patentsview.org) is
retired — PatentsView migrated into the USPTO Open Data Portal on 2026-03-20.
This connector targets the current live endpoint. Host, path, method, and auth
header were confirmed by a direct unauthenticated probe (POST to
api.uspto.gov/api/v1/patent/applications/search returns 401 Unauthorized, not a
DNS/connection failure — confirming the endpoint is live and those parts are
correct) and cross-referenced against USPTO ODP documentation and a third-party
client library. ODP API keys require a USPTO.gov account with ID.me identity
verification to obtain, which isn't something obtainable in this environment,
so exact field names inside the assignee/inventor arrays are best-effort and
parsed defensively (.get() with fallback keys) rather than assumed exact — if
USPTO renames a nested field, this connector degrades to a missing value, not
a crash.
"""
import os

import requests
from dotenv import load_dotenv

from connectors.base import Connector, ConnectorResult

load_dotenv()

_API = "https://api.uspto.gov/api/v1/patent/applications/search"


class USPTOConnector(Connector):
    @property
    def name(self) -> str:
        return "uspto"

    def search(self, query: str, max_results: int = 10) -> ConnectorResult:
        api_key = os.getenv("USPTO_API_KEY")
        if not api_key:
            return ConnectorResult(
                source=self.name,
                query=query,
                items=[],
                confidence=0.0,
                error=(
                    "USPTO_API_KEY not set in environment (USPTO's Open Data Portal "
                    "requires an ID.me-verified API key — see data.uspto.gov). Absence "
                    "of a key means patent presence/absence could not be checked at "
                    "all; treat this as data-blind, NOT as evidence the company has "
                    "no patents."
                ),
            )

        try:
            response = requests.post(
                _API,
                headers={"X-API-Key": api_key, "Content-Type": "application/json"},
                json={"q": query, "pagination": {"offset": 0, "limit": max_results}},
                timeout=15,
            )
        except requests.RequestException as exc:
            return ConnectorResult(
                source=self.name, query=query, items=[], confidence=0.0, error=str(exc),
            )

        if response.status_code != 200:
            return ConnectorResult(
                source=self.name,
                query=query,
                items=[],
                confidence=0.0,
                error=f"USPTO API returned HTTP {response.status_code}: {response.text[:300]}",
            )

        try:
            data = response.json()
        except ValueError as exc:
            return ConnectorResult(
                source=self.name, query=query, items=[], confidence=0.0,
                error=f"USPTO API returned non-JSON response: {exc}",
            )

        applications = data.get("patentFileWrapperDataBag") or []

        if not applications:
            # CRITICAL: absence of patents is AMBIGUOUS, not negative. Many strong AI
            # companies deliberately use trade secrets instead of patents — patenting
            # requires public disclosure of the method, which some choose to avoid.
            # confidence=0.0 here means "no signal either way," not "no IP." The
            # Phase 4 prompt must treat an empty result as neutral/data-blind, the
            # same pattern used for GitHub absence in Phase 1.
            return ConnectorResult(source=self.name, query=query, items=[], confidence=0.0)

        items = []
        for app in applications[:max_results]:
            meta = app.get("applicationMetaData") or {}
            assignees = meta.get("assigneeBag") or []
            inventors = meta.get("inventorBag") or []
            grant_date = meta.get("grantDate")
            items.append({
                "application_number": app.get("applicationNumberText"),
                "patent_number": meta.get("patentNumber"),
                "title": meta.get("inventionTitle"),
                "filing_date": meta.get("filingDate"),
                "grant_date": grant_date,
                # grant_date present = granted patent; absent = still-pending
                # application. Both are relevant signal for Phase 4.
                "status": "granted" if grant_date else "pending",
                "status_description": meta.get("applicationStatusDescriptionText"),
                "assignees": [
                    a.get("assigneeNameText") or a.get("assigneeOrganizationName") or a.get("name")
                    for a in assignees if isinstance(a, dict)
                ],
                "inventors": [
                    (a.get("inventorNameText")
                     or f"{a.get('firstName', '')} {a.get('lastName', '')}".strip()
                     or None)
                    for a in inventors if isinstance(a, dict)
                ],
            })

        confidence = 0.8 if len(items) >= 2 else 0.6
        return ConnectorResult(source=self.name, query=query, items=items, confidence=confidence)
