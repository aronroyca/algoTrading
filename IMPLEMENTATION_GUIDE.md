# Atlas Implementation Planning Guide

*Planning document for building your autonomous trading platform (personal project)*

**Note:** This is a **planning and design reference**, not a step-by-step tutorial to implement immediately. Use this to understand the architecture and implement components as you build out the system.

---

## Phase 1: Project Setup & Foundation

### Step 1: Create Directory Structure

```bash
# From algoTrading root directory
mkdir -p src/{agents,services,core,strategies}
mkdir -p tests config scripts
mkdir -p data/{opportunities,trades,logs}
```

**Final structure:**
```
algoTrading/
├── src/
│   ├── agents/
│   ├── services/
│   ├── core/
│   └── strategies/
├── tests/
├── config/
├── scripts/
├── data/
│   ├── opportunities/
│   ├── trades/
│   └── logs/
├── main.py
├── requirements.txt
└── .env
```

### Step 2: Update Requirements

Add these dependencies to `requirements.txt`:

```txt
# Existing
pandas==2.2.2
numpy==2.0.1
yfinance==0.2.43
python-dotenv==1.0.1
pandas-datareader==0.10.0
plotly==5.17.0

# New — Trading Infrastructure
alpaca-py==0.20.0              # Alpaca trading API
alpaca-trade-api==3.1.1        # Legacy API (for some features)

# New — Database
psycopg2-binary==2.9.9         # PostgreSQL driver
sqlalchemy==2.0.25             # ORM for database
alembic==1.13.1                # Database migrations

# New — LLM & AI (Local First)
ollama-python==0.1.6           # Ollama local LLM client (PRIMARY)
litellm==1.30.0                # Unified LLM interface
openai==1.10.0                 # OpenAI API (optional)
anthropic==0.18.1              # Claude API (optional)

# New — News & Sentiment (Optional)
newsapi-python==0.2.7          # News API client (optional)
praw==7.7.1                    # Reddit API (optional)

# New — Notifications (Personal)
rich==13.7.0                   # Beautiful terminal output
discord-webhook==1.3.0         # Discord notifications (optional)

# New — Utilities
pydantic==2.6.1                # Data validation
pydantic-settings==2.1.0       # Settings management
pytz==2024.1                   # Timezone handling
schedule==1.2.0                # Task scheduling
tenacity==8.2.3                # Retry logic
```

Install:
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Environment Configuration

Create `.env` file (never commit this!):

```bash
# .env
# Trading
ALPACA_API_KEY=your_alpaca_key_here
ALPACA_SECRET_KEY=your_alpaca_secret_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets  # Paper trading
# For live: https://api.alpaca.markets

# Database (SQLite for simplicity, or PostgreSQL if preferred)
DATABASE_URL=sqlite:///data/atlas_trading.db
# Or for PostgreSQL: postgresql://user:password@localhost:5432/atlas_trading

# LLM (Local First - using Ollama)
OLLAMA_BASE_URL=http://localhost:11434  # Ollama server
OLLAMA_MODEL=llama3.1:8b                # Or qwen2.5:7b, mistral:7b, etc.
# Optional cloud LLMs for comparison:
OPENAI_API_KEY=your_openai_key_here     # Optional
ANTHROPIC_API_KEY=your_anthropic_key    # Optional

# News & Sentiment (Optional for personal use)
NEWS_API_KEY=your_newsapi_key_here      # Optional
REDDIT_CLIENT_ID=your_reddit_client_id  # Optional
REDDIT_CLIENT_SECRET=your_reddit_secret # Optional
REDDIT_USER_AGENT=atlas_trading_bot_v1  # Optional

# Notifications (Personal Setup)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...  # Optional for mobile alerts
NOTIFICATION_EMAIL=your_email@gmail.com  # Optional for email alerts

# Risk Limits
MAX_POSITION_SIZE_PCT=5.0          # Max 5% of portfolio per trade
MAX_PORTFOLIO_RISK_PCT=20.0        # Max 20% of capital deployed
MAX_SECTOR_CONCENTRATION_PCT=40.0  # Max 40% in one sector
MAX_DAILY_TRADES=20                # Max trades per day
MAX_DAILY_LOSS_PCT=2.0             # Circuit breaker: stop trading if down 2%

# Strategy Parameters
DEFAULT_STOP_LOSS_PCT=1.5          # Default stop loss
DEFAULT_TAKE_PROFIT_PCT=3.0        # Default take profit
MIN_RISK_REWARD_RATIO=1.5          # Minimum R:R for approval
```

Create `.env.example` for version control:
```bash
cp .env .env.example
# Edit .env.example to remove actual keys, leave placeholders
```

Add to `.gitignore`:
```
.env
data/
*.db
__pycache__/
*.pyc
.venv/
```

---

## Phase 2: Core Infrastructure

### File 1: `src/core/config.py`

**Configuration management using Pydantic**

