import os
from datetime import date
from tavily import TavilyClient
from backend.schemas.evidence import EvidenceSpan
from backend.tools.source_ref import format_source_ref


def get_news_evidence(ticker: str, max_results: int = 5) -> list[EvidenceSpan]:
    client = TavilyClient(api_key=os.environ.get("TAVILY_KEY", ""))
    results = client.search(
        f"{ticker} stock earnings financial news analysis",
        max_results=max_results,
        search_depth="advanced",
    )
    spans = []
    for r in results.get("results", []):
        url_slug = r["url"].rstrip("/").split("/")[-1][:40]
        pub_date = (r.get("published_date") or str(date.today()))[:10]
        spans.append(EvidenceSpan(
            text=r["content"][:500],
            source_ref=format_source_ref("news", f"tavily-{url_slug}", pub_date),
            agent_origin="news",
            confidence=0.8,
        ))
    return spans
