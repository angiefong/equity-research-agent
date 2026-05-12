from typing import Optional
from pydantic import BaseModel, Field


class PricePoint(BaseModel):
    date: str
    price: float


class MarketSnapshot(BaseModel):
    ticker: str
    current_price: float
    change_abs: Optional[float] = None
    change_pct: Optional[float] = None
    high_52w: Optional[float] = None
    low_52w: Optional[float] = None
    market_cap: Optional[float] = None
    pe_forward: Optional[float] = None
    eps_ttm: Optional[float] = None
    dividend_yield: Optional[float] = None
    volume: Optional[int] = None
    series: list[PricePoint] = Field(default_factory=list)
