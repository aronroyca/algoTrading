import pandas as pd
from pandas_datareader import data as pdr


def main() -> None:
    # Stooq uses ticker format like 'SPY'
    df = pdr.DataReader("SPY", data_source="stooq")
    # Stooq returns most-recent-first; reverse to chronological
    df = df.sort_index()
    # Add a small 20-day SMA on Close
    df["SMA20"] = df["Close"].rolling(window=20, min_periods=1).mean()
    df = df.tail(5)
    pd.set_option("display.width", 120)
    pd.set_option("display.max_columns", 10)
    print(df[["Open", "High", "Low", "Close", "Volume", "SMA20"]])


if __name__ == "__main__":
    main()


