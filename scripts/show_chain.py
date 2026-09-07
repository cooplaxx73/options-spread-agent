from __future__ import annotations

import sys

from src import config
from src.broker import chain as chain_mod


def main(argv: list[str]) -> int:
    underlying = (argv[1] if len(argv) > 1 else config.UNIVERSE[0]).upper()

    try:
        spot = chain_mod.get_spot_price(underlying)
        quotes = chain_mod.fetch_chain(underlying, spot=spot)
    except Exception as exc:  # noqa: BLE001
        print(f"Could not fetch chain for {underlying}: {exc}")
        return 1

    if not quotes:
        print(f"No contracts returned for {underlying} in the {config.DTE_MIN}-{config.DTE_MAX} day window.")
        return 1

    path = chain_mod.save_snapshot(underlying, spot, quotes)
    expiries = sorted({q.expiry for q in quotes})
    liquid = [q for q in quotes if q.is_liquid]
    quote_age = quotes[0].quote_time

    print(f"{underlying} spot ${spot:,.2f}")
    print(f"  contracts     {len(quotes)}  ({len(liquid)} pass the liquidity gate)")
    print(f"  expiries      {', '.join(e.isoformat() for e in expiries)}")
    print(f"  strikes       ${min(q.strike for q in quotes):,.0f} - ${max(q.strike for q in quotes):,.0f}")
    print(f"  quotes as of  {quote_age:%Y-%m-%d %H:%M} UTC")
    print(f"  saved         {path.relative_to(config.PROJECT_ROOT)}")
    print()

    near_target = sorted(quotes, key=lambda q: abs(abs(q.delta) - config.SHORT_LEG_TARGET_DELTA))[:8]
    print(f"Closest to the {config.SHORT_LEG_TARGET_DELTA:.2f} delta short leg target:")
    print(f"  {'expiry':<12}{'type':<6}{'strike':>9}{'delta':>8}{'iv':>8}{'bid':>8}{'ask':>8}{'width':>8}")
    for q in sorted(near_target, key=lambda q: (q.expiry, q.option_type, q.strike)):
        flag = "" if q.is_liquid else "  <- wide"
        print(
            f"  {q.expiry.isoformat():<12}{q.option_type:<6}{q.strike:>9,.0f}"
            f"{q.delta:>8.3f}{q.implied_volatility:>8.3f}{q.bid:>8.2f}{q.ask:>8.2f}"
            f"{q.bid_ask_width_pct:>7.1%}{flag}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