```python
"""
Configuration management for Atlas trading platform.
Loads environment variables and provides type-safe config objects.
"""
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Literal


class TradingConfig(BaseSettings):
    """Trading API and broker configuration"""
    alpaca_api_key: str
    alpaca_secret_key: str
    alpaca_base_url: str = "https://paper-api.alpaca.markets"

    class Config:
        env_file = ".env"


class DatabaseConfig(BaseSettings):
    """Database connection configuration"""
    database_url: str = "sqlite:///data/atlas_trading.db"  # Default to SQLite

    class Config:
        env_file = ".env"

    def is_sqlite(self) -> bool:
        """Check if using SQLite"""
        return self.database_url.startswith("sqlite")


class LLMConfig(BaseSettings):
    """LLM configuration (local first)"""
    # Local LLM (Ollama) - primary option
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1:8b"

    # Optional cloud LLMs
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    # Shared parameters
    max_tokens: int = 1000
    temperature: float = 0.3  # Lower = more deterministic
    use_local: bool = True    # Use Ollama by default

    class Config:
        env_file = ".env"


class NewsConfig(BaseSettings):
    """News and sentiment API configuration"""
    news_api_key: str
    reddit_client_id: str
    reddit_client_secret: str
    reddit_user_agent: str

    class Config:
        env_file = ".env"


class NotificationConfig(BaseSettings):
    """Notification configuration (optional)"""
    discord_webhook_url: str | None = None
    notification_email: str | None = None

    class Config:
        env_file = ".env"


class RiskConfig(BaseSettings):
    """Risk management parameters"""
    max_position_size_pct: float = Field(default=5.0, ge=0.1, le=50.0)
    max_portfolio_risk_pct: float = Field(default=20.0, ge=1.0, le=100.0)
    max_sector_concentration_pct: float = Field(default=40.0, ge=5.0, le=100.0)
    max_daily_trades: int = Field(default=20, ge=1, le=100)
    max_daily_loss_pct: float = Field(default=2.0, ge=0.1, le=20.0)

    default_stop_loss_pct: float = Field(default=1.5, ge=0.1, le=10.0)
    default_take_profit_pct: float = Field(default=3.0, ge=0.1, le=50.0)
    min_risk_reward_ratio: float = Field(default=1.5, ge=0.5, le=10.0)

    class Config:
        env_file = ".env"

    @field_validator("max_position_size_pct")
    @classmethod
    def validate_position_size(cls, v):
        if v > 10.0:
            print(f"⚠️  Warning: max_position_size_pct is {v}% - this is aggressive!")
        return v


class StrategyConfig(BaseSettings):
    """Strategy-specific parameters"""
    enabled_strategies: list[str] = ["momentum", "breakout", "mean_reversion"]
    min_confidence_threshold: float = 0.6  # 0-1 scale
    lookback_periods: dict[str, int] = {
        "short": 20,
        "medium": 50,
        "long": 200
    }

    class Config:
        env_file = ".env"


class AppConfig:
    """Main application configuration aggregator"""

    def __init__(self):
        self.trading = TradingConfig()
        self.database = DatabaseConfig()
        self.llm = LLMConfig()
        self.news = NewsConfig()
        self.notifications = NotificationConfig()
        self.risk = RiskConfig()
        self.strategy = StrategyConfig()

    def validate(self) -> bool:
        """Validate all configuration before running"""
        try:
            # Check critical keys exist
            assert self.trading.alpaca_api_key, "Missing Alpaca API key"
            assert self.database.database_url, "Missing database URL"

            # Validate LLM config (local or cloud)
            if self.llm.use_local:
                print(f"🤖 Using local LLM: {self.llm.ollama_model}")
            else:
                assert self.llm.openai_api_key or self.llm.anthropic_api_key, \
                    "Missing LLM API key (enable use_local=True for Ollama)"

            # Validate risk parameters are sane
            assert self.risk.max_position_size_pct <= 20, "Position size too large"
            assert self.risk.max_daily_loss_pct <= 5, "Daily loss limit too high"

            print("✅ Configuration validated successfully")
            return True

        except AssertionError as e:
            print(f"❌ Configuration validation failed: {e}")
            return False

    def is_paper_trading(self) -> bool:
        """Check if running in paper trading mode"""
        return "paper-api" in self.trading.alpaca_base_url


# Global config instance
config = AppConfig()


if __name__ == "__main__":
    # Test config loading
    print("Testing configuration...")
    config.validate()
    print(f"Paper trading: {config.is_paper_trading()}")
    print(f"Max position size: {config.risk.max_position_size_pct}%")
    print(f"Enabled strategies: {config.strategy.enabled_strategies}")
```

### File 2: `src/core/models.py`

**Data models for opportunities, trades, and positions**

