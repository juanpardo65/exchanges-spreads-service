from typing import Protocol

from pydantic import BaseModel


class ExchangePrices(BaseModel):
    exchange: str
    bid: str
    ask: str
    last: str
    mark: str
    funding: str = "0"


def to_exchange_symbol(canonical: str, exchange: str) -> str:
    canonical = canonical.strip().upper()
    if exchange in ("mexc", "gate"):
        if "USDT" in canonical and "_" not in canonical:
            base = canonical.replace("USDT", "")
            return f"{base}_USDT"
        if "_" in canonical:
            return canonical
        for q in ("USDT", "USDC", "BUSD"):
            if canonical.endswith(q):
                return f"{canonical[:-len(q)]}_{q}"
        return canonical
    return canonical


def to_canonical_symbol(exchange_symbol: str) -> str:
    s = (exchange_symbol or "").strip().upper()
    if "_" in s:
        return s.replace("_", "")
    return s


class FetcherProtocol(Protocol):
    async def __call__(self, symbol: str, timeout: float) -> ExchangePrices: ...
