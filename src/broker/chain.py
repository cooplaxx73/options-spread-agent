from __future__ import annotations

import datetime as dt
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from alpaca.data.historical.option import OptionHistoricalDataClient
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import OptionChainRequest, StockLatestTradeRequest
from alpaca.trading.enums import ContractType

from src import config


@dataclass(frozen=True)
class OptionQuote:
    symbol: str
    underlying: str
    expiry: dt.date
    strike: float
    option_type: str
    bid: float
    ask: float
    implied_volatility: float
    delta: float
    quote_time: dt.datetime

    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2

    @property
    def bid_ask_width(self) -> float:
        return self.ask - self.bid

    @property
    def bid_ask_width_pct(self) -> float:
        if self.mid <= 0:
            return float("inf")
        return self.bid_ask_width / self.mid

    @property
    def is_liquid(self) -> bool:
        return self.bid_ask_width_pct <= config.MAX_BID_ASK_WIDTH_PCT

    def days_to_expiry(self, asof: dt.date | None = None) -> int:
        return (self.expiry - (asof or dt.date.today())).days


def _option_client() -> OptionHistoricalDataClient:
    creds = config.load_credentials()
    return OptionHistoricalDataClient(creds.api_key, creds.secret_key)


def _stock_client() -> StockHistoricalDataClient:
    creds = config.load_credentials()
    return StockHistoricalDataClient(creds.api_key, creds.secret_key)


def get_spot_price(symbol: str, client: StockHistoricalDataClient | None = None) -> float:
    client = client or _stock_client()
    request = StockLatestTradeRequest(symbol_or_symbols=symbol)
    return float(client.get_stock_latest_trade(request)[symbol].price)


def _parse_snapshot(symbol: str, underlying: str, snapshot) -> OptionQuote | None:
    quote = snapshot.latest_quote
    greeks = snapshot.greeks
    if quote is None or greeks is None or snapshot.implied_volatility is None:
        return None
    if quote.bid_price is None or quote.ask_price is None:
        return None

    return OptionQuote(
        symbol=symbol,
        underlying=underlying,
        expiry=dt.datetime.strptime(symbol[len(underlying) : len(underlying) + 6], "%y%m%d").date(),
        strike=int(symbol[-8:]) / 1000,
        option_type="call" if symbol[-9] == "C" else "put",
        bid=float(quote.bid_price),
        ask=float(quote.ask_price),
        implied_volatility=float(snapshot.implied_volatility),
        delta=float(greeks.delta),
        quote_time=quote.timestamp,
    )


def fetch_chain(
    underlying: str,
    option_type: str | None = None,
    asof: dt.date | None = None,
    client: OptionHistoricalDataClient | None = None,
    spot: float | None = None,
) -> list[OptionQuote]:
    asof = asof or dt.date.today()
    spot = spot if spot is not None else get_spot_price(underlying)

    request = OptionChainRequest(
        underlying_symbol=underlying,
        type={"call": ContractType.CALL, "put": ContractType.PUT}.get(option_type),
        strike_price_gte=spot * (1 - config.STRIKE_RANGE_PCT),
        strike_price_lte=spot * (1 + config.STRIKE_RANGE_PCT),
        expiration_date_gte=asof + dt.timedelta(days=config.DTE_MIN),
        expiration_date_lte=asof + dt.timedelta(days=config.DTE_MAX),
    )

    chain = (client or _option_client()).get_option_chain(request)
    quotes = [_parse_snapshot(sym, underlying, snap) for sym, snap in chain.items()]
    return sorted(
        (q for q in quotes if q is not None),
        key=lambda q: (q.expiry, q.option_type, q.strike),
    )


def snapshot_path(underlying: str, taken_at: dt.datetime) -> Path:
    stamp = taken_at.strftime("%Y%m%d-%H%M%S")
    return config.CHAIN_SNAPSHOT_DIR / f"{underlying}-{stamp}.json"


def save_snapshot(underlying: str, spot: float, quotes: list[OptionQuote]) -> Path:
    taken_at = dt.datetime.now(dt.timezone.utc)
    path = snapshot_path(underlying, taken_at)
    path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "underlying": underlying,
        "spot": spot,
        "taken_at": taken_at.isoformat(),
        "quotes": [
            {
                **asdict(q),
                "expiry": q.expiry.isoformat(),
                "quote_time": q.quote_time.isoformat(),
            }
            for q in quotes
        ],
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def load_snapshot(path: Path) -> tuple[str, float, list[OptionQuote]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    quotes = [
        OptionQuote(
            **{
                **q,
                "expiry": dt.date.fromisoformat(q["expiry"]),
                "quote_time": dt.datetime.fromisoformat(q["quote_time"]),
            }
        )
        for q in payload["quotes"]
    ]
    return payload["underlying"], float(payload["spot"]), quotes


def latest_snapshot(underlying: str) -> Path | None:
    matches = sorted(config.CHAIN_SNAPSHOT_DIR.glob(f"{underlying}-*.json"))
    return matches[-1] if matches else None
