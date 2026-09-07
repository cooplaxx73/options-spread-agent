from __future__ import annotations

from dataclasses import dataclass

from alpaca.trading.client import TradingClient

from src import config


def trading_client() -> TradingClient:
    creds = config.load_credentials()
    return TradingClient(
        api_key=creds.api_key,
        secret_key=creds.secret_key,
        paper=config.PAPER,
    )


@dataclass(frozen=True)
class AccountSummary:
    equity: float
    cash: float
    options_buying_power: float
    options_level: int
    status: str
    trading_blocked: bool

    @property
    def can_trade_spreads(self) -> bool:
        return (
            self.options_level >= config.REQUIRED_OPTIONS_LEVEL
            and not self.trading_blocked
        )

    @property
    def blocking_reason(self) -> str | None:
        if self.trading_blocked:
            return "trading is blocked on this account"
        if self.options_level < config.REQUIRED_OPTIONS_LEVEL:
            return (
                f"options level {self.options_level}, "
                f"but level {config.REQUIRED_OPTIONS_LEVEL} is required for spreads"
            )
        return None


def get_account_summary(client: TradingClient | None = None) -> AccountSummary:
    account = (client or trading_client()).get_account()
    return AccountSummary(
        equity=float(account.equity),
        cash=float(account.cash),
        options_buying_power=float(account.options_buying_power),
        options_level=int(account.options_trading_level),
        status=str(account.status.value),
        trading_blocked=bool(account.trading_blocked),
    )
