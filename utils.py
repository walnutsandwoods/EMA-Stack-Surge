import yfinance as yf
import pandas as pd
import pandas_ta as ta
import os

def get_stock_list(file_path='watchlist.txt'):
    """Reads a list of stock symbols from a text file."""
    # Construct path relative to this script's location
    script_dir = os.path.dirname(__file__)
    absolute_file_path = os.path.join(script_dir, file_path)

    with open(absolute_file_path, 'r') as f:
        stocks = [line.strip() for line in f.readlines()]
    return stocks

def get_stock_data(ticker, interval='5m', period='1d'):
    """Fetches stock data for a given ticker and timeframe."""
    stock = yf.Ticker(ticker)
    data = stock.history(period=period, interval=interval)
    return data

def calculate_indicators(df, timeframe):
    """
    Calculates technical indicators for a given DataFrame.
    """
    if timeframe == '5m':
        rsi_period = 7
        macd_fast = 12
        macd_slow = 26
        macd_signal = 9
    elif timeframe == '1h':
        rsi_period = 9
        macd_fast = 48
        macd_slow = 104
        macd_signal = 36
    else:
        raise ValueError("Invalid timeframe specified. Must be '5m' or '1h'.")

    # EMAs
    df.ta.ema(length=5, append=True)
    df.ta.ema(length=9, append=True)
    df.ta.ema(length=21, append=True)

    # RSI
    df.ta.rsi(length=rsi_period, append=True)

    # Volume
    df.ta.sma(close=df['Volume'], length=20, append=True)
    df.rename(columns={'SMA_20': 'VMA_20'}, inplace=True)

    # MACD
    df.ta.macd(fast=macd_fast, slow=macd_slow, signal=macd_signal, append=True)

    # ATR
    df.ta.atr(length=14, append=True)

    return df

if __name__ == '__main__':
    # Test the functions
    stocks = get_stock_list()
    print(f"Loaded {len(stocks)} stocks: {stocks}")

    sample_stock = 'RELIANCE.NS'
    print(f"\\nFetching 5m data for {sample_stock}...")
    data_5m = get_stock_data(sample_stock, interval='5m', period='5d')
    if not data_5m.empty:
        data_5m_with_indicators = calculate_indicators(data_5m.copy(), '5m')
        print(data_5m_with_indicators.tail())
    else:
        print("No 5m data returned.")

    print(f"\\nFetching 1h data for {sample_stock}...")
    data_1h = get_stock_data(sample_stock, interval='1h', period='1mo')
    if not data_1h.empty:
        data_1h_with_indicators = calculate_indicators(data_1h.copy(), '1h')
        print(data_1h_with_indicators.tail())
    else:
        print("No 1h data returned.")
