import pandas as pd
import yfinance as yf


def main() -> None:
    df = yf.download("SPY", period="60d", interval="1d", progress=False)
    df = df.tail(5)
    pd.set_option("display.width", 120)
    pd.set_option("display.max_columns", 10)
    print(df[["Open", "High", "Low", "Close", "Volume"]])


if __name__ == "__main__":
    main()


