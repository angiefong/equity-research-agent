from unittest.mock import patch, MagicMock
from backend.tools.market_data import get_market_data_evidence

def _mock_yf_ticker(pe=25.0, market_cap=3e12, revenue_growth=0.08):
    mock = MagicMock()
    mock.info = {
        "marketCap": market_cap,
        "trailingPE": pe,
        "revenueGrowth": revenue_growth,
        "grossMargins": 0.44,
        "operatingMargins": 0.30,
    }
    import pandas as pd
    import numpy as np
    dates = pd.date_range("2024-01-01", periods=90)
    mock.history.return_value = pd.DataFrame(
        {"Close": np.linspace(170, 195, 90)}, index=dates
    )
    return mock

def test_get_market_data_returns_evidence_spans():
    with patch("backend.tools.market_data.yf.Ticker", return_value=_mock_yf_ticker()), \
         patch("backend.tools.market_data.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {
            "Symbol": "AAPL", "Sector": "Technology", "Description": "Apple Inc."
        }
        spans = get_market_data_evidence("AAPL")
    assert len(spans) >= 3
    assert all(s.agent_origin == "market_data" for s in spans)
    assert all(s.source_ref.startswith("market:") for s in spans)

def test_get_market_data_price_span_has_return():
    with patch("backend.tools.market_data.yf.Ticker", return_value=_mock_yf_ticker()), \
         patch("backend.tools.market_data.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {}
        spans = get_market_data_evidence("AAPL")
    price_spans = [s for s in spans if "price" in s.source_ref]
    assert len(price_spans) >= 1
    assert "%" in price_spans[0].text

from backend.tools.filings import get_cik, fetch_recent_filings

def _mock_tickers_json():
    return {
        "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
        "1": {"cik_str": 789019, "ticker": "MSFT", "title": "Microsoft Corp."},
    }

def _mock_submissions_json():
    return {
        "filings": {
            "recent": {
                "form": ["10-K", "10-Q", "8-K", "10-Q"],
                "filingDate": ["2024-11-01", "2024-08-01", "2024-07-15", "2024-05-01"],
                "accessionNumber": ["0000320193-24-000123", "0000320193-24-000089",
                                    "0000320193-24-000067", "0000320193-24-000045"],
            }
        }
    }

def test_get_cik_known_ticker():
    with patch("backend.tools.filings.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = _mock_tickers_json()
        cik = get_cik("AAPL")
    assert cik == "0000320193"

def test_get_cik_unknown_ticker():
    import pytest
    with patch("backend.tools.filings.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = _mock_tickers_json()
        with pytest.raises(ValueError, match="CIK not found"):
            get_cik("UNKNOWN")

def test_fetch_recent_filings_returns_spans():
    with patch("backend.tools.filings.requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.side_effect = [
            _mock_tickers_json(),
            _mock_submissions_json(),
        ]
        spans = fetch_recent_filings("AAPL", forms=["10-K", "10-Q"], max_filings=2)
    assert len(spans) == 2
    assert all(s.source_ref.startswith("sec:") for s in spans)
    assert all(s.agent_origin == "filings" for s in spans)

from backend.tools.news import get_news_evidence

def _mock_tavily_response():
    return {
        "results": [
            {
                "url": "https://example.com/aapl-earnings-2024",
                "content": "Apple reported strong Q4 earnings with EPS of $1.64.",
                "published_date": "2024-11-01",
            },
            {
                "url": "https://example.com/aapl-china-risk",
                "content": "Apple faces headwinds in China amid competition.",
                "published_date": "2024-10-20",
            },
        ]
    }

def test_get_news_evidence_returns_spans():
    with patch("backend.tools.news.TavilyClient") as MockClient:
        MockClient.return_value.search.return_value = _mock_tavily_response()
        spans = get_news_evidence("AAPL")
    assert len(spans) == 2
    assert all(s.source_ref.startswith("news:") for s in spans)
    assert all(s.agent_origin == "news" for s in spans)
    assert all(s.confidence == 0.8 for s in spans)

def test_get_news_evidence_caps_content_at_500_chars():
    long_content = "x" * 1000
    with patch("backend.tools.news.TavilyClient") as MockClient:
        MockClient.return_value.search.return_value = {
            "results": [{"url": "http://a.com/b", "content": long_content, "published_date": "2024-01-01"}]
        }
        spans = get_news_evidence("AAPL")
    assert len(spans[0].text) <= 500

import numpy as np
import pandas as pd
from backend.tools.quant import (
    compute_returns, compute_volatility, compute_pe_ratio,
    compute_ev_ebitda, fetch_peer_comps, generate_price_chart,
)

def _mock_quant_ticker(pe=25.0, ev_ebitda=20.0):
    mock = MagicMock()
    mock.info = {"trailingPE": pe, "enterpriseToEbitda": ev_ebitda}
    dates = pd.date_range("2024-01-01", periods=90)
    mock.history.return_value = pd.DataFrame(
        {"Close": np.linspace(170, 195, 90)}, index=dates
    )
    return mock

def test_compute_returns_returns_span():
    with patch("backend.tools.quant.yf.Ticker", return_value=_mock_quant_ticker()):
        span = compute_returns("AAPL")
    assert "90-day return" in span.text
    assert span.source_ref.startswith("quant:")
    assert span.agent_origin == "quant_data"

def test_compute_volatility_returns_span():
    with patch("backend.tools.quant.yf.Ticker", return_value=_mock_quant_ticker()):
        span = compute_volatility("AAPL")
    assert "volatility" in span.text.lower()

def test_compute_pe_ratio_returns_span():
    with patch("backend.tools.quant.yf.Ticker", return_value=_mock_quant_ticker(pe=28.5)):
        span = compute_pe_ratio("AAPL")
    assert "28.5" in span.text
    assert span.agent_origin == "quant_interpretation"

def test_generate_price_chart_returns_base64():
    with patch("backend.tools.quant.yf.Ticker", return_value=_mock_quant_ticker()):
        span = generate_price_chart("AAPL")
    assert span.chart_data is not None
    import base64
    decoded = base64.b64decode(span.chart_data)
    assert decoded[:4] == b"\x89PNG"