```python
"""
Core data models for Atlas trading platform.
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class StrategyType(str, Enum):
    """Trading strategy types"""
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    BREAKOUT = "breakout"
    SWING = "swing"


class ConfidenceLevel(str, Enum):
    """Signal confidence levels"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class OpportunityStatus(str, Enum):
    """Opportunity processing status"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    EXPIRED = "expired"


class TradeStatus(str, Enum):
    """Trade lifecycle status"""
    PENDING = "pending"
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class TradeSide(str, Enum):
    """Trade direction"""
    LONG = "long"
    SHORT = "short"


@dataclass
class TradingOpportunity:
    """
    Represents a trading opportunity identified by Market Analysis Agent.
    """
    # Identity
    id: Optional[str] = None
    symbol: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    # Strategy
    strategy: StrategyType = StrategyType.MOMENTUM
    timeframe: str = "15m"  # 1m, 5m, 15m, 1h, 4h, 1d
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM

    # Trade parameters
    side: TradeSide = TradeSide.LONG
    entry_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0

    # Analysis
    reasoning: str = ""
    technical_signals: dict = field(default_factory=dict)
    sentiment_score: Optional[float] = None  # -1 to 1

    # Risk metrics
    risk_amount: float = 0.0  # Dollar amount at risk
    reward_amount: float = 0.0
    risk_reward_ratio: float = 0.0

    # Status
    status: OpportunityStatus = OpportunityStatus.PENDING
    rejection_reason: Optional[str] = None

    def to_formatted_string(self) -> str:
        """Format opportunity for terminal output and logs"""
        direction = "📈" if self.side == TradeSide.LONG else "📉"
        confidence_emoji = {
            ConfidenceLevel.HIGH: "🟢",
            ConfidenceLevel.MEDIUM: "🟡",
            ConfidenceLevel.LOW: "🟠"
        }

        return (
            f"{direction} {confidence_emoji[self.confidence]} "
            f"[{self.symbol}] - {self.strategy.value.title()} {self.side.value.title()} | {self.timeframe}\n"
            f"Entry: ${self.entry_price:.2f} | Stop: ${self.stop_loss:.2f} | Target: ${self.take_profit:.2f}\n"
            f"Risk: ${self.risk_amount:.2f} | Reward: ${self.reward_amount:.2f} | R:R {self.risk_reward_ratio:.1f}:1\n"
            f"Reasoning: {self.reasoning[:200]}"
        )

    def calculate_risk_reward(self):
        """Calculate risk and reward amounts"""
        if self.side == TradeSide.LONG:
            self.risk_amount = self.entry_price - self.stop_loss
            self.reward_amount = self.take_profit - self.entry_price
        else:
            self.risk_amount = self.stop_loss - self.entry_price
            self.reward_amount = self.entry_price - self.take_profit

        if self.risk_amount > 0:
            self.risk_reward_ratio = self.reward_amount / self.risk_amount
        else:
            self.risk_reward_ratio = 0.0


@dataclass
class Trade:
    """
    Represents an executed trade with full lifecycle tracking.
    """
    # Identity
    id: Optional[str] = None
    opportunity_id: Optional[str] = None
    symbol: str = ""

    # Order info
    order_id: Optional[str] = None  # Broker order ID
    side: TradeSide = TradeSide.LONG
    quantity: int = 0

    # Execution
    entry_price: float = 0.0
    entry_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None

    # Targets
    stop_loss: float = 0.0
    take_profit: float = 0.0

    # P&L
    pnl: float = 0.0
    pnl_pct: float = 0.0

    # Status
    status: TradeStatus = TradeStatus.PENDING
    exit_reason: Optional[str] = None  # "stop_hit", "target_hit", "time_based", "manual"

    # Metadata
    strategy: StrategyType = StrategyType.MOMENTUM
    reasoning: str = ""

    def calculate_pnl(self):
        """Calculate profit/loss if trade is closed"""
        if self.exit_price is None:
            return

        if self.side == TradeSide.LONG:
            self.pnl = (self.exit_price - self.entry_price) * self.quantity
            self.pnl_pct = ((self.exit_price - self.entry_price) / self.entry_price) * 100
        else:
            self.pnl = (self.entry_price - self.exit_price) * self.quantity
            self.pnl_pct = ((self.entry_price - self.exit_price) / self.entry_price) * 100

    def to_formatted_string(self) -> str:
        """Format trade for terminal output and logs"""
        if self.status == TradeStatus.OPEN:
            emoji = "🔵"
            title = "OPENED"
        elif self.pnl > 0:
            emoji = "🟢"
            title = "WIN"
        else:
            emoji = "🔴"
            title = "LOSS"

        base = (
            f"{emoji} {title}: {self.symbol} x{self.quantity} @ ${self.entry_price:.2f}\n"
            f"Stop: ${self.stop_loss:.2f} | Target: ${self.take_profit:.2f}"
        )

        if self.status == TradeStatus.CLOSED:
            base += (
                f"\nExit: ${self.exit_price:.2f} | Reason: {self.exit_reason}\n"
                f"P&L: ${self.pnl:.2f} ({self.pnl_pct:+.2f}%)"
            )

        return base


@dataclass
class Portfolio:
    """
    Current portfolio state for risk management.
    """
    total_equity: float = 0.0
    cash_available: float = 0.0
    positions_value: float = 0.0

    open_positions: list[Trade] = field(default_factory=list)
    daily_pnl: float = 0.0
    daily_trades_count: int = 0

    def utilization_pct(self) -> float:
        """Percentage of capital currently deployed"""
        if self.total_equity == 0:
            return 0.0
        return (self.positions_value / self.total_equity) * 100

    def available_for_trade(self, max_utilization_pct: float = 20.0) -> float:
        """Calculate available capital for new trades"""
        max_position_value = self.total_equity * (max_utilization_pct / 100)
        used_capital = self.positions_value
        return max(0, max_position_value - used_capital)

    def sector_exposure(self) -> dict[str, float]:
        """Calculate exposure by sector (simplified - would need sector lookup)"""
        # Placeholder - in production, map symbols to sectors
        return {}
```

---

## Phase 3: Service Layer

### File 3: `src/services/market_data.py`

**Market data fetching via Alpaca API**

