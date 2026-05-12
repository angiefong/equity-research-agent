from unittest.mock import patch
from backend.agents.market_data import market_data_agent
from backend.schemas.market_snapshot import MarketSnapshot


def test_market_data_returns_company_metadata():
    fake_overview = {
        "Name": "Apple Inc.",
        "Exchange": "NASDAQ",
        "Sector": "Consumer Electronics",
    }
    fake_snap = MarketSnapshot(ticker="AAPL", current_price=214.82)
    with patch("backend.agents.market_data.get_market_data_evidence") as mock_ev, \
         patch("backend.agents.market_data.get_company_overview", return_value=fake_overview), \
         patch("backend.agents.market_data.get_market_snapshot", return_value=fake_snap):
        mock_ev.return_value = []
        result = market_data_agent({"ticker": "AAPL"})
    assert result["company_name"] == "Apple Inc."
    assert result["exchange"] == "NASDAQ"
    assert result["sector"] == "Consumer Electronics"


def test_market_data_returns_market_snapshot():
    fake_snap = MarketSnapshot(ticker="AAPL", current_price=214.82, change_abs=2.94, change_pct=1.39)
    with patch("backend.agents.market_data.get_market_data_evidence") as mock_ev, \
         patch("backend.agents.market_data.get_company_overview", return_value={}), \
         patch("backend.agents.market_data.get_market_snapshot", return_value=fake_snap):
        mock_ev.return_value = []
        result = market_data_agent({"ticker": "AAPL"})
    assert "market_snapshot" in result
    snap = result["market_snapshot"]
    assert snap.ticker == "AAPL"
    assert snap.current_price == 214.82
    assert snap.change_abs == 2.94
