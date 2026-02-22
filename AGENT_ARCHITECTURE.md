# Project Atlas — Autonomous Algorithmic Trading Platform

*Architecture blueprint based on Project Spartan's proven agentic patterns*

---

## 1. What Problem It Solves

Manual algorithmic trading suffers from:
- **Inconsistent strategy execution** — traders manually monitor charts, miss signals, execute inconsistently
- **Scattered analysis** — technical indicators, news sentiment, risk checks happen in different tools
- **Cognitive overhead** — every trade requires manual verification of multiple data sources
- **Delayed execution** — by the time a human analyzes and acts, the opportunity window has closed
- **No institutional memory** — past trades, lessons learned, and pattern recognition are locked in human memory

**Atlas eliminates this by creating a fully autonomous trading pipeline** that analyzes markets, evaluates opportunities, manages risk, and executes trades without human intervention — just like Spartan processes tickets end-to-end.

---

## 2. How It Works End to End

Atlas runs as an autonomous pipeline with **three distinct stages**:

### Stage 1 — Market Analysis Agent

**Purpose:** Continuously scan markets and identify trading opportunities

**Workflow:**
1. Fetches real-time and historical market data from multiple sources (APIs, websockets)
2. Runs technical analysis:
   - Price action patterns (support/resistance, trends, breakouts)
   - Indicators (RSI, MACD, Bollinger Bands, volume analysis)
   - Multi-timeframe confirmation (5m, 15m, 1h, 4h, 1d)
3. Performs sentiment analysis:
   - News headlines (financial news APIs)
   - Social media sentiment (Twitter, Reddit via APIs)
   - Earnings reports and SEC filings
4. Sends each opportunity to an LLM for classification:
   - Strategy type: momentum, mean reversion, breakout, swing
   - Confidence score: high/medium/low based on confluence of signals
   - Entry/exit levels with reasoning
5. Writes opportunities to a **Trading Opportunities Queue** with standardized format:
   ```
   [SYMBOL] - [STRATEGY] | [TIMEFRAME] | Confidence: [H/M/L]
   Entry: $XX.XX | Target: $XX.XX | Stop: $XX.XX
   Reasoning: [AI-generated rationale]
   ```

### Stage 2 — Risk Management Agent

**Purpose:** Evaluate opportunities against portfolio risk limits and market conditions

**Workflow:**
1. Reads opportunities from the queue
2. Checks portfolio state:
   - Current positions and exposure
   - Available capital
   - Sector concentration
   - Correlation with existing positions
3. Evaluates market regime:
   - VIX level (volatility environment)
   - Market breadth indicators
   - Trend strength across major indices
4. Calculates position sizing:
   - Uses Kelly Criterion or fixed fractional based on confidence
   - Applies max position size limits (e.g., 5% per trade)
   - Adjusts for volatility (ATR-based stops)
5. Makes binary decision: **APPROVED** or **REJECTED**
   - If approved: forwards to execution queue with final parameters
   - If rejected: logs reason to database and Slack
6. Continuously monitors open positions for:
   - Stop loss triggers
   - Take profit targets
   - Time-based exits (holding period limits)
   - Correlation risk (if new positions create dangerous clustering)

### Stage 3 — Trade Execution Agent

**Purpose:** Execute approved trades and manage order lifecycle

**Workflow:**
1. Reads approved opportunities from execution queue
2. Checks live market conditions:
   - Current bid/ask spread
   - Available liquidity
   - Recent price movement (avoid chasing)
3. Determines order type:
   - Market order for high liquidity + urgent entry
   - Limit order for better price execution
   - Stop-limit for breakout entries
4. Places order via broker API (Alpaca, Interactive Brokers, etc.)
5. Monitors fill status:
   - Partial fills: adjust remaining size or cancel
   - No fill after N seconds: reassess or cancel
6. Updates position tracking:
   - Entry price, size, timestamp
   - Stop loss and take profit orders (OCO/bracket orders)