```python
"""
Market data service — fetches real-time and historical market data.
"""
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from datetime import datetime, timedelta
import pandas as pd
from src.core.config import config


class MarketDataService:
    """
    Fetches market data from Alpaca API.
    """

    def __init__(self):
        self.client = StockHistoricalDataClient(
            api_key=config.trading.alpaca_api_key,
            secret_key=config.trading.alpaca_secret_key
        )

    def get_bars(
        self,
        symbol: str,
        timeframe: str = "15Min",
        lookback_days: int = 30
    ) -> pd.DataFrame:
        """
        Fetch historical bars (OHLCV data).

        Args:
            symbol: Stock ticker (e.g., "AAPL")
            timeframe: Bar size ("1Min", "5Min", "15Min", "1Hour", "1Day")
            lookback_days: How many days of history to fetch

        Returns:
            DataFrame with OHLCV data
        """
        # Map timeframe string to Alpaca TimeFrame
        timeframe_map = {
            "1Min": TimeFrame(1, TimeFrameUnit.Minute),
            "5Min": TimeFrame(5, TimeFrameUnit.Minute),
            "15Min": TimeFrame(15, TimeFrameUnit.Minute),
            "1Hour": TimeFrame(1, TimeFrameUnit.Hour),
            "1Day": TimeFrame(1, TimeFrameUnit.Day)
        }

        tf = timeframe_map.get(timeframe, TimeFrame(15, TimeFrameUnit.Minute))

        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=tf,
            start=datetime.now() - timedelta(days=lookback_days),
            end=datetime.now()
        )

        bars = self.client.get_stock_bars(request)
        df = bars.df

        # If multi-index (symbol, timestamp), flatten
        if isinstance(df.index, pd.MultiIndex):
            df = df.reset_index(level=0, drop=True)

        return df

    def get_latest_price(self, symbol: str) -> float:
        """
        Get current market price for a symbol.

        Args:
            symbol: Stock ticker

        Returns:
            Latest price (mid-point of bid/ask)
        """
        request = StockLatestQuoteRequest(symbol_or_symbols=symbol)
        quote = self.client.get_stock_latest_quote(request)

        if symbol in quote:
            q = quote[symbol]
            return (q.ask_price + q.bid_price) / 2

        return 0.0

    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add technical indicators to OHLCV dataframe.

        Args:
            df: DataFrame with OHLCV columns

        Returns:
            DataFrame with added indicator columns
        """
        # SMA
        df["SMA_20"] = df["close"].rolling(window=20).mean()
        df["SMA_50"] = df["close"].rolling(window=50).mean()
        df["SMA_200"] = df["close"].rolling(window=200).mean()

        # Bollinger Bands
        std_20 = df["close"].rolling(window=20).std()
        df["BB_Upper"] = df["SMA_20"] + (std_20 * 2)
        df["BB_Lower"] = df["SMA_20"] - (std_20 * 2)

        # RSI
        delta = df["close"].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df["RSI"] = 100 - (100 / (1 + rs))

        # MACD
        ema_12 = df["close"].ewm(span=12, adjust=False).mean()
        ema_26 = df["close"].ewm(span=26, adjust=False).mean()
        df["MACD"] = ema_12 - ema_26
        df["MACD_Signal"] = df["MACD"].ewm(span=9, adjust=False).mean()
        df["MACD_Hist"] = df["MACD"] - df["MACD_Signal"]

        # Volume moving average
        df["Volume_MA"] = df["volume"].rolling(window=20).mean()

        return df


# Example usage
if __name__ == "__main__":
    service = MarketDataService()

    # Fetch 30 days of 15-minute bars for AAPL
    df = service.get_bars("AAPL", timeframe="15Min", lookback_days=30)
    df = service.calculate_indicators(df)

    print(f"Fetched {len(df)} bars")
    print(df.tail(5)[["close", "SMA_20", "RSI", "MACD"]])

    # Get current price
    price = service.get_latest_price("AAPL")
    print(f"\nCurrent AAPL price: ${price:.2f}")
```

### File 4: `src/services/llm.py`

**LLM service for opportunity analysis (supports local Ollama)**

