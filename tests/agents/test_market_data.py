from unittest.mock import patch
from backend.agents.market_data import market_data_agent


def test_market_data_returns_company_metadata():
    fake_overview = {
        "Name": "Apple Inc.",
        "Exchange": "NASDAQ",
        "Sector": "Consumer Electronics",
    }
    with patch("backend.agents.market_data.get_market_data_evidence") as mock_ev, \
         patch("backend.agents.market_data.get_company_overview", return_value=fake_overview):
        mock_ev.return_value = []
        result = market_data_agent({"ticker": "AAPL"})
    assert result["company_name"] == "Apple Inc."
    assert result["exchange"] == "NASDAQ"
    assert result["sector"] == "Consumer Electronics"
