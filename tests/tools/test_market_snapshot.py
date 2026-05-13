from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

from backend.tools.market_data import get_market_snapshot


def _mock_yf_ticker():
    mock = MagicMock()
    mock.info = {
        "marketCap": 3.2e12,
        "forwardPE": 28.5,
        "trailingEps": 6.05,
        "dividendYield": 0.49,
        "volume": 72_000_000,
        "fiftyTwoWeekHigh": 238.0,
        "fiftyTwoWeekLow": 164.0,
    }
    dates = pd.date_range("2026-02-10", periods=90)
    closes = np.linspace(180.0, 214.82, 90)
    mock.history.return_value = pd.DataFrame({"Close": closes}, index=dates)
    return mock


def test_get_market_snapshot_from_yfinance():
    with patch("backend.tools.market_data.yf.Ticker", return_value=_mock_yf_ticker()):
        snap = get_market_snapshot("AAPL")
    assert snap.ticker == "AAPL"
    assert abs(snap.current_price - 214.82) < 0.01
    assert snap.change_abs is not None
    assert snap.change_pct is not None
    assert snap.high_52w == 238.0
    assert snap.low_52w == 164.0
    assert snap.market_cap == 3.2e12
    assert snap.pe_forward == 28.5
    assert snap.eps_ttm == 6.05
    # yfinance returns dividendYield as a percent (0.49 → 0.49%); tool normalizes to fraction
    assert abs(snap.dividend_yield - 0.0049) < 1e-9
    assert snap.volume == 72_000_000
    assert len(snap.series) == 90
    assert snap.series[0].date == "2026-02-10"
    assert snap.series[-1].price == snap.current_price


def test_get_market_snapshot_handles_missing_info():
    mock = MagicMock()
    mock.info = {}
    dates = pd.date_range("2026-02-10", periods=2)
    mock.history.return_value = pd.DataFrame({"Close": [180.0, 185.0]}, index=dates)
    with patch("backend.tools.market_data.yf.Ticker", return_value=mock):
        snap = get_market_snapshot("XYZ")
    assert snap.current_price == 185.0
    assert snap.change_abs == 5.0
    assert abs(snap.change_pct - (5.0 / 180.0 * 100)) < 0.001
    assert snap.market_cap is None
    assert snap.pe_forward is None
    assert snap.eps_ttm is None
    assert snap.dividend_yield is None
    assert snap.volume is None
    assert snap.high_52w is None
    assert snap.low_52w is None
    assert len(snap.series) == 2


def test_get_market_snapshot_handles_empty_history():
    mock = MagicMock()
    mock.info = {}
    mock.history.return_value = pd.DataFrame({"Close": []})
    with patch("backend.tools.market_data.yf.Ticker", return_value=mock):
        snap = get_market_snapshot("XYZ")
    assert snap.current_price == 0.0
    assert snap.change_abs is None
    assert snap.change_pct is None
    assert snap.series == []


def test_get_market_snapshot_handles_nan_and_string_info():
    """yfinance can return float('nan') or 'N/A' for any numeric field."""
    mock = MagicMock()
    mock.info = {
        "marketCap": float("nan"),
        "forwardPE": "N/A",
        "trailingEps": float("nan"),
        "dividendYield": "N/A",
        "volume": float("nan"),
        "fiftyTwoWeekHigh": 100.0,
        "fiftyTwoWeekLow": float("nan"),
    }
    dates = pd.date_range("2026-02-10", periods=2)
    mock.history.return_value = pd.DataFrame({"Close": [180.0, 185.0]}, index=dates)
    with patch("backend.tools.market_data.yf.Ticker", return_value=mock):
        snap = get_market_snapshot("XYZ")
    assert snap.market_cap is None
    assert snap.pe_forward is None
    assert snap.eps_ttm is None
    assert snap.dividend_yield is None
    assert snap.volume is None
    assert snap.high_52w == 100.0
    assert snap.low_52w is None
