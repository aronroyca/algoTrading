# algoTrading
Python Algorithmic Trading Project

## Quick start

1. Create and activate a virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Run the demo script (fetch last 5 SPY daily OHLCV rows via Stooq)
```bash
python main.py
```

If your shell session is new, activate the venv first:
```bash
source .venv/bin/activate
```

## Notes
- Data source: Stooq via pandas-datareader (no API key required).
- Tested with Python 3.13.
- Now includes Bollinger Bands and SMA20 indicators.
