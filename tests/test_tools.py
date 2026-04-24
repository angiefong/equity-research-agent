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
