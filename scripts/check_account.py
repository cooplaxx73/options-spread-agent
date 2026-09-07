from __future__ import annotations

import sys

from src import config
from src.broker.client import get_account_summary


def main() -> int:
    try:
        account = get_account_summary()
    except Exception as exc:
        print(f"Could not reach Alpaca: {exc}")
        return 1

    print("Alpaca paper account")
    print(f"  status                {account.status}")
    print(f"  equity                ${account.equity:,.2f}")
    print(f"  cash                  ${account.cash:,.2f}")
    print(f"  options buying power  ${account.options_buying_power:,.2f}")
    print(f"  options level         {account.options_level}")
    print()

    if not account.can_trade_spreads:
        print(f"NOT READY: {account.blocking_reason}")
        return 1

    largest_risk = account.equity * max(config.RISK_BANDS.values())
    print("READY: multi-leg spreads are permitted on this account.")
    print(
        f"  at most {config.MAX_OPEN_POSITIONS} open positions, "
        f"risking up to ${largest_risk:,.0f} each"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