```python
"""
LLM service — uses local LLM (Ollama) or cloud LLMs for analysis.
"""
from src.core.config import config
from src.core.models import TradingOpportunity, StrategyType, ConfidenceLevel
import json
import requests


class LLMService:
    """
    Provides LLM-powered analysis for trading opportunities.
    Supports both local (Ollama) and cloud (OpenAI/Anthropic) LLMs.
    """

    def __init__(self):
        self.use_local = config.llm.use_local

        if self.use_local:
            # Use Ollama (local)
            self.base_url = config.llm.ollama_base_url
            self.model = config.llm.ollama_model
            print(f"🤖 Using local LLM: {self.model}")
        else:
            # Use OpenAI (cloud)
            from openai import OpenAI
            self.client = OpenAI(api_key=config.llm.openai_api_key)
            self.model = "gpt-4-turbo-preview"
            print(f"☁️  Using cloud LLM: {self.model}")

    def classify_opportunity(
        self,
        symbol: str,
        technical_data: dict,
        sentiment_data: dict = None
    ) -> TradingOpportunity:
        """
        Use LLM to classify a trading opportunity.

        Args:
            symbol: Stock ticker
            technical_data: Dict with technical indicators
            sentiment_data: Optional sentiment analysis

        Returns:
            TradingOpportunity with LLM-generated reasoning
        """
        # Build prompt with market context
        prompt = self._build_analysis_prompt(symbol, technical_data, sentiment_data)

        # Call LLM (local or cloud)
        if self.use_local:
            result = self._call_ollama(prompt)
        else:
            result = self._call_openai(prompt)

        # Parse response (already JSON)

        # Build TradingOpportunity object
        opportunity = TradingOpportunity(
            symbol=symbol,
            strategy=StrategyType(result.get("strategy", "momentum")),
            confidence=ConfidenceLevel(result.get("confidence", "medium")),
            entry_price=result.get("entry_price", 0.0),
            stop_loss=result.get("stop_loss", 0.0),
            take_profit=result.get("take_profit", 0.0),
            reasoning=result.get("reasoning", ""),
            technical_signals=technical_data
        )

        opportunity.calculate_risk_reward()

        return opportunity

    def _call_ollama(self, prompt: str) -> dict:
        """Call local Ollama LLM"""
        system_prompt = (
            "You are a professional quantitative trading analyst. "
            "Analyze market data and determine if there is a valid trading opportunity. "
            "Provide clear reasoning based on technical indicators and market context. "
            "Respond ONLY with valid JSON, no other text."
        )

        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": f"{system_prompt}\n\n{prompt}",
                "stream": False,
                "format": "json"
            }
        )

        if response.status_code == 200:
            return json.loads(response.json()["response"])
        else:
            raise Exception(f"Ollama API error: {response.status_code}")

    def _call_openai(self, prompt: str) -> dict:
        """Call OpenAI GPT-4"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a professional quantitative trading analyst. "
                        "Analyze market data and determine if there is a valid trading opportunity. "
                        "Provide clear reasoning based on technical indicators and market context. "
                        "Respond in JSON format."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=config.llm.temperature,
            max_tokens=config.llm.max_tokens,
            response_format={"type": "json_object"}
        )

        return json.loads(response.choices[0].message.content)

    def _build_analysis_prompt(
        self,
        symbol: str,
        technical_data: dict,
        sentiment_data: dict = None
    ) -> str:
        """Build detailed analysis prompt"""

        prompt = f"""Analyze the following trading opportunity for {symbol}:

TECHNICAL DATA:
- Current Price: ${technical_data.get('price', 0):.2f}
- SMA 20: ${technical_data.get('sma_20', 0):.2f}
- SMA 50: ${technical_data.get('sma_50', 0):.2f}
- RSI: {technical_data.get('rsi', 0):.1f}
- MACD: {technical_data.get('macd', 0):.2f}
- MACD Signal: {technical_data.get('macd_signal', 0):.2f}
- Volume vs Avg: {technical_data.get('volume_ratio', 0):.1f}x
- Bollinger Bands: Lower ${technical_data.get('bb_lower', 0):.2f}, Upper ${technical_data.get('bb_upper', 0):.2f}
"""

        if sentiment_data:
            prompt += f"\nSENTIMENT DATA:\n- News Sentiment: {sentiment_data.get('score', 'neutral')}\n"

        prompt += """
Based on this data, provide a JSON response with:
{
  "is_opportunity": true/false,
  "strategy": "momentum" | "mean_reversion" | "breakout" | "swing",
  "confidence": "high" | "medium" | "low",
  "entry_price": float,
  "stop_loss": float,
  "take_profit": float,
  "reasoning": "detailed explanation of why this is/isn't a good trade"
}

Consider:
1. Trend direction and strength
2. Support/resistance levels
3. Indicator confluence
4. Risk/reward ratio
5. Current market regime
"""

        return prompt


# Example usage
if __name__ == "__main__":
    service = LLMService()

    # Simulate technical data
    tech_data = {
        "price": 185.42,
        "sma_20": 183.50,
        "sma_50": 180.00,
        "rsi": 62.5,
        "macd": 2.3,
        "macd_signal": 1.8,
        "volume_ratio": 1.8,
        "bb_lower": 180.00,
        "bb_upper": 187.00
    }

    opp = service.classify_opportunity("AAPL", tech_data)
    print(opp.to_formatted_string())
```

---

## Phase 4: Agent Implementation

### File 5: `src/agents/base_agent.py`

**Base class for all agents**

```python
"""
Base agent class — shared interface for all Atlas agents.
"""
from abc import ABC, abstractmethod
from datetime import datetime
import logging
from pathlib import Path


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the Atlas system.

    All agents must implement:
    - run(): Main execution logic
    - validate(): Pre-run validation
    """

    def __init__(self, name: str, dry_run: bool = False):
        self.name = name
        self.dry_run = dry_run
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Configure agent-specific logger"""
        logger = logging.getLogger(f"atlas.{self.name}")
        logger.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            f"[%(asctime)s] [{self.name}] %(levelname)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File handler
        log_dir = Path("data/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(
            log_dir / f"{self.name}_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger

    @abstractmethod
    def run(self, *args, **kwargs):
        """
        Main agent execution logic.
        Must be implemented by all agents.
        """
        pass

    @abstractmethod
    def validate(self) -> bool:
        """
        Validate agent configuration and dependencies.
        Returns True if ready to run, False otherwise.
        """
        pass

    def log_info(self, message: str):
        """Log informational message"""
        prefix = "[DRY-RUN] " if self.dry_run else ""
        self.logger.info(f"{prefix}{message}")

    def log_warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)

    def log_error(self, message: str):
        """Log error message"""
        self.logger.error(message)

    def log_trade_action(self, action: str, details: str):
        """Log trade-related actions (special formatting)"""
        if self.dry_run:
            self.logger.info(f"[DRY-RUN] {action}: {details}")
        else:
            self.logger.info(f"🔔 {action}: {details}")
```

