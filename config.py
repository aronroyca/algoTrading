from dataclasses import dataclass
import os
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class Config:
    symbol: str
    timeframe: str
    lookback_days: int
    short_window: int
    long_window: int
    cash: float
    data_provider: str

def load_config() -> Config:
    return Config(
        symbol=os.getenv("SYMBOL", "SPY"),
        timeframe=os.getenv("TIMEFRAME", "1d"),
        lookback_days=int(os.getenv("LOOKBACK_DAYS", "365")),
        short_window=int(os.getenv("SHORT_WINDOW", "20")),
        long_window=int(os.getenv("LONG_WINDOW", "50")),
        cash=float(os.getenv("CASH", "10000")),
        data_provider=os.getenv("DATA_PROVIDER", "yfinance"),
    )
