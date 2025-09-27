import pandas as pd
import plotly.graph_objects as go
from pandas_datareader import data as pdr


def main() -> None:
    # Stooq uses ticker format like 'SPY'
    df = pdr.DataReader("SOUN", data_source="stooq")
    # Stooq returns most-recent-first; reverse to chronological
    df = df.sort_index()
    # Add a small 20-day SMA on Close
    df["SMA20"] = df["Close"].rolling(window=20, min_periods=1).mean()
    
    # Add Bollinger Bands (20-day, 2 standard deviations)
    rolling_std = df["Close"].rolling(window=20, min_periods=1).std()
    df["BB_Upper"] = df["SMA20"] + (rolling_std * 2)
    df["BB_Lower"] = df["SMA20"] - (rolling_std * 2)
    
    # Show last 10 rows in table, but use all data for chart
    df_display = df.tail(10)
    pd.set_option("display.width", 120)
    pd.set_option("display.max_columns", 10)
    print(f"Data points: {len(df)} days")
    print(df_display[["Open", "High", "Low", "Close", "Volume", "SMA20", "BB_Upper", "BB_Lower"]])
    
    # Create interactive chart
    fig = go.Figure()
    
    # Add candlestick chart
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'],
        high=df['High'],
        low=df['Low'],
        close=df['Close'],
        name='Price'
    ))
    
    # Add SMA20 line
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['SMA20'],
        mode='lines',
        name='SMA20',
        line=dict(color='blue', width=2)
    ))
    
    # Add Bollinger Bands
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['BB_Upper'],
        mode='lines',
        name='BB Upper',
        line=dict(color='red', width=2)
    ))
    
    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['BB_Lower'],
        mode='lines',
        name='BB Lower',
        line=dict(color='red', width=2)
    ))
    
    fig.update_layout(
        title=f'SOUN with Bollinger Bands ({len(df)} days)',
        xaxis_title='Date',
        yaxis_title='Price',
        height=600,
        showlegend=True
    )
    
    # Save as HTML file
    fig.write_html('chart.html')
    print("\nChart saved as 'chart.html' - open in your browser!")


if __name__ == "__main__":
    main()


