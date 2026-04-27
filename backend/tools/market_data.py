import os
import requests
import yfinance as yf
from backend.schemas.evidence import EvidenceSpan
from backend.tools.source_ref import format_source_ref


def fetch_price_history(ticker: str) -> EvidenceSpan:
    t = yf.Ticker(ticker)
    hist = t.history(period="90d")
    start = hist.index[0].strftime("%Y-%m-%d")
    end = hist.index[-1].strftime("%Y-%m-%d")
    current = hist["Close"].iloc[-1]
    change = (hist["Close"].iloc[-1] - hist["Close"].iloc[0]) / hist["Close"].iloc[0] * 100
    return EvidenceSpan(
        text=f"{ticker} price: ${current:.2f} ({change:+.1f}% over 90d, {start} to {end})",
        source_ref=format_source_ref("market", f"{ticker}-price", "90d-history"),
        agent_origin="market_data",
    )


def fetch_financials(ticker: str) -> list[EvidenceSpan]:
    t = yf.Ticker(ticker)
    info = t.info
    fields = {
        "marketCap": "market-cap",
        "trailingPE": "pe-ratio",
        "revenueGrowth": "revenue-growth",
        "grossMargins": "gross-margin",
        "operatingMargins": "operating-margin",
    }
    spans = []
    for key, label in fields.items():
        val = info.get(key)
        if val is not None:
            spans.append(EvidenceSpan(
                text=f"{ticker} {label}: {val}",
                source_ref=format_source_ref("market", f"{ticker}-financials", label),
                agent_origin="market_data",
            ))
    return spans


def fetch_alpha_vantage_overview(ticker: str) -> list[EvidenceSpan]:
    api_key = os.environ.get("ALPHA_VANTAGE_KEY", "")
    url = (
        f"https://www.alphavantage.co/query"
        f"?function=OVERVIEW&symbol={ticker}&apikey={api_key}"
    )
    resp = requests.get(url, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    if "Symbol" not in data:
        return []
    spans = []
    for field in ["Description", "Sector", "Industry", "52WeekHigh", "52WeekLow"]:
        val = data.get(field)
        if val and val != "None":
            spans.append(EvidenceSpan(
                text=f"{ticker} {field}: {val}",
                source_ref=format_source_ref("market", f"{ticker}-overview", field.lower()),
                agent_origin="market_data",
            ))
    return spans


def get_market_data_evidence(ticker: str) -> list[EvidenceSpan]:
    spans = [fetch_price_history(ticker)]
    spans.extend(fetch_financials(ticker))
    spans.extend(fetch_alpha_vantage_overview(ticker))
    return spans
