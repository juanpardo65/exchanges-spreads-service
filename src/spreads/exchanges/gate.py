"""Gate.io USDT-margined futures (fx-api) provider."""

import asyncio

import httpx

from .base import ExchangePrices, to_canonical_symbol, to_exchange_symbol

BASE = "https://fx-api.gateio.ws/api/v4"
SETTLE = "usdt"


async def fetch_all_symbols_gate(timeout: float) -> set[str]:
    """
    Fetch all USDT-margined perpetual symbols from Gate.io.
    GET /futures/usdt/contracts; /futures is for perpetuals. Filter status=="trading".
    Symbol is in field "name", e.g. BTC_USDT.
    """
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(f"{BASE}/futures/{SETTLE}/contracts")
        r.raise_for_status()
        data = r.json()
    contracts = data if isinstance(data, list) else []
    return {
        to_canonical_symbol(c.get("name", ""))
        for c in contracts
        if c and (str(c.get("status") or "trading").lower() == "trading")
    }


async def fetch_all_prices_gate(timeout: float) -> dict[str, ExchangePrices]:
    """
    Fetch all USDT-margined perpetual tickers from Gate.io in one request.
    GET /futures/usdt/tickers without contract. Use highest_bid/lowest_ask or last for bid/ask.
    """
    async with httpx.AsyncClient(timeout=timeout) as client:
        r = await client.get(f"{BASE}/futures/{SETTLE}/tickers")
        r.raise_for_status()
        data = r.json()
    lst = data if isinstance(data, list) else []
    out: dict[str, ExchangePrices] = {}
    for t in lst:
        contract = t.get("contract") or t.get("name") or ""
        if not contract:
            continue
        canon = to_canonical_symbol(contract)
        last = str(t.get("last") or "0")
        mark = str(t.get("mark_price") or last)
        bid = str(t.get("highest_bid") or t.get("best_bid") or last)
        ask = str(t.get("lowest_ask") or t.get("best_ask") or last)
        out[canon] = ExchangePrices(
            exchange="gate",
            bid=bid,
            ask=ask,
            last=last,
            mark=mark,
            funding=str(t.get("funding_rate") or t.get("fundingRate") or "0"),
        )
    return out


async def fetch_gate(symbol: str, timeout: float) -> ExchangePrices:
    """
    Fetch futures ticker from Gate.io fx-api.
    Combines /futures/usdt/tickers (last, mark_price) and
    /futures/usdt/order_book (bid/ask).
    """
    sym = to_exchange_symbol(symbol, "gate")
    async with httpx.AsyncClient(timeout=timeout) as client:
        tickers, ob = await asyncio.gather(
            client.get(
                f"{BASE}/futures/{SETTLE}/tickers",
                params={"contract": sym},
            ),
            client.get(
                f"{BASE}/futures/{SETTLE}/order_book",
                params={"contract": sym, "limit": 1},
            ),
        )
    tickers.raise_for_status()
    ob.raise_for_status()
    t_data = tickers.json()
    ob_data = ob.json()

    # Tickers: can be list of one or single object
    if isinstance(t_data, list):
        t = t_data[0] if t_data else {}
    else:
        t = t_data

    last = str(t.get("last") or "0")
    mark = str(t.get("mark_price") or last)

    # Order book: bids/asks are [[price, size], ...], best at index 0
    bids = ob_data.get("bids") or []
    asks = ob_data.get("asks") or []
    bid = str(bids[0][0]) if bids else last
    ask = str(asks[0][0]) if asks else last

    return ExchangePrices(
        exchange="gate",
        bid=bid,
        ask=ask,
        last=last,
        mark=mark,
    )
