"""Spread calculation: best_bid, best_ask, arbitrage, pairwise_spreads, direction."""

from ..models import Arbitrage, BestPrice, ExchangePrice
from ..utils import to_decimal_str


def compute_spreads(prices: list[ExchangePrice]) -> tuple[Arbitrage, dict[str, str]]:
    """
    From a list of exchange prices, compute arbitrage summary and pairwise spreads.

    - best_bid: max bid across exchanges (best price to open SHORT / sell)
    - best_ask: min ask across exchanges (best price to open LONG / buy)
    - spread_pct_abs = abs(best_bid - best_ask) / best_ask * 100 (завжди >= 0)
    - net_spread_pct = spread_pct_abs + (funding_bid - funding_ask)*100, без abs (чистий спред з урахуванням фандингу за 8h)
    - direction: "LONG on {ask_ex} @ {ask}, SHORT on {bid_ex} @ {bid}" or "No arbitrage"
      (futures: open LONG at best_ask, open SHORT at best_bid)
    - pairwise_spreads: for each pair (A,B) key "A_B" (A < B alphabetically), value = price_A - price_B (using last)
    """
    if not prices:
        return (
            Arbitrage(
                best_bid=BestPrice(exchange="", price="0"),
                best_ask=BestPrice(exchange="", price="0"),
                spread_pct_abs=0.0,
                net_spread_pct=0.0,
                direction="No arbitrage",
            ),
            {},
        )

    best_bid = max(prices, key=lambda p: float(p.bid or "0"))
    best_ask = min(prices, key=lambda p: float(p.ask or "inf"))

    spread = float(best_bid.bid or "0") - float(best_ask.ask or "0")
    ask_f = float(best_ask.ask or "0")
    spread_pct_abs = (abs(spread) / (ask_f or 1) * 100) if ask_f else 0.0

    # Чистий спред з урахуванням фандингу: LONG на ask (платимо funding_ask), SHORT на bid (отримуємо funding_bid)
    # net = spread_pct_abs + (funding_bid - funding_ask)*100 (funding у decimal, 0.0001 = 0.01%)
    funding_bid = float(best_bid.funding_rate or "0")
    funding_ask = float(best_ask.funding_rate or "0")
    net_spread_pct = round(spread_pct_abs + (funding_bid - funding_ask) * 100, 4)

    direction = (
        f"LONG on {best_ask.exchange} @ {best_ask.ask}, SHORT on {best_bid.exchange} @ {best_bid.bid}"
        if spread > 0
        else "No arbitrage"
    )

    arbitrage = Arbitrage(
        best_bid=BestPrice(exchange=best_bid.exchange, price=best_bid.bid),
        best_ask=BestPrice(exchange=best_ask.exchange, price=best_ask.ask),
        spread_pct_abs=round(spread_pct_abs, 4),
        net_spread_pct=net_spread_pct,
        direction=direction,
    )

    by_ex: dict[str, ExchangePrice] = {p.exchange: p for p in prices}
    ex_names = sorted(by_ex.keys())
    pairwise: dict[str, str] = {}
    for i in range(len(ex_names)):
        for j in range(i + 1, len(ex_names)):
            a, b = ex_names[i], ex_names[j]
            va = float(by_ex[a].last or "0")
            vb = float(by_ex[b].last or "0")
            pairwise[f"{a}_{b}"] = to_decimal_str(str(round(va - vb, 8)))

    return (arbitrage, pairwise)
