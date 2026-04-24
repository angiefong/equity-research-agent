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
