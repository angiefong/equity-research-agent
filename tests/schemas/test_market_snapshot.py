from backend.schemas.market_snapshot import MarketSnapshot, PricePoint


def test_market_snapshot_minimal():
    snap = MarketSnapshot(ticker="AAPL", current_price=214.82)
    assert snap.ticker == "AAPL"
    assert snap.current_price == 214.82
    assert snap.change_abs is None
    assert snap.change_pct is None
    assert snap.high_52w is None
    assert snap.low_52w is None
    assert snap.market_cap is None
    assert snap.pe_forward is None
    assert snap.eps_ttm is None
    assert snap.dividend_yield is None
    assert snap.volume is None
    assert snap.series == []


def test_market_snapshot_full():
    snap = MarketSnapshot(
        ticker="AAPL",
        current_price=214.82,
        change_abs=2.94,
        change_pct=1.39,
        high_52w=238.0,
        low_52w=164.0,
        market_cap=3.2e12,
        pe_forward=28.5,
        eps_ttm=6.05,
        dividend_yield=0.0049,
        volume=72_000_000,
        series=[
            PricePoint(date="2026-02-10", price=180.0),
            PricePoint(date="2026-05-10", price=214.82),
        ],
    )
    assert snap.market_cap == 3.2e12
    assert len(snap.series) == 2
    assert snap.series[0].date == "2026-02-10"
    assert snap.series[0].price == 180.0