### File 6: `src/agents/market_analysis.py`

**Market Analysis Agent — Stage 1**

```python
"""
Market Analysis Agent — identifies trading opportunities.
"""
from src.agents.base_agent import BaseAgent
from src.services.market_data import MarketDataService
from src.services.llm import LLMService
from src.core.models import TradingOpportunity, OpportunityStatus
from typing import List
import pandas as pd


class MarketAnalysisAgent(BaseAgent):
    """
    Stage 1 Agent: Scans markets and generates trading opportunities.

    Workflow:
    1. Fetch market data for watchlist symbols
    2. Calculate technical indicators
    3. Use LLM to classify opportunities
    4. Save opportunities to queue
    """

    def __init__(self, dry_run: bool = False):
        super().__init__(name="MarketAnalysis", dry_run=dry_run)
        self.market_data = MarketDataService()
        self.llm = LLMService()

    def validate(self) -> bool:
        """Ensure services are configured"""
        try:
            # Test market data connection
            self.market_data.get_latest_price("SPY")
            self.log_info("Market data service validated ✅")

            # Test LLM connection
            # (Would ping API here in production)
            self.log_info("LLM service validated ✅")

            return True
        except Exception as e:
            self.log_error(f"Validation failed: {e}")
            return False

    def run(self, symbols: List[str]) -> List[TradingOpportunity]:
        """
        Scan symbols and generate opportunities.

        Args:
            symbols: List of ticker symbols to analyze

        Returns:
            List of TradingOpportunity objects
        """
        self.log_info(f"Scanning {len(symbols)} symbols...")

        opportunities = []

        for symbol in symbols:
            try:
                opp = self._analyze_symbol(symbol)
                if opp:
                    opportunities.append(opp)
                    self.log_info(f"Found opportunity: {symbol}")
            except Exception as e:
                self.log_error(f"Failed to analyze {symbol}: {e}")

        self.log_info(f"Found {len(opportunities)} opportunities")
        return opportunities

    def _analyze_symbol(self, symbol: str) -> TradingOpportunity | None:
        """
        Analyze a single symbol.

        Returns:
            TradingOpportunity if valid setup found, None otherwise
        """
        # Fetch data
        df = self.market_data.get_bars(symbol, timeframe="15Min", lookback_days=30)
        df = self.market_data.calculate_indicators(df)

        # Get latest values
        latest = df.iloc[-1]
        current_price = self.market_data.get_latest_price(symbol)

        # Extract technical data
        tech_data = {
            "price": current_price,
            "sma_20": latest.get("SMA_20", 0),
            "sma_50": latest.get("SMA_50", 0),
            "rsi": latest.get("RSI", 0),
            "macd": latest.get("MACD", 0),
            "macd_signal": latest.get("MACD_Signal", 0),
            "volume_ratio": latest.get("volume", 0) / latest.get("Volume_MA", 1),
            "bb_lower": latest.get("BB_Lower", 0),
            "bb_upper": latest.get("BB_Upper", 0)
        }

        # LLM classification
        opportunity = self.llm.classify_opportunity(symbol, tech_data)

        # Only return if valid setup
        if opportunity.entry_price > 0 and opportunity.risk_reward_ratio >= 1.5:
            opportunity.status = OpportunityStatus.PENDING
            return opportunity

        return None


# Example usage
if __name__ == "__main__":
    agent = MarketAnalysisAgent(dry_run=True)

    if agent.validate():
        watchlist = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN"]
        opportunities = agent.run(watchlist)

        print(f"\n{'='*60}")
        print(f"Found {len(opportunities)} opportunities:")
        print(f"{'='*60}\n")

        for opp in opportunities:
            print(opp.to_formatted_string())
            print()
```

---

## Phase 5: Pipeline Orchestration

### File 7: `src/core/pipeline.py`

**Main pipeline that orchestrates all agents**

```python
"""
Atlas Pipeline — orchestrates all agents in sequence.
"""
from src.agents.market_analysis import MarketAnalysisAgent
# from src.agents.risk_management import RiskManagementAgent  # To be built
# from src.agents.trade_execution import TradeExecutionAgent  # To be built
from src.core.config import config
from src.core.models import TradingOpportunity
from typing import List
import time


class AtlasPipeline:
    """
    Main pipeline that runs all agents in sequence.

    Flow:
    1. Market Analysis Agent → generates opportunities
    2. Risk Management Agent → approves/rejects based on portfolio risk
    3. Trade Execution Agent → executes approved trades
    """

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run

        # Initialize agents
        self.market_agent = MarketAnalysisAgent(dry_run=dry_run)
        # self.risk_agent = RiskManagementAgent(dry_run=dry_run)
        # self.execution_agent = TradeExecutionAgent(dry_run=dry_run)

    def run(self, symbols: List[str]):
        """
        Run full pipeline.

        Args:
            symbols: List of symbols to scan
        """
        print("\n" + "="*60)
        print("🚀 Atlas Trading Pipeline — Starting")
        print(f"Mode: {'DRY-RUN' if self.dry_run else 'LIVE'}")
        print(f"Symbols: {len(symbols)}")
        print("="*60 + "\n")

        start_time = time.time()

        # Stage 1: Market Analysis
        print("📊 Stage 1: Market Analysis")
        print("-" * 60)
        opportunities = self.market_agent.run(symbols)
        print(f"✅ Found {len(opportunities)} opportunities\n")

        # Stage 2: Risk Management (placeholder)
        print("🛡️  Stage 2: Risk Management")
        print("-" * 60)
        print("⚠️  Risk agent not yet implemented")
        print("   All opportunities auto-approved for demo\n")

        # Stage 3: Trade Execution (placeholder)
        print("⚡ Stage 3: Trade Execution")
        print("-" * 60)
        print("⚠️  Execution agent not yet implemented")
        print("   No trades executed (dry-run mode)\n")

        # Summary
        elapsed = time.time() - start_time
        print("="*60)
        print(f"✅ Pipeline completed in {elapsed:.2f}s")
        print(f"Opportunities identified: {len(opportunities)}")
        print("="*60 + "\n")

        return opportunities


# Example usage
if __name__ == "__main__":
    from src.core.config import config

    # Validate config first
    if not config.validate():
        print("❌ Configuration invalid, exiting")
        exit(1)

    # Run pipeline
    pipeline = AtlasPipeline(dry_run=True)

    watchlist = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA"]

    opportunities = pipeline.run(watchlist)

    # Display results
    if opportunities:
        print("\n📋 OPPORTUNITIES FOUND:\n")
        for opp in opportunities:
            print(opp.to_formatted_string())
            print("\n" + "-"*60 + "\n")
```