7. Logs trade to database and posts summary to Slack:
   ```
   ✅ EXECUTED: AAPL - Momentum Long | 15m
   Entry: $185.42 x 100 shares
   Stop: $182.50 | Target: $192.00
   Reason: Breakout above resistance + high volume + positive sentiment
   ```

---

## 3. What Systems It Connects To

### Market Data
- **Alpaca Markets API** — real-time quotes, historical bars, market status
- **Polygon.io** — high-frequency tick data and news
- **Yahoo Finance / Stooq** — backup data source (already integrated)
- **TradingView WebSocket** — real-time chart data

### Broker / Execution
- **Alpaca Trading API** — commission-free equity trading, paper trading mode
- **Interactive Brokers TWS API** — for advanced order types and futures
- **TDAmeritrade API** — alternative execution venue

### Sentiment & News
- **NewsAPI** — financial news headlines with sentiment scoring
- **Twitter API** — real-time social sentiment (via keywords like $TICKER)
- **Reddit API (PRAW)** — r/wallstreetbets, r/stocks, r/algotrading sentiment
- **Alpha Vantage News Sentiment API** — aggregated sentiment scores

### Risk & Market Regime
- **CBOE VIX API** — volatility index for market regime detection
- **FRED API** — economic indicators (interest rates, GDP, unemployment)
- **Portfolio tracking database** — PostgreSQL or MongoDB

### Communication & Logging
- **Slack API** — real-time trade notifications, performance summaries, error alerts
- **PostgreSQL / TimescaleDB** — trade history, performance metrics, signal logs
- **Grafana** — real-time dashboard for portfolio health, win rate, P&L

### AI / LLM
- **OpenAI API** — GPT-4 for opportunity classification, reasoning, report generation
- **Anthropic API (Claude)** — alternative LLM for strategy reasoning
- **Local LLM (Ollama)** — cost-effective alternative for high-frequency analysis

---

## 4. Current Status (Starting Point)

**Already built:**
- Basic market data fetching (Stooq via pandas-datareader)
- Technical indicators (SMA, Bollinger Bands)
- Plotly chart visualization
- Python foundation (pandas, numpy)

**Next to build (Phase 1 - Core Pipeline):**
- [ ] Modular architecture: `src/agents/`, `src/services/`, `src/core/`
- [ ] Market Analysis Agent with LLM integration
- [ ] Risk Management Agent with portfolio tracking
- [ ] Trade Execution Agent with paper trading (Alpaca sandbox)
- [ ] PostgreSQL database for opportunity and trade logging
- [ ] Slack integration for notifications
- [ ] Single-symbol test mode (`--symbol AAPL --dry-run`)

**Phase 2 — Production Hardening:**
- [ ] Multi-symbol scanning (S&P 500, NASDAQ 100, custom watchlists)
- [ ] WebSocket real-time data feeds
- [ ] Advanced risk controls (correlation matrix, VAR, max drawdown circuit breaker)
- [ ] Backtesting framework against historical data
- [ ] Performance analytics dashboard (Grafana + TimescaleDB)

**Phase 3 — Autonomous Operation:**
- [ ] Deploy to Google Cloud Run / AWS Lambda
- [ ] Event-driven triggers (market open, price alerts, news events)
- [ ] Self-healing: automatically pause on anomalies (flash crash, API outages)
- [ ] Strategy optimization: LLM analyzes closed trades and suggests parameter tuning

**Phase 4 — Advanced Intelligence:**
- [ ] Multi-agent orchestration (specialist agents per strategy type)
- [ ] Reinforcement learning layer (learns from wins/losses over time)
- [ ] Cross-asset correlation (equities + options + crypto)
- [ ] Automated report generation: daily summaries written by AI

---

## 5. Architecture — Modular Design

Following Spartan's proven structure:

