import httpx

from .base import ExchangePrices, to_canonical_symbol, to_exchange_symbol

BASE = "https://api.bitget.com"
# V2 API: productType USDT-FUTURES (V1 umcbl and /api/mix/v1/ are decommissioned)
PRODUCT_TYPE = "USDT-FUTURES"


async def fetch_all_symbols_bitget(timeout: float) -> set[str]:
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(
            f"{BASE}/api/v2/mix/market/contracts",
            params={"productType": PRODUCT_TYPE},
        )
        r.raise_for_status()
        data = r.json()
    if data.get("code") != "00000":
        raise RuntimeError(data.get("msg", "Bitget API error"))
    lst = data.get("data") or []
    return {
        to_canonical_symbol(c.get("symbol", ""))
        for c in lst
        if (c.get("symbolType") or "") == "perpetual"
    }


async def fetch_all_prices_bitget(timeout: float) -> dict[str, ExchangePrices]:
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(
            f"{BASE}/api/v2/mix/market/tickers",
            params={"productType": PRODUCT_TYPE},
        )
        r.raise_for_status()
        data = r.json()
    if data.get("code") != "00000":
        raise RuntimeError(data.get("msg", "Bitget API error"))
    lst = data.get("data") or []
    out: dict[str, ExchangePrices] = {}
    for t in lst:
        sym = t.get("symbol") or ""
        if not sym:
            continue
        canon = to_canonical_symbol(sym)
        last = str(t.get("lastPr") or "0")
        bid = str(t.get("bidPr") or last)
        ask = str(t.get("askPr") or last)
        mark = str(t.get("markPrice") or t.get("indexPrice") or last)
        funding = str(t.get("fundingRate") or "0")
        out[canon] = ExchangePrices(
            exchange="bitget",
            bid=bid,
            ask=ask,
            last=last,
            mark=mark,
            funding=funding,
        )
    return out


async def fetch_bitget(symbol: str, timeout: float) -> ExchangePrices:
    sym = to_exchange_symbol(symbol, "bitget")
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(
            f"{BASE}/api/v2/mix/market/ticker",
            params={"symbol": sym, "productType": PRODUCT_TYPE},
        )
        r.raise_for_status()
        data = r.json()
    if data.get("code") != "00000":
        raise RuntimeError(data.get("msg", "Bitget API error"))
    arr = data.get("data") or []
    t = arr[0] if arr else {}
    last = str(t.get("lastPr") or "0")
    return ExchangePrices(
        exchange="bitget",
        bid=str(t.get("bidPr") or last),
        ask=str(t.get("askPr") or last),
        last=last,
        mark=str(t.get("markPrice") or t.get("indexPrice") or last),
        funding=str(t.get("fundingRate") or "0"),
    )
