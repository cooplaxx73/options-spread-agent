from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Credentials:
    api_key: str
    secret_key: str


def load_credentials() -> Credentials:
    missing = [
        name
        for name in ("ALPACA_API_KEY", "ALPACA_SECRET_KEY")
        if not os.environ.get(name)
    ]
    if missing:
        raise RuntimeError(
            f"Missing {' and '.join(missing)} in {PROJECT_ROOT / '.env'}.\n"
            "Copy .env.example to .env and paste in your Alpaca paper keys."
        )
    return Credentials(
        api_key=os.environ["ALPACA_API_KEY"],
        secret_key=os.environ["ALPACA_SECRET_KEY"],
    )


PAPER = True
REQUIRED_OPTIONS_LEVEL = 3

UNIVERSE = ("SPY", "QQQ", "AAPL")
CYCLE_MINUTES = 20

REALIZED_VOL_DAYS = 20
IV_RV_SELL_THRESHOLD = 1.20
IV_RV_BUY_THRESHOLD = 0.90

STRIKE_RANGE_PCT = 0.10

DTE_MIN = 30
DTE_MAX = 45

SHORT_LEG_TARGET_DELTA = 0.30
WING_WIDTHS = (5.0, 10.0, 15.0)
TREND_SMA_DAYS = 50
MAX_BID_ASK_WIDTH_PCT = 0.10

MAX_OPEN_POSITIONS = 3
RISK_BANDS = {"weak": 0.01, "medium": 0.02, "strong": 0.03}
SCORE_FLOOR = 0.50

PROFIT_TARGET_PCT = 0.50
STOP_LOSS_CREDIT_MULTIPLE = 2.0
TIME_EXIT_DTE = 21

DATA_DIR = PROJECT_ROOT / "data"
CHAIN_SNAPSHOT_DIR = DATA_DIR / "chains"
DECISION_LOG = DATA_DIR / "decisions.csv"
STATE_FILE = PROJECT_ROOT / "state.json"
