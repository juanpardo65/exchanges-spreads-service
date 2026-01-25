"""Base provider interface and symbol mapping."""

from typing import Protocol

from pydantic import BaseModel


class ExchangePrices(BaseModel):
    """Raw price data from an exchange (bid, ask, last, mark, funding, exchange name)."""

    exchange: str
    bid: str
    ask: str
    last: str
    mark: str
    funding: str = "0"  # funding rate, decimal e.g. 0.0001 = 0.01% per 8h


def to_exchange_symbol(canonical: str, exchange: str) -> str:
    """
    Convert canonical symbol (e.g. BTCUSDT) to exchange-specific format.

    - bybit, binance: BTCUSDT (unchanged)
    - mexc, gate: BTC_USDT
    """
    canonical = canonical.strip().upper()
    if exchange in ("mexc", "gate"):
        if "USDT" in canonical and "_" not in canonical:
            base = canonical.replace("USDT", "")
            return f"{base}_USDT"
        if "_" in canonical:
            return canonical
        # fallback: assume BASEUSDT
        for q in ("USDT", "USDC", "BUSD"):
            if canonical.endswith(q):
                return f"{canonical[:-len(q)]}_{q}"
        return canonical
    return canonical


def to_canonical_symbol(exchange_symbol: str) -> str:
    """
    Convert exchange-specific symbol to canonical (e.g. BTC_USDT -> BTCUSDT).
    Used when parsing symbol lists from exchange APIs.
    """
    s = (exchange_symbol or "").strip().upper()
    if "_" in s:
        return s.replace("_", "")
    return s


class FetcherProtocol(Protocol):
    """Protocol for exchange price fetchers. Implementations return ExchangePrices or raise."""

    async def __call__(self, symbol: str, timeout: float) -> ExchangePrices: ...
