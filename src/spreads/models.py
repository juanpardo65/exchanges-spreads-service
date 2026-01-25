"""Pydantic models for API requests and responses."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ExchangePrice(BaseModel):
    """Price snapshot from one exchange."""

    exchange: str
    bid: str
    ask: str
    last: str
    mark: str
    funding_rate: str = "0"  # funding rate, decimal e.g. 0.0001 = 0.01% per 8h


class BestPrice(BaseModel):
    """Best bid or ask with exchange."""

    exchange: str
    price: str


class Arbitrage(BaseModel):
    """Arbitrage opportunity summary for bots."""

    best_bid: BestPrice
    best_ask: BestPrice
    spread_pct_abs: float  # abs(best_bid - best_ask) / best_ask * 100, завжди >= 0
    net_spread_pct: float  # spread_pct_abs + (funding_bid - funding_ask)*100, чистий спред з урахуванням фандингу
    direction: str


class PricesResponse(BaseModel):
    """Response for GET /v1/prices."""

    symbol: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    prices: list[ExchangePrice]
    arbitrage: Arbitrage
    pairwise_spreads: dict[str, str] = Field(default_factory=dict)  # value = decimal string, e.g. "0.00001234"
    errors: list[dict[str, str]] = Field(default_factory=list)


class FetchError(BaseModel):
    """Error from a failed exchange fetch."""

    exchange: str
    error: str