```
algoTrading/
├── src/
│   ├── agents/
│   │   ├── market_analysis.py      # Stage 1: Scans markets, generates signals
│   │   ├── risk_management.py      # Stage 2: Portfolio risk evaluation
│   │   ├── trade_execution.py      # Stage 3: Order placement and management
│   │   └── base_agent.py           # Shared agent interface
│   │
│   ├── services/
│   │   ├── market_data.py          # Alpaca, Polygon, Yahoo Finance clients
│   │   ├── broker.py               # Alpaca Trading API wrapper
│   │   ├── news_sentiment.py      # NewsAPI, Twitter, Reddit sentiment
│   │   ├── database.py             # PostgreSQL connection and models
│   │   ├── slack.py                # Slack notifications
│   │   └── llm.py                  # OpenAI/Anthropic client wrapper
│   │
│   ├── core/
│   │   ├── config.py               # Environment variables, API keys
│   │   ├── pipeline.py             # Orchestrates agent workflow
│   │   ├── models.py               # Data models (Opportunity, Trade, Position)
│   │   └── utils.py                # Shared utilities
│   │
│   └── strategies/
│       ├── momentum.py             # Momentum strategy logic
│       ├── mean_reversion.py       # Mean reversion strategy logic
│       └── breakout.py             # Breakout strategy logic
│
├── tests/
│   ├── test_agents.py
│   ├── test_services.py
│   └── test_strategies.py
│
├── scripts/
│   ├── run_single_symbol.py       # Test mode: analyze one symbol
│   ├── deploy.py                   # Cloud deployment script
│   └── backtest.py                 # Historical simulation
│
├── config/
│   ├── symbols.yaml                # Watchlist configuration
│   ├── risk_limits.yaml            # Risk parameters
│   └── strategies.yaml             # Active strategies and their params
│
├── main.py                         # Entry point: runs full pipeline
├── requirements.txt
├── .env.example                    # API keys template
└── README.md
```

### Key Design Principles (Borrowed from Spartan)

1. **Dry-run safety harness** — all agents support `--dry-run` flag for testing without live trades
2. **Idempotency** — agents can safely retry failed operations
3. **Service abstraction** — swappable data sources (easy to switch from Alpaca to IBKR)
4. **LLM-augmented decisions** — use AI for reasoning, not just rule-based signals
5. **Comprehensive logging** — every opportunity, decision, and trade is logged with full reasoning
6. **Slack as the source of truth** — human oversight without blocking automation

---

## 6. Example Flow — End to End

**9:30 AM — Market Opens**

1. **Market Analysis Agent** wakes up (scheduled trigger)
   - Scans 500 symbols from watchlist
   - Detects: `NVDA breaking above $890 with high volume + bullish MACD crossover`
   - LLM classifies: `[NVDA] - Momentum Long | 15m | Confidence: HIGH`
   - Writes opportunity to queue

2. **Risk Management Agent** reads queue (runs every 30 seconds)
   - Checks portfolio: $50,000 total, $10,000 currently deployed (20% utilization)
   - Checks sector exposure: Tech is 30% of portfolio (within 40% limit)
   - Checks NVDA correlation with existing positions: Low (only 0.3 with TSLA)
   - Calculates position size: $2,500 (5% of portfolio) = ~2.8 shares at $890
   - Decision: **APPROVED** ✅
   - Forwards to execution queue with parameters

3. **Trade Execution Agent** receives approved opportunity
   - Checks current NVDA price: Bid $889.50 / Ask $890.10
   - Places limit order: Buy 2 shares @ $890.00 (split the spread)
   - Order fills immediately
   - Places bracket order: Stop @ $882 (-0.9% / $16 risk) | Target @ $910 (+2.2% / $40 reward)
   - Posts to Slack:
     ```
     ✅ LONG NVDA x2 @ $890.00 | 15m Momentum
     Stop: $882 | Target: $910 | Risk: $16 | Reward: $40 | R:R 2.5:1
     Reason: Breakout above resistance + volume spike + bullish MACD + strong sector
     ```

**11:15 AM — Target Hit**