---

## Phase 6: Main Entry Point

### File 8: `main.py` (Updated)

**Replace existing main.py with pipeline runner**

```python
"""
Atlas Trading Platform — Main Entry Point

Usage:
    python main.py --symbols AAPL MSFT NVDA --dry-run
    python main.py --watchlist config/watchlist.txt
    python main.py --symbol AAPL --dry-run  # Single symbol test
"""
import argparse
from src.core.pipeline import AtlasPipeline
from src.core.config import config
from pathlib import Path


def load_watchlist(file_path: str) -> list[str]:
    """Load symbols from a text file (one per line)"""
    path = Path(file_path)
    if not path.exists():
        print(f"❌ Watchlist file not found: {file_path}")
        return []

    with open(path) as f:
        symbols = [line.strip().upper() for line in f if line.strip()]

    return symbols


def main():
    parser = argparse.ArgumentParser(description="Atlas Autonomous Trading Platform")

    # Symbol input options
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--symbols", nargs="+", help="List of symbols to trade")
    group.add_argument("--watchlist", help="Path to watchlist file")
    group.add_argument("--symbol", help="Single symbol (test mode)")

    # Options
    parser.add_argument("--dry-run", action="store_true", help="Run without executing real trades")
    parser.add_argument("--live", action="store_true", help="Run with real trades (requires confirmation)")

    args = parser.parse_args()

    # Determine symbols to trade
    if args.symbols:
        symbols = [s.upper() for s in args.symbols]
    elif args.watchlist:
        symbols = load_watchlist(args.watchlist)
    elif args.symbol:
        symbols = [args.symbol.upper()]
    else:
        symbols = []

    if not symbols:
        print("❌ No symbols provided")
        return

    # Safety check for live mode
    dry_run = True
    if args.live:
        if not config.is_paper_trading():
            confirm = input("⚠️  WARNING: Running in LIVE mode with real money. Type 'CONFIRM' to proceed: ")
            if confirm != "CONFIRM":
                print("❌ Live trading cancelled")
                return
        dry_run = False

    # Validate configuration
    if not config.validate():
        print("❌ Configuration validation failed")
        return

    # Run pipeline
    pipeline = AtlasPipeline(dry_run=dry_run)
    opportunities = pipeline.run(symbols)

    # Summary
    print(f"\n✅ Pipeline complete")
    print(f"Total opportunities: {len(opportunities)}")


if __name__ == "__main__":
    main()
```

---

## Phase 7: Quick Start

### Create Sample Watchlist

```bash
# config/watchlist.txt
AAPL
MSFT
NVDA
GOOGL
AMZN
META
TSLA
AMD
NFLX
COST
```

### Run Your First Test

```bash
# Activate virtual environment
source .venv/bin/activate

# Single symbol test
python main.py --symbol AAPL --dry-run

# Multiple symbols
python main.py --symbols AAPL MSFT NVDA --dry-run

# Full watchlist
python main.py --watchlist config/watchlist.txt --dry-run
```

---

## Next Steps (Planning Phase)

**This planning guide provides reference code for:**
✅ Modular architecture (`src/agents/`, `src/services/`, `src/core/`)
✅ Configuration management with environment variables
✅ Market data fetching via Alpaca
✅ Local LLM integration (Ollama) with cloud fallback
✅ Market Analysis Agent (Stage 1)
✅ Base agent class for consistency
✅ Pipeline orchestration
✅ Dry-run safety harness

**Priority components to build (in order):**

### Phase 1: Local LLM Setup
1. **Install and configure Ollama** locally
   ```bash
   # Install Ollama: https://ollama.ai
   ollama pull llama3.1:8b
   # Or: ollama pull qwen2.5:7b
   ```
2. **Test LLM service** with local model
3. **Verify cost savings** (zero API costs vs. cloud)

### Phase 2: Core Agents
1. **Risk Management Agent** (`src/agents/risk_management.py`)
   - Portfolio tracking
   - Position sizing
   - Approval/rejection logic
2. **Trade Execution Agent** (`src/agents/trade_execution.py`)
   - Alpaca order placement
   - Fill monitoring
   - P&L tracking

