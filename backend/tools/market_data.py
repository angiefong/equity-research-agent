import math
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


def fetch_alpha_vantage_overview(ticker: str, overview: dict | None = None) -> list[EvidenceSpan]:
    if overview is None:
        overview = get_company_overview(ticker)
    if "Symbol" not in overview:
        return []
    spans = []
    for field in ["Description", "Sector", "Industry", "52WeekHigh", "52WeekLow"]:
        val = overview.get(field)
        if val and val != "None":
            spans.append(EvidenceSpan(
                text=f"{ticker} {field}: {val}",
                source_ref=format_source_ref("market", f"{ticker}-overview", field.lower()),
                agent_origin="market_data",
            ))
    return spans


def get_market_data_evidence(ticker: str, overview: dict | None = None) -> list[EvidenceSpan]:
    spans = [fetch_price_history(ticker)]
    spans.extend(fetch_financials(ticker))
    spans.extend(fetch_alpha_vantage_overview(ticker, overview=overview))
    return spans


def get_company_overview(ticker: str) -> dict:
    """Return Alpha Vantage OVERVIEW response for the ticker, or empty dict on error."""
    api_key = os.environ.get("ALPHA_VANTAGE_KEY")
    if not api_key:
        return {}
    try:
        resp = requests.get(
            "https://www.alphavantage.co/query",
            params={"function": "OVERVIEW", "symbol": ticker, "apikey": api_key},
            timeout=10,
        )
        if resp.ok:
            return resp.json() or {}
    except requests.RequestException:
        pass
    return {}


from backend.schemas.market_snapshot import MarketSnapshot, PricePoint


def get_market_snapshot(ticker: str) -> MarketSnapshot:
    """Return a structured snapshot of the ticker's recent market data.

    Uses yfinance for price history and the .info dict for facts. Returns
    a MarketSnapshot with None for any field yfinance does not provide.
    """
    t = yf.Ticker(ticker)
    info = t.info or {}
    hist = t.history(period="90d")

    if len(hist) == 0:
        return MarketSnapshot(ticker=ticker, current_price=0.0)

    closes = hist["Close"]
    current = float(closes.iloc[-1])
    prior = float(closes.iloc[-2]) if len(closes) >= 2 else None

    change_abs: float | None = None
    change_pct: float | None = None
    if prior is not None and prior != 0:
        change_abs = current - prior
        change_pct = (change_abs / prior) * 100.0

    series = [
        PricePoint(date=idx.strftime("%Y-%m-%d"), price=float(price))
        for idx, price in zip(hist.index, closes)
    ]

    def _opt_float(key: str) -> float | None:
        v = info.get(key)
        if v is None:
            return None
        try:
            f = float(v)
        except (TypeError, ValueError):
            return None
        return None if math.isnan(f) else f

    def _opt_int(key: str) -> int | None:
        f = _opt_float(key)
        return int(f) if f is not None else None

    # yfinance returns dividendYield as a percent value (0.37 = 0.37%); normalize to fraction
    _dy = _opt_float("dividendYield")

    return MarketSnapshot(
        ticker=ticker,
        current_price=current,
        change_abs=change_abs,
        change_pct=change_pct,
        high_52w=_opt_float("fiftyTwoWeekHigh"),
        low_52w=_opt_float("fiftyTwoWeekLow"),
        market_cap=_opt_float("marketCap"),
        pe_forward=_opt_float("forwardPE"),
        eps_ttm=_opt_float("trailingEps"),
        dividend_yield=(_dy / 100.0) if _dy is not None else None,
        volume=_opt_int("volume"),
        series=series,
    )