- Execution Agent monitors position
- NVDA hits $910.00
- Take profit order executes automatically
- P&L: +$40 (2.2% gain)
- Logs to database, posts update to Slack:
  ```
  🎯 CLOSED: NVDA x2 @ $910.00 | +$40 (+2.2%)
  Hold time: 1h 45m | Exit reason: Target reached
  ```

**End of Day — Daily Summary**

- Pipeline generates summary report (LLM-written):
  ```
  📊 Daily Performance Summary — Feb 22, 2026

  Trades: 8 executed | 6 wins, 2 losses | 75% win rate
  P&L: +$340 (+0.68% portfolio) | Best: NVDA +$40 | Worst: AMD -$25
  Opportunities scanned: 1,240 | Approved: 12 | Rejected: 8 (6 risk limits, 2 correlation)

  Market regime: Moderate volatility (VIX 16.5) | Trend: Bullish (SPY +0.4%)
  Top signals: Momentum (5 trades), Breakout (2), Mean reversion (1)

  Notes: Tech sector outperformed. Rejected 2 trades due to portfolio tech concentration.
  ```

---

## 7. Metrics and Expected Performance

Based on Spartan's production learnings, expected Atlas performance:

### Time Savings
- **Manual monitoring time eliminated:** ~4-6 hours/day of chart watching
- **Analysis paralysis removed:** Decisions made in milliseconds vs. minutes
- **Opportunity capture rate:** 100% of signals within operating hours (vs. ~30% when human has to manually act)

### Trading Metrics (Target)
- **Win rate:** 55-65% (typical for quantitative strategies)
- **Average R:R:** 1.5:1 to 2:1 (risk $100 to make $150-200)
- **Max drawdown:** < 10% (enforced by risk agent circuit breaker)
- **Sharpe ratio:** > 1.5 (risk-adjusted returns)
- **Trades per day:** 5-15 (depends on market conditions)

### System Reliability
- **Uptime:** 99.5%+ (with cloud deployment and health checks)
- **Missed opportunities:** < 2% (due to API latency, order rejections)
- **False positive rate:** < 20% (opportunities that get rejected by risk agent)

### Consistency Improvements
- **100% of trades follow risk rules** (vs. emotional overrides in manual trading)
- **Every trade has documented reasoning** (vs. "gut feel" decisions)
- **Complete audit trail** (regulatory compliance ready)

---

## 8. Vision — Where It Goes Next

### Near Term (4-6 weeks)
- **Deploy to Google Cloud Run** — Atlas becomes always-on, not a script you run manually
- **Paper trading validation** — run on Alpaca paper account, prove profitability over 30+ days
- **Multi-strategy portfolio** — run momentum, mean reversion, and breakout agents in parallel
- **Real-time dashboards** — Grafana visualization of live positions, P&L, signals

### Medium Term (Q2-Q3 2026)
- **Go live with real capital** — transition from paper to small live account ($5K-10K)
- **Options trading layer** — add agent for covered calls, cash-secured puts, spreads
- **Reinforcement learning** — agent learns from wins/losses, adjusts parameters autonomously
- **Cross-asset expansion** — add crypto trading (Bitcoin, Ethereum) via Coinbase API

### Long Term (2026+)
- **Multi-agent specialist teams** — dedicated agents per asset class (equities, options, crypto, futures)
- **Self-improving strategies** — Atlas analyzes closed trades, updates strategy parameters, generates new strategy ideas
- **Institutional knowledge loop** — every trade becomes training data; system compounds intelligence over time
- **Portfolio management as a service** — Atlas manages multiple accounts with different risk profiles

---

## 9. What Makes Atlas Different From Manual Trading With AI

This is the critical distinction — same as with Spartan:

**Using Claude or ChatGPT manually** means:
- Human opens a chart
- Human asks AI "Should I buy NVDA?"
- AI responds with analysis
- Human manually places order (or doesn't)
- Human has to remember to check back later

**That's still human-in-the-loop.** You're using AI as a tool, but you're still the operator.

**Atlas is autonomous infrastructure:**
- Runs 24/7 without attention
- Scans hundreds of symbols continuously
- Makes decisions and executes trades independently
- Learns from outcomes and adjusts
- Only alerts you for exceptions or daily summaries

**The difference:**
- **Tool you use** vs. **system that works for you**
- **Manual intervention** vs. **autonomous operation**
- **One-off insights** vs. **compounding intelligence**

Just like Spartan processes tickets whether or not an engineer is at their desk, **Atlas trades whether or not you're watching the market.**

And just like Spartan's data quality improves over time, **Atlas's trading performance compounds** — every trade adds to the dataset, making risk models more accurate and strategy signals more refined.

---

## 10. Risk Disclaimers & Ethical Considerations

**This is a blueprint for educational and experimental purposes.**

Before deploying Atlas with real capital:

1. **Start with paper trading** — validate profitability over 30+ days minimum
2. **Understand the code completely** — don't run autonomous trading systems you don't understand
3. **Regulatory compliance** — ensure compliance with SEC rules, pattern day trader requirements, etc.
4. **Risk management is critical** — wrong implementation can lead to catastrophic losses
5. **Market risk remains** — no system eliminates market risk; flash crashes, black swans, and system failures happen
6. **API and broker reliability** — your system depends on third-party infrastructure
7. **Tax implications** — frequent trading has tax consequences (short-term capital gains)

**Atlas should augment your trading, not replace your judgment.**

Even with autonomous operation, maintain:
- Daily review of trades and decisions
- Weekly performance analysis
- Manual override capability (kill switch)
- Position size limits appropriate for your risk tolerance
- Continuous monitoring of system logs and errors

**This is infrastructure, not a money printer.** Treat it with the same care and rigor you'd apply to any production system that manages real financial assets.

---

## 11. Getting Started — Implementation Roadmap

### Week 1: Foundation
- [ ] Set up modular architecture (`src/agents/`, `src/services/`, `src/core/`)
- [ ] Create config management (`.env`, `config.py`)
- [ ] Set up PostgreSQL database schema
- [ ] Integrate Alpaca API (paper trading account)
- [ ] Build basic Market Analysis Agent (single symbol, technical indicators only)

### Week 2: Pipeline Integration
- [ ] Build Risk Management Agent (simple position sizing)
- [ ] Build Trade Execution Agent (market orders only)
- [ ] Connect agents in pipeline (`pipeline.py`)
- [ ] Add Slack notifications
- [ ] Test end-to-end with `--dry-run` flag

### Week 3: Intelligence Layer
- [ ] Integrate OpenAI API for opportunity classification
- [ ] Add sentiment analysis (NewsAPI)
- [ ] Implement multi-timeframe analysis
- [ ] Add strategy reasoning to trade logs

### Week 4: Production Hardening
- [ ] Add comprehensive error handling and retries
- [ ] Implement circuit breakers (max daily loss, API failures)
- [ ] Set up logging and monitoring
- [ ] Run paper trading for 1 week, analyze results
- [ ] Document learnings and refine parameters

### Weeks 5-8: Scaling & Optimization
- [ ] Expand to multi-symbol scanning (10-50 symbols)
- [ ] Add WebSocket real-time feeds
- [ ] Build backtesting framework
- [ ] Deploy to cloud (Google Cloud Run or AWS Lambda)
- [ ] Continue paper trading, iterate based on performance

### Month 3+: Live Trading (If Validated)
- [ ] Audit all code for bugs and edge cases
- [ ] Start with tiny position sizes (1-2 shares)
- [ ] Monitor closely for 2 weeks
- [ ] Gradually increase capital allocation if performance holds

---

## 12. Key Files to Build (Priority Order)

1. **src/core/config.py** — Environment variables, API keys
2. **src/services/market_data.py** — Alpaca data client
3. **src/services/broker.py** — Alpaca trading client
4. **src/agents/base_agent.py** — Shared agent interface
5. **src/agents/market_analysis.py** — Signal generation
6. **src/agents/risk_management.py** — Position sizing and approval
7. **src/agents/trade_execution.py** — Order placement
8. **src/core/pipeline.py** — Orchestration logic
9. **src/services/database.py** — PostgreSQL models
10. **src/services/slack.py** — Notifications
11. **main.py** — Entry point with CLI args
12. **tests/** — Unit tests for each component

---

## 13. Technology Stack Recommendations

### Core Languages & Frameworks
- **Python 3.11+** — Main language (already in use)
- **FastAPI** — If building a REST API for remote control
- **Celery + Redis** — For task queue and scheduling (alternative to simple loops)

### Data & Database
- **PostgreSQL** — Trade history, positions, signals
- **TimescaleDB** — Time-series extension for tick data
- **Redis** — Caching market data, opportunity queue

### Market Data & Trading
- **Alpaca Markets API** — Primary (commission-free, great API, paper trading)
- **Polygon.io** — Alternative for data (Alpaca includes it)
- **ccxt** — If expanding to crypto (unified exchange API)

### AI / LLM
- **OpenAI Python SDK** — GPT-4 for reasoning
- **LangChain** — If building complex LLM workflows
- **Ollama + Llama 3** — Cost-effective local alternative

### Monitoring & Alerting
- **Slack API** — Real-time notifications
- **Grafana + Prometheus** — Dashboards and metrics
- **Sentry** — Error tracking and alerting

### Deployment
- **Docker** — Containerization
- **Google Cloud Run** — Serverless deployment (cost-effective)
- **AWS Lambda + EventBridge** — Alternative serverless option
- **GitHub Actions** — CI/CD pipeline

### Already Installed (Keep Using)
- `pandas`, `numpy` — Data manipulation
- `plotly` — Visualization (useful for backtesting reports)
- `yfinance`, `pandas-datareader` — Backup data sources

---

## 14. Success Criteria — How You'll Know Atlas Works

After 30 days of paper trading, Atlas should demonstrate:

✅ **Operational Excellence**
- 99%+ uptime (no crashes, handles API errors gracefully)
- 100% of trades logged with reasoning
- No missed opportunities due to system errors
- All risk limits respected (no overtrading)

✅ **Trading Performance**
- Positive net P&L (even small gains prove the concept)
- Win rate > 50%
- Average winner > average loser (R:R ratio > 1:1)
- Max drawdown < 10%

✅ **Intelligence Quality**
- LLM reasoning is coherent and aligns with market reality
- Rejected trades (by risk agent) were correct decisions in hindsight
- No obvious signal quality issues (false breakouts, whipsaws)

✅ **Compounding Improvements**
- Week 4 performance > Week 1 (learning from data)
- Strategy parameters self-adjusted based on market regime
- Clear improvement in signal quality over time

If these criteria are met, Atlas is ready for **micro-live testing** (1-share trades with real money).

If not, iterate on:
- Signal quality (better indicators, timeframe selection)
- Risk management (tighter stops, better position sizing)
- Execution quality (limit orders vs. market, slippage control)

---

## 15. Final Thoughts — Why This Matters

Spartan saves **2-4 hours per week** by automating ticket triage.

Atlas can save **20-30 hours per week** by automating:
- Market monitoring and analysis
- Trade execution and management
- Risk compliance and position tracking
- Performance reporting and strategy optimization

But more importantly, **Atlas doesn't get tired, emotional, or distracted.**

It doesn't:
- Skip a setup because it "doesn't feel right"
- Hold a losing trade too long due to hope
- Revenge trade after a loss
- Miss an opportunity because it's lunchtime

**It executes the strategy exactly as designed, every single time.**

That's the power of agentic infrastructure.

Spartan turned ticket triage from a manual chore into background infrastructure.

**Atlas turns active trading into autonomous infrastructure.**

---

**Next Steps:** Ready to start building? See `IMPLEMENTATION_GUIDE.md` for step-by-step code examples and setup instructions.