### Phase 3: Data & Logging
1. **Database integration** (`src/services/database.py` + SQLite)
   - Trade history
   - Signal logs
   - Performance metrics
2. **Notification system** (`src/services/notifications.py`)
   - Rich terminal output
   - Optional Discord webhook
   - Log file management

### Phase 4: Testing & Validation
1. **Position tracking** (monitor open trades)
2. **Backtesting framework** (test strategies on historical data)
3. **Paper trading validation** (30 days minimum)

See `AGENT_ARCHITECTURE.md` Section 11 for detailed week-by-week implementation roadmap.

**Remember:** This is a personal project — start simple, iterate as you learn, and keep costs low with local LLMs!

---

## Appendix A: Setting Up Local LLM with Ollama

### Why Use Local LLMs for Trading?

**Benefits:**
- ✅ **Zero API costs** — No per-token charges
- ✅ **Full privacy** — Your trading strategies never leave your machine
- ✅ **No rate limits** — Analyze as many opportunities as needed
- ✅ **Customizable** — Fine-tune models on your historical trade data
- ✅ **Offline capable** — Works without internet connection

**Trade-offs:**
- ⚠️ Requires decent hardware (8GB+ RAM, ideally GPU)
- ⚠️ Slightly slower than cloud APIs (seconds vs. milliseconds)
- ⚠️ Quality varies by model (test to find what works)

### Installation

**macOS / Linux:**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Or on macOS with Homebrew:
brew install ollama

# Start Ollama service
ollama serve  # Runs in background
```

**Windows:**
Download installer from: https://ollama.ai/download

### Recommended Models for Trading

```bash
# Llama 3.1 8B (best balance of speed and quality)
ollama pull llama3.1:8b

# Qwen 2.5 7B (excellent for structured output like JSON)
ollama pull qwen2.5:7b

# Mistral 7B (fast, good reasoning)
ollama pull mistral:7b

# For more powerful hardware (16GB+ RAM):
ollama pull llama3.1:70b  # Much better reasoning, slower
```

### Test Your Setup

```bash
# Test that Ollama is running
curl http://localhost:11434/api/tags

# Test generating a response
ollama run llama3.1:8b "Explain what a momentum trading strategy is"
```

### Update Your .env File

```bash
# .env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b
```

### Performance Tips

1. **Use smaller models for frequent analysis** (8B models)
2. **Use larger models for strategy development** (70B models)
3. **Enable GPU acceleration** if you have NVIDIA GPU:
   ```bash
   # Ollama automatically uses GPU if available
   # Verify with: nvidia-smi
   ```
4. **Set context length** for longer prompts:
   ```bash
   # In Ollama, default is 2048 tokens
   # Can increase in API calls if needed
   ```

### Switching Between Local and Cloud

The LLM service in this guide supports both. Toggle in config:

```python
# Use local Ollama (default)
config.llm.use_local = True

# Switch to OpenAI for comparison
config.llm.use_local = False
config.llm.openai_api_key = "sk-..."
```

### Troubleshooting

**"Connection refused" error:**
```bash
# Make sure Ollama is running
ollama serve

# Or check if it's already running
ps aux | grep ollama
```

**Model not found:**
```bash
# List installed models
ollama list

# Pull the model if missing
ollama pull llama3.1:8b
```

**Slow responses:**
- Use smaller models (7B/8B instead of 70B)
- Check CPU/RAM usage during generation
- Consider upgrading hardware or using cloud APIs for time-sensitive operations

---

## Appendix B: Personal Notifications Setup

Since this is a personal project, you don't need Slack. Here are lightweight alternatives:

### Option 1: Terminal Output Only (Simplest)

Already included in the code examples — just use `print()` and logging.

### Option 2: Discord Webhook (Mobile Notifications)

**Setup:**
1. Create a Discord server (free)
2. Create a webhook in Server Settings → Integrations
3. Add to `.env`:
   ```bash
   DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...
   ```

**Send notifications:**
```python
import requests

def send_discord_alert(message: str):
    webhook_url = config.notifications.discord_webhook_url
    if webhook_url:
        requests.post(webhook_url, json={"content": message})

# Usage
send_discord_alert("✅ Trade executed: AAPL +$45")
```

### Option 3: Email Alerts (For Critical Events)

**Setup SMTP (Gmail example):**
```python
import smtplib
from email.message import EmailMessage

def send_email_alert(subject: str, body: str):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = "your_email@gmail.com"
    msg['To'] = "your_email@gmail.com"
    msg.set_content(body)

    # Gmail requires app-specific password
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login("your_email@gmail.com", "your_app_password")
        smtp.send_message(msg)

# Usage
send_email_alert("Atlas Alert", "Circuit breaker triggered: -2% daily loss")
```

### Option 4: Rich Terminal UI

Use the `rich` library for beautiful console output:

```bash
pip install rich
```

```python
from rich.console import Console
from rich.table import Table

console = Console()

# Print with colors
console.print("[green]✅ Trade executed[/green]")
console.print("[red]❌ Risk limit exceeded[/red]")

# Create tables
table = Table(title="Today's Trades")
table.add_column("Symbol", style="cyan")
table.add_column("P&L", style="magenta")
table.add_row("AAPL", "+$45")
table.add_row("NVDA", "-$12")
console.print(table)
```

Choose what works best for your workflow. Most personal projects start with terminal-only and add notifications later if needed.
